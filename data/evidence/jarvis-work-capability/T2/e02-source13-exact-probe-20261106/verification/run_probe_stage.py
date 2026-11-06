from pathlib import Path
import datetime as dt,hashlib,json,os,re,subprocess,sys,xml.etree.ElementTree as ET
Q=Path(__file__).resolve().parents[1];PY=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
name=sys.argv[1];assert re.fullmatch('[a-z0-9-]{1,40}',name)
stage=Q/'offline'/name;stage.mkdir(parents=True,exist_ok=False);(stage/'snapshot').mkdir()
files=[Q/'profile-preparation'/n for n in ('profile.py','test_profile.py','manifest.json')]
before={str(p):sha(p) for p in files}
for p in files:(stage/'snapshot'/p.name).write_bytes(p.read_bytes())
(stage/'pytest.ini').write_text('[pytest]\n',encoding='utf-8')
forbidden={'OLLAMA_HOST','OLLAMA_API_KEY','OLLAMA_MODELS','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP','OPENJARVIS_HOME','OPENJARVIS_CONFIG','XDG_DATA_HOME','XDG_CACHE_HOME','TMP','TEMP','TMPDIR','OPENJARVIS_SSRF_FAIL_OPEN'}
env={k:v for k,v in os.environ.items() if k.upper() not in forbidden and not k.upper().endswith('_PROXY') and not k.startswith('PYTEST_')};env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
command=[str(PY),'-I','-B','-X','utf8','-m','pytest','-q','test_profile.py','-k','probe_rejects or probe_incomplete or probe_open or real_urllib3_probe',
    '-c',str(stage/'pytest.ini'),'--noconftest','--confcutdir='+str(Q/'profile-preparation'),'--rootdir='+str(Q/'profile-preparation'),
    '--import-mode=importlib','--junitxml='+str(stage/'junit.xml'),'--basetemp='+str(stage/'temp'),'-o','cache_dir='+str(stage/'cache')]
save(stage/'command.json',dict(command=command,scope='OFFLINE_GUARD_AND_LOCAL_IMPORT_TESTS',actual_profile_runs=0))
run=subprocess.run(command,cwd=Q/'profile-preparation',env=env,capture_output=True,timeout=120,creationflags=subprocess.CREATE_NO_WINDOW)
(stage/'stdout.txt').write_bytes(run.stdout);(stage/'stderr.txt').write_bytes(run.stderr)
cases=ET.parse(stage/'junit.xml').findall('.//testcase');counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
after={str(p):sha(p) for p in files};save(stage/'receipt.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),exit_code=run.returncode,counts=counts,before=before,after=after,sources_unchanged=before==after,actual_profile_runs=0))
print(json.dumps(dict(stage=str(stage),exit_code=run.returncode,counts=counts,sources_unchanged=before==after)));raise SystemExit(run.returncode)
