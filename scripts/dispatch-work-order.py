"""One registered engineering order per real Codex process; no automatic approval."""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT.parent / '_shared/queue'
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock, process_identity
from tasks.queue_engine.card_contract import check_version_gates

spec = importlib.util.spec_from_file_location('native_environment', ROOT / 'scripts/inspect-native-environment.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)


def registered(order):
    text = (SHARED / 'global-queue-index.md').read_text(encoding='utf-8')
    pattern = r'^\| UltimaAgent \| ' + re.escape(order) + r' \| (\w+) \| ([^\n]*)\|$'
    start, end = text.find('<!-- queue-items:start -->'), text.find('<!-- queue-items:end -->')
    matches = list(re.finditer(pattern, text, re.M))
    if start < 0 or end <= start or len(matches) != 1 or not start < matches[0].start() < end:
        raise ValueError('工单未在全局唯一登记，拒绝派发')
    match = matches[0]
    return text, match, pattern


def state(order, target, reason, run, *, expected=None, expected_run=None):
    path = SHARED / 'global-queue-index.md'
    original, match, pattern = registered(order)
    if expected is not None and match.group(1) != expected:
        raise RuntimeError('工单状态已变化，拒绝覆盖其他裁决')
    if expected_run is not None and expected_run not in match.group(2):
        raise RuntimeError('运行轮次已变化，拒绝旧执行回写')
    (run / ('registry-before-' + target + '.md')).write_text(original, encoding='utf-8')
    text = re.sub(pattern, lambda _: f'| UltimaAgent | {order} | {target} | {reason} |', original, count=1, flags=re.M)
    if path.read_text(encoding='utf-8') != original:
        raise RuntimeError('全局登记已并发变化，拒绝覆盖')
    temporary = path.with_name('global-queue-index.' + run.name + '.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(path)
    subprocess.run([sys.executable, str(SHARED / 'queue-status-gen.py')], check=True,
                   capture_output=True, timeout=20, creationflags=0x08000000)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--order', required=True)
    parser.add_argument('--prompt', required=True, type=Path)
    parser.add_argument('--execute', action='store_true')
    parser.add_argument('--repair', action='store_true')
    args = parser.parse_args()
    order_path = ROOT / 'tasks/queue' / (args.order + '.md')
    if not re.fullmatch(r'wo-s1-[a-z-]+', args.order) or not order_path.is_file():
        raise ValueError('未知开发工单')
    text, match, _ = registered(args.order)
    if match.group(1) not in ({'pending', 'blocked', 'audit'} if args.repair else {'pending'}):
        raise ValueError('当前状态不允许派发；修复续行须显式 --repair')
    prompt = args.prompt.read_text(encoding='utf-8-sig')
    if 'docs/INDEX.md' not in prompt or args.order not in prompt:
        raise ValueError('派发载荷必须引用 INDEX 及当前唯一工单')
    cards = re.findall(r'\| T\d+ (s1-[a-z0-9-]+) \|', order_path.read_text(encoding='utf-8'))
    if not cards:
        raise ValueError('工单没有可核对的任务卡')
    versions = set()
    for card_id in set(cards):
        card = ROOT / 'tasks/cards' / card_id / 'task.md'
        if not card.is_file():
            raise ValueError('工单引用的任务卡缺失')
        version = re.search(r'^-\s*\*\*stage\*\*[^\n]*\b(v\d+\.\d+)', card.read_text(encoding='utf-8-sig'), re.M)
        if not version:
            raise ValueError('任务卡阶段不可核对')
        versions.add(version.group(1))
    if len(versions) != 1:
        raise ValueError('工单引用任务阶段不一致')
    check_version_gates({'card_path': str(ROOT / 'tasks/cards' / cards[0] / 'task.md')}, ROOT / 'tasks')
    if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
        raise ValueError('派发暂停标记存在')
    codex = shutil.which('codex.exe')
    if not codex:
        raise ValueError('Codex 执行器不存在')
    with DispatchLock(SHARED / '.engineering-dispatch.lock'):
        text, match, _ = registered(args.order)
        if match.group(1) not in ({'pending', 'blocked', 'audit'} if args.repair else {'pending'}):
            raise ValueError('锁内复核：工单状态不再允许派发')
        check_version_gates({'card_path': str(ROOT / 'tasks/cards' / cards[0] / 'task.md')}, ROOT / 'tasks')
        if any(not (ROOT / 'tasks/cards' / card_id / 'task.md').is_file() for card_id in cards):
            raise ValueError('锁内复核：任务卡缺失')
        if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
            raise ValueError('锁内复核：派发已暂停')
        processes = native.codex_processes()
        active = [item for item in processes if item['role'] == 'exec']
        if any(item['role'] == 'unknown' for item in processes):
            raise ValueError('Codex 进程用途不明，按忙处理')
        if len(active) >= 3 or any(not item['project'] or Path(item['project']).resolve() == ROOT for item in active):
            raise ValueError('全局或项目实际执行 WIP 闸门未通过')
        if re.search(r'^\| UltimaAgent \| [^|]+ \| executing \|', text, re.M):
            raise ValueError('本项目登记仍有执行中工单，须先核查回执')
        if not args.execute:
            print(json.dumps({'ready': True, 'order': args.order, 'codex_roles': processes}, ensure_ascii=False))
            return 0
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        run = ROOT / 'tasks/queue/runs' / (args.order + '-' + stamp)
        run.mkdir(parents=True, exist_ok=False)
        (run / 'prompt.txt').write_text(prompt, encoding='utf-8')
        (run / 'before.json').write_text(json.dumps({'order': args.order, 'processes': processes}, indent=2), encoding='utf-8')
        parent = os.getppid()
        parent_identity = process_identity(parent)
        if parent_identity is None:
            raise ValueError('父进程已失联，拒绝自治派发')
        final = run / 'final.json'
        command = [codex, '-a', 'never', '-c', 'model_reasoning_effort="high"', 'exec',
                   '-m', 'gpt-5.6-sol', '-C', str(ROOT), '--sandbox', 'danger-full-access',
                   '--skip-git-repo-check', '--json', '--color', 'never',
                   '--output-last-message', str(final), '-']
        state(args.order, 'executing', f'真实工单派发 {run.name}，一单一进程；尚未验收', run, expected=match.group(1))
        worker = None
        guardian = None
        try:
            guardian = subprocess.Popen([sys.executable, str(ROOT / 'tasks/queue_engine/guardian.py'),
                str(os.getpid()), str(process_identity(os.getpid())), str(SHARED / '.pause-dispatch'), str(run / 'done.json')],
                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=0x08000000)
            if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
                raise ValueError('启动前复核：派发已暂停')
            with (run / 'out.jsonl').open('wb') as out, (run / 'err.log').open('wb') as err:
                worker = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=out,
                                          stderr=err, creationflags=0x08000000)
                (run / 'session.json').write_text(json.dumps({'pid': worker.pid,
                    'identity': process_identity(worker.pid), 'parent_pid': parent,
                    'guardian_pid': guardian.pid,
                    'parent_identity': parent_identity, 'started_at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
                worker.stdin.write(prompt.encode('utf-8'))
                worker.stdin.close()
                parent_lost = False
                while worker.poll() is None:
                    parent_lost = parent_lost or process_identity(parent) != parent_identity
                    if parent_lost and not (SHARED / '.pause-dispatch').exists():
                        try:
                            with (SHARED / '.pause-dispatch').open('x', encoding='utf-8') as stream:
                                json.dump({'mode': 'read-only', 'action': 'no-further-dispatch', 'run': run.name}, stream)
                        except FileExistsError:
                            pass
                    time.sleep(0.25)
                code = worker.wait()
            try:
                receipt = json.loads(final.read_text(encoding='utf-8-sig')) if final.is_file() else {}
            except (ValueError, UnicodeError):
                receipt = {}
            valid = (isinstance(receipt, dict) and receipt.get('work_order') == args.order
                     and isinstance(receipt.get('evidence'), list) and bool(receipt['evidence'])
                     and isinstance(receipt.get('landed_files'), list)
                     and all(Path(path).is_file() for path in receipt['evidence']))
            target = 'audit' if code == 0 and valid and receipt.get('status') == 'READY_FOR_REVIEW' else 'blocked'
            if parent_lost:
                target = 'blocked'
            current, _, _ = registered(args.order)
            if target == 'audit' and any(line.startswith('| ') and ' | audit | ' in line
                                         and f'| {args.order} |' not in line for line in current.splitlines()):
                target = 'blocked'
            (run / 'done.json').write_text(json.dumps({'exit_code': code, 'receipt_valid': valid,
                'state': target, 'parent_lost': parent_lost, 'finished_at': datetime.now(timezone.utc).isoformat()}), encoding='utf-8')
            guardian.wait(timeout=5)
            if not parent_lost:
                state(args.order, target, f'真实执行结束 exit={code}；{run.name}；待独立核对，不自动批准或续派', run,
                      expected='executing', expected_run=run.name)
            print(json.dumps({'order': args.order, 'state': target, 'run': str(run)}, ensure_ascii=False))
            return 0 if target == 'audit' else 2
        except Exception as exc:
            (run / 'dispatch-error.json').write_text(json.dumps({'error': type(exc).__name__}), encoding='utf-8')
            if worker is None:
                (run / 'done.json').write_text(json.dumps({'exit_code': None, 'launched': False, 'error': type(exc).__name__}), encoding='utf-8')
                if guardian:
                    guardian.wait(timeout=5)
                state(args.order, 'blocked', f'执行器未启动，派发失败：{run.name}', run, expected='executing', expected_run=run.name)
            # Keep EXECUTING if a launched process might still be alive.
            raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        print(json.dumps({'blocked': True, 'reason': str(exc)}, ensure_ascii=False))
        raise SystemExit(2)
