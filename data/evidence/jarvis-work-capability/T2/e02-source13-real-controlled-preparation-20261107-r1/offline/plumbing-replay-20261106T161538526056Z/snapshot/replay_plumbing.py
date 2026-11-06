"""One offline reader of the immutable zero-inference case, with raw logs."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

N=Path(__file__).resolve().parents[1]
PY=N.parents[4]/'tools/venv-openjarvis/Scripts/python.exe'
assert Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
run=N/'offline'/('plumbing-replay-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
run.mkdir(parents=True,exist_ok=False)
sources=[N/'verification/offline_pytest.py',N/'tests/test_plumbing_replay.py',N/'harness/adapter.py',Path(__file__)]
before={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
(run/'snapshot').mkdir()
for p in sources:(run/'snapshot'/p.name).write_bytes(p.read_bytes())
env={k:v for k,v in os.environ.items() if not k.upper().endswith('_PROXY') and not k.upper().startswith(('OLLAMA_','OPENJARVIS_','PYTHON','PYTEST'))}
env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',TEMP=str(run),TMP=str(run),OPENJARVIS_HOME=str(run/'home'),XDG_CACHE_HOME=str(run/'cache'))
argv=[str(PY),'-I','-B','-X','utf8',str(sources[0]),str(sources[1]),'-q','-p','no:cacheprovider','--basetemp='+str(run/'temp'),'--junitxml='+str(run/'result.xml')]
with (run/'stdout.log').open('xb') as out,(run/'stderr.log').open('xb') as err:
    result=subprocess.run(argv,cwd=run,env=env,stdout=out,stderr=err,timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
same=before=={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
receipt=dict(exit_code=result.returncode,sources=before,sources_unchanged=same,argv=argv,actual=False,model_calls=0,acceptance_credit=0)
with (run/'receipt.json').open('x',encoding='utf8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(path=str(run),exit_code=result.returncode,sources_unchanged=same)))
raise SystemExit(result.returncode if same else 2)
