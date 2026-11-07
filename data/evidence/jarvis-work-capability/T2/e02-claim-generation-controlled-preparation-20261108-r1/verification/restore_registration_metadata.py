"""Recover controller metadata from the preserved snapshot after a PowerShell JSON failure."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
p=T/'current-run.json';before=p.read_bytes()
assert before.strip() in (b'',b'null'), 'Unexpected current state; do not overwrite'
with (N/'verification/registration-metadata-failure-current-run.txt').open('xb') as f:f.write(before)
state=json.loads((N/'inputs/previous-current-run.json').read_bytes())
assert state['active_candidate']=='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
assert 'T2' in state and 't2' in state
original_keys=set(state);original_result=state['last_actual_result']
state.update(phase='SOURCE35_E02_CLAIM_GENERATION_ENTRY_PLAN_REVIEW',workflow_status='executing',stage_queue_state='EXECUTING',active_evidence=str(N),active_plan=str(R/'docs/plans/jarvis-work-e02-claim-generation-controlled-entry-plan-20261108.md'),active_review_agent='/root/review_e02_claim_generation_entry_plan',
    next_action='Complete authorized offline Task3: independent plan review, frozen rebind, guarded checks, preparation review and local readback',
    next_action_scope=dict(authorized=True,question_id='call_5411de619a6c4de0bab414126a228c7d',scope='Offline controlled entry preparation only',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,service_operations=0),
    live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',goal_registry_status='blocked',goal_status='blocked',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
assert p.read_bytes()==before
p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
read=json.loads(p.read_bytes());assert original_keys<=set(read) and read==state and read['last_actual_result']==original_result
receipt=dict(verdict='PASS_CONTROLLER_METADATA_RECOVERY',root_cause='PowerShell ConvertFrom-Json without -AsHashtable rejects distinct T2 and t2 keys; non-terminating error allowed null write',recovery_source=str(N/'inputs/previous-current-run.json'),original_keys_preserved=True,last_actual_preserved=True,actual_allocations=0,product_changed=False,followup='Use Python JSON for all case-sensitive state mutations',sha256=hashlib.sha256(p.read_bytes()).hexdigest(),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
with (N/'verification/registration-metadata-recovery.json').open('x',encoding='utf8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(receipt))
