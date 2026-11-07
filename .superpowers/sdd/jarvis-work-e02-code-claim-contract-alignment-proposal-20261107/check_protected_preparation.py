"""Read-only point check before preparation; no service/model/cleanup action."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source-reference-schema-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-code-claim-contract-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
manifest=json.loads((OLD/'manifest.json').read_bytes())
adapter=OLD/'harness/adapter.py';assert sha(adapter)==manifest['files']['harness/adapter.py']
spec=importlib.util.spec_from_file_location('prior_protection_readonly',adapter)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);p4=a.load_p4()
inputs=json.loads((OLD/'inputs/input-manifest.json').read_bytes());baseline=json.loads(Path(inputs['protected_baseline_path']).read_bytes())
rows=baseline['protected5']+baseline['protected_listener_pair']
started=dt.datetime.now(dt.timezone.utc).isoformat();snapshot=p4.process_snapshot(pids=[row['pid'] for row in rows]);result=[]
for row in rows:
    key={k:row[k] for k in ('pid','created_filetime','exe')};cim=snapshot.get(row['pid'])
    try:native=p4.identity(row['pid']);error=None
    except OSError as exc:native=None;error=type(exc).__name__
    command=hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest() if cim else None
    result.append(dict(role=row['role'],pid=row['pid'],native_identity_equal=native==key,cim_identity_equal=bool(cim and p4.snapshot_identity_matches(key,cim)),parent_equal=bool(cim and cim['ParentProcessId']==row['parent_pid']),command_equal=command==row['command_line_sha256'],native_error=error))
equal=all(all(row[k] for k in ('native_identity_equal','cim_identity_equal','parent_equal','command_equal')) for row in result)
value=dict(kind='READONLY_PREPARATION_PROTECTION_POINT_CHECK',started_utc=started,finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),protected=result,all_equal=equal,continuous_liveness_measured=False,model_calls=0,service_operations=0,termination_calls=0)
with (L/'protected-preparation-readback.json').open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(value,ensure_ascii=False))
