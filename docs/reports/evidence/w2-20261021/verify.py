import sys, json, hashlib, subprocess, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
OUT=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(ROOT/'tasks/tests')]
import test_audit_e2e as fixtures
from tasks.queue_engine.dispatcher import Dispatcher
from tasks.queue_engine.priority_deps import QueuePlanner
from tasks.queue_engine.audit import RecoveryManager
before=(ROOT/'tasks/tasks.json').read_bytes()
run=subprocess.run([sys.executable,'-m','unittest','discover','-s','tasks/tests','-v'],cwd=ROOT,capture_output=True)
(OUT/'unittest.stdout.txt').write_bytes(run.stdout)
(OUT/'unittest.stderr.txt').write_bytes(run.stderr)
result={'suite_exit':run.returncode,'production_before_sha256':hashlib.sha256(before).hexdigest(),'observations':[]}
f=fixtures.AuditE2ETests('test_no_receipt_is_blocked_and_never_completed');f.setUp()
try:
    task=f.task(); QueuePlanner(f.storage).enqueue(task)
    card=f.task_root/'cards/e2e/task.md';card.parent.mkdir(parents=True)
    card.write_text('## acceptance[]\n- ACCEPT: artifact must contain REQUIRED_RESULT\n',encoding='utf-8')
    artifact=f.task_root/'artifact.txt';artifact.write_text('wrong result',encoding='utf-8')
    # Remove synthetic incomplete card before low-level dispatch; audit retains the card afterwards.
    card.unlink()
    d=Dispatcher(f.storage);r=d.dispatch('e2e',[sys.executable,'-c',"print('{\"business_success\":true}')"])
    d.take_process(r.pid).wait(timeout=5)
    card.write_text('## acceptance[]\n- ACCEPT: artifact must contain REQUIRED_RESULT\n',encoding='utf-8')
    m=RecoveryManager(f.storage);m.recover_finished_run('e2e');task=m.finish_self_check_from_run('e2e')
    receipt=f.receipt(artifact);receipt['acceptance']={'unrelated_check':True}
    summary=f.summary();summary.update(developer_id='same-person',auditor_id='same-person',work_order='wrong-work-order')
    verdict=f.audit_engine.audit(task,receipt,summary,auditor_skill='eng.audit')
    result['observations'].append({'case':'wrong_acceptance_and_same_person_and_wrong_work_order','verdict':verdict.verdict,'reasons':verdict.reasons,'receipt':receipt,'summary':summary})
    for name,rec,summ in [
        ('wrong_acceptance_only',receipt,f.summary()),
        ('same_person_only',f.receipt(artifact),dict(f.summary(),developer_id='same-person',auditor_id='same-person')),
        ('wrong_work_order_only',f.receipt(artifact),dict(f.summary(),work_order='wrong-work-order'))]:
        v=f.audit_engine.audit(task,rec,summ,auditor_skill='eng.audit')
        result['observations'].append({'case':name,'verdict':v.verdict,'reasons':v.reasons})
    for p in (f.storage.runs_dir/'e2e').iterdir():
        (OUT/('probe-run-'+p.name)).write_bytes(p.read_bytes())
    result['observations'].append({'case':'guard_lifecycle_references','references':[(str(p.relative_to(ROOT)),i+1,line.strip()) for p in (ROOT/'tasks/queue_engine').glob('*.py') for i,line in enumerate(p.read_text(encoding='utf-8').splitlines()) if 'guardian_parent_lost' in line]})
finally:f.tearDown()
after=(ROOT/'tasks/tasks.json').read_bytes();result['production_after_sha256']=hashlib.sha256(after).hexdigest();result['production_unchanged']=before==after
result['source_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'tasks/queue_engine').glob('*.py')}
result['git_probe']=subprocess.run(['git','rev-parse','--is-inside-work-tree'],cwd=ROOT,capture_output=True,text=True).stderr.strip()
(OUT/'result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=True,indent=2))
