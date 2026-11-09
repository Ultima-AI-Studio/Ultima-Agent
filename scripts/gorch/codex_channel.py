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
GIT_EXE = r'C:\Program Files\Git\cmd\git.exe'
# 子进程不建控制台窗口（L78）
_NO_WINDOW = 0x08000000 if sys.platform == 'win32' else 0

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


def worktree_state(workdir):
    """执行端到底有没有在 worktree 里留下改动。

    退出码 0 只说明 CLI 正常退出，不说明它写过东西：Codex 可以一声不响地跑完、
    什么都不改，回执照样 done 再被 merge 合进主线，等于把"没干活"当成果。
    返回 (kind, detail)：
      changed  有改动，detail 是 git status 首段（留作证据）
      clean    干净，一个字节都没动
      not_repo 不是 git 工作树，无从校验（保持只看退出码，记下供审计）
      error    查不动（git 不存在/超时/status 失败），fail-closed
    """
    try:
        probe = subprocess.run(
            [GIT_EXE, '-C', str(workdir), 'rev-parse', '--is-inside-work-tree'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=30, creationflags=_NO_WINDOW)
    except Exception:
        return 'error', 'rev-parse 调用失败'
    if probe.returncode != 0 or probe.stdout.strip() != 'true':
        return 'not_repo', (probe.stderr or '').strip()[:200]
    try:
        st = subprocess.run(
            [GIT_EXE, '-C', str(workdir), 'status', '--porcelain'],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=180, creationflags=_NO_WINDOW)
    except Exception:
        return 'error', 'git status 调用失败'
    if st.returncode != 0:
        return 'error', (st.stderr or '').strip()[:200]
    text = (st.stdout or '').strip()
    return ('changed', text) if text else ('clean', '')


def _status_set(detail):
    """把 git status --porcelain 文本拆成行集合，用于执行前后对比。

    第三轮审计：只有"执行后一次快照"无法区分"本次改的"和"worktree 本来就有"的。
    provision 幂等复用既有 worktree 时，旧改动会被算成本次成果。这里用执行前
    快照做基线，只有**相对基线新增的行**才算本次产出。
    """
    return {ln for ln in (detail or '').splitlines() if ln.strip()}


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
    ap.add_argument('--allow-non-repo', action='store_true',
                    help='允许 workdir 不是 git 工作树（仅手工验证用；批量路径默认 fail-closed）')
    ap.add_argument('--no-change-allowed', action='store_true',
                    help=('本次任务按约定不产生仓库改动（纯验证卡、只回 last-message.md 的报告卡）。'
                          '默认不带：worktree 零改动一律判空产出 blocked'))
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
    guard_reason = ''
    if args.dry_run:
        record['exit_code'] = 0 if not args.simulate_fail else 1
        ok = not args.simulate_fail
        summary = '[dry-run] 未真实执行 Codex'
        (run_dir / 'out.log').write_text(summary, encoding='utf-8')
    else:
        last_msg = run_dir / 'last-message.md'
        # 执行前基线（第三轮审计 A4）：只认相对基线**新增**的改动，
        # 复用脏 worktree 时不把旧文件当成本次产出。
        base_kind, base_detail = worktree_state(args.workdir)
        record['worktree_baseline'] = base_kind
        if base_kind == 'changed':
            record['worktree_baseline_dirty'] = base_detail[:2000]
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
            # 产出校验：done 不能只凭退出码（§七-8）。只在退出码已为 0 时追加判定，
            # 退出码非 0 的失败原因仍以原生错误为准，不被这里的结论覆盖。
            if ok:
                kind, detail = worktree_state(args.workdir)
                record['worktree_state'] = kind
                record['worktree_changes'] = (detail or '')[:2000]
                # 本次产出 = 相对基线新增的条目（第三轮审计 A4）
                before = _status_set(base_detail) if base_kind == 'changed' else set()
                fresh = _status_set(detail) - before
                record['worktree_new_changes'] = '\n'.join(sorted(fresh))[:2000]
                if kind == 'clean':
                    if args.no_change_allowed:
                        record['worktree_state_note'] = (
                            'clean，按 --no-change-allowed 放行（本次约定不产生仓库改动）')
                    else:
                        ok = False
                        guard_reason = ('Codex 退出码 0，但 worktree 无任何改动——'
                                        '判空产出，不写 done（执行端没留下任何可合并内容）。'
                                        '若本次本就约定不改仓库，须显式加 --no-change-allowed')
                elif kind == 'changed' and base_kind == 'changed' and not fresh:
                    ok = False
                    guard_reason = ('Codex 退出码 0，worktree 有改动但相对执行前基线无新增——'
                                    '改动全部来自复用前既有的脏状态，判空产出，不写 done')
                elif kind == 'error':
                    ok = False
                    guard_reason = f'无法确认 worktree 改动，fail-closed：{detail}'
                elif kind == 'not_repo':
                    # 批量路径下"不是 git 工作树"等于无法确认产出：get worktree 的编排
                    # 一定给的是 worktree，落到 not_repo 说明接线错了或 workdir 指错。
                    # 只有明确声明无仓库（手工验证场景）才放行（第二轮审计）。
                    if args.allow_non_repo:
                        record['worktree_state_note'] = 'not_repo，已按 --allow-non-repo 放行'
                    else:
                        ok = False
                        guard_reason = ('workdir 不是 git 工作树，无法确认产出，'
                                        '批量路径 fail-closed（确需在无仓库目录执行时加 '
                                        '--allow-non-repo）')
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
        reason = guard_reason or (
            f'Codex 退出码 {record.get("exit_code")}：{err_tail or summary or "无输出"}')
        record['reason'] = reason
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
