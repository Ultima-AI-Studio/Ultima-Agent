"""One bounded serialized recovery of the unchanged offline group; never actual."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

N = Path(__file__).resolve().parents[1]
FAILED = N / 'code/harness-preparation-20261108T055251046439Z/receipt.json'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def save(p, obj):
    with p.open('x', encoding='utf8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

failed = json.loads(FAILED.read_bytes())
assert failed['group'] == 'base-b' and failed['exit_code'] == 124 and failed['timed_out']
assert failed['inputs_unchanged'] and failed['harness_unchanged']
assert not (FAILED.parent / 'harness/adapter.xml').exists()
assert not (FAILED.parent / 'offline-audit.json').exists()
assert json.loads((N / 'verification/final-batch-checks.json').read_bytes()) == {
    'base-a': 0, 'recovery': 0, 'base-b': 124, 'failure-export-green': 0,
    'bindings': 0, 'entry': 0, 'export-green': 0, 'boundary': 0}
observation = N / 'verification/base-b-timeout-process-observation.json'
observed = json.loads(observation.read_text('utf-8-sig'))
assert observed['matching_count'] == 0 and observed['read_only'] is True
for name, digest in failed['harness_before'].items():
    assert sha(N / 'harness' / name) == digest == sha(FAILED.parent / 'harness-source' / name)
assert sha(N / 'verification/offline_pytest.py') == sha(FAILED.parent / 'harness-source/offline_pytest.py')
before = set((N / 'code').glob('harness-preparation-*/receipt.json'))
save(N / 'verification/base-b-recovery-start.json', dict(
    recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    failed_receipt=str(FAILED), failed_sha256=sha(FAILED),
    process_observation_sha256=sha(observation),
    reason='Original group stopped at90s after138 progress dots, with no assertion failure shown. Prior same group finished in57-59s. Concurrency is a hypothesis, not an established cause. One serialized run of the same exact tests and original90s bound is permitted in offline preparation; no further retry here.',
    original_failure_credit=0, attempts=1, source_changes=False,
    actual_cases=0, model_calls=0, acceptance_credit=0))
result = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8',
    str(N / 'harness/run_checks.py'), 'base-b'], capture_output=True,
    creationflags=subprocess.CREATE_NO_WINDOW)
with (N / 'verification/base-b-recovery.log').open('xb') as f:
    f.write(result.stdout + result.stderr)
new = set((N / 'code').glob('harness-preparation-*/receipt.json')) - before
assert len(new) == 1
receipt, = new
save(N / 'verification/base-b-recovery-result.json', dict(
    failed_receipt=str(FAILED), failed_sha256=sha(FAILED),
    recovery_receipt=str(receipt), recovery_sha256=sha(receipt),
    exit_code=result.returncode, original_timeout_seconds=90,
    scope='offline-only-same-byte-serialized', actual_cases=0, model_calls=0,
    acceptance_credit=0, recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
print(result.stdout.decode('utf8'), end='')
print(result.stderr.decode('utf8'), end='', file=sys.stderr)
raise SystemExit(result.returncode)
