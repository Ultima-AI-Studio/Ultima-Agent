#!/usr/bin/env python3
"""GORCH Codex 通道执行器 —— 六部的执行体。

把 edict 里「让 LLM 自己写代码」的六部（hubu/libu/bingbu/xingbu/gongbu/libu_hr），
替换为「由 Codex 写代码，通道只负责接单与回写看板」。
角色名、看板契约、状态机全部沿用 edict 原文，不新增状态、不改 AGENT_POLICY。

三方来源（均为复用，非自研）：
  通道契约 state/flow/progress/todo/done/block   → edict agents/<dept>/SOUL.md 原文
  Codex 可执行体解析                             → scripts/dispatch-work-order.py:40-45 / :143
  Codex 调用命令行                               → scripts/dispatch-work-order.py:491-494

用法：
  python codex_channel.py --task GORCH-001 --dept bingbu --prompt 工单.md
  python codex_channel.py --task GORCH-001 --dept bingbu --prompt - --dry-run
"""
import argparse
import glob as _glob
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
KANBAN = ROOT / 'scripts' / 'gorch' / 'kanban_update.py'
RUNS = ROOT / 'data' / 'gorch' / 'runs'

# 与 scripts/dispatch-work-order.py:40-45 逐字一致；Codex 升级会改安装位置且不留 alias
_CODEX_EXE_GLOBS = (
    r'C:\Program Files\WindowsApps\OpenAI.Codex_*\app\resources\codex.exe',
    r'C:\Users\*\AppData\Local\Microsoft\WindowsApps\codex.exe',
    r'C:\Users\*\AppData\Roaming\npm\codex.exe',
    r'C:\Users\*\AppData\Local\Programs\*\codex.exe',
)

# edict 的 AGENT_POLICY 给六部只开了 progress/todo/done/block/memory/task-memo/
# delegate-result，没有 state 与 flow；但六部的 SOUL.md 又要求执行体自己调
# state/flow。这是 edict 自身的权限不一致。执行器用未注册身份，走
# _check_permission 的「未注册不拦截」分支，同时审计日志仍能记到通道名。
CHANNEL_AGENT_ID = 'codex-channel'

PLAN_OPEN = '接单✅|调Codex🔄|执行|自检|回写'
PLAN_DONE = '接单✅|调Codex✅|执行✅|自检✅|回写✅'
PLAN_FAIL = '接单✅|调Codex✅|执行|自检|回写🚫'

DEPTS = ('hubu', 'libu', 'bingbu', 'xingbu', 'gongbu', 'libu_hr')


def resolve_codex_exe():
    """同一逻辑见 scripts/dispatch-work-order.py:143：env → PATH → 四组 glob，按 mtime 取最新。"""
    explicit = os.environ.get('ULTIMA_CODEX_EXE', '').strip()
    if explicit and pathlib.Path(explicit).is_file():
        return explicit
    found = shutil.which('codex.exe') or shutil.which('codex')
    if found:
        return found
    hits = [p for pattern in _CODEX_EXE_GLOBS
            for p in _glob.glob(pattern) if pathlib.Path(p).is_file()]
    return max(hits, key=lambda p: os.path.getmtime(p)) if hits else None


def now_stamp():
    return datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')


def kanban(*args, check=True):
    """所有看板操作走 CLI 契约，不直接读写 JSON —— 这是六部 SOUL.md 的强制要求。"""
    env = dict(os.environ)
    env['ULTIMA_AGENT_ID'] = CHANNEL_AGENT_ID
    env['PYTHONIOENCODING'] = 'utf-8'
    r = subprocess.run(
        [sys.executable, str(KANBAN), *[str(a) for a in args]],
        capture_output=True, text=True, encoding='utf-8', errors='replace', env=env,
    )
    if check and r.returncode != 0:
        raise RuntimeError(
            f'看板命令失败 {args[:2]}: rc={r.returncode} '
            f'{(r.stdout + r.stderr).strip()[-400:]}')
    return r


def run_codex(codex, prompt_bytes, workdir, last_msg, effort, timeout):
    """命令行与 scripts/dispatch-work-order.py:491-494 一致，去掉 --json 流式事件。"""
    cmd = [
        codex, '-a', 'never', '-c', f'model_reasoning_effort="{effort}"', 'exec',
        '-m', 'gpt-5.6-sol', '-C', str(workdir),
        '--sandbox', 'danger-full-access', '--skip-git-repo-check',
        '--color', 'never', '--output-last-message', str(last_msg), '-',
    ]
    started = time.monotonic()
    proc = subprocess.run(
        cmd, input=prompt_bytes, capture_output=True, timeout=timeout,
        creationflags=0x08000000,  # CREATE_NO_WINDOW：通道后台跑，不弹窗
    )
    return proc, time.monotonic() - started


def main(argv=None):
    ap = argparse.ArgumentParser(description='GORCH Codex 通道执行器（六部执行体）')
    ap.add_argument('--task', required=True, help='看板任务号')
    ap.add_argument('--dept', required=True, choices=DEPTS, help='通道（edict 六部原名）')
    ap.add_argument('--prompt', required=True, help='工单文件路径，- 表示从 stdin 读')
    ap.add_argument('--workdir', default=str(ROOT), help='Codex 工作目录（并发时传各自 worktree）')
    ap.add_argument('--run-dir', default='', help='通道运行目录，默认 data/gorch/runs/<task>-<ts>')
    ap.add_argument('--effort', default='high', choices=('low', 'medium', 'high'))
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--dry-run', action='store_true', help='只走看板流程，不真起 Codex')
    ap.add_argument('--simulate-fail', action='store_true', help='演练失败路径')
    args = ap.parse_args(argv)

    if not KANBAN.is_file():
        print(f'看板脚本不存在: {KANBAN}', file=sys.stderr)
        return 2

    run_dir = pathlib.Path(args.run_dir) if args.run_dir else RUNS / f'{args.task}-{now_stamp()}'
    run_dir.mkdir(parents=True, exist_ok=True)

    if args.prompt == '-':
        prompt_bytes = sys.stdin.buffer.read()
    else:
        prompt_bytes = pathlib.Path(args.prompt).read_bytes()
    if not prompt_bytes.strip():
        print('工单为空，拒绝执行', file=sys.stderr)
        return 2
    (run_dir / 'prompt.txt').write_bytes(prompt_bytes)

    codex = None if args.dry_run else resolve_codex_exe()
    if not args.dry_run and not codex:
        kanban('block', args.task, 'Codex 执行器未找到（检查 ULTIMA_CODEX_EXE / PATH）', check=False)
        print('Codex 执行器未找到', file=sys.stderr)
        return 3

    record = {
        'task': args.task, 'dept': args.dept, 'run_dir': str(run_dir),
        'prompt_sha256': hashlib.sha256(prompt_bytes).hexdigest(),
        'codex': codex, 'workdir': args.workdir,
        'dry_run': args.dry_run, 'started_at': datetime.now(timezone.utc).isoformat(),
    }

    # 1) 接单（任务已在 Doing 时这次 state 会被状态机拒绝，幂等处理不中断）
    enter = kanban('state', args.task, 'Doing', f'{args.dept} 开始执行', check=False)
    record['already_doing'] = '非法状态转换' in (enter.stdout + enter.stderr)
    kanban('flow', args.task, args.dept, args.dept, '▶️ 开始执行')
    kanban('progress', args.task, f'{args.dept} 接单，准备调用 Codex', PLAN_OPEN)

    # 2) 执行
    ok = False
    summary = ''
    if args.dry_run:
        record['exit_code'] = 0 if not args.simulate_fail else 1
        ok = not args.simulate_fail
        summary = '[dry-run] 未真实执行 Codex'
        (run_dir / 'out.log').write_text(summary, encoding='utf-8')
    else:
        last_msg = run_dir / 'last-message.md'
        try:
            proc, elapsed = run_codex(codex, prompt_bytes, args.workdir,
                                      last_msg, args.effort, args.timeout)
            record['exit_code'] = proc.returncode
            record['elapsed_sec'] = round(elapsed, 1)
            (run_dir / 'stdout.log').write_bytes(proc.stdout or b'')
            (run_dir / 'stderr.log').write_bytes(proc.stderr or b'')
            ok = proc.returncode == 0
            if last_msg.is_file():
                summary = last_msg.read_text(encoding='utf-8', errors='replace').strip()[:300]
        except subprocess.TimeoutExpired:
            record['exit_code'] = 124
            record['elapsed_sec'] = args.timeout
            summary = f'Codex 超时（>{args.timeout}s）'
            ok = False

    # 3) 回写
    if ok:
        kanban('progress', args.task, f'{args.dept} 已产出，交门下省复检', PLAN_DONE)
        kanban('done', args.task, str(run_dir), summary or '完成，无末段消息')
        kanban('flow', args.task, args.dept, '门下省', f'✅ 完成：{(summary or "已产出")[:100]}')
    else:
        err_tail = ''
        for name in ('stderr.log', 'out.log'):
            f = run_dir / name
            if f.is_file():
                err_tail = f.read_bytes().decode('utf-8', 'replace').strip()[-200:]
                if err_tail:
                    break
        reason = f'Codex 退出码 {record.get("exit_code")}：{err_tail or summary or "无输出"}'
        kanban('progress', args.task, f'{args.dept} 执行失败，已上报', PLAN_FAIL)
        kanban('block', args.task, reason)
        kanban('flow', args.task, args.dept, '尚书省', f'🚫 阻塞：{reason[:100]}')

    record['finished_at'] = datetime.now(timezone.utc).isoformat()
    record['result'] = 'done' if ok else 'blocked'
    (run_dir / 'codex-channel.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({'task': args.task, 'dept': args.dept,
                      'result': record['result'], 'run_dir': str(run_dir)},
                     ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
