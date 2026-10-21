import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];OUT=Path(__file__).resolve().parent/'round2';sys.path[:0]=[str(ROOT),str(ROOT/'tasks/tests')]
from test_cli_execution import fixture_card
from tasks.queue_engine.storage import QueueStorage
from tasks.queue_engine.audit import RecoveryManager,AuditEngine
from tasks.queue_engine.dispatcher import Dispatcher
library=OUT/'correction-library';storage=QueueStorage(library);storage.ensure_layout()
card=storage.cards_dir/'example/task.md';card.parent.mkdir(parents=True);card.write_text(fixture_card(library),encoding='utf-8')
(storage.queue_dir/'wo-example.md').write_text('task: example\n',encoding='utf-8')
registry=OUT/'correction-registry.md';registry.write_text('| `task-queue-engine` |\n',encoding='utf-8')
parent=dict(task_id='example',state='FAILED',priority=50,dependsOn=[],parallelGroup=None,fileDomain=[str(library)],reasoningEffort='high',created_at='2026-10-21',updated_at='2026-10-21',terminal_reason='independent reproduced failure',card_path=str(card))
storage.save_tasks([parent]);recovery=RecoveryManager(storage);child=recovery.create_correction('example',actor='brain',reason='independent verification of correction lifecycle')
assert child['task_id']=='example~r1'
blocked=Dispatcher(storage,developer_id='/root').dispatch('example',[sys.executable,'-c','pass']);assert not blocked.dispatched
auditor=AuditEngine(storage,OUT/'correction-execution-reports',registry,auditor_id='/root/w2_acceptance')
results=[]
for task_id in ['example~r1','example']:
    artifact=library/(task_id+'-artifact.txt')
    command=[sys.executable,'-c',f"from pathlib import Path;Path({str(artifact)!r}).write_text('verified result');print('{{\"business_success\":true}}')"]
    dispatcher=Dispatcher(storage,developer_id='/root');run=dispatcher.dispatch(task_id,command);assert run.dispatched,run.reason
    dispatcher.take_process(run.pid).wait(timeout=10)
    recovery.recover_finished_run(task_id);task=recovery.finish_self_check_from_run(task_id)
    receipt=dict(completion='independent chain validated',landed_files=[str(artifact)],reviewReason='file content read back',stdoutText='business_success true',evidence=[str(artifact)],acceptance={'structured result':True})
    assert artifact.read_text()=='verified result'
    summary=dict(version='S1/v0.1',work_order='wo-example',task_id=task_id,business_success=True,exit_code=0,receipt_present=True,developer_skill='eng.code',auditor_skill='eng.audit',developer_id='/root',auditor_id='/root/w2_acceptance',file_domain_ok=True,registry_entry='task-queue-engine')
    auditor.write_summary(task_id,summary);verdict=auditor.audit(task,receipt,summary,auditor_skill='eng.audit');assert verdict.verdict=='PASS',verdict
    closed=auditor.close(task_id,verdict);assert closed['state']=='COMPLETED';results.append(closed)
assert all(t['state']=='COMPLETED' for t in storage.load_tasks())
(OUT/'correction-independent-receipt.json').write_text(json.dumps({'parent_initially_waited':blocked.reason,'final_tasks':results,'auditor_id':'/root/w2_acceptance'},ensure_ascii=False,indent=2),encoding='utf-8')
print('CORRECTION_INDEPENDENT_CHAIN_OK')
