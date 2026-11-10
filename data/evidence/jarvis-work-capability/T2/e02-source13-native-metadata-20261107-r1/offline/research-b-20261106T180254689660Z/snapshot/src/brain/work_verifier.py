"""Independent readback of this request's successful SDK writes."""
from pathlib import Path
import hashlib
from .work_tools import checked_path


def verify_artifacts(binding, write_candidates):
    if not write_candidates:
        raise ValueError('No successful write in this request')
    latest = {}
    for candidate in write_candidates:
        for key in ('request_id', 'session_id', 'task_id'):
            if candidate.get(key) != getattr(binding, key):
                raise ValueError('Artifact identity mismatch')
        if not candidate.get('success') or not candidate.get('call_id'):
            raise ValueError('Unsuccessful or unattributed write')
        latest[candidate['path']] = candidate
    artifacts = []
    for path, candidate in latest.items():
        target = checked_path(binding, path)
        raw = target.read_bytes()
        expected = candidate['content']
        if not isinstance(expected, str) or raw.decode('utf-8').replace('\r\n', '\n') != expected.replace('\r\n', '\n'):
            raise ValueError('Readback content mismatch')
        artifacts.append({k: candidate[k] for k in ('request_id', 'session_id', 'task_id', 'call_id')})
        artifacts[-1].update(path=str(target), sha256=hashlib.sha256(raw).hexdigest(), verified=True)
    return artifacts
