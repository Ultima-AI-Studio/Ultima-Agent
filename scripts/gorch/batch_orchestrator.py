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
批次目录约定：只放任务文件，每个 <id>.md 带 frontmatter
  name/status/depends_on/parallel/conflicts_with，同目录引用 <ref>.md。
provision 先跑 gate，仅对判定“可开工”的任务调 wt 建独立 worktree（幂等）。
execute 对可开工任务并发调 codex_channel（--workdir 指向各自 worktree），
执行逻辑全在 codex_channel 内，本文件只做 fan-out/join 与 fail-closed 校验。
"""
import argparse
import json
import os
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
CCPM_DIR = ROOT / 'scripts' / 'gorch' / 'ccpm'
BASH = r'C:\Program Files\Git\bin\bash.exe'
WT_EXE = r'H:\UltimaAI\_vendor\worktrunk-bin\wt.exe'
GIT_CMD_DIR = r'C:\Program Files\Git\cmd'
BASH_TIMEOUT = 60
# 工单 frontmatter 允许的状态词（与 ccpm is_done_status / next.sh 对齐）。
VALID_STATUSES = {'open', 'in-progress', 'in_progress',
                 'closed', 'completed', 'done'}
# 并发 worktree 集中根目录（仓库外，避免与历史 ~/.codex/worktrees 混淆）。
WORKTREE_ROOT = pathlib.Path(r'H:\UltimaAI\_worktrees\gorch')
WT_TIMEOUT = 180
BRANCH_PREFIX = 'gorch/'
# 执行段是现成件（codex_channel.py），本编排只负责并发调用它，不重写执行逻辑。
CHANNEL_SCRIPT = ROOT / 'scripts' / 'gorch' / 'codex_channel.py'
MAX_CHANNELS = 3


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
            f"source '{lib}'; "
            f"printf 'STATUS:%s\\n' \"$(frontmatter_field '{tb}' status)\"; "
            f"printf 'UNMET:%s\\n' \"$(unmet_deps '{tb}')\"; "
            f"printf 'CONFLICTS:%s\\n' \"$(active_conflicts '{tb}')\""
        )
        try:
            r = subprocess.run([BASH, '-c', script], capture_output=True,
                               text=True, encoding='utf-8', errors='replace',
                               timeout=BASH_TIMEOUT)
        except subprocess.TimeoutExpired:
            raise SystemExit(
                f'ccpm 判定超时 {task.name}（{BASH_TIMEOUT}s），fail-closed 不派发')
        if r.returncode != 0:
            raise SystemExit(
                f'ccpm 判定失败 {task.name}: rc={r.returncode} {r.stderr.strip()}')
        if r.stderr.strip():
            raise SystemExit(
                f'ccpm 判定出现错误输出 {task.name}: {r.stderr.strip()}')

        seen = set()
        status = ''
        unmet, conflicts = [], []
        for line in r.stdout.splitlines():
            if line.startswith('STATUS:'):
                status = line[len('STATUS:'):].strip()
                seen.add('STATUS')
            elif line.startswith('UNMET:'):
                unmet = line[len('UNMET:'):].split()
                seen.add('UNMET')
            elif line.startswith('CONFLICTS:'):
                conflicts = line[len('CONFLICTS:'):].split()
                seen.add('CONFLICTS')

        # fail-closed：三个标记必须齐全、status 必须是已知合法值。
        # 调用/读取不可靠时宁可报错，也不把缺失当成“开放/无依赖”而放行。
        missing = {'STATUS', 'UNMET', 'CONFLICTS'} - seen
        if missing:
            raise SystemExit(
                f'ccpm 输出不完整 {task.name}: 缺 {sorted(missing)}，fail-closed 不派发')
        if status not in VALID_STATUSES:
            raise SystemExit(
                f'ccpm 读到未知状态 {task.name}: {status!r}，fail-closed 不派发')

        # 值/空映射（确定性，非算法）：判定词只反映 ccpm 函数的输出。
        if status != 'open':
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
        })
    return rows


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
                           env=_wt_env(), timeout=WT_TIMEOUT)
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


def execute(batch_dir, prompts_dir, max_channels=MAX_CHANNELS, dry_run=False):
    """对可开工任务并发调 codex_channel（--workdir 指向各自 worktree）。

    执行逻辑全在 codex_channel 内；本函数只做：校验、fan-out 起进程、join 收集。
    并发用标准库 subprocess（fan-out + join），分批受 max_channels 限制。
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
        jobs.append((task, wt_path, prompt))

    results = []
    # 分批：每批最多 max_channels 个进程并发，批内 fan-out 后 join，再进下一批。
    for start in range(0, len(jobs), max_channels):
        batch = jobs[start:start + max_channels]
        procs = []
        for channel, (task, wt_path, prompt) in enumerate(batch, start=1):
            cmd = [sys.executable, str(CHANNEL_SCRIPT),
                   '--task', task, '--channel', str(channel),
                   '--prompt', str(prompt), '--workdir', str(wt_path)]
            if dry_run:
                cmd.append('--dry-run')
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                 text=True, encoding='utf-8', errors='replace')
            procs.append((task, channel, p))
        for task, channel, p in procs:
            out, err = p.communicate()
            results.append({
                'task': task,
                'channel': channel,
                'returncode': p.returncode,
                'stdout': out.strip(),
                'stderr': err.strip()[-300:],
            })
    return rows, results


def main(argv=None):
    ap = argparse.ArgumentParser(description='GORCH 多通道薄编排（只接线）')
    sub = ap.add_subparsers(dest='cmd', required=True)
    g = sub.add_parser('gate', help='开工前判定（调 ccpm 原函数）')
    g.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    p = sub.add_parser('provision', help='对可开工任务用 wt 建隔离 worktree')
    p.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    e = sub.add_parser('execute', help='并发调 codex_channel 在各自 worktree 执行')
    e.add_argument('batch_dir', help='批次任务目录（只放 <id>.md）')
    e.add_argument('--prompts-dir', required=True, help='prompt 文件目录（<id>.md|.txt）')
    e.add_argument('--max-channels', type=int, default=MAX_CHANNELS, help='并发上限（默认 3）')
    e.add_argument('--dry-run', action='store_true', help='透传给 codex_channel，不真起 Codex')
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


if __name__ == '__main__':
    sys.exit(main())
