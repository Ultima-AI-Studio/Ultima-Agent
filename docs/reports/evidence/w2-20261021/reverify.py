import sys,json,hashlib,subprocess,re
from pathlib import Path
from datetime import datetime,UTC
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent/'round2';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT))
from tasks.queue_engine.storage import QueueStorage,INDEX_FIELDS,RUN_PARTS
from tasks.queue_engine.audit import AuditEngine
from tasks.queue_engine.card_contract import section,validate_card
manifest=json.loads((ROOT/'logs/goal-repair/20261021T022156612893Z/source-manifest.json').read_text(encoding='utf-8'))
hashes={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in manifest}
assert hashes==manifest,'source manifest changed'
(OUT/'source-manifest.json').write_text(json.dumps(hashes,indent=2),encoding='utf-8')
production=(ROOT/'tasks/tasks.json').read_bytes()
test=subprocess.run([sys.executable,'-m','unittest','discover','-s','tasks/tests','-v'],cwd=ROOT,capture_output=True)
(OUT/'tests.stdout.txt').write_bytes(test.stdout);(OUT/'tests.stderr.txt').write_bytes(test.stderr)
assert test.returncode==0,test.stderr
data=json.loads((ROOT/'docs/reports/evidence/w2-real-card-20261021T022119636372Z/audit-input.json').read_text(encoding='utf-8'))
source=Path(data['card_source']);assert hashlib.sha256(source.read_bytes()).hexdigest()==data['card_source_sha256']
storage=QueueStorage(data['library']);task=storage.load_tasks()[0];card=Path(task['card_path'])
validate_card(task,storage.root)
original=source.read_text(encoding='utf-8-sig');relocated=card.read_text(encoding='utf-8-sig')
assert section(original,'goal')==section(relocated,'goal')
assert section(original,'acceptance[]').replace('[x]','[ ]')==section(relocated,'acceptance[]')
expected=original.replace(str(ROOT/'tasks'),str(storage.root)).replace('[x] ACCEPT:','[ ] ACCEPT:')
assert expected==relocated,'unexpected relocation change'
proof=Path(data['receipt']['evidence'][0]);proof_data=json.loads(proof.read_text(encoding='utf-8'))
probe=Path(proof_data['probe_root'])
assert all((probe/name).is_dir() for name in ['cards','queue','events','runs','archive'])
probe_tasks=json.loads((probe/'tasks.json').read_text(encoding='utf-8'))
assert len(probe_tasks)==1 and probe_tasks[0]['task_id']=='pending' and set(probe_tasks[0])==set(INDEX_FIELDS)
events=(probe/'events/sample.jsonl').read_bytes();assert events==b'{"sequence":1}\n{"sequence":2}\n'
assert (probe/'cards/sample/task.md').is_file()
archived=[json.loads(l) for l in (probe/'archive/index-items.jsonl').read_text(encoding='utf-8').splitlines()]
assert len(archived)==1 and set(archived[0])==set(INDEX_FIELDS)
assert len(list((probe/'runs/sample').iterdir()))==6
run=list((storage.runs_dir/task['task_id']).glob('*.done'));assert len(run)==1
parts={name:run[0].with_suffix('.'+name) for name in RUN_PARTS};assert all(p.is_file() for p in parts.values())
done=json.loads(parts['done'].read_text(encoding='utf-8'));before=json.loads(parts['before'].read_text(encoding='utf-8'))
progress=json.loads(parts['progress'].read_text(encoding='utf-8'));assert done['exit_code']==0 and before['developer_id']=='/root'
assert progress['worker_pid'] in done['window_audit']['observed_pids'] and done['window_audit']['visible_windows']==[]
assert json.loads(parts['out'].read_text(encoding='utf-8').splitlines()[-1])['business_success'] is True
summary=dict(data['summary'],auditor_id='/root/w2_acceptance')
audit=AuditEngine(storage,OUT/'execution-reports',data['registry'],auditor_id='/root/w2_acceptance')
# Repeat the initial bypass probes separately against this real auditable card/run.
negative=[]
for label,receipt,report in [
 ('unrelated_acceptance',dict(data['receipt'],acceptance={'unrelated':True}),summary),
 ('same_identity',data['receipt'],dict(summary,developer_id='/root/w2_acceptance')),
 ('wrong_order',data['receipt'],dict(summary,work_order='wrong-order'))]:
    v=audit.audit(task,receipt,report,auditor_skill='eng.audit');assert v.verdict!='PASS'
    negative.append({'case':label,'verdict':v.verdict,'reasons':v.reasons})
audit.write_summary(task['task_id'],summary)
verdict=audit.audit(task,data['receipt'],summary,auditor_skill='eng.audit');assert verdict.verdict=='PASS',verdict
closed=audit.close(task['task_id'],verdict);assert closed['state']=='COMPLETED'
assert production==(ROOT/'tasks/tasks.json').read_bytes()
result={'at':datetime.now(UTC).isoformat(),'auditor_id':'/root/w2_acceptance','verdict':verdict.verdict,'closed_state':closed['state'],'negative_probes':negative,'source_card_sha256':data['card_source_sha256'],'relocation_check':'exact path replacement and checkbox reset only','storage_five_checks':'independently read back actual files','run_done':done,'run_progress':progress,'production_unchanged':True,'production_sha256':hashlib.sha256(production).hexdigest(),'tests_exit':test.returncode}
(OUT/'audit-receipt.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
