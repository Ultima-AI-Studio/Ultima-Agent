import datetime,hashlib,json,os,subprocess,sys,xml.etree.ElementTree as ET
from pathlib import Path
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
ROOT=Path(__file__).resolve().parent.parent
OUT=ROOT/'candidate-fixwave1-compat';OUT.mkdir(exist_ok=False)
H=lambda raw:hashlib.sha256(raw).hexdigest()
original=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/native-read-budget-source9/run_compat.py').read_bytes()
assert H(original)=='b165772a736de13006064a25b3d26db6aaa58afdcb38d8025fe91aa49bacc5c2'
old=b"evidence=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/native-read-budget-source9')"
new=("evidence=Path('"+OUT.as_posix()+"')").encode()
assert original.count(old)==1
copy=original.replace(old,new);assert copy.replace(new,old)==original
(OUT/'run_compat.py').write_bytes(copy)
prior=json.loads((ROOT/'unit23-fix1-compat/invocation.json').read_bytes())
env={k:v.replace('unit23-fix1-compat','candidate-fixwave1-compat') for k,v in prior['env'].items()}
for k in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','MPLCONFIGDIR','NUMBA_CACHE_DIR'):
    Path(env[k]).mkdir(parents=True,exist_ok=True)
paths=json.loads((ROOT/'unit23-fix1-covering/receipt.json').read_bytes())['source_inputs_before']
snapshot=lambda:{p:H((C/p).read_bytes()) for p in paths}
argv=[sys.executable,'-B','-X','utf8',str(OUT/'run_compat.py')]
receipt=dict(argv=argv,cwd=str(C),env=env,source_inputs_before=snapshot(),original_sha256=H(original),
    copy_sha256=H(copy),only_evidence_root_changed=True,started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(OUT/'invocation.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
with (OUT/'stdout.log').open('wb') as stdout,(OUT/'stderr.log').open('wb') as stderr:
    result=subprocess.run(argv,cwd=C,env=dict(os.environ,**env),stdout=stdout,stderr=stderr)
receipt.update(exit_code=result.returncode,source_inputs_after=snapshot(),finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
receipt['source_unchanged']=receipt['source_inputs_before']==receipt['source_inputs_after']
cases=ET.parse(OUT/'compat.xml').getroot().findall('.//testcase')
receipt['counts']=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
    errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
receipt['files']={p.name:H(p.read_bytes()) for p in OUT.iterdir() if p.is_file()}
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
print(json.dumps(dict(exit_code=result.returncode,counts=receipt['counts'],source_unchanged=receipt['source_unchanged'])))
raise SystemExit(result.returncode)
