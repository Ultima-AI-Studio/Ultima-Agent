"""At most four fixed <=5s inert children across explicit old/new phases."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

PREP = Path(__file__).resolve().parent
OUTPUT = PREP.parent/'fix1-guard-tests'
PYTHON = 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe'
phase = sys.argv[1]
if phase not in ('old','new'):
    raise SystemExit('Choose one fixed phase')
OUTPUT.mkdir(exist_ok=True)
runner = PREP.parent/'preparation-r2/run_probe.py' if phase == 'old' else PREP/'run_probe.py'
records = []
for mode in ('denial','ordinary'):
    folder = OUTPUT/(phase+'-'+mode)
    folder.mkdir(exist_ok=False)
    argv = [PYTHON,'-B','-X','utf8',str(PREP/'guard_regression_child.py'),str(runner),str(folder),mode]
    started=time.monotonic()
    done=subprocess.run(argv,capture_output=True,timeout=5,check=False)
    (folder/'stdout.bin').write_bytes(done.stdout)
    (folder/'stderr.bin').write_bytes(done.stderr)
    sentinel=(folder/'continuation-sentinel.txt').exists()
    abort=(folder/'guard-abort.json').exists()
    result=json.loads((folder/'result.json').read_text()) if (folder/'result.json').exists() else None
    expected = (done.returncode == 17 and sentinel and not abort) if phase=='old' and mode=='denial' else (
        done.returncode==123 and not sentinel and abort and result['status']=='INCOMPLETE'
        if mode=='denial' else done.returncode==0 and sentinel and not abort)
    records.append(dict(phase=phase,mode=mode,argv=argv,exit_code=done.returncode,
        seconds=time.monotonic()-started,expected_observation=expected,
        prevention_oracle_pass=not sentinel if mode=='denial' else None,
        sentinel_exists=sentinel,first_denial_exists=abort,terminal=result,
        stdout_sha256=hashlib.sha256(done.stdout).hexdigest(),stderr_sha256=hashlib.sha256(done.stderr).hexdigest()))
receipt=OUTPUT/(phase+'-receipt.json')
with receipt.open('x',encoding='utf8') as stream:json.dump(records,stream,indent=2)
print(json.dumps(records,indent=2))
if not all(r['expected_observation'] for r in records):raise SystemExit(1)
