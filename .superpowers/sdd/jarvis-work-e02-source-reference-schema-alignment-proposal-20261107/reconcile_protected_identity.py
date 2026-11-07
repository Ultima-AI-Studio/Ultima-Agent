"""Capture a fresh seven-role baseline without controlling any service."""
from pathlib import Path
import copy,datetime as dt,hashlib,importlib.util,json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-source-reference-schema-20261107-r1';OLD=T/'e02-fixed-target-schema-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
source=OLD/'harness/adapter.py';assert sha(source)==load(OLD/'manifest.json')['files']['harness/adapter.py']
spec=importlib.util.spec_from_file_location('readonly_previous_identity_helper',source)
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);p4=a.load_p4()
old_path=Path(load(OLD/'inputs/input-manifest.json')['protected_baseline_path']);old=load(old_path)
rows=copy.deepcopy(old['protected5']+old['protected_listener_pair']);assert rows[0]['pid']==5708
current=11464; parent=rows[0]['parent_pid'];pids=[current,parent,5708]+[r['pid'] for r in rows[1:]]
started=dt.datetime.now(dt.timezone.utc).isoformat();snap=p4.process_snapshot(pids=pids)
assert 5708 not in snap and p4.listener_owner(11434)==[current]
new=p4.identity(current);cim=snap[current]
assert p4.snapshot_identity_matches(new,cim) and new['exe']==rows[0]['exe'] and cim['ParentProcessId']==parent
command=hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest()
assert command==rows[0]['command_line_sha256']
parent_key=p4.identity(parent)
assert parent_key['exe']==str(Path(new['exe']).parent/'ollama app.exe') and p4.snapshot_identity_matches(parent_key,snap[parent])
for row in rows[1:]:
    key={k:row[k] for k in ('pid','created_filetime','exe')};row_cim=snap[row['pid']]
    assert p4.identity(row['pid'])==key and p4.snapshot_identity_matches(key,row_cim)
    assert row_cim['ParentProcessId']==row['parent_pid'] and hashlib.sha256(row_cim['CommandLine'].encode('utf-16le')).hexdigest()==row['command_line_sha256']
metadata=load(N/'verification/native-drift-metadata.json')
assert metadata['version']=={'version':'0.32.15'} and len(metadata['tags'])==1
assert metadata['tags'][0]['digest']==metadata['local_model_manifest_sha256']=='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
raw=Path('C:/Users/Administrator/AppData/Local/Ollama/app.log').read_bytes()
selected=[dict(line=i,text=line) for i,line in enumerate(raw.decode('utf8').splitlines(),1)
          if '2026-11-07T12:18:37.' in line and any(s in line for s in ('starting Ollama','starting ollama server','detected previous ollama process','graceful terminate failed'))]
assert len(selected)==4
save(N/'inputs/ollama-app-start-excerpt.json',dict(source='C:/Users/Administrator/AppData/Local/Ollama/app.log',observed_source_sha256=hashlib.sha256(raw).hexdigest(),lines=selected,causal_limit='App log records start and old PID cleanup; launch initiator is unknown.'))
stamp=dt.datetime(1601,1,1,tzinfo=dt.timezone.utc)+dt.timedelta(microseconds=new['created_filetime']//10)
new_row=dict(rows[0],**new,created_utc=stamp.strftime('%Y-%m-%dT%H:%M:%S.')+f'{stamp.microsecond:06d}'+str(new['created_filetime']%10)+'Z')
rows[0]=new_row
assert p4.identity(current)==new and p4.listener_owner(11434)==[current]
proof=dict(kind='NEW_BASELINE_READONLY_RECONCILIATION',started_utc=started,finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    previous_baseline=str(old_path),previous_baseline_sha256=sha(old_path),old_pid_absent=True,new_identity=new,parent_identity=p4.identity(parent),
    same_executable=True,same_parent_pid=True,same_command_sha256=True,unchanged_other_six=True,listener_owner=[current],
    native_metadata_sha256=sha(N/'verification/native-drift-metadata.json'),app_excerpt_sha256=sha(N/'inputs/ollama-app-start-excerpt.json'),
    user_reply=dict(question_id='call_bf5fa9f4197e4118b2aab2d505c6ae66',answer='没有主动关闭、重启或更新'),
    lifecycle_cause='UNKNOWN_INITIATOR_APP_START_AND_OLD_PID_CLEANUP_RECORDED',continuous_liveness_claim=False,
    service_operations=0,termination_calls=0,model_calls=0,new_case_calls=0)
save(N/'inputs/protected-reconciliation.json',proof)
baseline=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',captured_at_utc=proof['finished_utc'],
    action='Read-only re-pin of already-running unchanged Ollama version/model after externally observed identity replacement; no service operations',
    protected5=rows[:5],protected_listener_pair=rows[5:],protected_process_count=7,
    ollama_listener=[dict(LocalAddress='127.0.0.1',LocalPort=11434,OwningProcess=current)],ollama_listener_owner_match=True,
    scope='This new candidate case only; never rewrites prior baselines or claims old process survival.',
    predecessor_baseline=str(old_path),predecessor_baseline_sha256=sha(old_path),runtime_reconciliation_sha256=sha(N/'inputs/protected-reconciliation.json'))
save(N/'inputs/protected-baseline.json',baseline)
print(json.dumps(dict(new_baseline=str(N/'inputs/protected-baseline.json'),old_pid=5708,new_pid=current,other_six_equal=True,service_operations=0)))
