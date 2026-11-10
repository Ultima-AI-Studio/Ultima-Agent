"""Test child only: no real model, network, UI or process operations."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

N = Path(__file__).resolve().parents[1]
Q = N.parent / 'e02-source13-exact-probe-20261106'
PROFILE = Q / 'profile-preparation/profile.py'
PROFILE_SHA = '444081b115829e29d9203601091fac5303b0facb4f7b65ae0f9101b63400f29e'

def main():
    if hashlib.sha256(PROFILE.read_bytes()).hexdigest() != PROFILE_SHA:
        raise ValueError('Accepted cold-import guard drift')
    spec = importlib.util.spec_from_file_location('accepted_offline_guard', PROFILE)
    profile = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profile)
    pins = json.loads((N / 'inputs/input-manifest.json').read_bytes())
    origin = str(profile.PY.parent.parent / 'Lib/site-packages/ollama/__init__.py')
    eager = {}
    audit = profile.WorkerAudit()
    sys.addaudithook(audit)
    code = 2
    error = None
    try:
        with profile.own_ollama_types(dict(ollama_origin=origin, files=pins['files']), eager):
            sys.path.insert(0, 'C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-metadata/UltimaAgent')
            import pytest
            code = int(pytest.main(sys.argv[1:]))
    except BaseException as exc:
        error = type(exc).__name__ + ': ' + str(exc)
        raise
    finally:
        audit.enabled = False
        receipt = dict(pytest_exit_code=code, error=error, denied=audit.denied,
                       denied_sites=audit.denied_sites, expected=audit.expected,
                       expected_probe_closed=audit.probe_closed(), eager=eager,
                       python_operations_clean=not audit.denied and audit.probe_closed(),
                       ssrf_unit_fixture='Python fallback with mocked DNS; actual harness unchanged',
                       actual=False, model_calls=0, os_packets=None)
        with (Path.cwd() / 'offline-audit.json').open('x', encoding='utf8') as stream:
            json.dump(receipt, stream, indent=2)
    return code if receipt['python_operations_clean'] and eager.get('eager', {}).get('clean') else 2

if __name__ == '__main__':
    raise SystemExit(main())
