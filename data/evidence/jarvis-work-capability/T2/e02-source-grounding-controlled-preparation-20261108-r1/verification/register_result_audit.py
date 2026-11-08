"""Consume only the authorized result-review allocation after sealing the first outcome."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
QUESTION='call_7004c6eafaca48e3a6f19dd87f59d024'
REVIEWER='/root/review_e02_source_grounding_actual_result'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,value):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
manifest_path=N/'review/result-inputs/result-manifest.json';manifest=load(manifest_path)
assert manifest['user_question_id']==QUESTION and manifest['actual_invocations']==manifest['result_review_allocation']==1
for path,h in manifest['files'].items():assert sha(N/path)==h,path
decision=load(N/'verification/allocated-user-decision.json')
assert decision['question_id']==QUESTION and decision['result_review_allocation']==1
assert load(N/'release/tool-execution-receipt.json')['invocations']==1
assert not (N/'review/independent-result-review.json').exists()
rb=load(N/'review/result-inputs/byte-readback.json')
allocation=dict(question_id=QUESTION,reviewer=REVIEWER,result_manifest_sha256=sha(manifest_path),allocated=1,consumed=1,remaining=0,
    actual_consumed=1,actual_remaining=0,retry=0,scope='Read-only first-result independent review; no model/actual/test/runtime calls')
save(N/'review/result-review-allocation.json',allocation)
summary=f"E02 43da3f0唯一实跑{rb['original_status']}待结果独审：research.md数量{rb['research_files']}，native POST {rb['application_native_POST_attempts']}，清理{rb['cleanup']}；实际已消费、不重试。"
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
assert state['current_one_case_allocation']['question_id']==QUESTION
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE37_E02_SOURCE_GROUNDING_RESULT_REVIEW',
    workflow_status='audit',stage_queue_state='AUDIT',active_review_agent=REVIEWER,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,
    pending_actual_result=dict(run_id=rb['run_id'],candidate=rb['candidate'],status=rb['original_status'],
        result_manifest_sha256=sha(manifest_path),byte_readback_sha256=sha(N/'review/result-inputs/byte-readback.json'),acceptance_credit=0),
    current_one_case_allocation=dict(question_id=QUESTION,candidate=rb['candidate'],status='ACTUAL_CONSUMED_RESULT_REVIEW_ALLOCATED',remaining=0,result_review_remaining=0,retry=0))
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-08 E02 source grounding result audit\n\n'+summary+'\n结果manifest：'+sha(manifest_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | audit | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=index
backup=N/'verification/result-audit-before';backup.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(backup/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-audit-registration.json',dict(summary=summary,before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},
    after={str(p):sha(p) for p in paths},allocation=allocation))
save(N/'review/result-registration.json',dict(status='PENDING_ROOT_INDEPENDENT_REVIEW',candidate=rb['candidate'],run_id=rb['run_id'],
    result_manifest_sha256=sha(manifest_path),allocation=allocation,acceptance_credit=0))
save(N/'review/result-audit-queue-refresh.json',dict(status='NOT_RERUN_KNOWN_INVALID_OTHER_ORDER_STATE',aggregate_regenerated=False,prior_failure_sha256=sha(N/'verification/queue-refresh.json'),canonical_registration_updated=True))
print(json.dumps(dict(summary=summary,result_manifest_sha256=sha(manifest_path),review_allocated=1,actual_remaining=0),ensure_ascii=False))
