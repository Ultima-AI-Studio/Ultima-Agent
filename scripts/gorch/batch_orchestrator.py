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
import hashlib
import json
import os
import pathlib
import re
import stat
import subprocess
import sys
from datetime import datetime, timedelta, timezone

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
    # 每条都要求**整行**格式对上（含行尾锚定）：噪声前缀后面若还挂着额外文本，
    # 那就不再是已知噪声，而是真错误（第四轮审计 Q1：只锚行首会把
    # `bash: fork: Permission denied` 整行吞掉）。
    r'^\s*\d+\s*\[main\]\s+\S+\s+\d+\s+(?:fork|dofork|child_copy):'
    r'\s*(?:retry:\s*Resource temporarily unavailable|child \d+ - forked OK)\s*$'
    r'|'
    r'^\s*bash:\s*(?:child_copy|dofork|fork):\s*cygheap\s+'
    r'(?:read|write)\s+copy\s+failed,\s*0x[0-9A-F]+\s*$'
    r'|'
    r'^\s*\S+:\s*fork:\s*retry:\s*Resource temporarily unavailable\s*$',
    re.IGNORECASE)
# 「已删干净」的唯一可信 branch_outcome。实测（临时仓库 wtprobe-r5，2026-11-09）
# `wt remove --format json` 返回**数组**，元素字段是
#   {kind, branch, path, branch_outcome, branch_checked_out_at}
# branch_outcome="deleted"，**没有 removed 字段**（与 wt merge 回执一样，不能照名字猜）。
# 因此 cleanup 只认 deleted；其它取值（retained_unmerged 等）或缺失一律按未清理处理，
# 不拿"目录恰好不在"顶上成功。
REMOVED_OUTCOMES = frozenset({'deleted'})
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


def provision(batch_dir, tasks=None):
    """先 gate 判定，再对每个可开工任务用 wt 建独立 worktree（幂等，只接线）。

    r8（第七轮审计 N5）：``tasks`` 用来收窄。run_all 剔除拒签任务后必须把过滤后的
    ready 传进来——否则 provision 自己重跑 gate，会给**未获授权**的任务也建 worktree
    与分支（授权缺了，工作现场却已经铺开）。``tasks=None`` 保留独立调用时的全量语义。
    """
    rows = gate_check(batch_dir)
    allow = None if tasks is None else set(str(t) for t in tasks)
    provisioned, skipped = [], []
    for row in rows:
        task = row['task']
        if allow is not None and task not in allow:
            skipped.append(task)
            continue

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


# 卡片里只能写「请求」，不能写「授权」（第五轮审计 Q3-9 / 7.3-6）。
# 授权由编排方在派发时签发到 invocation manifest，执行端只读那份清单：
# 人不在执行过程中逐次点头，判断权在编排/审核这一侧的 agent。
REQUEST_KEYS = ('request_no_change_allowed', 'request_allow_non_repo')
LEGACY_REQUEST_KEYS = ('no_change_allowed', 'allow_non_repo')  # 兼容旧卡，按请求对待
WRITE_SCOPE_KEY = 'writes'
MANIFEST_DIRNAME = '_invocations'


def _write_scope(meta):
    """解析卡片声明的授权写域：`writes: docs/reports/, scripts/gorch/*.py`。

    只在**编排方派发时**读一次并固化进 manifest；执行端不读卡片，避免"卡片自己
    把自己放行"。支持逗号分隔，也容忍 `[a, b]` 写法与引号。
    """
    raw = str(meta.get(WRITE_SCOPE_KEY) or '').strip()
    if not raw:
        return []
    raw = raw.strip().strip('[]')
    out = []
    for part in raw.replace('\uff0c', ',').split(','):
        s = part.strip().strip('\'"').strip()
        if s:
            out.append(s.replace('\\', '/'))
    return out


def grant_invocation(batch_dir, ready, invocation, target):
    """签发 invocation manifest：把「请求」提升为「授权」，或拒绝签发。

    返回 (manifest_path, blocked)。``blocked`` 是 ``{task: reason}``——编排方
    拒绝授权（例如卡片既声明了写域又请求"零改动"这类自相矛盾），这些任务不进
    执行段，也不参与后续 merge。
    """
    batch_dir = pathlib.Path(batch_dir)
    tasks, blocked = {}, {}
    for task in ready:
        card = batch_dir / f'{task}.md'
        meta = _task_meta(card)
        scope = _write_scope(meta)
        req_nc = _truthy(meta.get(REQUEST_KEYS[0])) or _truthy(
            meta.get(LEGACY_REQUEST_KEYS[0]))
        req_nr = _truthy(meta.get(REQUEST_KEYS[1])) or _truthy(
            meta.get(LEGACY_REQUEST_KEYS[1]))
        # 自相矛盾：声明了要改哪些路径，又说本次不产生改动 —— 拒绝授权，
        # 不猜哪一边是真的（第五轮审计 7.3-6）。
        if scope and req_nc:
            blocked[task] = ('卡片同时声明 writes 与 no_change_allowed，'
                             '编排方无法判定本次是否应产出，拒绝授权；'
                             '请改卡后重派')
            continue
        tasks[task] = {
            'card': str(card),
            'write_scope': scope,
            'write_scope_source': 'card:writes@gate（由编排方固化）' if scope
            else 'undeclared（本卡未声明写域，本次不做写域校验）',
            'write_scope_enforced': bool(scope),
            'no_change_allowed': req_nc,
            'allow_non_repo': req_nr,
            'requests': {'no_change_allowed': req_nc, 'allow_non_repo': req_nr},
            'granted_by': 'batch_orchestrator（编排方）',
        }
    manifest = {
        'manifest_version': 1,
        'invocation': invocation,
        'target': target,
        'created_at': datetime.now(timezone.utc).isoformat(timespec='seconds'),
        'granted_by': 'batch_orchestrator（编排方）',
        'policy': ('卡片只能提请求；授权只由编排方在派发时签发；'
                   '执行端只读本清单，不读卡片自由字段；人不在执行过程中审批'),
        'tasks': tasks,
        'blocked': blocked,
    }
    out_dir = RUNS / MANIFEST_DIRNAME
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f'{invocation}.json'
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return path, blocked


def _load_grants(manifest_path):
    """读回编排方签发的授权清单；结构不对直接 SystemExit（fail-closed）。

    r8（第七轮审计 N6）：解析后先验**根节点必须是对象**——此前合法 JSON 数组会抛
    未捕获的 AttributeError（既不是 SystemExit 也不是 blocked），审计记录直接缺失。
    """
    p = pathlib.Path(manifest_path)
    if not p.is_file():
        raise SystemExit(f'invocation manifest 不存在：{p}，fail-closed')
    try:
        data = json.loads(p.read_text(encoding='utf-8'))
    except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
        raise SystemExit(f'invocation manifest 不可解析：{p}（{exc}）')
    if not isinstance(data, dict):
        raise SystemExit(
            f'invocation manifest 根节点不是对象（{type(data).__name__}）：{p}，fail-closed')
    tasks = data.get('tasks')
    if not isinstance(tasks, dict):
        raise SystemExit(f'invocation manifest 结构不对（tasks 不是对象）：{p}')
    return data, tasks



def execute(batch_dir, prompts_dir, max_channels=MAX_CHANNELS, dry_run=False,
            invocation=None, manifest=None, tasks=None):
    """对可开工任务并发调 codex_channel（--workdir 指向各自 worktree）。

    执行逻辑全在 codex_channel 内；本函数只做：校验、fan-out 起进程、join 收集。
    产出策略类开关**不再从卡片 frontmatter 读**（第五轮审计 Q3-9）：改为读取
    编排方签发的 invocation manifest，执行端只认那份授权。

    r8（第七轮审计 N5 反向问题）：``tasks`` 由编排方给定（run_all 传过滤后的 ready）；
    直接走 CLI ``execute --manifest <子集>`` 而不给 ``tasks`` 时，ready 仍是 gate 全量，
    清单里没有的卡会在下面"未授权任务"处整批 SystemExit，连已授权的也跑不了。所以
    拿回 grants 后统一按清单收窄一层。
    """
    rows = gate_check(batch_dir)
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']
    if tasks is not None:
        # 第七轮审计 #8b：编排方已在 gate 之后过滤（含剔除拒签任务），这里只能
        # 收窄、不能再从 gate 重建全量 ready——否则被拒签的卡会重新进来，然后在
        # manifest 里找不到条目而抛错，连已授权任务也执行不了。
        allow = set(tasks)
        ready = [t for t in ready if t in allow]

    inv = invocation or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    if manifest is None:
        # 直接跑 execute（不经 run_all）时也由编排方就地签发一份清单，保证
        # 「授权一定有清单可审计」，而不是执行端自己去读卡片字段。
        manifest, blocked = grant_invocation(batch_dir, ready, inv, _current_branch())
        if blocked:
            ready = [t for t in ready if t not in blocked]
    _mdata, grants = _load_grants(manifest)
    inv = str(_mdata.get('invocation') or inv)
    ready = [t for t in ready if t in grants]


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
        g = grants.get(task)
        if not isinstance(g, dict):
            raise SystemExit(f'invocation manifest 未授权任务 {task}，fail-closed')
        jobs.append((task, wt_path, prompt, g))

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
                   '--run-dir', str(run_dir),
                   '--manifest', str(manifest)]
            if dry_run:
                cmd.append('--dry-run')
            # 只认编排方签发的那份清单（变量名沿用 meta，内容是授权而不是卡片原文）。
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
        # 用三态 `_branch_state`：查询失败（unknown）不能读成"分支不存在"，
        # 否则会误报"wt 已删分支"（第四轮审计 Q1）。
        state = _branch_state(branch)
        if state == 'absent':
            raise SystemExit(
                f'wt merge 超时 {branch}（{MERGE_TIMEOUT}s），且分支已不存在——'
                '说明 wt 可能已删分支但未完成合入，请核对主线后再处理，不要假定无改动')
        if state == 'exists':
            raise SystemExit(
                f'wt merge 超时 {branch}（{MERGE_TIMEOUT}s），分支仍存在，'
                'wt 未进入 cleanup 阶段，主线应未变更')
        raise SystemExit(
            f'wt merge 超时 {branch}（{MERGE_TIMEOUT}s），分支状态查询失败'
            '（unknown）——不能假定分支在与不在，请人工核对主线与分支后再处理')
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


def _utc_ts(value):
    """把记录里的 started_at 解析成可比较的 epoch；解析不了返回 None。

    第五轮审计 Q3-3：此前直接拿字符串比大小——`+08:00` 与 `Z` 混用、缺时区、
    非法值都会让"谁更新"变成字典序游戏。这里统一转 UTC，解析失败当作缺失，
    由调用方阻断（不猜、不退 mtime）。第七轮审计 #5 进一步收紧为**严格 UTC**：
    无时区与任何非零偏移都不算合法时间。
    """
    s = str(value or '').strip()
    if not s:
        return None
    if s.endswith('Z'):
        s = s[:-1] + '+00:00'
    try:
        dt = datetime.fromisoformat(s)
    except ValueError:
        return None
    if dt.tzinfo is None:
        # 第七轮审计 #5：无时区值不能 replace(tzinfo=UTC) 冒充 UTC——
        # `2026-11-09`、`2026-11-09T08:00:00` 会被当成合法授权时间。
        return None
    if dt.utcoffset() != timedelta(0):
        # 只接受 UTC；+08:00 等非零偏移一律视为不可判定（不换算、不猜）。
        return None
    return dt.timestamp()


def _ts_label(ts):
    """把 epoch 还原成可读的 UTC 时间，供失败文案使用。"""
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).isoformat(
            timespec='seconds')
    except (TypeError, ValueError, OSError):
        return str(ts)


def find_done_tasks(batch_dir, with_blocked=False, run_dirs=None, only_tasks=None,
                     expect_invocation=None):
    """返回 result=done 且**可合并**的任务。

    两种取法：
      · ``run_dirs`` 给定时（run 模式）：只看本次 invocation 显式登记、真的跑出记录的
        那批 run-dir。不看 mtime、不 glob、不回退——第四轮审计 #1 的根因正是
        「全局目录 + mtime 排序找最新」：并列时靠枚举顺序、损坏记录被静默跳过、
        `--run-dir` 指到别处的新 blocked 完全漏匹配。
      · 未给时（独立 CLI merge，已不推荐）：按严格 UTC started_at + invocation
        唯一性取证；损坏记录、无时区时间、缺 invocation、同 invocation 多条、
        并列时间任一命中即阻断，调用方应改走 run 模式拿 invocation 绑定。
    ``only_tasks`` 给定时只算这些任务——run 模式只关心本轮 ready 的那几张卡，
    否则批次里任何一张非 ready 卡都会被算成「本次没有执行记录」而假失败
    （第四轮审计 Q1）。
    ``done_no_merge``（纯验证卡）不是可合并成果，一律不进合并池。
    """
    batch_dir = pathlib.Path(batch_dir)
    tasks = (list(only_tasks) if only_tasks is not None
             else sorted(p.stem for p in batch_dir.glob('*.md') if p.is_file()))
    done, stale = {}, {}

    # 显式给了 run_dirs（哪怕空映射）就是 invocation 模式：空映射意味着「本次一个
    # 记录都没有」，必须整体阻断，不能落回 glob + mtime 去翻历史（审计 Q1）。
    # r9（第八轮审计 N10）：只有 compare-to-expected 才是身份校验。r8 写成
    # `if expect_invocation and ...`，不给期望时退化成「只验非空」，任何历史
    # invocation 的记录都能通过。explicit 模式必须给出本次 invocation，否则拒绝。
    if run_dirs is not None and not expect_invocation:
        raise SystemExit(
            '显式 run-dir 模式必须同时给出本次 invocation（--invocation），'
            '否则无法证明记录属于本次调用，fail-closed')
    if run_dirs is not None:
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
            if not isinstance(data, dict):
                stale[task] = {'run_record': str(h),
                               'reason': '执行记录根节点不是对象，无法确认归属'}
                continue
            # 第七轮审计 #5：显式 run-dir 必须核对记录身份，否则 B 的 done 记录
            # 可以被映射成 A=PATH_TO_B，从而授权合并 gorch/A。
            rec_task = str(data.get('task') or '')
            if rec_task != task:
                stale[task] = {'run_record': str(h),
                               'reason': (f'执行记录身份不符：记录 task={rec_task!r}，'
                                          f'请求 {task!r}')}
                continue
            # r8（第七轮审计 N1 / B5）：身份校验必须完整。r7 只比 basename（把
            # A 的记录映射成 B=PATH_TO_B 就能授权合并 gorch/A）、run_dir 缺失即放行、
            # invocation 只验非空不验等于本次、mergeable 完全没验。这里逐项收紧。
            rec_run = str(data.get('run_dir') or '')
            if not rec_run:
                stale[task] = {'run_record': str(h),
                               'reason': '执行记录缺少 run_dir，无法确认归属'}
                continue
            try:
                same_dir = (pathlib.Path(rec_run).resolve()
                            == pathlib.Path(rd).resolve())
            except (OSError, ValueError):
                same_dir = False
            if not same_dir:
                stale[task] = {'run_record': str(h),
                               'reason': (f'执行记录身份不符：记录 run_dir={rec_run!r}，'
                                          f'请求 {rd!r}（须为同一绝对路径）')}
                continue
            rec_inv = str(data.get('invocation') or '')
            if not rec_inv:
                stale[task] = {'run_record': str(h),
                               'reason': '执行记录缺少 invocation，无法绑定本次调用'}
                continue
            if rec_inv != str(expect_invocation):
                stale[task] = {'run_record': str(h),
                               'reason': (f'执行记录 invocation 不匹配：记录 {rec_inv!r}，'
                                          f'本次 {expect_invocation!r}')}
                continue
            # r9（第八轮审计 N10）：`if data.get('dry_run')` 只判 truthy——缺字段、
            # None、0 都会被当成"真实执行"放行。必须严格等于 False。
            if data.get('dry_run') is not False:
                stale[task] = {'run_record': str(h),
                               'reason': ('执行记录 dry_run 不是严格 False：'
                                          f'{data.get("dry_run")!r}，不授权合并')}
                continue
            if data.get('result') != 'done':
                stale[task] = {
                    'run_record': str(h),
                    'result': data.get('result'),
                    'reason': data.get('reason')
                    or f'本次记录 result={data.get("result")!r}，不是可合并的 done'}
                continue
            if data.get('mergeable') is not True:
                stale[task] = {'run_record': str(h),
                               'result': data.get('result'),
                               'reason': ('本次记录 mergeable 不是严格 True：'
                                          f'{data.get("mergeable")!r}，不可合并')}
                continue
            done[task] = str(h)
        return (done, stale) if with_blocked else done

    # 兜底路径（不给 run_dirs 时）：不再有"文件最新即授权"这种语义。
    # 第四轮 Q1/Q3 + 第五轮 7.3：按 mtime 选"最新的 done"等于谁最后被 touch 谁拿到
    # 合并授权；损坏记录只进 broken 收集、仍让更旧的 done 上来；started_at 拿字符串
    # 比大小；invocation 在真实记录里根本不写。这里逐条收紧，且**不再退化 mtime**。
    for task in tasks:
        entries, broken = [], []
        for h in RUNS.glob(f'{task}-ch*/codex-channel.json'):
            try:
                data = json.loads(h.read_text(encoding='utf-8'))
            except (json.JSONDecodeError, OSError, UnicodeDecodeError) as exc:
                broken.append((str(h), str(exc)))
                continue
            # r8（第七轮审计 A⑤ / N6）：根节点非对象此前会在 data.get 上抛未捕获的
            # AttributeError，把整个 merge 打崩；这里按"记录不可确认"收进 broken。
            if not isinstance(data, dict):
                broken.append((str(h), f'根节点不是对象（{type(data).__name__}）'))
                continue
            # r9（第八轮审计 N10/N12）：七项身份**全部前置**到加入 entries 之前。
            # r8 只在选定"最新记录"之后才验 result / mergeable，等于先用一批不合格
            # 记录参与时间排序、再用它决定"本次执行是哪一条"，诊断顺序也不对。
            if data.get('dry_run') is not False:
                broken.append((str(h),
                               f'dry_run={data.get("dry_run")!r} 不是严格 False'))
                continue
            rec_inv = str(data.get('invocation') or '')
            if not rec_inv:
                broken.append((str(h), '记录缺少 invocation，无法绑定本次调用'))
                continue
            if expect_invocation and rec_inv != str(expect_invocation):
                broken.append((str(h),
                               f'invocation={rec_inv!r} 不是本次 {expect_invocation!r}'))
                continue
            if data.get('result') != 'done':
                broken.append((str(h), f'result={data.get("result")!r} 不是 done'))
                continue
            if data.get('mergeable') is not True:
                broken.append((str(h),
                               f'mergeable={data.get("mergeable")!r} 不是严格 True'))
                continue
            # 身份同样要核（第七轮审计 B5）：task 精确相等、run_dir 必须指回本记录
            # 所在目录——否则"任何 done 就进池"仍在放行不可合并的记录。
            if str(data.get('task') or '') != task:
                broken.append((str(h),
                               f'记录 task={data.get("task")!r} 与目录任务 {task!r} 不符'))
                continue
            rec_run = str(data.get('run_dir') or '')
            try:
                same_dir = (bool(rec_run)
                            and pathlib.Path(rec_run).resolve() == h.parent.resolve())
            except (OSError, ValueError):
                same_dir = False
            if not same_dir:
                broken.append((str(h), f'记录 run_dir={rec_run!r} 不指向本目录'))
                continue
            entries.append({'path': str(h), 'data': data,
                            'started_at': _utc_ts(data.get('started_at')),
                            'inv': str(data.get('invocation') or '')})

        # 任何损坏记录都阻断（第五轮 Q3-1）：此前 broken 只被收集、扫描继续，
        # 只要还有一条更旧的 done 就会拿到授权——坏掉的那次执行被悄悄忽略。
        if broken:
            stale[task] = {
                'run_record': broken[0][0],
                'reason': (f'历史执行记录损坏 {len(broken)} 条，无法确认本次结果：'
                           f'{broken[0][1]}；请显式传 --run-dir')}
            continue
        if not entries:
            stale[task] = {'run_record': None, 'reason': '无真实执行记录'}
            continue
        # started_at 必须是可解析的 UTC ISO（第五轮 Q3-3）：解析不了就阻断，
        # 不再退回 mtime 当弱判据——弱判据本身就是被点名的授权漏洞。
        missing_at = [e for e in entries if e['started_at'] is None]
        if missing_at:
            stale[task] = {
                'run_record': missing_at[0]['path'],
                'reason': ('历史记录缺少可解析的 started_at（UTC ISO8601），'
                           '拒绝按 mtime 授权；请显式传 --run-dir')}
            continue
        empty_inv = [e for e in entries if not e['inv']]
        if empty_inv:
            stale[task] = {
                'run_record': empty_inv[0]['path'],
                'reason': ('历史记录缺少 invocation，无法唯一确定本次执行；'
                           '请显式传 --run-dir')}
            continue
        # 同一 invocation 出现多条记录 = 本次调用结果不唯一（第七轮审计 #5）。
        dup_inv = sorted({i for i in (e['inv'] for e in entries)
                          if sum(1 for e in entries if e['inv'] == i) > 1})
        if dup_inv:
            stale[task] = {
                'run_record': entries[0]['path'],
                'reason': (f'invocation {dup_inv[:3]} 出现多条执行记录，'
                           '无法唯一确定本次结果；请显式传 --run-dir')}
            continue
        best = max(entries, key=lambda e: e['started_at'])
        tie = [e for e in entries if e['started_at'] == best['started_at']]
        if len(tie) > 1:
            stale[task] = {
                'run_record': best['path'],
                'reason': (f'存在 {len(tie)} 条并列 started_at='
                           f'{_ts_label(best["started_at"])} 的记录'
                           '（含同一 invocation 的多条），无法唯一确定本次执行；'
                           '请显式传 --run-dir')}
            continue
        # r9：result / mergeable / dry_run / invocation 已在进 entries 前全部验过，
        # 走到这里说明这条最新记录本身就是合格的可合并 done。
        done[task] = best['path']
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


def _git_out(args, timeout=60):
    """在仓库根跑一条只读 git 命令，返回 (rc|None, stdout.strip())。失败不抛。"""
    try:
        r = subprocess.run([GIT_EXE, '-C', str(ROOT), *args],
                           capture_output=True, text=True, encoding='utf-8',
                           errors='replace', env=_wt_env(), timeout=timeout,
                           creationflags=_NO_WINDOW)
    except Exception:
        return None, ''
    return r.returncode, (r.stdout or '').strip()


def _ref_sha(ref):
    """取某个 ref 的 commit sha；查不到返回空串（调用方按 fail-closed 处理）。"""
    return _git_out(['rev-parse', '--verify', f'{ref}^{{commit}}'])[1]


def _norm_ref(ref):
    """把 `refs/heads/x` 与 `x` 归一成同一个分支名。

    wt merge 的 JSON 里 branch/target 可能带 refs/heads 前缀，直接字符串比对会把
    "合成功了、只是写法不同"误判成目标不符，让整批在 merge 段 SystemExit。
    """
    s = str(ref or '').strip()
    return s[len('refs/heads/'):] if s.startswith('refs/heads/') else s


class _MergeLock:
    """同一 repo+target 的合并窗口互斥（本机文件锁，跨进程）。

    r8（第七轮审计口径②）：SHA 时序判据排除不了「另一个 gorch 进程在同一窗口
    推进同一个 source」。这把锁把同仓合并串行化——这是本工程自己能保证的部分；
    不受本锁约束的外部 git 操作仍是残余风险，已写入报告 §12.5。

    锁目录按 ``RUNS`` 在**运行时**计算：RUNS 是可被测试/编排重定向的模块常量，
    写成模块级常量会让用例把锁落到真实仓库 data/gorch（污染且不可隔离）。
    """

    def __init__(self, target):
        # r10（第九轮审计）：锁键必须先归一化 ref 写法。`main` 与 `refs/heads/main`
        # 指同一个 ref，未归一化会得到两把不同的锁文件，两个 gorch 就能同时进入
        # 同一 target 的取证窗口——锁等于没加。
        # r11（第十轮审计 C-3）：只做 `re.sub` 会**反向**出事——`feature/a` 与
        # `feature_a` 被压成同一个文件名，两个不同 target 互相阻塞（假互斥，
        # 属可用性误杀）。所以文件名用「可读前缀 + 归一后 ref 的 sha256 前 16 位」：
        # 归一后相同 → 摘要必然相同（同锁）；归一后不同 → 摘要必然不同（不同锁）。
        norm_target = _norm_ref(target) or 'target'
        digest = hashlib.sha256(norm_target.encode('utf-8')).hexdigest()[:16]
        safe = re.sub(r'[^0-9A-Za-z._-]', '_', norm_target)[:40] or 'target'
        self.dir = pathlib.Path(RUNS).parent / 'locks'
        self.path = self.dir / f'merge-{safe}-{digest}.lock'

    def __enter__(self):
        self.dir.mkdir(parents=True, exist_ok=True)
        self.fh = open(str(self.path), 'a+')
        try:
            if os.name == 'nt':
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            try:
                self.fh.close()
            except OSError:
                pass
            raise SystemExit(
                f'合并锁被占用（{self.path}）：同仓已有合并在进行，fail-closed（{exc}）')
        return self

    def __exit__(self, *_exc):
        try:
            if os.name == 'nt':
                import msvcrt
                self.fh.seek(0)
                msvcrt.locking(self.fh.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(self.fh.fileno(), fcntl.LOCK_UN)
        except OSError:
            pass
        try:
            self.fh.close()
        except OSError:
            pass
        return False


def merge(batch_dir, tasks=None, target=None, run_dirs=None, only_tasks=None,
          expect_invocation=None, trace=None):

    """串行把已完成任务的分支合回主线；任一失败即停，不跳过错继续合下一个。

    ``target`` 默认取当前检出分支，不交给 wt 的 default branch 默认值——见
    ``_current_branch()`` 里的原因说明。要合到别处（如发布时合 main）必须显式传。

    冲突时 wt 会把 rebase 留在源 worktree 的未完成态，必须人工 abort 或解决后才能继续；
    因此这里宁可整批停下并如实回传原始输出，也不在半合并历史上叠加后续分支。
    """
    done, stale = find_done_tasks(batch_dir, with_blocked=True, run_dirs=run_dirs,
                                  only_tasks=only_tasks,
                                  expect_invocation=expect_invocation)

    if tasks is not None:
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

    # r12（第十一轮审计 E-5）：首条失败即 break，后续任务既不在 merged 也不在
    # failed——现场"归属不明"。attempted / not_attempted 如实回传，由调用方
    # 写进 summary，不再靠推断。trace 为可选出参，保持既有四元返回值不变。
    merged, failed, attempted = [], [], []
    for task in targets:
        attempted.append(task)
        branch = BRANCH_PREFIX + task
        # r9（第八轮审计 N8）：整段因果取证必须在**同一把锁内**——r8 只把
        # `wt_merge()` 包进 with，前态（target_sha / src_before / src_tree / pre_anc）
        # 在锁外取、后态（rc_anc / sha_after / src_after / tree / proof）也在锁外取，
        # 锁只串行了 wt_merge 这一个子进程。同仓另一个 gorch 仍可在释放锁后、后态
        # 采样前推进 target，于是"本次造成"仍可能是别人的推进。
        with _MergeLock(resolved_target):
            target_sha = _ref_sha(resolved_target)   # 锁内取前态
            if not target_sha:
                # r12（第十一轮审计 E-3，高）：取证失败是**预期内**业务失败，不能
                # raise SystemExit——那会绕开 failed/kind 与 run_all 的结构化
                # summary，调用方只看得到进程退出，拿不到"哪个任务、什么类别、
                # 现场有没有被动过"。合并未执行，归 evidence_failure。
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'evidence_failure', 'stdout': '',
                    'stderr': (f'无法取得合并目标 {resolved_target} 的 commit sha，'
                               '未执行合并，fail-closed'),
                    'hint': '未执行合并；确认合并目标 ref/对象可读后重跑。',
                })
                break
            # 调用前把源分支状态钉住（第五轮审计 7.2）：只记 target SHA 不够——
            # ① 源分支在调用前本来就已是 target 祖先时，调用后 is-ancestor 必然为真，
            #    这证明不了"这一次"合入了任何东西（worktree 里的未提交产出根本不进历史）；
            # ② 只要 target tip 变了就算成功，则任何无关进程的推进都能替本任务作证。
            src_before = _ref_sha(branch)
            # r8 口径② 的 B 级证据要在调用前取到：源分支的 tree sha。分支被 wt 删掉后
            # 分支名查不到，但对象仍在，`<sha>^{tree}` 可读。
            src_tree = ''
            if src_before:
                _rc, _t = _git_out(['rev-parse', f'{src_before}^{{tree}}'])
                src_tree = (_t or '').strip() if _rc == 0 else ''
            # r9（第八轮审计 N9）：还需要 target 的**前态 tree**，否则"tree 档"无法
            # 排除"空提交 / revert 回同一个 tree"——那种情况 top_tree == src_tree 也成立，
            # 但 target 的内容其实一个字都没变。
            target_tree_before = ''
            target_tree_err = ''
            if target_sha:
                _rcb, _tb = _git_out(['rev-parse', f'{target_sha}^{{tree}}'])
                if _rcb == 0:
                    target_tree_before = (_tb or '').strip()
                else:
                    target_tree_err = f'rc={_rcb}'
            # r10（第九轮审计 E-4）：前态祖先检查必须对**冻结的** src_before 做。
            # 用可变分支名时，两次读取之间分支被外部移动，pre_anc 与后态 rc_anc
            # 会描述两个不同的 source 状态，判决自相矛盾。
            rc_pre, _ = ((0, '') if not src_before else _git_out(
                ['merge-base', '--is-ancestor', src_before, resolved_target]))
            if not src_before or rc_pre not in (0, 1):
                # 第七轮审计 #4：前态取证失败（SHA 取不到 / rc=128 等）不能折叠成
                # "前态不是祖先"——那样 `not pre_anc` 恒真，只要调后 target 前进且
                # is-ancestor=0 就能通过，等于把取证失败当成功。
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    # r11（第十轮审计 E-6）：失败必须带**类别**，否则 run_all 只能
                    # 把所有失败都写成 kept_for_conflict，自动消费者分不清
                    # 「取证失败可重试」与「真冲突」。三值：evidence_failure /
                    # merge_conflict / proof_failure。
                    'kind': 'evidence_failure',
                    'stdout': '',
                    'stderr': (f'合并前取证失败：源分支 SHA={src_before[:12] or "?"}，'
                               f'is-ancestor rc={rc_pre!r}（只接受 0/1），fail-closed'),
                    'hint': '未执行合并；先核对源分支与目标分支是否可读，再重跑。',
                })
                break
            if not target_tree_before:
                # r10（第九轮审计 E-5）：前态 tree 取证失败必须在调 wt_merge **之前**停。
                # 否则真实合并已经完成（wt 还可能顺手清掉 source 分支），却因
                # content_changed 恒假落进"未证明合入"的通用出口，把"取证失败"
                # 和"确实没合进去"混成同一个结论。
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'evidence_failure',
                    'stdout': '',
                    'stderr': (f'合并前取证失败：target 前态 tree 取不到'
                               f'（{target_tree_err or "空输出"}），未执行合并，fail-closed'),
                    'hint': '未执行合并；先核对合并目标是否可读（rev-parse 失败多为 ref 或对象缺失）。',
                })
                break
            pre_anc = (rc_pre == 0)
            r = wt_merge(branch, target=resolved_target)
            if r.returncode != 0:
                failed.append({
                    'task': task,
                    'branch': branch,
                    'kind': 'merge_conflict',
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
                # r12（第十一轮审计 E-3）：到这一步 wt 已经跑过，合并**可能**发生，
                # 只是回执不可解析——归 proof_failure（不是取证失败，现场可能已动）。
                failed.append({
                    'task': task, 'branch': branch, 'returncode': r.returncode,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': (f'wt merge 输出无法解析（{r.stdout.strip()[:300]}）；'
                               '合并可能已发生但无法确认'),
                    'hint': '人工核对 target 后重跑或人工合；后续分支已停止。',
                })
                break
            # rc=0 不足以证明合进去了（第四轮审计 #8）：要看 wt 自己的 JSON。
            # 实测（临时仓库，2026-11-09）：`wt merge --format json` 返回**对象**，字段是
            # branch / target / committed / squashed / rebased / removed —— **没有 merged**
            # 字段。所以判据不能是 `merged is True`（那样每次合并都会被判失败），改为：
            #   ① branch、target 必须存在且与请求一致；
            #   ② 去 git 侧验一遍到底合没合（target tip 前进，或源分支已成为 target 祖先）。
            obj = data
            if isinstance(data, list):
                obj = next((x for x in data if isinstance(x, dict)), None)
            if not isinstance(obj, dict):
                failed.append({
                    'task': task, 'branch': branch, 'returncode': r.returncode,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': f'wt merge 输出不是对象（{data!r}），合并可能已发生但无法确认',
                    'hint': '人工核对 target 后重跑或人工合；后续分支已停止。',
                })
                break
            got_branch = obj.get('branch')
            got_target = obj.get('target')
            # 回执里 branch/target 必须存在且与请求一致：只在"非空才比"时，
            # `{"merged": true}` 或空字段也能通过并进 merged（审计 Q1）。
            if not got_branch or not got_target:
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': f'wt 回报缺少 branch/target（branch={got_branch!r}, '
                              f'target={got_target!r}），无法确认合到哪',
                    'hint': '回执不完整，按未合并处理；核对主线后再决定重试或人工合。',
                })
                break
            # 同一分支可能被 wt 写成 `x` 或 `refs/heads/x`，先归一化再比，
            # 否则会把"合成功了但写法不同"误判成目标不符而整批 SystemExit。
            if _norm_ref(got_branch) != _norm_ref(branch):
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': f'wt 回报的分支与请求不一致：请求 {branch} 实际 {got_branch}',
                    'hint': '回执身份不符，按未合并处理；人工核对现场后再决定。',
                })
                break
            if _norm_ref(got_target) != _norm_ref(resolved_target):
                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': (f'wt 回报的目标与请求不一致：请求 {resolved_target} '
                               f'实际 {got_target}'),
                    'hint': '回执身份不符，按未合并处理；人工核对现场后再决定。',
                })
                break
            # ② git 侧复核（第五轮审计 7.2）：wt 说 rc=0 也要证明**这一次**把本任务
            #    真的合进去了。成立条件：
            #      a) target tip 相对调用前前进了（progressed）；
            #      b) 且满足其一：
            #         · wt 回执里 committed/squashed/rebased 有一项为真（wt 明确做了
            #           提交/squash 动作，这是"本次动作"的直接证据）；或
            #         · 调用前 sha 现在是 target 的祖先（rc_anc==0），且
            #           - 调用前不是祖先（pre_anc=False）→ 本次把源 tip 带了进来；
            #           - 调用前本来就已是祖先时，要求源 tip 变过（src_moved）——
            #             否则就是"合了一个早就在里面的老提交"，本次产出没进去。
            #    b) 的第二支同时挡掉"无关进程推进 target"（target 动了但源分支不在里面）。
            # r8（第七轮审计 N3）：wt merge 默认会 cleanup 掉源 worktree **与源分支**
            # （见 wt_merge 的注释），squash 之后源 ref 已不存在：
            #   · 用分支名查 merge-base 必然失败 → 真成功被判 failed；
            #   · 强制 src_moved 也必然不成立（分支没了，tip 自然"没变"）。
            # 改为：源 commit 用**调用前 sha** 查祖先（分支删了对象还在），并接受 wt 回执
            # 里的 committed / squashed / rebased 作为"这次确实做了合并动作"的证据。
            # 口径说明：wt 自报不能证明"唯一因果"；正式口径（独占锁 / 可绑定 invocation
            # 的事务回执 / reflog 对应）待 Owner 拍板，本条只先修"真成功被判失败"的误杀。
            rc_anc, _ = _git_out(['merge-base', '--is-ancestor', src_before, resolved_target])
            sha_after = _ref_sha(resolved_target)
            src_after = _ref_sha(branch)          # 分支被 wt 清掉时为空
            progressed = bool(target_sha and sha_after and target_sha != sha_after)
            src_alive = bool(src_after)
            src_moved = bool(src_alive and src_before and src_after != src_before)
            wt_action = any(obj.get(k) is True for k in ('committed', 'squashed', 'rebased'))
            # r8（第七轮审计口径②）：把「本次调用造成」拆成可机检的三级证据，
            # record 里写明用了哪一级，不再是一个布尔 `proven`。
            #   A ff     —— 调用前源不是祖先、调用后调用前的源 tip 是 target 祖先：
            #               本次把这个 tip 带进了 target（历史图直接可核）。
            #   B tree   —— 目标 tip 的 tree 与调用前源分支的 tree 完全相同：squash
            #               把源内容原样落到目标，逐字节可核，不依赖分支名是否还在。
            #   C receipt— wt 回执 committed/squashed/rebased 为真（wt 自报动作）。只在
            #               A/B 都不成立时兜底：worktree 里未提交的产出经 wt 提交后
            #               squash，source 旧 tip 的 tree 与结果 tree 本就不同，此时
            #               A/B 都会判否，若再不给 C 就会把合法 squash 判死。
            top_tree = ''
            if sha_after:
                _rc2, _tt = _git_out(['rev-parse', f'{sha_after}^{{tree}}'])
                top_tree = (_tt or '').strip() if _rc2 == 0 else ''
            # r9（第八轮审计 N9）：三档共同前置 —— target 的**内容**必须真的变了。
            # progressed 只看 SHA，空提交 / revert 回同一个 tree 也会越过它。
            content_changed = bool(target_tree_before and top_tree
                                   and top_tree != target_tree_before)
            ff_ok = False
            if not pre_anc:
                ff_ok = (rc_anc == 0)      # 调用前不是祖先：旧 tip 现在进来了
            elif src_moved and src_after:
                # 调用前已是祖先时，旧 tip 恒为祖先，拿它查 merge-base 证明不了本次
                # （r8 在这里只查 src_before，等于恒真）。必须核**新 tip** 进没进。
                rc_new, _ = _git_out(['merge-base', '--is-ancestor', src_after,
                                      resolved_target])
                ff_ok = (rc_new == 0)
            proof = ''
            if progressed and content_changed and ff_ok:
                proof = 'ff'
            elif (progressed and content_changed and src_tree and top_tree
                  and top_tree == src_tree):
                proof = 'tree'
            elif progressed and content_changed and wt_action:
                proof = 'wt_receipt'
            proven = bool(proof)
            if not progressed or not proven:

                failed.append({
                    'task': task, 'branch': branch, 'returncode': 0,
                    'kind': 'proof_failure',
                    'stdout': r.stdout.strip()[-600:],
                    'stderr': (f'wt 报成功但 git 侧未证明本次合入：'
                               f'调用前已是祖先={pre_anc}，源分支 tip '
                               f'{src_before[:12] or "?"}→{src_after[:12] or "?"}'
                               f'（{"已变" if src_moved else "未变"}），'
                               f'源 ref {"仍在" if src_alive else "已被 wt 删除"}，'
                               f'is-ancestor(src_before) rc={rc_anc}，'
                               f'wt 回执 committed/squashed/rebased={wt_action}，'
                               f'src_tree={src_tree[:12] or "?"} target_tree={top_tree[:12] or "?"}，'
                               f'target tip {target_sha[:12] or "?"}→'
                               f'{sha_after[:12] or "?"}'),

                    'hint': ('按未合并处理：wt 可能把未提交产出留在源 worktree 里。'
                             '核对源 worktree 与主线后再决定重试或人工合；后续分支已停止。'),
                })
                break
            merged.append({'task': task, 'branch': branch,
                           'result': obj, 'run_record': done[task],
                           'source_sha_before': src_before,
                           'source_sha_after': src_after,
                           'pre_ancestor': pre_anc,
                           'wt_action': wt_action,
                           'source_ref_alive': src_alive,
                           'proof': proof,
                           'source_tree_before': src_tree,
                           'target_tree_before': target_tree_before,
                           'target_tree_after': top_tree,

                           'target_sha_after': sha_after})
    if trace is not None:
        trace['attempted'] = attempted
        trace['not_attempted'] = [t for t in targets if t not in attempted]
    return done, merged, failed, stale


def _path_state(p):
    """路径状态四态：exists / absent / wrong_type / unknown（r11 + r12）。

    `Path.is_dir()` 只有两态：权限不足或 IO 异常时它返回 False，与"确实不存在"
    共用一个值，于是不可读的残留目录会被记成"已清理"。r10 把不可确认拆成
    unknown，r11 又把**存在的非目录**（普通文件、symlink、挂载点残留）拆成
    wrong_type——worktree 路径被一个普通文件占据、branch 又恰好已删、登记又已清
    时，就会记 removed，尽管路径还在。

    r12（第十一轮审计 E-1，高）：`os.stat` 会**跟随** symlink。dangling symlink
    的目标不存在 → stat 抛 FileNotFoundError → 落 absent，而路径本身（link 对象）
    实际还在：worktree 路径被 dangling symlink 占据时仍会被记 removed。改用
    `os.lstat`（不跟随）：任何非真实目录（含所有 symlink/reparse 对象）一律
    wrong_type，只有 lstat 明确报"不存在"才是 absent。

    本机实测：Windows junction 的 lstat 仍报目录（islnk=False / isdir=True），
    因此 junction 落 exists 并走正常 wt remove + 回读，不会被记 absent——不属于
    fail-open；但"junction 是否该算残留"是口径问题（报告 §16 残余）。
    """
    try:
        st = os.lstat(str(p))
    except FileNotFoundError:
        return 'absent'
    except OSError:
        return 'unknown'
    if not stat.S_ISDIR(st.st_mode):
        return 'wrong_type'
    return 'exists'


def cleanup(batch_dir, tasks=None, force=False, delete_branch=False):
    """清理残留 worktree 与分支（合并失败、空分支、合并后未清干净时兜底）。

    force=True 才会删带未跟踪文件的 worktree（--force 语义）。
    delete_branch=True 才会强删未合并分支（-D 语义，会丢提交），默认保留。
    """
    batch_dir = pathlib.Path(batch_dir)
    all_tasks = sorted(p.stem for p in batch_dir.glob('*.md') if p.is_file())
    # 语义收紧（第四轮审计 Q1）：None = 全部；空列表 = 一个也不做。
    # 之前 `if tasks` 把空列表当"未指定"，`cleanup(tasks=merged_tasks)` 在没合到
    # 任何任务时会清掉整批现场。
    targets = list(tasks) if tasks is not None else all_tasks
    removed, skipped = [], []
    for task in targets:
        branch = BRANCH_PREFIX + task
        wt_path = WORKTREE_ROOT / task
        dir_state = _path_state(wt_path)
        if dir_state != 'exists':
            # 目录不在 ≠ 清干净（第四轮审计 #7）：半清理态（目录已删、分支还在）此前
            # 被直接记"已不存在"、cleanup 还返回 0。这里补查 worktree 登记与分支。
            br = _branch_state(branch)
            reg = _worktree_registered(wt_path)
            if dir_state == 'absent' and br == 'absent' and reg is False:
                # r7 口径③：两条豁免都必须带独立证据（三处回读值），
                # 不能只凭 wt 的 rc 或一句说明就记成功。
                removed.append({'task': task, 'branch': branch,
                                'worktree': str(wt_path), 'branch_outcomes': [],
                                # r12（第十一轮审计 E-6）：removed 条目**外层**也必须是
                                # 固定 key 集。r11 只统一了 evidence 内层，按
                                # `removed[0]['schema_ok']` 读的 consumer 在前两个出口会
                                # KeyError。缺失维度显式写 None / 空串，不省略键。
                                'result': None, 'schema_ok': None,
                                'wt_remove_rc': None, 'raw_tail': '',
                                'note': '调用前 目录/登记/分支 三处均已不存在，按已清理处理',
                                # r11（第十轮审计 E-4/B7）：三个 removed 出口写**同形**
                                # evidence（同一组 key），不再一处带 dir_exists、一处不带，
                                # 让下游消费者可以按统一 schema 读。
                                'evidence': {'dir_state': dir_state,
                                             'branch_state': br,
                                             'worktree_registered': reg,
                                             'wt_returncode': None,
                                             'exemption': 'pre_absent',
                                             'readback': '目录/登记/分支'}})
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
            dir_state = _path_state(wt_path)
            wt_gone = (dir_state == 'absent')
            br = _branch_state(branch)
            reg = _worktree_registered(wt_path)
            raw_tail = (r.stdout + r.stderr).strip()[-400:]
            if wt_gone and br == 'absent' and reg is False:
                removed.append({'task': task, 'branch': branch,
                                'worktree': str(wt_path), 'branch_outcomes': [],
                                'result': None, 'schema_ok': None,
                                'wt_remove_rc': r.returncode, 'raw_tail': raw_tail,
                                'note': (f'wt remove 返回 rc={r.returncode}（rc<0 表示超时），'
                                         '但 目录/登记/分支 三处均已消失，按已清理处理'),
                                'evidence': {'dir_state': dir_state,
                                             'branch_state': br,
                                             'worktree_registered': reg,
                                             'wt_returncode': r.returncode,
                                             'exemption': 'rc_zero_not_required',
                                             'readback': '目录/登记/分支'}})
                continue
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': (f'rc={r.returncode} 且现场未清干净 '
                                       f'(目录状态={dir_state}, 分支={br}, '
                                       f'登记={"在" if reg is True else reg}) {raw_tail}')})
            continue
        data = _parse_braced_json(r.stdout)
        # wt remove 实测（临时仓库 wtprobe-r5，2026-11-09）：返回数组，元素形如
        #   {"kind":"worktree","branch":"feat/x","path":"…",
        #    "branch_outcome":"deleted","branch_checked_out_at":null}
        # **没有 removed 字段**——与 wt merge 回执同样不能照名字猜字段。
        items = (data if isinstance(data, list)
                 else ([data] if isinstance(data, dict) else []))
        outcomes = [x.get('branch_outcome') for x in items if isinstance(x, dict)]
        # schema 先验、再回读现场（第五轮审计 7.3-5）：rc=0 但回执解析失败、空数组、
        # 元素不是对象、缺 branch_outcome、outcome 不是 deleted，一律 partial。
        # 此前 schema_ok 只被记录、不参与 removed 判定，坏回执照样记成功。
        schema_ok = (bool(items)
                     and all(isinstance(x, dict) for x in items)
                     and all(isinstance(x.get('branch_outcome'), str)
                             and x.get('branch_outcome') for x in items))
        retained = any(o and 'retained' in str(o) for o in outcomes)
        unexpected = [o for o in outcomes if o not in REMOVED_OUTCOMES]
        dir_state = _path_state(wt_path)
        wt_gone = (dir_state == 'absent')
        br = _branch_state(branch)
        reg = _worktree_registered(wt_path)
        if retained:
            # rc=0 也可能"worktree 删了、分支留着"（未合并分支的既定行为）：那是
            # 保留了待处理分支，不等于清理完成，不能记 removed。
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': f'wt 返回 rc=0 但分支被保留（{outcomes}），'
                                      '属预期保留，需确认是否该 -D',
                            'result': data})
            continue
        if not schema_ok:
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': (f'wt remove 结构化回执不可用（schema_ok=False，'
                                       f'items={len(items)}，outcomes={outcomes}）；'
                                       'rc=0 也不能据此记清理完成，需人工核对现场'),
                            'result': data})
            continue
        if unexpected:
            skipped.append({'task': task, 'branch': branch, 'partial': True,
                            'reason': (f'回执 branch_outcome 非 deleted（{outcomes}）；'
                                       '按未清理处理（实测唯一可信值为 deleted）'),
                            'result': data})
            continue
        if wt_gone and br == 'absent' and reg is False:
            removed.append({'task': task, 'branch': branch,
                            'worktree': str(wt_path),
                            'branch_outcomes': outcomes,
                            'result': data, 'schema_ok': schema_ok,
                            'wt_remove_rc': r.returncode, 'raw_tail': '',
                            'note': 'rc=0、schema 合法且 目录/登记/分支 三处回读均已消失',
                            'evidence': {'dir_state': dir_state,
                                         'branch_state': br,
                                         'worktree_registered': reg,
                                         'wt_returncode': r.returncode,
                                         'exemption': 'rc_zero_confirmed',
                                         'readback': '目录/登记/分支'}})
            continue
        skipped.append({'task': task, 'branch': branch, 'partial': True,
                        'reason': (f'wt 返回 rc=0 但现场未清干净 '
                                   f'(目录还在={not wt_gone}, 分支={br}, '
                                   f'登记={"在" if reg is True else reg}, '
                                   f'schema_ok={schema_ok}, outcomes={outcomes})'),
                        'result': data})
        continue
    return removed, skipped


def run_all(batch_dir, prompts_dir, max_channels=MAX_CHANNELS, target=None,
            dry_run=False, force_cleanup=False, invocation=None):
    """一条命令走完 gate → provision → execute → merge → cleanup。

    第四轮口径（一条对上一轮审计一条 fail-open）：
      · invocation 与 target 在开始时固定，全程用同一份，不再中途解析；
      · execute 任一任务非零退出即 stopped_at='execute'，不进 merge；
      · merge 只接受**本次 invocation** 真跑出 result=done 的任务（精确 run-dir），
        纯验证卡（done_no_merge）不进合并池；
      · cleanup 只清**已确认合并成功**的任务，冲突/未尝试/未合并的一律保现场；
      · stopped_at 覆盖 gate/provision/execute/dry_run/merge/cleanup/done；
      · not_merged（stale）与 cleanup 的 partial 都让整次 run 记为未完成。

    ``invocation`` 只用于复现/测试：生产调用一律由本函数就地生成，保证
    「同一次 run 的 gate→execute→merge 共用同一个 invocation」。
    """
    inv = invocation or datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%f')
    resolved_target = (target or _current_branch()).strip()
    base = {'invocation': inv, 'target': resolved_target}
    steps = {}
    rows = gate_check(batch_dir)
    ready = [r['task'] for r in rows if r['verdict'] == '可开工']
    steps['gate'] = {'ready': ready,
                     'blocked': [r['task'] for r in rows if r['verdict'] != '可开工']}
    # 派发前由编排方签发授权清单（第五轮审计 7.3-6）：卡片只能提请求，授权在这一侧
    # 产生并固化；拒绝签发的卡（例如 writes 与 no_change_allowed 自相矛盾）不进执行段。
    manifest_path, refused = grant_invocation(batch_dir, ready, inv, resolved_target)
    _mdata, grants = _load_grants(manifest_path)
    steps['authorizations'] = {
        'manifest': str(manifest_path),
        'refused': refused,
        'tasks': {t: {'write_scope': g.get('write_scope'),
                      'enforced': g.get('write_scope_enforced'),
                      'no_change_allowed': g.get('no_change_allowed'),
                      'allow_non_repo': g.get('allow_non_repo')}
                  for t, g in grants.items()},
    }
    def _stop(at, note):
        # 第七轮审计 #8a：定义必须在首次使用之前（此前定义在校验之后，全部拒签
        # 时先调用会触发局部名未绑定）。
        steps.setdefault('merge', {'merged': [], 'failed': [], 'not_merged': {}})
        steps.setdefault('cleanup', {'removed': [], 'skipped': [],
                                     'kept_for_conflict': []})
        return {**base, 'steps': steps, 'stopped_at': at, 'note': note}

    if refused:
        ready = [t for t in ready if t not in refused]
        steps['gate']['blocked'] = steps['gate']['blocked'] + list(refused)
        if not ready:
            return _stop('gate', '编排方拒绝签发授权（见 authorizations.refused），'
                                 '无可执行任务')

    if not ready:
        return _stop('gate', '没有可开工任务')

    try:
        _, provisioned, p_skipped = provision(batch_dir, tasks=ready)
    except SystemExit as exc:
        steps['provision'] = {'error': str(exc)}
        return _stop('provision', f'provision 失败：{exc}')
    steps['provision'] = {
        'provisioned': [p.get('task') for p in provisioned if isinstance(p, dict)],
        'skipped': p_skipped,
    }

    _, results = execute(batch_dir, prompts_dir, max_channels=max_channels,
                         dry_run=dry_run, invocation=inv, manifest=manifest_path,
                         tasks=ready)
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
    # 只看本轮 ready 的卡：批次里其它卡（done / blocked 等）不该被算成"本次没有
    # 执行记录"，否则 run 会因非 ready 卡恒判失败（第四轮审计 Q1）。
    probe_done, probe_stale = find_done_tasks(batch_dir, with_blocked=True,
                                              run_dirs=run_dirs,
                                              only_tasks=ready,
                                              expect_invocation=inv)
    to_merge = [t for t in ready if t in probe_done]
    # done_no_merge（纯验证卡）是可接受的非合并终态。判定只看记录里的 result 字段
    # （第五轮审计 7.2-1）：此前用 `'done_no_merge' in reason` 子串，任何 blocked
    # 记录只要 reason 里出现这段文字就被当成功终态，从而同时从 stale 与 leftover
    # 里消失、最终可能 stopped_at='done' 且 run 返回 0——这是本轮新引入的 fail-open。
    verified = [t for t in ready if t in probe_stale
                and probe_stale[t].get('result') == 'done_no_merge']
    real_stale = {t: v for t, v in probe_stale.items() if t not in verified}

    merge_trace = {}
    done, merged, failed, stale = merge(batch_dir, tasks=to_merge,
                                        target=resolved_target, run_dirs=run_dirs,
                                        only_tasks=ready,
                                        expect_invocation=inv, trace=merge_trace)
    steps['merge'] = {'merged': [m['task'] for m in merged],
                      'failed': failed, 'not_merged': stale,
                      'verified_only': verified,
                      # r12（第十一轮审计 E-5）：首条失败 break 之后，后续任务既不在
                      # merged 也不在 failed——现场"归属不明"。attempted 与
                      # not_attempted 由 merge() 如实回传，不靠推断。
                      'attempted': merge_trace.get('attempted', []),
                      'not_attempted_after_failure': merge_trace.get('not_attempted', [])}

    if failed:
        # r11（第十轮审计 E-6）：取证失败不是冲突。前态 tree / 源 SHA 取不到时
        # 根本没调 wt_merge，现场原封不动；把它写进 kept_for_conflict 会让调用方
        # 误按冲突流程去 abort/solve rebase（那会把干净现场搞脏）。
        # r12（第十一轮审计 E-4，中）：只按「是不是 evidence」二分仍会把
        # proof_failure（wt 回执不成立 / 回执身份不符）和未知 kind 一起塞进
        # conflict。proof 失败的现场通常**没有** rebase 可 abort，把下游引去
        # 解决不存在的冲突就是新的误导。改成按 kind 四分流，未知单独一档并
        # fail-closed（既不并进 conflict，也不当成可继续）。
        buckets = {'merge_conflict': [], 'evidence_failure': [],
                   'proof_failure': [], 'unknown': []}
        for f in failed:
            k = f.get('kind')
            buckets[k if k in ('merge_conflict', 'evidence_failure', 'proof_failure')
                    else 'unknown'].append(f['task'])
        steps['cleanup'] = {'removed': [], 'skipped': [],
                            'kept_for_conflict': buckets['merge_conflict'],
                            'kept_for_evidence': buckets['evidence_failure'],
                            'kept_for_proof': buckets['proof_failure'],
                            'kept_for_unknown': buckets['unknown']}
        kinds = sorted({f.get('kind') or 'unspecified' for f in failed})
        return {**base, 'steps': steps, 'stopped_at': 'merge',
                'note': (f'合并段停止（失败类别={kinds}），跳过 cleanup 以保留现场；'
                         f'未尝试任务={steps["merge"]["not_attempted_after_failure"]}；'
                         'evidence_failure = 取证未通过且**未执行合并**，可直接重试')}

    # 先判定"是否还有任务没闭合"，再决定要不要清现场：之前 cleanup 跑在 stale
    # 判定之前，一旦最后判失败，该保留的证据已经被删了（审计 Q1）。
    merged_tasks = [m['task'] for m in merged]
    leftover = [t for t in ready if t not in merged_tasks and t not in verified]
    if real_stale or leftover:
        steps['cleanup'] = {'removed': [], 'skipped': [],
                            'kept_for_conflict': merged_tasks,
                            'kept_for_evidence': [], 'kept_for_proof': [],
                            'kept_for_unknown': []}
        return {**base, 'steps': steps, 'stopped_at': 'merge',
                'note': (f'{len(real_stale) + len(leftover)} 个任务未进入合并池'
                         '（见 not_merged / verified_only），未执行 cleanup 以保留现场')}

    # 只清"已确认合并成功"的任务：之前清的是全部 ready，把本轮没尝试的后续任务、
    # 以及 stale 任务的现场一起清掉了（审计 #8）。空列表 = 一个也不做。
    removed, c_skipped = cleanup(batch_dir, tasks=merged_tasks,
                                 force=force_cleanup, delete_branch=False)
    steps['cleanup'] = {'removed': [r['task'] for r in removed],
                        'skipped': c_skipped,
                        'kept_for_conflict': []}

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
    p.add_argument('--tasks', nargs='*', default=None,
                   help='只给这些任务建 worktree（默认 gate 全量；run_all 传过滤后的 ready）')
    e = sub.add_parser('execute', help='并发调 codex_channel 在各自 worktree 执行')
    e.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    e.add_argument('--prompts-dir', required=True, help='prompt 文件目录（<id>.md|.txt）')
    e.add_argument('--max-channels', type=int, default=MAX_CHANNELS, help='并发上限（默认 3）')
    e.add_argument('--dry-run', action='store_true', help='透传给 codex_channel，不真起 Codex')
    e.add_argument('--manifest', default=None,
                   help='编排方签发的 invocation manifest（不给则就地签发一份）')
    e.add_argument('--tasks', nargs='*', default=None,
                   help='只执行这些任务（默认 gate 全量；给了 manifest 时还会按清单收窄）')
    m = sub.add_parser('merge', help='串行把已完成任务的分支合回主线（调 wt merge）')
    m.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    m.add_argument('--tasks', nargs='*', default=None,
                   help='只合这些任务（默认合所有 result=done 的）')
    m.add_argument('--target', default=None,
                   help='合并目标分支（默认当前检出分支；合到 main 属发布动作，须显式传）')
    # r9（第八轮审计 N10）：`--invocation` 改 required。r8 允许不传，函数层就退化成
    # "只验记录自身非空"——任何历史 invocation 的 done 记录都能拿到合并授权。
    # 合并是一个需要身份的动作，没有本次 invocation 就没有可核的归属。
    m.add_argument('--invocation', required=True,
                   help=('本次 invocation（必填）：执行记录的 invocation 必须与它严格相等，'
                         '否则该任务判 stale，不授权合并'))
    m.add_argument('--run-dir', nargs='*', default=None, metavar='TASK=PATH',
                   help=('本次 invocation 的精确 run-dir，可给多个，形如 '
                         'GORCH-A=C:\\...\\runs\\GORCH-A-ch1-2026...。'
                         '不给就拒绝执行：独立 merge 不再按历史 glob/mtime 授权'))
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
        rows, provisioned, skipped = provision(args.batch_dir, tasks=args.tasks)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'provisioned': provisioned, 'skipped_blocked': skipped,
             'tasks': rows},
            ensure_ascii=False, indent=2))
        return 0

    if args.cmd == 'execute':
        rows, results = execute(
            args.batch_dir, args.prompts_dir,
            max_channels=args.max_channels, dry_run=args.dry_run,
            manifest=args.manifest, tasks=args.tasks)
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'results': results, 'tasks': rows},
            ensure_ascii=False, indent=2))
        return 0

    if args.cmd == 'merge':
        # 第五轮审计 7.3-3：独立 merge 不再按历史 glob/mtime 授权。没有精确
        # run-dir 就等于"让磁盘上最后被 touch 的那次执行替这次授权"，直接拒绝。
        if not args.run_dir:
            print(json.dumps(
                {'error': ('独立 merge 必须显式传 --run-dir TASK=PATH；'
                           '历史 glob/mtime 授权已移除。批量路径请用 run 子命令。')},
                ensure_ascii=False, indent=2))
            return 2
        run_dirs = {}
        for spec in args.run_dir:
            if '=' not in spec:
                print(json.dumps({'error': f'--run-dir 需 TASK=PATH 形式：{spec}'},
                                 ensure_ascii=False, indent=2))
                return 2
            task, path = spec.split('=', 1)
            core = task.strip()
            if not core or not path.strip():
                print(json.dumps({'error': f'--run-dir 参数不完整：{spec}'},
                                 ensure_ascii=False, indent=2))
                return 2
            run_dirs[core] = path.strip()
        done, merged, failed, stale = merge(
            args.batch_dir, tasks=args.tasks, target=args.target,
            run_dirs=run_dirs, only_tasks=list(run_dirs),
            expect_invocation=args.invocation)
        # 只跑纯验证卡（result=done_no_merge）也是合法收敛：没有可合并成果，
        # 但也没有失败。此前这种情形一律返回 1（第五轮 Q3-4）。
        verified_only = [t for t, v in stale.items()
                         if v.get('result') == 'done_no_merge']
        real_stale = {t: v for t, v in stale.items() if t not in verified_only}
        print(json.dumps(
            {'batch': str(pathlib.Path(args.batch_dir)),
             'target': args.target or _current_branch(),
             'done_tasks': done, 'merged': merged, 'failed': failed,
             'verified_only': verified_only, 'not_merged': real_stale,
             'run_dirs': run_dirs},
            ensure_ascii=False, indent=2))
        # 任一分支合并失败（含冲突）即非 0；仍有真实 stale 未闭合同样非 0；
        # 什么都没合、也没有 verified_only 的收敛结论时也非 0。
        return 0 if (not failed and not real_stale and (merged or verified_only)) else 1

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
