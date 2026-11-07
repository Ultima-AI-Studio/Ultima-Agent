"""Bind exact independent PASS; preparation is never actual authority."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
HEAD='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
TAG='ultimaagent-e02-claim-generation-controlled-ready-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
manifest=load(N/'manifest.json');manifest_sha=sha(N/'manifest.json')
rp=N/'review/independent-preparation-review.json';review=load(rp)
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==HEAD and review['manifest_sha256']==manifest_sha and review['actual_run_authorized'] is False
verification=module('entry_closeout_verification',N/'verification/verify_preparation.py').verify()
tests=verification['tests'];assert tests==manifest['test_count']
save(N/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),review_sha256=sha(rp),preparation_manifest_sha256=manifest_sha))
e=module('prepared_original_entry',N/'code/entry.py');package=e.read_ready(N)
try:e.read_release(N,package,dt.datetime.now(dt.timezone.utc))
except FileNotFoundError:missing_grant_rejected=True
else:raise AssertionError('Preparation must not contain an actual grant')
save(N/'verification/ready-readback.json',dict(verdict='PASS_READY_WITHOUT_ACTUAL_ALLOCATION',candidate=HEAD,package=package,missing_grant_rejected=missing_grant_rejected,read_release_only=True,run_once_called=False,verification=verification,live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',current_runtime_verified=False,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
report=R/'docs/reports/jarvis-work-t2-e02-claim-generation-controlled-preparation-20261108.md'
plan=R/'docs/plans/jarvis-work-e02-claim-generation-controlled-entry-plan-20261108.md'
text=(N/'preparation-report.md').read_text('utf8').replace('状态：待独立准备审查。','状态：PASS_OFFLINE_AND_INDEPENDENT_PREPARATION_REVIEW；仅准备通过。',1)
text+='\n独立准备审查PASS_PREPARATION_ONLY；manifest '+manifest_sha+'，'+str(len(manifest['files']))+'成员；review SHA256 '+sha(rp)+'。harness-approval/read_ready通过；缺少grant时read_release拒绝，run_once未调用。\n'
for p in (report,N/'completion-report.md'):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
pairs=[(plan,M/'plans'/plan.name),(report,M/'reports'/report.name),(N/'execution-proposal.md',M/'execution-proposals/e02-claim-generation-controlled-20261108.md')]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(source.read_bytes())
    assert source.read_bytes()==target.read_bytes()
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=load(paths[0]);last_actual=state['last_actual_result']
assert last_actual==load(N/'inputs/previous-current-run.json')['last_actual_result']
summary=f'E02受控入口就绪：d8f8d97冻结，{tests}项新鲜入口检查及独立准备PASS；当前8B/原预算/完整原题验收保持，待明确单例分配；实际与模型0，E02仍0/3。'
aliases=('preparation_review_path','preparation_tests_passed','preparation_sync','local_checkpoint_tag','remote_sync','next_action','next_offline_plan','source_candidate_tag')
state['source35_superseded_preparation_aliases']={k:state.get(k) for k in aliases}
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE35_E02_CLAIM_GENERATION_CONTROLLED_READY_AWAITING_ALLOCATION',live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',workflow_status='AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',stage_queue_state='BLOCKED',goal_status='blocked',goal_registry_status='blocked',
    active_evidence=str(N),active_preparation_root=str(N),active_report=str(report),active_plan=str(plan),active_product_candidate=HEAD,active_product_root=str(C),active_candidate=HEAD,active_candidate_root=str(C),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=tests,preparation_tests_passed=tests,
    preparation_test_scope=f"{sum(v['tests'] for v in verification['stdlib'].values())} entry/binding/boundary plus {verification['harness_unique']} unique adapter; N34 product994 plus compatibility4 and official reference6 frozen evidence, not rerun",
    preparation_review_path=str(rp),preparation_review_receipt=str(rp),preparation_review_sha256=sha(rp),preparation_manifest_sha256=manifest_sha,
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    active_preparation=dict(root=str(N),candidate=HEAD,status='READY_OFFLINE_AWAITING_EXPLICIT_ALLOCATION_AND_FRESH_PREFLIGHT',tests=tests,manifest_sha256=manifest_sha,review_sha256=sha(rp),harness_approval_sha256=sha(N/'harness-approval.json'),actual_authority=False),
    next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Authorized offline claim-generation controlled entry preparation',status='COMPLETED',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    source35_preparation=dict(status='READY_OFFLINE_AWAITING_EXPLICIT_ALLOCATION_AND_FRESH_PREFLIGHT',candidate=HEAD,tests=tests,manifest_sha256=manifest_sha,review_sha256=sha(rp),actual_case_allocation=0,result_review_allocation=0),
    e02_claim_generation_controlled_preparation=dict(candidate=HEAD,completed=True,tests=tests,review='PASS_PREPARATION_ONLY',actual_cases=0,model_calls=0,current_runtime_verified=False,live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',new_candidate_actual_output_not_yet_captured=True,real_delivery_improvement_proven=False,remote_synced=False),
    next_proposal=dict(path=str(N/'execution-proposal.md'),status='PENDING_EXPLICIT_ONE_CASE_ALLOCATION',actual_case_allocation=0,result_review_allocation=0),
    preparation_sync=dict(status='REFER_TO_LOCAL_PUBLICATION_READBACK_REMOTE_BLOCKED',local_tag=TAG,publication_receipt=str(N/'verification/publication-readback.json'),new_push_attempted=False,remote_synced=False),
    local_checkpoint_tag=TAG,source_candidate_tag='ultimaagent-e02-claim-generation-candidate-20261108-r1',
    remote_sync=dict(status='PRIOR_AUTOMATIC_APPROVAL_BLOCK_NO_RETRY',local_tag=TAG,new_push_attempted=False,remote_synced=False),
    next_action='Await explicit one-case and independent result-review allocation; do not execute before allocation',next_offline_plan=str(plan),next_work='Explicit one-case allocation is required; original fresh runtime preflight must pass before model work')
assert state['last_actual_result']==last_actual and state['e02']=='NOT_PASSED' and state['t2']=='NOT_PASSED'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-08 E02 claim generation controlled preparation reviewed\n\n'+summary+'\n报告：'+str(report)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
ledger=before[str(paths[4])].decode('utf8')
ledger=re.sub(r'(?m)^- Task 1: IN_PROGRESS.*$',f'- Task 1: COMPLETE; frozen product unchanged, original core AST unchanged, {tests} fresh entry checks PASS.',ledger)
ledger=re.sub(r'(?m)^- Task 2: PENDING.*$', '- Task 2: PREPARATION_REVIEW_COMPLETE; independent preparation PASS and missing-grant refusal; publication/final readback recorded in later receipts.',ledger)
texts[str(paths[4])]=ledger+'\n- Actual/model/result-review allocation0. E02/T2/Owner not passed. No remote push retry.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)]
    with (snap/(str(i)+'-'+p.name)).open('xb') as f:f.write(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=manifest_sha,review_sha256=sha(rp),before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report),mirror_files=len(pairs)),ensure_ascii=False))
