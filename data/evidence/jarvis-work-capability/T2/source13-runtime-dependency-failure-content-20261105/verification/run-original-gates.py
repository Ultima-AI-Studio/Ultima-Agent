"""Run one inherited offline gate with fresh configuration and hash receipts."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

ROOT = Path(r"C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent")
EVIDENCE = Path(__file__).resolve().parent
PYTHON = r"H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe"
MODE = sys.argv[1]
assert MODE in ('covering', 'compat', 'interaction') and len(sys.argv) in (2, 3)
label = sys.argv[2] if len(sys.argv) == 3 else MODE
assert label.replace('-', '').isalnum()
RUN = EVIDENCE / 'original-gates' / label
RUN.mkdir(exist_ok=False)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


manifest_path = EVIDENCE.parent / 'candidate-manifest.json'
assert sha(manifest_path) == '1201e883c213c2d95cdb63c9e8ab796e07264cbe1f3a866c33ea0a455ba29634'
manifest = json.loads(manifest_path.read_text(encoding='utf8'))
inputs = dict(manifest['source_files'])
inputs.update(json.loads((EVIDENCE / 'original-gates' / 'supplemental-inputs.json').read_text(encoding='utf8'))['source_files'])
before = {p: sha(p) for p in inputs}
assert before == inputs, 'Current candidate/source inputs differ'
candidate = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
assert candidate == manifest['candidate']
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
           PYTHONPATH=str(ROOT) + os.pathsep + str(EVIDENCE),
           PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
           HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1',
           NO_PROXY='localhost,127.0.0.1,::1',
           ULTIMA_SOURCE13_GATE_ROOT=str(RUN), ULTIMA_SOURCE13_GATE_MODE=MODE,
           ULTIMA_OFFLINE_GUARD_RECEIPT=str(RUN / 'io-guard.json'))
private_env = {}
for key in ('TEMP', 'TMP', 'TMPDIR', 'OPENJARVIS_HOME', 'XDG_CACHE_HOME',
            'HF_HOME', 'TORCH_HOME', 'MPLCONFIGDIR', 'NUMBA_CACHE_DIR'):
    location = RUN / 'env' / key
    location.mkdir(parents=True)
    private_env[key] = str(location)
env.update(private_env)
modules = [
    'src/brain/tests/test_work_research.py',
    'src/brain/tests/test_work_context.py',
    'src/brain/tests/test_work_delivery.py',
    'src/brain/tests/test_agent_server_sse.py',
    'src/brain/browser/tests/test_browser_channel_s3.py',
    'src/brain/tests/test_interaction.py',
    'src/brain/tests/test_work_navigation.py',
    'src/brain/tests/test_work_navigation_sdk.py',
    'src/brain/tests/test_work_navigation_transport.py',
] if MODE == 'covering' else (['src/brain/tests/test_agent_tools_extend.py'] if MODE == 'compat'
                            else ['src/brain/tests/test_interaction.py'])
args = [PYTHON, '-B', '-m', 'pytest', '-q', '-p', 'no:cacheprovider', '-p', 'offline_guards',
        '-p', 'source13_paths', '--basetemp', str(RUN / 'tmp'),
        '--junitxml', str(RUN / 'junit.xml'), *modules]
receipt = dict(candidate=candidate, candidate_manifest_sha256=sha(manifest_path), argv=args,
               cwd=str(ROOT), private_env=private_env, source_inputs_before=before,
               started_utc=datetime.now(timezone.utc).isoformat(),
               new_actual_cases=0, new_model_calls=0,
               scope='Original offline covering/compatibility gate on source13; no live E03 authority')
receipt['harness_sha256'] = {name: sha(EVIDENCE / name) for name in
                            ('run-original-gates.py', 'source13_paths.py', 'offline_guards.py')}
(RUN / 'invocation.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
started = time.monotonic()
with (RUN / 'stdout.log').open('w', encoding='utf8') as out:
    result = subprocess.run(args, cwd=ROOT, env=env, stdout=out, stderr=subprocess.STDOUT)
after = {p: sha(p) for p in inputs}
counts = None
if (RUN / 'junit.xml').exists():
    xml = ET.parse(RUN / 'junit.xml').getroot()
    suites = [xml] if xml.tag == 'testsuite' else list(xml.iter('testsuite'))
    counts = {k: sum(int(s.get(k, 0)) for s in suites) for k in ('tests', 'failures', 'errors', 'skipped')}
receipt.update(finished_utc=datetime.now(timezone.utc).isoformat(), elapsed_seconds=time.monotonic()-started,
               exit_code=result.returncode, counts=counts, source_inputs_after=after,
               source_unchanged=before == after,
               harness_adaptations=['candidate checkout rebound to source13', 'fresh precollection SDK home',
                                    'all temporary/cache directories privately rebound',
                                    'inherited compatibility sandbox rebinding',
                                    'Python I/O guard and current loaded-module path check',
                                    'one queue-state unit test uses explicit confirmation embedding fixture; live semantic routing is not tested'])
receipt['files'] = {p.name: sha(p) for p in RUN.iterdir() if p.is_file()}
(RUN / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf8')
print(json.dumps({k: receipt[k] for k in ('candidate', 'elapsed_seconds', 'exit_code', 'counts', 'source_unchanged')}))
print('\n'.join((RUN / 'stdout.log').read_text(encoding='utf8').splitlines()[-50:]))
sys.exit(result.returncode if before == after else 1)
