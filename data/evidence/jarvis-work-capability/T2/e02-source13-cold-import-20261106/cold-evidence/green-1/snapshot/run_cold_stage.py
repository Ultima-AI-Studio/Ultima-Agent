"""Named RED/GREEN regression runner; never invokes the actual profile entry."""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
PY=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)

stage_name=sys.argv[1];assert re.fullmatch('[a-z0-9-]{1,40}',stage_name)
stage=ROOT/'cold-evidence'/stage_name;stage.mkdir(parents=True,exist_ok=False)
snapshot=stage/'snapshot';snapshot.mkdir()
files=[ROOT/'profile-preparation'/n for n in ('profile.py','test_profile.py','manifest.json','run_checks.py','README.md')]+[ROOT/'cold/cold_import_probe.py',Path(__file__)]
before={str(p):sha(p) for p in files}
for p in files:(snapshot/p.name).write_bytes(p.read_bytes())
config=stage/'pytest.ini';config.write_text('[pytest]\n',encoding='utf-8')
env={k:v for k,v in os.environ.items() if not k.startswith('PYTEST_') and k.upper() not in ('PYTHONPATH','PYTHONHOME','PYTHONSTARTUP')}
env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
command=[str(PY),'-I','-B','-X','utf8','-m','pytest','-q',str(ROOT/'profile-preparation/test_profile.py'),
    '-k','real_sdk_cold_import or hostname_exception_is_exact','-c',str(config),'--noconftest',
    '--rootdir='+str(ROOT/'profile-preparation'),'--confcutdir='+str(ROOT/'profile-preparation'),
    '--import-mode=importlib','--junitxml='+str(stage/'junit.xml'),'-o','cache_dir='+str(stage/'cache'),'--basetemp='+str(stage/'temp')]
save(stage/'command.json',dict(command=command,scope='OFFLINE_REAL_IMPORT_AND_AUDIT_REGRESSIONS',actual_profile_invocations=0))
run=subprocess.run(command,env=env,cwd=ROOT/'profile-preparation',capture_output=True,timeout=150,creationflags=subprocess.CREATE_NO_WINDOW)
(stage/'stdout.txt').write_bytes(run.stdout);(stage/'stderr.txt').write_bytes(run.stderr)
cases=ET.parse(stage/'junit.xml').findall('.//testcase')
counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
after={str(p):sha(p) for p in files}
value=dict(stage=stage_name,scope='COLD_IMPORT_ONLY_NOT_ACTUAL_PROFILE',exit_code=run.returncode,counts=counts,before=before,after=after,sources_unchanged=before==after,probe_results=[dict(path=str(p),sha256=sha(p),result=json.loads(p.read_bytes())) for p in sorted((stage/'temp').rglob('result.json'))])
save(stage/'receipt.json',value)
print(json.dumps(dict(stage=str(stage),exit_code=run.returncode,counts=counts,sources_unchanged=before==after,probes=[dict(role=row['result']['role'],outcome=row['result']['outcome'],error=row['result'].get('error'),events=row['result']['audit_events']) for row in value['probe_results']])))
raise SystemExit(run.returncode if before==after else 2)
