#!/usr/bin/env python3
"""GORCH 多通道薄编排（只接线，不含判断算法）。

判断逻辑全部来自成熟件，本文件不重写任何一个：
  开工前判定（依赖/冲突）→ ccpm lib.sh 的 unmet_deps / active_conflicts
                           （原文复制于 automazeio/ccpm，哈希一致，未改一字）
  worktree 隔离 / 合并 / 清理 → worktrunk 的 wt.exe（switch/merge/remove）
  写码执行                 → scripts/gorch/codex_channel.py（已落地，真跑通过）

本文件只做：遍历任务、调用上述现成件、传递参数、记录结构化结果。
“能不能开工”的判定发生在 ccpm 函数内部；这里只把它的输出做空/非空映射。
若现成件覆盖不了，直接报错退出并报 Owner，不临时发明算法。

用法：
  python batch_orchestrator.py gate <批次目录>
  python batch_orchestrator.py provision <批次目录>
  python batch_orchestrator.py execute <批次目录> --prompts-dir <prompt目录>
  python batch_orchestrator.py merge <批次目录> [--tasks T1 T2]
  python batch_orchestrator.py cleanup <批次目录> [--tasks T1] [--force]
批次目录约定：只放任务文件，每个 <id>.md 带 frontmatter
  name/status/depends_on/parallel/conflicts_with，同目录引用 <ref>.md。
provision 先跑 gate，仅对判定“可开工”的任务调 wt 建独立 worktree（幂等）。
execute 对可开工任务并发调 codex_channel（--workdir 指向各自 worktree），
执行逻辑全在 codex_channel 内，本文件只做 fan-out/join 与 fail-closed 校验。
merge 只合“run 记录 result=done”的任务，逐个串行调 wt merge；任一失败即停。
cleanup 调 wt remove 清残留 worktree/分支，脏目录需显式 --force。
"""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys
from datetime import datetime, timezone

# 状态词适配层在同目录；按文件路径注入 sys.path，避免依赖启动方式。
_GORCH_DIR = pathlib.Path(__file__).resolve().parent
if str(_GORCH_DIR) not in sys.path:
    sys.path.insert(0, str(_GORCH_DIR))

import status_map  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CCPM_DIR = ROOT / 'scripts' / 'gorch' / 'ccpm'
BASH = r'C:\Program Files\Git\bin\bash.exe'
WT_EXE = r'H:\UltimaAI\_vendor\worktrunk-bin\wt.exe'
GIT_CMD_DIR = r'C:\Program Files\Git\cmd'
BASH_TIMEOUT = 60
# 工单 frontmatter 允许的状态词：由 status_map 单处维护，不在此手写第二份。
# ccpm 的 lib.sh 仍是判定权威；这里只收敛入参，不产生任何判定。
VALID_STATUSES = frozenset(status_map.STATUS_WORDS)
# 并发 worktree 集中根目录（仓库外，避免与历史 ~/.codex/worktrees 混淆）。
WORKTREE_ROOT = pathlib.Path(r'H:\UltimaAI\_worktrees\gorch')
WT_TIMEOUT = 180
# wt merge 比 switch 慢得多：它要在源 worktree 里 commit/squash、再 rebase 到主线。
# 本仓库有 32 万+ 未跟踪文件（data/evidence/），单次 git status 就要 90s+，
# 合并实测会超过 180s。用独立的更长预算，避免把"还在干活"误判成"卡住"。
MERGE_TIMEOUT = 600
GIT_EXE = str(pathlib.Path(GIT_CMD_DIR) / 'git.exe')
# 子进程一律不建控制台窗口：bash / wt / git 每次被调用都会创建 conhost，
# 派发一批要跑十几次，否则屏幕上会连续闪黑窗（L78）。
_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0
BRANCH_PREFIX = 'gorch/'
# 只把 git-bash/cygwin 的 fork 噪声降级为诊断；其余 stderr 一律当错误看。
# 噪声特征：fork 重试、cygheap 读写失败、dofork 死亡，以及 cygwin 的 "123 [main] xxx" 前缀行。
# 第四轮审计：原来按关键词**子串**匹配，会把「真实错误里恰好含 cygheap /
# Resource temporarily unavailable」整行降级成噪声。改成锚定 cygwin / bash 的
# 整行格式，只有行首形态对上才放行，其余（含未知形态）继续 fail-closed。
_CYGWIN_NOISE = re.compile(
    r'^\s*\d+\s*\[main\]'                        # 123 [main] bash 4567 fork: retry: ...
    r'|^\s*bash:\s*(child_copy|dofork|fork)'     # bash: child_copy: / dofork: / fork: ...
    r'|^\s*\S+:\s*fork: retry:',                 # foo: fork: retry: Resource temporarily unavailable
    re.IGNORECASE)
# 执行段是现成件（codex_channel.py），本编排只负责并发调用它，不重写执行逻辑。
CHANNEL_SCRIPT = ROOT / 'scripts' / 'gorch' / 'codex_channel.py'
MAX_CHANNELS = 3
# 执行记录目录：merge 阶段据此确认某任务“真的执行完成”，不凭人工记忆。
RUNS = ROOT / 'data' / 'gorch' / 'runs'
# A（审议链）→ B（执行链）的交接证据目录名，放在批次目录内，不参与 gate 扫描。
HANDOFF_DIRNAME = '_handoff'


def to_bash(path):
    """Windows 绝对路径 → git bash 路径（仅格式转换，非业务判断）。"""
    p = str(pathlib.Path(path).resolve())
    if len(p) >= 2 and p[1] == ':':
        return '/' + p[0].lower() + p[2:].replace('\\', '/')
    return p.replace('\\', '/')


def gate_check(batch_dir):
    """对每个任务调 ccpm 原函数，结构化返回判定。判断逻辑在 ccpm 内。"""
    batch_dir = pathlib.Path(batch_dir)
    if not batch_dir.is_dir():
        raise SystemExit(f'批次目录不存在: {batch_dir}')
    tasks = sorted(p for p in batch_dir.glob('*.md') if p.is_file())
    if not tasks:
        raise SystemExit(f'批次目录下没有任务 .md: {batch_dir}')

    lib = to_bash(CCPM_DIR / 'lib.sh')
    rows = []
    for task in tasks:
        tb = to_bash(task)
        # 直接调用 ccpm 的三个原函数；本脚本不解析 next.sh 的人类可读表格。
        # 对齐 next.sh 的 ready 三条件：status=open、unmet_deps 空、active_conflicts 空。
        script = (
            # 三个函数先各自赋值并显式传递失败：`printf "$(f)"` 里命令替换的失败码
            # 不会传出来，函数内部报错（如 grep: Permission denied）会被外层 printf
            # 吞掉，最终凑出「rc=0 + 三标记齐全 + CONFLICTS 空」，把有冲突的卡判成
            # 可开工。审计（2026-11-09 第二轮）实测复现过这条 fail-open。
            "set -o pipefail; "
            f"source '{lib}'; "
            f"status=$(frontmatter_field '{tb}' status) || exit 71; "
            f"unmet=$(unmet_deps '{tb}') || exit 72; "
            f"conflicts=$(active_conflicts '{tb}') || exit 73; "
            "printf 'STATUS:%s\\n' \"$status\"; "
            "printf 'UNMET:%s\\n' \"$unmet\"; "
            "printf 'CONFLICTS:%s\\n' \"$conflicts\""
        )
        try:
            r = subprocess.run([BASH, '-c', script], capture_output=True,
                               text=True, encoding='utf-8', errors='replace',
                               timeout=BASH_TIMEOUT, creationflags=_NO_WINDOW)
        except subprocess.TimeoutExpired:
            raise SystemExit(
                f'ccpm 判定超时 {task.name}（{BASH_TIMEOUT}s），fail-closed 不派发')
        if r.returncode != 0:
            raise SystemExit(
                f'ccpm 判定失败 {task.name}: rc={r.returncode} {r.stderr.strip()}')
        # stderr 双向判定（L77 + 第二轮审计）：只放行 git-bash/cygwin 的 fork 噪声，
        # 其余一律 fail-closed。单纯"stderr 非空即拒"会把一次噪声放大成整批拒派；
        # 单纯"一律忽略"又会放过真错误（Permission denied / No such file 之类），
        # 让坏判定凑成"三标记齐全"被放行。两头都得堵。
        # 第四轮审计：先全量逐行分类，再截断展示。此前只取前 200 字符，
        # 「噪声在前、真错误在后」的组合会让真错误整体不可见。
        raw_err = r.stderr or ''
        real_errs = [ln.strip() for ln in raw_err.splitlines()
                     if ln.strip() and not _CYGWIN_NOISE.match(ln)]
        stderr_diag = raw_err.strip()[-400:]
        if real_errs:
            # 只贴第一行会把"垃圾行在前、真错误在后"的情况又遮住一次，所以拼前 3 行。
            detail = ' | '.join(x[:120] for x in real_errs[:3])
            raise SystemExit(
                f'ccpm 判定出现错误输出 {task.name}: {detail}'
                + (f'（共 {len(real_errs)} 行真错误）' if len(real_errs) > 1 else ''))

        seen = {}
        status = ''
        unmet, conflicts = [], []
        extra = []
        for line in r.stdout.splitlines():
            s = line.strip()
            if not s:
                continue
            if s.startswith('STATUS:'):
                status = s[len('STATUS:'):].strip()
                seen['STATUS'] = seen.get('STATUS', 0) + 1
            elif s.startswith('UNMET:'):
                unmet = s[len('UNMET:'):].split()
                seen['UNMET'] = seen.get('UNMET', 0) + 1
            elif s.startswith('CONFLICTS:'):
                conflicts = s[len('CONFLICTS:'):].split()
                seen['CONFLICTS'] = seen.get('CONFLICTS', 0) + 1
            else:
                extra.append(s)

        # fail-closed：三标记必须**各出现且仅一次**，stdout 不得夹带其他行。
        # 只要求"出现过"时，重复的 STATUS 以后者覆盖前者（末行生效）、多余行被
        # 静默忽略——多打一行就能改写判定（第三轮审计 A3）。
        missing = {'STATUS', 'UNMET', 'CONFLICTS'} - set(seen)
        if missing:
            raise SystemExit(
                f'ccpm 输出不完整 {task.name}: 缺 {sorted(missing)}，fail-closed 不派发')
        dup = sorted(k for k, v in seen.items() if v > 1)
        if dup:
            raise SystemExit(
                f'ccpm 输出重复 {task.name}: {dup} 出现多次，fail-closed 不派发')
        if extra:
            raise SystemExit(
                f'ccpm 输出含多余行 {task.name}: {extra[0][:120]}，fail-closed 不派发')
        canon = status_map.normalize_status(status)
        if canon is None:
            raise SystemExit(
                f'ccpm 读到未知状态 {task.name}: {status!r}，fail-closed 不派发')

        # 值/空映射（确定性，非算法）：判定词只反映 ccpm 函数的输出。
        # 用规范值判 open，别名（done/completed/in_progress）统一落到完成态/进行态。
        if canon != 'open':
            verdict = '非开放状态'
        elif unmet:
            verdict = '等待依赖'
        elif conflicts:
            verdict = '等待冲突解除'
        else:
            verdict = '可开工'
        rows.append({
            'task': task.stem,
            'status': status,
            'verdict': verdict,
            'unmet_deps': unmet,
            'active_conflicts': conflicts,
            'stderr_diag': stderr_diag,
        })
    return rows


def next_task(batch_dir):
    """选下一单：接 ccpm ``next.sh`` 的 ready 语义（status=open + 依赖已清 + 无在途冲突）。

    ``next.sh`` 本身在本仓不能直接跑：它靠 ``list_task_files()`` 枚举任务，而后者只
    认 ``.claude/epics/<纯数字>.md``。所以这里接的是它的**判定语义**，不是它的脚本：
    ``gate_check`` 调的就是 ccpm 原函数 ``unmet_deps`` / ``active_conflicts``，本函数
    只补「从候选里选出一个」这个动作——next.sh 输出的也是「Ready」列表，谁先动手
    由调用方决定，这里固定取第一个并把它之外的候选一并交出。

    与 next.sh 的一处口径差异：next.sh 把**空 status** 当作候选（``!= open`` 且
    ``-n`` 才跳过），这里按 ``VALID_STATUSES`` 把空 status 当未知状态拒绝（fail-closed）。
    """
    rows = gate_check(batch_dir)
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']
    return {
        'next': ready[0] if ready else None,
        'ready': ready,
        'not_ready': [{'task': r['task'], 'verdict': r['verdict'],
                       'unmet_deps': r['unmet_deps'],
                       'active_conflicts': r['active_conflicts']}
                      for r in rows if r['verdict'] != '可开工'],
        'tasks': rows,
    }


def _wt_env():
    """wt 内部调 git，需把 Git\\cmd 前置进 PATH（运行环境约定，非改 wt）。"""
    env = dict(os.environ)
    env['PATH'] = GIT_CMD_DIR + os.pathsep + env.get('PATH', '')
    return env


def _parse_first_json(text):
    """wt switch 的 JSON 在首个以 { 开头的行，解析该行；没有则 None。"""
    for line in text.splitlines():
        line = line.strip()
        if line.startswith('{'):
            try:
                return json.loads(line)
            except json.JSONDecodeError:
                return None
    return None


def wt_switch(branch, wt_path, create):
    """调 wt switch；create=True 带 -c 且从当前 HEAD 建分支。返回子进程结果。"""
    cmd = [WT_EXE, '-C', str(ROOT), 'switch']
    if create:
        # --base @ 让新分支从当前 HEAD（工作分支）建，而非 wt 默认的 main；
        # 否则 worktree 里没有本分支已落地的 gorch 代码。
        cmd += ['-c', branch, '--base', '@']
    else:
        cmd.append(branch)
    cmd += ['--path', str(wt_path), '--format', 'json',
            '-y', '--no-hooks', '--no-cd']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace',
                           env=_wt_env(), timeout=WT_TIMEOUT,
                           creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        raise SystemExit(f'wt 调用超时 {branch}（{WT_TIMEOUT}s），fail-closed')
    return r


def provision(batch_dir):
    """先 gate 判定，再对每个可开工任务用 wt 建独立 worktree（幂等，只接线）。"""
    rows = gate_check(batch_dir)
    provisioned, skipped = [], []
    for row in rows:
        task = row['task']
        if row['verdict'] != '可开工':
            skipped.append(task)
            continue
        branch = BRANCH_PREFIX + task
        wt_path = WORKTREE_ROOT / task
        wt_path.parent.mkdir(parents=True, exist_ok=True)

        # 幂等两步：先无 -c 探测已存在，returncode 非 0 再 -c 创建；只看 returncode。
        r = wt_switch(branch, wt_path, create=False)
        if r.returncode != 0:
            r = wt_switch(branch, wt_path, create=True)
        if r.returncode != 0:
            raise SystemExit(
                f'wt 建隔离位失败 {task}: rc={r.returncode} '
                f'{(r.stdout + r.stderr).strip()[-300:]}')

        data = _parse_first_json(r.stdout)
        if not data or 'path' not in data or 'action' not in data:
            raise SystemExit(
                f'wt 输出无法解析 {task}: {r.stdout.strip()[:300]}，fail-closed')
        if not pathlib.Path(data['path']).is_dir():
            raise SystemExit(
                f'wt 报告的 worktree 路径不存在 {task}: {data["path"]}，fail-closed')
        provisioned.append({
            'task': task,
            'branch': branch,
            'worktree': data['path'],
            'action': data['action'],
        })
    return rows, provisioned, skipped


def _find_prompt(prompts_dir, task):
    """按任务 id 找对应 prompt 文件（.md 或 .txt），没有则 None。"""
    base = pathlib.Path(prompts_dir)
    for ext in ('.md', '.txt'):
        p = base / f'{task}{ext}'
        if p.is_file():
            return p
    return None


def _task_meta(card_path):
    """读任务卡 frontmatter 的单行键值（本工程卡只有 `key: value`，够用）。

    用途：把"这张卡约定零改动 / 允许非 git 目录"这类声明**按卡**透传给
    codex_channel。批次级一个总开关会把整批都放开，等于没关（第三轮审计 A2/A5）。
    """
    p = pathlib.Path(card_path)
    if not p.is_file():
        return {}
    text = p.read_text(encoding='utf-8', errors='replace')
    if not text.startswith('---'):
        return {}
    parts = text.split('---', 2)
    if len(parts) < 3:
        return {}
    meta = {}
    for line in parts[1].splitlines():
        s = line.strip()
        if not s or s.startswith('#') or ':' not in s:
            continue
        k, v = s.split(':', 1)
        meta[k.strip()] = v.strip()
    return meta


def _truthy(value):
    return str(value or '').strip().lower() in ('true', 'yes', '1', 'on')


def execute(batch_dir, prompts_dir, max_channels=MAX_CHANNELS, dry_run=False,
            invocation=None):
    """对可开工任务并发调 codex_channel（--workdir 指向各自 worktree）。

    执行逻辑全在 codex_channel 内；本函数只做：校验、fan-out 起进程、join 收集。
    并发用标准库 subprocess（fan-out + join），分批受 max_channels 限制。
    产出策略类开关（no_change_allowed / allow_non_repo）**逐卡从任务卡 frontmatter
    读**，不在批次层统一打开。
    """
    rows = gate_check(batch_dir)
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']

    # fail-closed 校验：每个任务的隔离位与 prompt 必须先就绪。
    jobs = []
    for task in ready:
        wt_path = WORKTREE_ROOT / task
        if not wt_path.is_dir():
            raise SystemExit(f'worktree 不存在 {task}，请先 provision，fail-closed')
        prompt = _find_prompt(prompts_dir, task)
        if not prompt:
            raise SystemExit(
                f'找不到 prompt {task}（{prompts_dir}\\<id>.md|.txt），fail-closed')
        meta = _task_meta(pathlib.Path(batch_dir) / f'{task}.md')
        jobs.append((task, wt_path, prompt, meta))

    inv = invocation or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    results = []
    # 分批：每批最多 max_channels 个进程并发，批内 fan-out 后 join，再进下一批。
    for start in range(0, len(jobs), max_channels):
        batch = jobs[start:start + max_channels]
        procs = []
        for channel, (task, wt_path, prompt, meta) in enumerate(batch, start=1):
            # run-dir 由编排显式指定（第四轮审计 #1）：merge 只认这一批的精确路径，
            # 不再靠"全局目录 + mtime 找最新"，免得并列、损坏、指向别处三种路径漏判。
            run_dir = RUNS / f'{task}-ch{channel}-{inv}'
            cmd = [sys.executable, str(CHANNEL_SCRIPT),
                   '--task', task, '--channel', str(channel),
                   '--prompt', str(prompt), '--workdir', str(wt_path),
                   '--run-dir', str(run_dir)]
            if dry_run:
                cmd.append('--dry-run')
            if _truthy(meta.get('no_change_allowed')):
                cmd.append('--no-change-allowed')
            if _truthy(meta.get('allow_non_repo')):
                cmd.append('--allow-non-repo')
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding='utf-8', errors='replace',
                                 creationflags=_NO_WINDOW)
            procs.append((task, channel, run_dir, p))
        for task, channel, run_dir, p in procs:
            out, err = p.communicate()
            results.append({
                'task': task,
                'channel': channel,
                'returncode': p.returncode,
                'run_dir': str(run_dir),
                'stdout': out.strip(),
                'stderr': err.strip()[-300:],
            })
    return rows, results


def _parse_braced_json(text):
    """从 wt 的混合输出里取出末尾那段 JSON（对象或数组）。

    实测两种真实格式（都与人类可读日志混在同一个 stdout）：
      wt merge  → 单个对象 {"branch":"feat1","target":"main","removed":true,...}
      wt remove → 数组 [{"kind":"worktree","branch":"feat2",
                        "branch_outcome":"retained_unmerged",...}]
    所以不能简单用首个 { 到末个 } ——日志里若出现代码花括号会截错位置，
    数组也会被误当成内层对象。这里要求「整行只有开括号」与「整行只有闭括号」配对。
    """
    lines = text.splitlines()
    for i in range(len(lines) - 1, -1, -1):
        tail = lines[i].strip()
        if tail not in ('}', ']'):
            continue
        opener = '{' if tail == '}' else '['
        for j in range(i, -1, -1):
            if lines[j].strip() == opener:
                try:
                    return json.loads('\n'.join(lines[j:i + 1]))
                except json.JSONDecodeError:
                    break
    # 回退：单行 JSON。按末尾字符判断是数组还是对象，否则单行数组会被
    # 误解析成数组里的内层对象（实测单行 [{"kind":"worktree",...}] 就会这样）。
    body = text.rstrip()
    if not body or body[-1] not in ']}':
        return None
    opener, closer = ('[', ']') if body[-1] == ']' else ('{', '}')
    start = text.find(opener)
    stop = text.rfind(closer)
    if start < 0 or stop <= start:
        return None
    try:
        return json.loads(text[start:stop + 1])
    except json.JSONDecodeError:
        return None


def _branch_state(branch):
    """分支在不在：'exists' / 'absent' / 'unknown'（查询本身失败）。

    第四轮审计：#7 的清理回读靠"分支是否消失"作判据，所以不能用
    ``branch --list <pattern>``——那是 glob 模式匹配（同名前缀的分支会被当成命中），
    也完全不看 rc（git 出错时 stdout 为空会被读成"分支不存在"）。
    改用 ``show-ref --verify refs/heads/<branch>`` 精确查：rc=0 存在、rc=1 明确不存在，
    其余（含超时、仓库损坏）一律 unknown，交给调用方 fail-closed。
    """
    full = f'refs/heads/{branch}'
    try:
        r = subprocess.run([GIT_EXE, '-C', str(ROOT), 'show-ref', '--verify', full],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', env=_wt_env(), timeout=WT_TIMEOUT,
                           creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return 'unknown'
    if r.returncode == 0 and r.stdout.strip():
        return 'exists'
    if r.returncode == 1 and not r.stdout.strip():
        return 'absent'
    return 'unknown'


def _branch_exists(branch):
    """兼容旧调用点：只有**确定存在**才返回 True，unknown 一律不当作存在。"""
    return _branch_state(branch) == 'exists'


def _worktree_registered(wt_path):
    """该 worktree 是否仍登记在 ``git worktree list --porcelain`` 里。

    第四轮审计：目录消失不等于登记也清了，反过来目录还在而登记已被摘掉也算半清理态。
    返回 True / False / None（查询失败），由调用方决定怎么算。
    """
    try:
        r = subprocess.run([GIT_EXE, '-C', str(ROOT), 'worktree', 'list', '--porcelain'],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', env=_wt_env(), timeout=WT_TIMEOUT,
                           creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        return None
    if r.returncode != 0:
        return None
    want = str(pathlib.Path(wt_path).resolve()).replace('\\', '/').lower()
    for line in (r.stdout or '').splitlines():
        s = line.strip()
        if s.startswith('worktree '):
            got = s[len('worktree '):].strip().replace('\\', '/').lower()
            if got == want:
                return True
    return False


def wt_merge(branch, target=None):
    """调 wt merge 把源分支合进目标分支，合并成功后由 wt 自己清理 worktree。

    参数按 `wt merge --help` 真实用法：--branch 指定源分支、--format json 取结构化结果、
    -y 免交互、--no-hooks 跳过项目钩子（本仓库未配 pre-merge 钩子）。
    不传 --no-remove：wt 的第 7 步 cleanup 会删 worktree 与分支（无 commit 时 removed:false）。
    串行由调用方保证——一次只调一个分支。
    """
    cmd = [WT_EXE, '-C', str(ROOT), 'merge']
    if target:
        cmd.append(target)
    cmd += ['--branch', branch, '--format', 'json', '-y', '--no-hooks']
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace',
                           env=_wt_env(), timeout=MERGE_TIMEOUT,
                           creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        # 超时不等于"什么都没发生"。wt 的第 7 步 cleanup 会删分支与 worktree，
        # 若超时点落在 cleanup 之后、合并确认之前，分支就没了但主线也没进账。
        # 必须先查现场再下结论，不能一律当成"未变更"。
        raise SystemExit(
            f'wt merge 超时 {branch}（{MERGE_TIMEOUT}s），且分支已不存在——'
            '说明 wt 可能已删分支但未完成合入，请核对主线后再处理，不要假定无改动'
            if not _branch_exists(branch) else
            f'wt merge 超时 {branch}（{MERGE_TIMEOUT}s），分支仍存在，'
            'wt 未进入 cleanup 阶段，主线应未变更'
        )
    return r


def wt_remove(branch, force=False, delete_branch=False):
    """调 wt remove 清 worktree。

    -f 只删脏 worktree（含未跟踪/已改文件）；未合并的分支仍会保留
    （实测回 branch_outcome=retained_unmerged），要连分支一起删必须再用 -D。
    -D 会丢未合并的提交，属明确危险操作，默认关闭、由调用方显式开启。
    --foreground 阻塞到删完，避免后台异步导致后续判定读到旧状态。
    """
    cmd = [WT_EXE, '-C', str(ROOT), 'remove', branch,
           '--foreground', '--format', 'json', '-y', '--no-hooks']
    if force:
        cmd.append('-f')
    if delete_branch:
        cmd.append('-D')
    try:
        r = subprocess.run(cmd, capture_output=True, text=True,
                           encoding='utf-8', errors='replace',
                           env=_wt_env(), timeout=WT_TIMEOUT,
                           creationflags=_NO_WINDOW)
    except subprocess.TimeoutExpired:
        # 第四轮审计 #7：此前这里 raise SystemExit，cleanup 根本拿不到返回值，它新加的
        # "rc 非 0 就回读现场"分支永远不会执行。超时必须当成**结构化结果**交回 cleanup，
        # 由它回读 目录 / worktree 登记 / 分支 三处再决定算不算清理完。
        return subprocess.CompletedProcess(
            args=cmd, returncode=-1, stdout='',
            stderr=f'wt remove 超时 {branch}（{WT_TIMEOUT}s），未返回结构化结果')
    return r


def find_done_tasks(batch_dir, with_blocked=False, run_dirs=None):
    """返回 result=done 且**可合并**的任务。

    两种取法：
      · ``run_dirs`` 给定时（run 模式）：只看本次 invocation 显式登记、真的跑出记录的
        那批 run-dir。不看 mtime、不 glob、不回退——第四轮审计 #1 的根因正是
        「全局目录 + mtime 排序找最新」：并列时靠枚举顺序、损坏记录被静默跳过、
        `--run-dir` 指到别处的新 blocked 完全漏匹配。
      · 未给时（独立 CLI merge）：退化为按 mtime 取最新（保留但不推荐），
        调用方应改走 run 模式拿 invocation 绑定。
    ``done_no_merge``（纯验证卡）不是可合并成果，一律不进合并池。
    """
    batch_dir = pathlib.Path(batch_dir)
    tasks = sorted(p.stem for p in batch_dir.glob('*.md') if p.is_file())
    done, stale = {}, {}

    if run_dirs:
        for task in tasks:
            rd = run_dirs.get(task)
            if not rd:
                stale[task] = {'run_record': None,
                               'reason': '本次 invocation 没有该任务的执行记录'}
                continue
            h = pathlib.Path(rd) / 'codex-channel.json'
            if not h.is_file():
                stale[task] = {'run_record': None, 'reason': f'本次记录缺失: {h}'}
                continue
            try:
                data = json.loads(h.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
                # 记录损坏 = 本次结果不可确认：阻断，绝不跳过回退到旧成功（审计 #1b）
                stale[task] = {'run_record': str(h), 'reason': f'执行记录损坏：{exc}'}
                continue
            if data.get('dry_run'):
                stale[task] = {'run_record': str(h), 'reason': 'dry-run 记录不授权合并'}
                continue
            if data.get('result') == 'done':
                done[task] = str(h)
            else:
                stale[task] = {
                    'run_record': str(h),
                    'reason': data.get('reason')
                    or f'本次记录 result={data.get("result")!r}，不是可合并的 done'}
        return (done, stale) if with_blocked else done

    for task in tasks:
        hits = sorted(RUNS.glob(f'{task}-ch*/codex-channel.json'),
                      key=lambda p: p.stat().st_mtime, reverse=True)
        latest = None
        for h in hits:
            try:
                data = json.loads(h.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                continue
            if data.get('dry_run'):
                continue
            latest = (h, data)
            break
        if latest is None:
            stale[task] = {'run_record': None, 'reason': '无真实执行记录'}
            continue
        h, data = latest
        if data.get('result') == 'done':
            done[task] = str(h)
        else:
            stale[task] = {'run_record': str(h),
                           'reason': data.get('reason') or '最新记录的 result 不是 done'}
    return (done, stale) if with_blocked else done


def _current_branch():
    """本仓库当前检出的分支名——合并的默认目标。

    wt merge 的 TARGET 缺省是 default branch（本仓库为 main），而编排实际是在工作
    分支上施工的。把 target 交给 wt 默认值，等于把施工直接铺到 main、工作分支反而
    落后；再合第二个分支时 main 已有同名文件，就变成 add/add 冲突。
    """
    r = subprocess.run([GIT_EXE, '-C', str(ROOT), 'rev-parse', '--abbrev-ref', 'HEAD'],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace', env=_wt_env(), timeout=WT_TIMEOUT,
                       creationflags=_NO_WINDOW)
    return r.stdout.strip()


def _norm_ref(ref):
    """把 `refs/heads/x` 与 `x` 归一成同一个分支名。

    wt merge 的 JSON 里 branch/target 可能带 refs/heads 前缀，直接字符串比对会把
    "合成功了、只是写法不同"误判成目标不符，让整批在 merge 段 SystemExit。
    """
    s = str(ref or '').strip()
    return s[len('refs/heads/'):] if s.startswith('refs/heads/') else s


def merge(batch_dir, tasks=None, target=None, run_dirs=None):
    """串行把已完成任务的分支合回主线；任一失败即停，不跳过错继续合下一个。

    ``target`` 默认取当前检出分支，不交给 wt 的 default branch 默认值——见
    ``_current_branch()`` 里的原因说明。要合到别处（如发布时合 main）必须显式传。

    冲突时 wt 会把 rebase 留在源 worktree 的未完成态，必须人工 abort 或解决后才能继续；
    因此这里宁可整批停下并如实回传原始输出，也不在半合并历史上叠加后续分支。
    """
    done, stale = find_done_tasks(batch_dir, with_blocked=True, run_dirs=run_dirs)
    if tasks:
        unknown = [t for t in tasks if t not in done]
        if unknown:
            detail = [f'{t}（{stale[t]["reason"][:80]}）' if t in stale else t
                      for t in unknown]
            raise SystemExit(
                f'以下任务最新记录不是 done，拒绝合并: {detail}，fail-closed')
        targets = list(tasks)
    else:
        targets = list(done)
    if not targets:
        return done, [], [], stale

    resolved_target = (target or _current_branch()).strip()
    if not resolved_target or resolved_target == 'HEAD':
        raise SystemExit('无法确定合并目标分支（当前处于 detached HEAD），请显式传 target')

    merged, failed = [], []
    for task in targets:
        branch = BRANCH_PREFIX + task
        r = wt_merge(branch, target=resolved_target)
        if r.returncode != 0:
            failed.append({
                'task': task,
                'branch': branch,
                'returncode': r.returncode,
                'stdout': r.stdout.strip()[-600:],
                'stderr': r.stderr.strip()[-600:],
                # 固定提示文案（非判断）：实测冲突时 wt 把 rebase 留在源 worktree
                # 的未完成态，必须人工 abort/解决后才能继续合下游分支。
                'hint': ('合并未成功。若为冲突，wt 已把 rebase 留在源 worktree 未完成态；'
                         '解决后 rebase --continue，或执行 '
                         'git -C <源worktree> rebase --abort 放弃本次合并再重跑。'
                         '后续分支已停止，不会自动继续。'),
            })
            break
        data = _parse_braced_json(r.stdout)
        if data is None:
            raise SystemExit(
                f'wt merge 输出无法解析 {task}: {r.stdout.strip()[:400]}，fail-closed')
        # rc=0 不足以证明合进去了（第四轮审计 #8）：wt 自己的 JSON 才是结论来源。
        # 必须看到 merged is true，且 branch / target 与本次请求一致——
        # 否则 {"merged": false} 也会被当成成功记进 merged，下游 cleanup 就照它清现场。
        if not isinstance(data, dict):
            raise SystemExit(f'wt merge 输出不是对象 {task}: {data!r}，fail-closed')
        if data.get('merged') is not True:
            failed.append({
                'task': task, 'branch': branch, 'returncode': 0,
                'stdout': r.stdout.strip()[-600:],
                'stderr': f'wt 报 merged={data.get("merged")!r}，未真正合入',
                'hint': ('wt 返回 rc=0 但 merged 不为 true，按未合并处理；'
                         '请核对主线与源 worktree 后再决定是重试还是人工合。'),
            })
            break
        got_branch = data.get('branch')
        got_target = data.get('target')
        # 同一分支可能被 wt 写成 `x` 或 `refs/heads/x`，先归一化再比，
        # 否则会把"合成功了但写法不同"误判成目标不符而整批 SystemExit。
        if got_branch and _norm_ref(got_branch) != _norm_ref(branch):
            raise SystemExit(
                f'wt merge 回报的分支与请求不一致 {task}: 请求 {branch} 实际 {got_branch}')
        if got_target and _norm_ref(got_target) != _norm_ref(resolved_target):
            raise SystemExit(
                f'wt merge 回报的目标与请求不一致 {task}: '
                f'请求 {resolved_target} 实际 {got_target}')
        merged.append({'task': task, 'branch': branch,
                       'result': data, 'run_record': done[task]})
    return done, merged, failed, stale


def cleanup(batch_dir, tasks=None, force=False, delete_branch=False):
    """清理残留 worktree 与分支（合并失败、空分支、合并后未清干净时兜底）。

    force=True 才会删带未跟踪文件的 worktree（--force 语义）。
    delete_branch=True 才会强删未合并分支（-D 语义，会丢提交），默认保留。
    """
    batch_dir = pathlib.Path(batch_dir)
    all_tasks = sorted(p.stem for p in batch_dir.glob('*.md') if p.is_file())
    targets = list(tasks) if tasks else all_tasks
    removed, skipped = [], []
    for task in targets:
        branch = BRANCH_PREFIX + task
        wt_path = WORKTREE_ROOT / task
        if not wt_path.is_dir():
            # 目录不在 ≠ 清干净（第四轮审计 #7）：半清理态（目录已删、分支还在）此前
            # 被直接记"已不存在"、cleanup 还返回 0。这里补查 worktree 登记与分支。
            br = _branch_state(branch)
            reg = _worktree_registered(wt_path)
            if br == 'absent' and reg is False:
                removed.append({'task': task, 'branch': branch,
                                'worktree': str(wt_path), 'branch_outcomes': [],
                                'note': '调用前 目录/登记/分支 三处均已不存在，按已清理处理'})
            elif br == 'exists' or reg is True:
                skipped.append({'task': task, 'branch': branch, 'partial': True,
                                'reason': (f'半清理态：worktree 目录已不存在，但分支={br}、'
                                           f'worktree 登记={"在" if reg is True else reg}；'
                                           '不能记成功，需人工确认后补删分支或清登记')})
            else:
                skipped.append({'task': task, 'branch': branch, 'partial': True,
                                'reason': f'无法确认是否已清理（分支={br}，登记查询={reg}）'})
            continue
        r = wt_remove(branch, force=force, delete_branch=delete_branch)
        if r.returncode != 0:
            # 超时/非 0 ≠ 没清理（L72）：Windows 上 wt remove 稳定跑不完 180s，而它的
            # 内部 cleanup 往往在超时点之前已经删掉了目录与分支。所以不能凭 rc 判失败，
            # 必须回读现场——目录、worktree 登记、分支三处都确认清空才算清干净
            # （第三/第四轮审计 A7）。
            wt_gone = not wt_path.is_dir()
            br = _branch_state(branch)
            reg = _worktree_registered(wt_path)
            raw_tail = (r.stdout + r.stderr).strip()[-400:]
            if wt_gone and br == 'absent' and reg is False:
                removed.append({'task': task, 'branch': branch,
                                'worktree': str(wt_path), 'branch_outcomes': [],
                                'note': (f'wt remove 返回 rc={r.returncode}（rc<0 表示超时），'
                                         '但 目录/登记/分支 三处均已消失，按已清理处理'),
                                'raw_tail': raw_tail})
                continue
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': (f'rc={r.returncode} 且现场未清干净 '
                                       f'(目录还在={not wt_gone}, 分支={br}, '
                                       f'登记={"在" if reg is True else reg}) {raw_tail}')})
            continue
        data = _parse_braced_json(r.stdout)
        # wt remove 返回数组；把分支结局原样带出，让人看清分支到底删没删。
        outcomes = [x.get('branch_outcome') for x in data
                    if isinstance(x, dict)] if isinstance(data, list) else []
        if any(o and 'retained' in str(o) for o in outcomes):
            # rc=0 也可能"worktree 删了、分支留着"（未合并分支的既定行为）：那是
            # 保留了待处理分支，不等于清理完成，不能记 removed。
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': f'wt 返回 rc=0 但分支被保留（{outcomes}），'
                                      '属预期保留，需确认是否该 -D',
                            'result': data})
            continue
        removed.append({'task': task, 'branch': branch,
                        'result': data, 'branch_outcomes': outcomes,
                        'worktree': str(wt_path)})
    return removed, skipped


def run_all(batch_dir, prompts_dir, max_channels=MAX_CHANNELS, target=None,
            dry_run=False, force_cleanup=False):
    """一条命令走完 gate → provision → execute → merge → cleanup。

    第四轮口径（一条对上一轮审计一条 fail-open）：
      · invocation 与 target 在开始时固定，全程用同一份，不再中途解析；
      · execute 任一任务非零退出即 stopped_at='execute'，不进 merge；
      · merge 只接受**本次 invocation** 真跑出 result=done 的任务（精确 run-dir），
        纯验证卡（done_no_merge）不进合并池；
      · cleanup 只清**已确认合并成功**的任务，冲突/未尝试/未合并的一律保现场；
      · stopped_at 覆盖 gate/provision/execute/dry_run/merge/cleanup/done；
      · not_merged（stale）与 cleanup 的 partial 都让整次 run 记为未完成。
    """
    inv = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    resolved_target = (target or _current_branch()).strip()
    base = {'invocation': inv, 'target': resolved_target}
    steps = {}
    rows = gate_check(batch_dir)
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']
    steps['gate'] = {'ready': ready,
                     'blocked': [r['task'] for r in rows if r['verdict'] != '可开工']}

    def _stop(at, note):
        steps.setdefault('merge', {'merged': [], 'failed': [], 'not_merged': {}})
        steps.setdefault('cleanup', {'removed': [], 'skipped': [],
                                     'kept_for_conflict': []})
        return {**base, 'steps': steps, 'stopped_at': at, 'note': note}

    if not ready:
        return _stop('gate', '没有可开工任务')

    try:
        _, provisioned, p_skipped = provision(batch_dir)
    except SystemExit as exc:
        steps['provision'] = {'error': str(exc)}
        return _stop('provision', f'provision 失败：{exc}')
    steps['provision'] = {
        'provisioned': [p.get('task') for p in provisioned if isinstance(p, dict)],
        'skipped': p_skipped,
    }

    _, results = execute(batch_dir, prompts_dir, max_channels=max_channels,
                         dry_run=dry_run, invocation=inv)
    steps['execute'] = {
        'results': [{'task': r['task'], 'channel': r['channel'],
                     'returncode': r['returncode'], 'run_dir': r.get('run_dir')}
                    for r in results],
        'failed': [r['task'] for r in results if r['returncode'] != 0],
    }
    if steps['execute']['failed']:
        # 之前只看 merge 的失败，execute 非 0 照样往下合（审计 #8 的主路径）。
        return _stop('execute', f'{len(steps["execute"]["failed"])} 个任务执行非 0，'
                               '未进入 merge，现场保留供排查')
    if dry_run:
        # dry-run 只空转执行段：之前它照样真 merge + 真 cleanup（审计 #1e）。
        return _stop('dry_run', 'dry-run：不合并、不清理')

    run_dirs = {r['task']: r['run_dir'] for r in results if r.get('run_dir')}
    probe_done, probe_stale = find_done_tasks(batch_dir, with_blocked=True,
                                              run_dirs=run_dirs)
    to_merge = [t for t in ready if t in probe_done]
    verified = [t for t in ready if t in probe_stale
                and 'done_no_merge' in str(probe_stale[t].get('reason'))]

    done, merged, failed, stale = merge(batch_dir, tasks=to_merge,
                                        target=resolved_target, run_dirs=run_dirs)
    steps['merge'] = {'merged': [m['task'] for m in merged],
                      'failed': failed, 'not_merged': stale,
                      'verified_only': verified}

    if failed:
        steps['cleanup'] = {'removed': [], 'skipped': [],
                            'kept_for_conflict': [f['task'] for f in failed]}
        return {**base, 'steps': steps, 'stopped_at': 'merge',
                'note': '合并失败（可能为冲突），跳过 cleanup 以保留现场'}

    # 只清"已确认合并成功"的任务：之前清的是全部 ready，把本轮没尝试的后续任务、
    # 以及 stale 任务的现场一起清掉了（审计 #8）。
    merged_tasks = [m['task'] for m in merged]
    removed, c_skipped = cleanup(batch_dir, tasks=merged_tasks,
                                 force=force_cleanup, delete_branch=False)
    steps['cleanup'] = {'removed': [r['task'] for r in removed],
                        'skipped': c_skipped,
                        'kept_for_conflict': []}

    leftover = [t for t in ready if t not in merged_tasks and t not in verified]
    if stale or leftover:
        return _stop('merge', f'{len(stale) + len(leftover)} 个任务未进入合并池'
                              '（见 not_merged / verified_only），run 记为未完成')
    partial = [s for s in c_skipped if s.get('partial')] or c_skipped
    if partial:
        return _stop('cleanup', f'{len(c_skipped)} 个任务清理未完成（见 cleanup.skipped）')
    return {**base, 'steps': steps, 'stopped_at': 'done'}


def bridge(run_dir, batch_dir):
    """A（审议链）→ B（执行链）的唯一交接点：只搬证据，不解析语义。

    为什么不做自动解析：work_order 阶段的产出是自然语言，把它反解成
    depends_on / conflicts_with 属于"拿 Markdown 当类型系统"——一旦误解析就会
    派错写域，而并发写域切错是这套链路里代价最高的事故。所以这里只做三件
    确定性的事：
      1. fail-closed：每一段 verdict 必须是 completed，否则不许进执行；
      2. 把 stages/*.json 原样复制到 <批次>/_handoff/ 作为可审计证据；
      3. 写 manifest.json，记录 run_dir、需求原文、各段结论、模型与时间戳。
    工单 md（含 frontmatter）是第 3 跳 Owner 确认的产物，由人确认后放进来；
    本函数不替人做这一步，也不猜测工单该怎么切。
    """
    run_dir = pathlib.Path(run_dir)
    batch_dir = pathlib.Path(batch_dir)
    stages_dir = run_dir / 'stages'
    if not stages_dir.is_dir():
        raise SystemExit(f'A 的产出不存在：{stages_dir}')

    stage_files = sorted(stages_dir.glob('*.json'))
    if not stage_files:
        raise SystemExit(f'stages 目录里没有任何产物：{stages_dir}')

    stages = {}
    for f in stage_files:
        try:
            artifact = json.loads(f.read_text(encoding='utf-8'))
        except ValueError as exc:
            raise SystemExit(f'审议产物不是合法 JSON：{f}（{exc}）')
        if not isinstance(artifact, dict):
            raise SystemExit(f'审议产物结构不对（应为对象）：{f}')
        verdict = str(artifact.get('verdict') or '').strip().lower()
        if verdict != 'completed':
            # 未完成的审议绝不能进执行，否则执行端会拿着半成品工单开工。
            raise SystemExit(
                f'审议未完成，禁止进执行：{f.stem} verdict={verdict or "缺失"}')
        stages[f.stem] = {
            'verdict': verdict,
            'model': artifact.get('model'),
            'artifact': str(f),
        }

    handoff = batch_dir / HANDOFF_DIRNAME
    handoff.mkdir(parents=True, exist_ok=True)
    for f in stage_files:
        (handoff / f.name).write_bytes(f.read_bytes())

    task_files = sorted(p.name for p in batch_dir.glob('*.md') if p.is_file())
    manifest = {
        'run_dir': str(run_dir),
        'batch_dir': str(batch_dir),
        'stages': stages,
        'task_files': task_files,
        # 没有工单 md 就是"交接了但没人放工单"，如实反映，不假装可开工。
        'ready_to_gate': bool(task_files),
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
    }
    (handoff / 'manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest


def main(argv=None):
    ap = argparse.ArgumentParser(description='GORCH 多通道薄编排（只接线）')
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('gate', help='开工前判定（调 ccpm 原函数）')
    g.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    n = sub.add_parser('next', help='选下一单（接 ccpm next.sh 的 ready 语义）')
    n.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    p = sub.add_parser('provision', help='对可开工任务用 wt 建隔离 worktree')
    p.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    e = sub.add_parser('execute', help='并发调 codex_channel 在各自 worktree 执行')
    e.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    e.add_argument('--prompts-dir', required=True, help='prompt 文件目录（<id>.md|.txt）')
    e.add_argument('--max-channels', type=int, default=MAX_CHANNELS, help='并发上限（默认 3）')
    e.add_argument('--dry-run', action='store_true', help='透传给 codex_channel，不真起 Codex')
    m = sub.add_parser('merge', help='串行把已完成任务的分支合回主线（调 wt merge）')
    m.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    m.add_argument('--tasks', nargs='*', default=None,
                   help='只合这些任务（默认合所有 result=done 的）')
    m.add_argument('--target', default=None,
                   help='合并目标分支（默认当前检出分支；合到 main 属发布动作，须显式传）')
    c = sub.add_parser('cleanup', help='清理残留 worktree 与分支（调 wt remove）')
    c.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    c.add_argument('--tasks', nargs='*', default=None, help='只清这些任务')
    c.add_argument('--force', action='store_true',
                   help='删除带未跟踪/已改文件的脏 worktree（--force 语义）')
    c.add_argument('--delete-branch', action='store_true',
                   help='连未合并分支一起删（-D 语义，会丢提交，默认保留）')
    b = sub.add_parser('bridge', help='把审议链 run_dir 的产物登记成交接单（只搬不解析）')
    b.add_argument('--run-dir', required=True, help='orchestrate-order 的 run_dir')
    b.add_argument('--batch-dir', required=True, help='交接给 gate/provision 的批次目录')
    rn = sub.add_parser('run', help='一条命令走完 gate→provision→execute→merge→cleanup')
    rn.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    rn.add_argument('--prompts-dir', required=True, help='prompt 文件目录（<id>.md|.txt）')
    rn.add_argument('--max-channels', type=int, default=MAX_CHANNELS,
                    help='并发上限（默认 %d）' % MAX_CHANNELS)
    rn.add_argument('--target', default=None, help='合并目标分支（默认当前检出分支）')
    rn.add_argument('--dry-run', action='store_true', help='透传给 execute，不真起 Codex')
    rn.add_argument('--force-cleanup', action='store_true',
                    help='cleanup 阶段删带未跟踪文件的脏 worktree')
    args = ap.parse_args(argv)

    if args.cmd == 'gate':
        rows = gate_check(args.batch_dir)
        ready = [r['task'] for r in rows if r['verdict'] == '可开工']
        blocked = [r['task'] for r in rows if r['verdict'] != '可开工']
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'ready': ready, 'blocked': blocked, 'tasks': rows},
            ensure_ascii=False, indent=2))
        return 0

    if args.cmd == 'next':
        out = next_task(args.batch_dir)
        print(json.dumps({'batch': str(pathlib.Path(args.batch_dir)), **out},
                         ensure_ascii=False, indent=2))
        # 没有可开工任务即非 0：调用方要能区分“没有下一单”与“命令跑完”。
        return 0 if out['next'] else 1

    if args.cmd == 'provision':
        rows, provisioned, skipped = provision(args.batch_dir)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'provisioned': provisioned, 'skipped_blocked': skipped,
             'tasks': rows},
            ensure_ascii=False, indent=2))
        return 0

    if args.cmd == 'execute':
        rows, results = execute(
            args.batch_dir, args.prompts_dir,
            max_channels=args.max_channels, dry_run=args.dry_run)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'results': results, 'tasks': rows},
            ensure_ascii=False, indent=2))
        return 0

    if args.cmd == 'merge':
        done, merged, failed, stale = merge(args.batch_dir, tasks=args.tasks,
                                            target=args.target)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'target': args.target or _current_branch(),
             'done_tasks': done, 'merged': merged, 'failed': failed,
             'not_merged': stale},
            ensure_ascii=False, indent=2))
        # 任一分支合并失败（含冲突）即非 0，让上游看到失败而不是“跑完了”。
        return 0 if not failed else 1

    if args.cmd == 'bridge':
        manifest = bridge(args.run_dir, args.batch_dir)
        print(json.dumps(manifest, ensure_ascii=False, indent=2))
        # 没工单 md 不算失败（交接完成但等第 3 跳），但要让人看见它还不能开工。
        return 0

    if args.cmd == 'run':
        summary = run_all(args.batch_dir, args.prompts_dir,
                          max_channels=args.max_channels, target=args.target,
                          dry_run=args.dry_run, force_cleanup=args.force_cleanup)
        print(json.dumps({'batch': str(pathlib.Path(args.batch_dir)), **summary},
                         ensure_ascii=False, indent=2))
        # 只有真走到 done 才算 0（第四轮审计）：merge 无失败但停在 execute / cleanup /
        # gate，或者有 not_merged 未闭合时，都不该让上游看到"跑完了"。
        return 0 if summary.get('stopped_at') == 'done' else 1

    if args.cmd == 'cleanup':
        removed, skipped = cleanup(
            args.batch_dir, tasks=args.tasks, force=args.force,
            delete_branch=args.delete_branch)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'removed': removed, 'skipped': skipped},
            ensure_ascii=False, indent=2))
        # “worktree 已不存在”属正常；其余 skip 说明 remove 真失败，按失败返回。
        real_fail = [s for s in skipped if '已不存在' not in s['reason']]
        return 0 if not real_fail else 1


if __name__ == '__main__':
    sys.exit(main())
