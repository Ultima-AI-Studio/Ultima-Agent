"""Bind independent preparation PASS and record readiness, without actual allocation."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
HEAD='d860b2ab4e4d9974e33c96472e4ea15abb807280'
MANIFEST=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
MANIFEST=sha(N/'manifest.json')
review_path=N/'review/independent-preparation-review.json';review=json.loads(review_path.read_bytes())
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==HEAD and review['manifest_sha256']==MANIFEST and review['actual_run_authorized'] is False
assert sha(N/'manifest.json')==MANIFEST
verification=module('current_closeout_verification',N/'verification/verify_preparation.py').verify()
assert verification['tests']==346
approval=dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),review_sha256=sha(review_path),preparation_manifest_sha256=MANIFEST)
save(N/'harness-approval.json',approval)
e=module('current_prepared_entry',N/'code/entry.py');package=e.read_ready(N)
try:e.read_release(N,package,dt.datetime.now(dt.timezone.utc))
except FileNotFoundError:missing_grant_rejected=True
else:raise AssertionError('No actual grant may exist at preparation closeout')
save(N/'verification/ready-readback.json',dict(verdict='PASS_READY_WITHOUT_ACTUAL_ALLOCATION',candidate=HEAD,package=package,
    missing_grant_rejected=missing_grant_rejected,read_release_only=True,run_once_called=False,
    verification=verification,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
report_path=R/'docs/reports/jarvis-work-t2-e02-native-rejection-controlled-preparation-20261107.md'
plan_path=R/'docs/plans/jarvis-work-e02-native-rejection-controlled-entry-plan-20261107.md'
runtime=json.loads((N/'verification/runtime-readiness.json').read_bytes())
member_count=len(json.loads((N/'manifest.json').read_bytes())['files'])
text=(N/'preparation-report.md').read_text('utf8').replace('状态：待独立准备审查。','状态：PASS_OFFLINE_AND_INDEPENDENT_PREPARATION_REVIEW；仅准备通过。',1)
text+='\n独立准备审查PASS_PREPARATION_ONLY；manifest '+MANIFEST+'，'+str(member_count)+'成员；review SHA256 '+sha(review_path)+'。harness-approval/read_ready通过，缺少grant时read_release拒绝，run_once未调用。\n'
for p in (report_path,N/'completion-report.md'):
    assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
pairs=[(plan_path,M/'plans'/plan_path.name),(report_path,M/'reports'/report_path.name),
       (N/'execution-proposal.md',M/'execution-proposals/e02-native-rejection-controlled-20261107.md')]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    target.write_bytes(source.read_bytes());assert source.read_bytes()==target.read_bytes()
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary='E02受控入口就绪：d860b2a冻结，346项离线检查及独立准备PASS；当前8B/原预算保持，待明确单例分配；实际与模型0，E02仍0/3。'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE29_E02_NATIVE_REJECTION_CONTROLLED_READY_AWAITING_ALLOCATION',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report_path),
    active_plan=str(plan_path),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=346,
    preparation_test_scope='61 entry/binding/boundary + 285 deduplicated adapter; N18 product909 frozen baseline not rerun',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    active_preparation=dict(root=str(N),candidate=HEAD,status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',tests=346,
        manifest_sha256=MANIFEST,review_sha256=sha(review_path),harness_approval_sha256=sha(N/'harness-approval.json'),actual_authority=False),
    next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Controlled entry and input preparation',
        status='COMPLETED',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    e02_native_rejection_controlled_preparation=dict(candidate=HEAD,completed=True,review='PASS_PREPARATION_ONLY',tests=346,
        actual_cases=0,model_calls=0,protected_at_readonly_points=True,native_parser_cause_proven=False,remote_synced=False))
state['next_proposal']=dict(path=str(N/'execution-proposal.md'),status='PENDING_EXPLICIT_ONE_CASE_ALLOCATION',actual_case_allocation=0,result_review_allocation=0)
state.update(active_candidate=HEAD, preparation_review_receipt=str(review_path), preparation_review_sha256=sha(review_path),
    preparation_manifest_sha256=MANIFEST,
    next_work='Explicitly allocate one case and one result review on the concrete proposal before actual execution')
state['source29_preparation']=dict(status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',candidate=HEAD,tests=346,manifest_sha256=MANIFEST,review_sha256=sha(review_path),actual_case_allocation=0,result_review_allocation=0)
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 native rejection controlled preparation complete\n\n'+summary+'\n报告：'+str(report_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
ledger=before[str(paths[4])].decode('utf8')
ledger=re.sub(r'(?m)^- Task 1: IN_PROGRESS.*$', '- Task 1: COMPLETE; independent plan PASS, C15 frozen, complete source-only binding and current public/private export contract verified.',ledger)
ledger=re.sub(r'(?m)^- Task 2: PENDING.*$', '- Task 2: COMPLETE; current offline346 and independent preparation PASS; local publication tracked separately.',ledger)
texts[str(paths[4])]=ledger+f'\n- Task 1 COMPLETE; Task 2 offline346 and independent preparation PASS. Manifest {MANIFEST}.\n- read_ready PASS; missing grant rejected by read_release; run_once not called. Actual/model0, E02 0/3.\n- Local publication tracked separately in verification/publication-readback.json; remote push not attempted.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report_path),mirror_files=len(pairs)),ensure_ascii=False))
