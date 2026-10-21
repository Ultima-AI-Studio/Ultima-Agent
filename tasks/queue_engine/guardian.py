"""Bounded read-only guardian: stop on run completion or parent identity loss."""
import json
from pathlib import Path
import sys
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tasks.queue_engine.dispatcher import process_identity


def guard(parent_pid, parent_identity, marker, done):
    marker, done = Path(marker), Path(done)
    while True:
        try:
            alive = process_identity(parent_pid) == parent_identity
        except OSError:
            alive = False
        if not alive:
            payload = {'parent_pid': parent_pid, 'parent_identity': parent_identity,
                       'mode': 'read-only', 'action': 'graceful-exit'}
            # Parent loss disables future dispatch; this process never dispatches work.
            try:
                with marker.open('x', encoding='utf-8') as stream:
                    json.dump(payload, stream)
            except FileExistsError:
                pass
            return 0
        if done.is_file() and done.stat().st_size:
            return 0
        time.sleep(.05)


if __name__ == '__main__':
    raise SystemExit(guard(int(sys.argv[1]), sys.argv[2], sys.argv[3], sys.argv[4]))
