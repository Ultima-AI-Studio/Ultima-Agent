"""Windowless durable supervisor; completion survives the dispatching parent."""
from __future__ import annotations
import json,os,subprocess,sys
from pathlib import Path
from datetime import datetime,UTC
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tasks.queue_engine.windows_runtime import WindowMonitor
from tasks.queue_engine.dispatcher import process_identity

def main():
    progress=Path(sys.argv[1])
    config=json.loads(progress.read_text(encoding='utf-8'))
    done=Path(config['done'])
    outcome={'exit_code':1,'supervisor_error':'not_started'}
    monitor = WindowMonitor(os.getpid())
    try:
        monitor.start()
        flags=0x08000000 | 0x00000008 if os.name=='nt' else 0
        process=subprocess.Popen(config['command'],cwd=config['cwd'],stdin=subprocess.DEVNULL,
                                 stdout=sys.stdout.buffer,stderr=sys.stderr.buffer,
                                 shell=False,creationflags=flags,close_fds=True,
                                 env={**os.environ, 'PYTHONIOENCODING':'utf-8', 'PYTHONUTF8':'1'})
        config.update(worker_pid=process.pid, worker_identity=process_identity(process.pid))
        temporary_progress=progress.with_name(progress.name+f'.{os.getpid()}.tmp')
        temporary_progress.write_text(json.dumps(config),encoding='utf-8')
        temporary_progress.replace(progress)
        outcome={'exit_code':process.wait()}
    except BaseException as exc:
        outcome={'exit_code':1,'supervisor_error':type(exc).__name__}
    finally:
        try:
            outcome['window_audit'] = monitor.stop()
            if outcome['window_audit']['visible_windows']:
                outcome['supervisor_error'] = 'VISIBLE_DESCENDANT_WINDOW'
                outcome['exit_code'] = 1
        except Exception as exc:
            outcome.update(exit_code=1, supervisor_error='WINDOW_AUDIT_'+type(exc).__name__)
        outcome['finished_at']=datetime.now(UTC).isoformat()
        temporary=done.with_name(done.name+f'.{os.getpid()}.tmp')
        with temporary.open('w',encoding='utf-8') as stream:
            json.dump(outcome,stream);stream.flush();os.fsync(stream.fileno())
        temporary.replace(done)
    return outcome['exit_code']

if __name__=='__main__': raise SystemExit(main())
