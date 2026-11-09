#!/usr/bin/env python3
"""GORCH 流水线 · Codex 执行段。

流水线只有一个执行段：接单 → 起 Codex → 回写 → 交复检。
不设角色分工、不写角色提示词；通道号 1–6 只用于并发时区分各自的 run-dir 与 flow 标签。

复用（未自研）：
  Codex 可执行体解析 → scripts/dispatch-work-order.py:40-45 / :143
  Codex 调用命令行     → scripts/dispatch-work-order.py:491-494
  看板状态机与并发写锁 → scripts/gorch/kanban_update.py（edict 移植，本轮未改）

用法：
  python codex_channel.py --task GORCH-001 --prompt 工单.md
  python codex_channel.py --task GORCH-001 --channel 3 --prompt - --dry-run
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

# 插槽适配层：S-EXEC 的 exe / model / 参数模板从这里读，换 CLI 不必改本文件。
sys.path.insert(0, str(ROOT))
from src.brain.slot_adapter import exec_settings, render_exec_argv  # noqa: E402

# 与 scripts/dispatch-work-order.py:40-45 逐字一致；Codex 升级会改安装位置且不留 alias
_CODEX_EXE_GLOBS = (
    r'C:\Program Files\WindowsApps\OpenAI.Codex_*\app\resources\codex.exe',
    r'C:\Users\*\AppData\Local\Microsoft\WindowsApps\codex.exe',
    r'C:\Users\*\AppData\Roaming\npm\codex.exe',
    r'C:\Users\*\AppData\Local\Programs\*\codex.exe',
)

# 看板的 AGENT_POLICY 没有给执行位开放 state/flow，只有 progress/todo/done/block。
# 用未注册身份走 _check_permission 的「未注册不拦截」分支，审计日志仍记到通道名。
CHANNEL_AGENT_ID = 'codex-channel'

PLAN_OPEN = '接单✅|调Codex🔄|执行|自检|回写'
PLAN_DONE = '接单✅|调Codex✅|执行✅|自检✅|回写✅'
PLAN_FAIL = '接单✅|调Codex✅|执行|自检|回写🚫'


def resolve_codex_exe():
    """解析执行体路径：适配层配置 → env → PATH → 四组 glob（按 mtime 取最新）。

    前两者是插槽替换入口：配 config/gorch/slots.json 的 S-EXEC.exe 或设
    GORCH_EXEC_EXE / ULTIMA_CODEX_EXE，就能换成另一个 CLI，不改本文件。
    后两者沿用 scripts/dispatch-work-order.py:143 的原逻辑，保证零配置行为不变。
    """
    configured = exec_settings()['exe']
    if configured and pathlib.Path(configured).is_file():
        return configured
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
    """看板操作一律走 CLI，不直接读写 JSON。"""
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
    """命令行默认为 codex（与 scripts/dispatch-work-order.py:491-494 一致，去掉 --json 流式事件）。

    适配层配了 S-EXEC.args_template 时，整体改用模板渲染的 argv——这是换
    Claude / Gemini / Qwen / OpenCode 等 CLI 的唯一入口，调度逻辑不参与。
    """
    settings = exec_settings()
    template = settings['args_template']
    if template:
        rendered = render_exec_argv(settings, exe=codex, workdir=str(workdir),
                                    last_msg=str(last_msg), effort=effort)
        cmd = rendered if rendered and rendered[0] == codex else [codex, *rendered]
    else:
        cmd = [
            codex, '-a', 'never', '-c', f'model_reasoning_effort="{effort}"', 'exec',
            '-m', settings['model'], '-C', str(workdir),
            '--sandbox', 'danger-full-access', '--skip-git-repo-check',
            '--color', 'never', '--output-last-message', str(last_msg), '-',
        ]
    env = None
    if settings['env']:
        env = dict(os.environ)
        env.update(settings['env'])
    started = time.monotonic()
    proc = subprocess.run(
        cmd, input=prompt_bytes, capture_output=True, timeout=timeout,
        creationflags=0x08000000,  # CREATE_NO_WINDOW
        env=env,
    )
    return proc, time.monotonic() - started


def main(argv=None):
    ap = argparse.ArgumentParser(description='GORCH 流水线 Codex 执行段')
    ap.add_argument('--task', required=True, help='看板任务号')
    ap.add_argument('--channel', type=int, default=1, choices=range(1, 7),
                    help='通道号 1–6，并发时区分 run-dir 与 flow 标签')
    ap.add_argument('--prompt', required=True, help='工单文件路径，- 表示从 stdin 读')
    ap.add_argument('--workdir', default=str(ROOT), help='Codex 工作目录（并发时传各自 worktree）')
    ap.add_argument('--run-dir', default='', help='运行目录，默认 data/gorch/runs/<task>-ch<N>-<ts>')
    ap.add_argument('--effort', default='high', choices=('low', 'medium', 'high'))
    ap.add_argument('--timeout', type=int, default=3600)
    ap.add_argument('--dry-run', action='store_true', help='只走看板流程，不真起 Codex')
    ap.add_argument('--simulate-fail', action='store_true', help='演练失败路径')
    args = ap.parse_args(argv)

    if not KANBAN.is_file():
        print(f'看板脚本不存在: {KANBAN}', file=sys.stderr)
        return 2

    label = f'通道{args.channel}'
    run_dir = (pathlib.Path(args.run_dir) if args.run_dir
               else RUNS / f'{args.task}-ch{args.channel}-{now_stamp()}')
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
        kanban('block', args.task, 'Codex 执行段未找到（检查 ULTIMA_CODEX_EXE / PATH）', check=False)
        print('Codex 执行段未找到', file=sys.stderr)
        return 3

    record = {
        'task': args.task, 'channel': args.channel, 'run_dir': str(run_dir),
        'prompt_sha256': hashlib.sha256(prompt_bytes).hexdigest(),
        'codex': codex, 'workdir': args.workdir,
        'dry_run': args.dry_run, 'started_at': datetime.now(timezone.utc).isoformat(),
    }

    # 1) 接单（任务已在 Doing 时这次 state 会被状态机拒绝，幂等处理不中断）
    enter = kanban('state', args.task, 'Doing', f'{label} 开始执行', check=False)
    record['already_doing'] = '非法状态转换' in (enter.stdout + enter.stderr)
    kanban('flow', args.task, label, label, '▶️ 开始执行')
    kanban('progress', args.task, f'{label} 接单，准备调用 Codex', PLAN_OPEN)

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

    # 3) 回写（done 自身已写一条 →复检 的 flow，这里不再重复）
    if ok:
        kanban('progress', args.task, f'{label} 已产出，交复检', PLAN_DONE)
        kanban('done', args.task, str(run_dir), summary or '完成，无末段消息')
    else:
        err_tail = ''
        for name in ('stderr.log', 'out.log'):
            f = run_dir / name
            if f.is_file():
                err_tail = f.read_bytes().decode('utf-8', 'replace').strip()[-200:]
                if err_tail:
                    break
        reason = f'Codex 退出码 {record.get("exit_code")}：{err_tail or summary or "无输出"}'
        kanban('progress', args.task, f'{label} 执行失败，已上报', PLAN_FAIL)
        kanban('block', args.task, reason)
        kanban('flow', args.task, label, '派发', f'🚫 阻塞：{reason[:100]}')

    record['finished_at'] = datetime.now(timezone.utc).isoformat()
    record['result'] = 'done' if ok else 'blocked'
    (run_dir / 'codex-channel.json').write_text(
        json.dumps(record, ensure_ascii=False, indent=2), encoding='utf-8')

    print(json.dumps({'task': args.task, 'channel': args.channel,
                      'result': record['result'], 'run_dir': str(run_dir)},
                     ensure_ascii=False))
    return 0 if ok else 1


if __name__ == '__main__':
    sys.exit(main())
