"""Authorized Windows maintenance restart with a durable handoff and dispatch pause."""
import argparse
import ctypes
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock, process_identity

def write(path, data):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temporary.replace(path)

def environment():
    spec = importlib.util.spec_from_file_location('native_restart_check', ROOT / 'scripts/inspect-native-environment.py')
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    roles = native.codex_processes()
    if any(row['role'] in {'exec', 'unknown'} for row in roles):
        raise RuntimeError('Active or unknown Codex work prevents this maintenance window')
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetTickCount64.restype = ctypes.c_ulonglong
    kernel.OpenProcess.argtypes = [ctypes.c_ulong, ctypes.c_int, ctypes.c_ulong]
    kernel.OpenProcess.restype = ctypes.c_void_p
    kernel.GetExitCodeProcess.argtypes = [ctypes.c_void_p, ctypes.POINTER(ctypes.c_ulong)]
    kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    kernel.WaitForSingleObject.restype = ctypes.c_ulong
    kernel.CloseHandle.argtypes = [ctypes.c_void_p]
    old_state = {}
    old_handle = kernel.OpenProcess(0x1000 | 0x100000, False, 59328)
    if old_handle:
        try:
            code = ctypes.c_ulong()
            if not kernel.GetExitCodeProcess(old_handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            old_state = {'exit_code': code.value, 'wait_status': kernel.WaitForSingleObject(old_handle, 0)}
        finally:
            kernel.CloseHandle(old_handle)
    else:
        old_state = {'open_error': ctypes.get_last_error()}
    uptime = kernel.GetTickCount64()
    now = datetime.now(timezone.utc)
    return {'at_utc': now.isoformat(), 'uptime_ms': uptime,
            'boot_time_estimate_utc': (now - timedelta(milliseconds=uptime)).isoformat(),
            'codex_roles': roles, 'old_test_process_identity': process_identity(59328),
            'old_test_process_kernel': old_state,
            'identity_none_is_not_proof_of_absence': True}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['prepare', 'arm', 'perform'])
    parser.add_argument('--evidence', required=True, type=Path)
    args = parser.parse_args()
    evidence = args.evidence.resolve()
    if not evidence.is_relative_to(ROOT / 'logs/maintenance'):
        raise ValueError('Maintenance evidence must be inside this project logs/maintenance')
    shared = ROOT.parent / '_shared/queue'
    if args.action == 'prepare':
        evidence.mkdir(parents=True, exist_ok=False)
        with DispatchLock(shared / '.engineering-dispatch.lock'):
            baseline = environment()
            register = shared / 'global-queue-index.md'
            text = register.read_text(encoding='utf-8')
            if any(' | executing | ' in line for line in text.splitlines() if line.startswith('| ')):
                raise RuntimeError('Registered executing work prevents maintenance')
            token = str(uuid.uuid4())
            markers = []
            for path in [shared / '.pause-dispatch', ROOT / 'tasks/.pause-dispatch']:
                if path.exists():
                    markers.append({'path': str(path), 'created_by_this_maintenance': False,
                                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
                else:
                    data = {'mode': 'read-only', 'action': 'no-further-dispatch', 'maintenance_token': token,
                            'reason': 'Owner authorized Windows restart then W1 revalidation', 'evidence': str(evidence)}
                    with path.open('x', encoding='utf-8') as stream:
                        json.dump(data, stream)
                    markers.append({'path': str(path), 'created_by_this_maintenance': True,
                                    'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
            (evidence / 'global-queue.before.md').write_bytes(register.read_bytes())
            head = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], creationflags=0x08000000).decode().strip()
            baseline.update(maintenance_token=token, dispatch_markers=markers, git_head=head,
                            user_authorization='允许在维护窗口重启 Windows，之后继续复验并收口 W1',
                            resume_heartbeat='windows-ultimaagent-w1', version_freeze_approved=False)
            write(evidence / 'before.json', baseline)
        print(json.dumps({'prepared': True, 'evidence': str(evidence), 'baseline': baseline}, ensure_ascii=False))
    elif args.action == 'arm':
        baseline = json.loads((evidence / 'before.json').read_text(encoding='utf-8'))
        assert baseline['user_authorization']
        if (evidence / 'armed.json').exists():
            raise ValueError('Restart already armed; refuse duplicate')
        with (evidence / 'helper.stdout.log').open('wb') as out, (evidence / 'helper.stderr.log').open('wb') as err:
            child = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'perform', '--evidence', str(evidence)],
                                     cwd=ROOT, stdin=subprocess.DEVNULL, stdout=out, stderr=err,
                                     creationflags=0x08000000 | 0x00000200)
        record = {'at_utc': datetime.now(timezone.utc).isoformat(), 'helper_pid': child.pid,
                  'helper_identity': process_identity(child.pid), 'delay_seconds': 60,
                  'mode': 'normal restart; no force flag', 'maintenance_token': baseline['maintenance_token']}
        write(evidence / 'armed.json', record)
        print(json.dumps(record))
    else:
        time.sleep(60)
        try:
            baseline = json.loads((evidence / 'before.json').read_text(encoding='utf-8'))
            with DispatchLock(shared / '.engineering-dispatch.lock'):
                live = environment()
                old_boot = datetime.fromisoformat(baseline['boot_time_estimate_utc'])
                new_boot = datetime.fromisoformat(live['boot_time_estimate_utc'])
                if abs((old_boot - new_boot).total_seconds()) > 30:
                    raise RuntimeError('Boot already changed; refuse a second restart')
                for marker in baseline['dispatch_markers']:
                    path = Path(marker['path'])
                    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != marker['sha256']:
                        raise RuntimeError('Dispatch pause changed; refuse restart')
                text = (shared / 'global-queue-index.md').read_text(encoding='utf-8')
                if any(' | executing | ' in line for line in text.splitlines() if line.startswith('| ')):
                    raise RuntimeError('New registered executing work; refuse restart')
                command = [str(Path(os.environ['SystemRoot']) / 'System32/shutdown.exe'), '/r', '/t', '0',
                           '/d', 'p:0:0', '/c', 'UltimaAgent W1 Owner authorized maintenance restart']
                write(evidence / 'restart-intent.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                      'maintenance_token': baseline['maintenance_token'], 'command': command, 'preflight': live,
                      'actual_restart_verified': False})
                result = subprocess.run(command, capture_output=True, timeout=15, creationflags=0x08000000)
                write(evidence / 'restart-command-result.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                      'exit_code': result.returncode, 'stdout': result.stdout.decode(errors='replace'),
                      'stderr': result.stderr.decode(errors='replace'), 'actual_restart_verified': False})
        except Exception as exc:
            write(evidence / 'restart-error.json', {'at_utc': datetime.now(timezone.utc).isoformat(),
                  'error': f'{type(exc).__name__}: {exc}', 'actual_restart_verified': False})
            raise

if __name__ == '__main__':
    main()
