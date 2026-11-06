from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parents[1]
verification = root / 'verification'
label = sys.argv[1]
assert label.replace('-', '').isalnum()
log = verification / (label + '.log')
assert not log.exists()
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
           PYTHONIOENCODING='utf-8', PYTHONUTF8='1',
           PYTHONPATH=str(root/'code')+os.pathsep+str(verification),
           ULTIMA_OFFLINE_GUARD_RECEIPT=str(verification/(label+'-io-guard.json')))
for key in ('TEMP', 'TMP', 'TMPDIR', 'OPENJARVIS_HOME'):
    location = verification / ('env-' + label) / key
    location.mkdir(parents=True, exist_ok=False)
    env[key] = str(location)
xml = verification / (label+'.xml')
args = [r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe', '-B', '-m', 'pytest',
        '-q', '-p', 'no:cacheprovider', '-p', 'offline_guards',
        '--basetemp', str(verification/('tmp-'+label)), '--junitxml', str(xml), *sys.argv[2:]]
inputs = [*sorted((root/'code').glob('*.py')), *sorted((root/'preparation-support').glob('*.py'))]
before = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
started = time.monotonic()
with log.open('w', encoding='utf8') as out:
    result = subprocess.run(args, cwd=root, env=env, stdout=out, stderr=subprocess.STDOUT)
after = {str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
counts = None
if xml.exists():
    suites = ET.parse(xml).getroot().iter('testsuite')
    rows = list(suites)
    counts = {k:sum(int(s.get(k,0)) for s in rows) for k in ('tests','failures','errors','skipped')}
receipt = dict(argv=args,cwd=str(root),elapsed_seconds=time.monotonic()-started,exit_code=result.returncode,
               counts=counts,source_inputs_before=before,source_inputs_after=after,source_unchanged=before==after,
               actual_cases=0,model_calls=0,audio_actions=0,
               limitations='Mock native boundaries and synthetic files; no standalone import probe or actual native UI validation')
(verification/(label+'.json')).write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf8')
print(json.dumps({k:receipt[k] for k in ('elapsed_seconds','exit_code','counts','source_unchanged')}))
print('\n'.join(log.read_text(encoding='utf8').splitlines()[-35:]))
sys.exit(result.returncode if before==after else 1)
