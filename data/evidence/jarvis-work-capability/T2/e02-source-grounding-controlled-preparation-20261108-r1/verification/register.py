"""Register only the already authorized offline entry task before plan review."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
B=T/'e02-source-grounding-coverage-20261108-r2'
PLAN=R/'docs/plans/jarvis-work-e02-source-grounding-controlled-entry-plan-20261108.md'
HEAD='43da3f014a763b8ea3963872a8f1ce8ebea77531'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def copy(a,b):
    if b.exists():assert b.read_bytes()==a.read_bytes(),str(b)
    else:
        with b.open('xb') as f:f.write(a.read_bytes())
for folder in ('inputs','review'):(N/folder).mkdir(exist_ok=True)
final=load(B/'verification/final-readback.json');pub=load(B/'verification/publication-readback.json')
assert final['verdict']=='PASS_FINAL_LOCAL_READBACK' and pub['heads']['candidate']==HEAD
review=load(B/'review/independent-preparation-review.json')
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['manifest_sha256']==sha(B/'manifest.json')
for name,h in load(B/'manifest.json')['files'].items():assert sha(B/name)==h,name
copy(PLAN,N/'plan.md')
copy(T/'current-run.json',N/'inputs/previous-current-run.json')
worker=load(N/'inputs/worker-observation.json');assert worker['count']==worker['foreign_worker_count']==1 and worker['this_order_worker_count']==0
save(N/'inputs/DoR.json',dict(original_order='wo-ultimaagent-20261101-0021',stage='T2',objective=True,exact_write_domain=True,acceptance=True,forbidden=True,history_and_budget=True,independent_plan_review_required=True,plan_sha256=sha(PLAN),actual_case_allocation=0,result_review_allocation=0,product_frozen=True,actual_codex_exec_workers_observed=worker['count'],this_order_workers=0,foreign_workers_preserved=1,reasoning_effort='high'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
assert state['active_candidate']==HEAD and state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(phase='SOURCE37_E02_SOURCE_GROUNDING_ENTRY_PLAN_REVIEW',workflow_status='executing',stage_queue_state='EXECUTING',active_evidence=str(N),active_plan=str(PLAN),active_review_agent=None,
    next_action='Complete authorized offline Task3: independent plan review, frozen rebind, guarded checks, preparation review and local readback',
    next_action_scope=dict(authorized=True,question_id='call_3d33440cc40c401ea7a2cf11c8bc2bcf',scope='Offline controlled entry preparation only',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,service_operations=0),
    live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',goal_registry_status='cleared_by_user',goal_status='none',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
summary='E02候选43da3f0产品1022项检查与独审、本地冻结已完成；继续已授权Task3离线入口准备与必要独审，actual/model/network0，运行态新鲜度待另行分配实跑后原门核验。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
note='\n\n## 2026-11-08 SOURCE37 controlled entry plan\n\n'+summary+'\n计划：'+str(PLAN)+'\n'
texts[str(paths[1])]=wo+note;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+note
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1;texts[str(paths[3])]=index
snapshot=N/'verification/registration-before';snapshot.mkdir()
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];copy(p,snapshot/str(i))
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/registration.json',dict(plan_sha256=sha(PLAN),product_manifest_sha256=sha(B/'manifest.json'),product_final_readback_sha256=sha(B/'verification/final-readback.json'),files={str(p):sha(p) for p in paths},actual_allocation=0,model_calls=0,network_requests=0))
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
review_inputs=[PLAN,R/'docs/plans/jarvis-work-e02-source-grounding-coverage-plan-20261108.md',R/'docs/plans/jarvis-work-e02-source-grounding-and-coverage-proposal-20261108.md',B/'manifest.json',B/'review/independent-preparation-review.json',B/'verification/publication-readback.json',B/'verification/final-readback.json',B/'inputs/current-inputs.json',B/'preparation-report.md',O/'manifest.json',O/'code/entry.py',O/'harness/adapter.py',O/'code/bindings.py',O/'verification/verify_preparation.py',O/'review/independent-result-review.json',N/'inputs/DoR.json',N/'inputs/worker-observation.json']
save(N/'review/plan-inputs.json',dict(plan_sha256=sha(PLAN),candidate=HEAD,files={str(p):sha(p) for p in review_inputs},actual_run_authorized=False))
print(json.dumps(dict(status='REGISTERED_FOR_INDEPENDENT_PLAN_REVIEW',plan_sha256=sha(PLAN),candidate=HEAD,actual=0)))
