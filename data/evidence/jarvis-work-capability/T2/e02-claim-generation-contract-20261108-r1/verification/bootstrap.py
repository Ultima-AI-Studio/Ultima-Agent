"""Register explicitly authorized offline claim-contract work; no live allocation."""
from pathlib import Path
import datetime as dt, hashlib, json, re, subprocess, sys
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
P=T/'e02-output-structure-controlled-preparation-20261108-r1'
B=T/'e02-output-structure-diagnostics-20261108-r2'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
BASE='bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
QUESTION='call_5411de619a6c4de0bab414126a228c7d'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
assert git(R,'rev-parse','HEAD')=='6e30ba9b38ac11f49b88b908d9b8014a154cd9a4'
for root in (C,OLD):
    assert git(root,'rev-parse','HEAD')==BASE and not git(root,'status','--porcelain')
assert sha(P/'review/result-inputs/result-manifest.json')=='2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0'
assert sha(P/'review/independent-result-review.json')=='119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58'
for name,h in load(P/'review/result-inputs/result-manifest.json')['files'].items():assert sha(P/name)==h,name
for name,h in load(P/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
for folder in ('inputs','offline','review','exploration'):(N/folder).mkdir(exist_ok=False)
git(C,'switch','-c','codex/jarvis-e02-claim-generation-r1')
proposal=R/'docs/plans/jarvis-work-e02-claim-generation-contract-proposal-20261108.md'
save(N/'inputs/scope.json',dict(
    work_order='wo-ultimaagent-20261101-0021',stage='T2',question_id=QUESTION,
    answer='授权离线补修、必要独审与入口准备（推荐）',
    scope='Offline code-claim generation expression verification, evidence-led minimal repair, necessary independent reviews and controlled entry preparation',
    source_proposal=str(proposal),spec_sha256=sha(proposal),product_parent=BASE,
    actual_case_allocation=0,result_review_allocation=0,model_calls=0,retry=0,
    model='qwen3-8b-uncensored',model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',
    budgets=load(P/'inputs/input-manifest.json')['budgets'],
    original_question_and_full_acceptance_unchanged=True,
    service_operations=0,UI_operations=0,audio_operations=0,network_requests=0,
    implementation='root inline; independent reviewers only',
    new_actual_requires_explicit_allocation=True))
save(N/'inputs/worktree.json',dict(root=str(C),base=BASE,branch='codex/jarvis-e02-claim-generation-r1',native_created=True,operation_id='4190839a-b100-4cce-aa76-883f2392ba05'))
for target,source in [('accepted-dependency-pins.json',B/'inputs/accepted-dependency-pins.json'),('unrelated-working-tree.json',P/'inputs/unrelated-working-tree.json'),('previous-current-run.json',T/'current-run.json')]:
    (N/'inputs'/target).write_bytes(source.read_bytes())
save(N/'inputs/predecessor.json',dict(root=str(P),candidate=BASE,candidate_root=str(OLD),
    manifest_sha256=sha(P/'manifest.json'),preparation_review_sha256=sha(P/'review/independent-preparation-review.json'),
    result_manifest_sha256=sha(P/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(P/'review/independent-result-review.json'),
    final_readback_sha256=sha(P/'verification/result-final-readback.json'),
    product_preparation=str(B),product_manifest_sha256=sha(B/'manifest.json'),product_review_sha256=sha(B/'review/independent-preparation-review.json')))
copied={}
for name in ('run_product_checks.py','product_pytest.py'):
    src=B/'verification'/name
    text=src.read_text('utf8').replace('/jarvis-e02-output-structure-r2/','/jarvis-e02-claim-generation-r1/')
    (N/'verification'/name).write_text(text,encoding='utf8',newline='\n');copied[name]=sha(src)
save(N/'inputs/copied-test-tools.json',dict(source_root=str(B/'verification'),source_sha256=copied,change='Candidate path only at bootstrap; new focused group will be added before use'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
(N/'inputs/registration-before').mkdir()
before={str(p):p.read_bytes() for p in paths}
for i,p in enumerate(paths):(N/'inputs/registration-before'/str(i)).write_bytes(before[str(p)])
state=load(paths[0]);assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['last_actual_result']['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'
state.update(phase='SOURCE34_E02_CLAIM_GENERATION_OFFLINE_INVESTIGATION',workflow_status='executing',stage_queue_state='EXECUTING',
    active_evidence=str(N),active_implementation_root=str(C),active_review_agent=None,
    active_plan=str(proposal),active_spec=str(proposal),
    source34_offline=dict(status='AUTHORIZED_OFFLINE_INVESTIGATION',root=str(N),parent=BASE,model_calls=0,actual_cases=0,actual_case_allocation=0,result_review_allocation=0),
    next_action_scope=dict(authorized=True,question_id=QUESTION,scope='Offline minimal repair, necessary preparation reviews and controlled entry preparation; no model calls or actual allocation',actual_case_allocation=0,result_review_allocation=0),
    next_work='Verify claim generation expression offline, record implementation plan, minimally repair and independently review, then prepare controlled entry',
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
summary='E02已明确授权离线核验claim生成表达、最小补修、必要独审与入口准备；保留bf7f7a9失败，8B/原预算/完整原题不变，实跑额度0。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
note='\n\n## 2026-11-08 SOURCE34 claim generation offline scope\n\n'+summary+'\n授权：'+QUESTION+'；提案：'+str(proposal)+'\n'
texts[str(paths[1])]=wo+note;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+note
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1;texts[str(paths[3])]=index
for p in paths:assert p.read_bytes()==before[str(p)]
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/registration.json',dict(question_id=QUESTION,files={str(p):sha(p) for p in paths},scope_sha256=sha(N/'inputs/scope.json'),actual_allocation=0))
(N/'progress.md').write_text('# SOURCE34 offline claim generation progress\n\n- User authorized offline repair, necessary review, entry preparation; actual0/model0.\n- Parent and previous actual failure immutable; new native worktree created.\n',encoding='utf8')
print(json.dumps(dict(status='REGISTERED_OFFLINE_ONLY',root=str(C),parent=BASE,actual_allocation=0)))
