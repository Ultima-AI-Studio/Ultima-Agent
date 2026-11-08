"""Register the explicit offline scope; retain the completed actual-case receipt."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess

N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
P=T/'e02-claim-generation-controlled-preparation-20261108-r1'
B=T/'e02-claim-generation-contract-20261108-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
BASE='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
QUESTION='call_3d33440cc40c401ea7a2cf11c8bc2bcf'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
assert git(R,'rev-parse','HEAD')=='9ab8d0c6a064cd2bda557cf1f4e887e181ec9c57'
for root in (C,OLD):assert git(root,'rev-parse','HEAD')==BASE and not git(root,'status','--porcelain')
assert sha(P/'review/result-inputs/result-manifest.json')=='ab388abe9d994ee56b985c14183d14e2af3530a499de4cfe116a8c1a2315dddf'
assert sha(P/'review/independent-result-review.json')=='065d3f6fa910976672f01c02850d0c52f1f34567ccaa295451e427efbe0bb9af'
for name,h in load(P/'review/result-inputs/result-manifest.json')['files'].items():assert sha(P/name)==h,name
for name,h in load(P/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
for folder in ('inputs','offline','review','exploration'):(N/folder).mkdir(exist_ok=False)
git(C,'switch','-c','codex/jarvis-e02-source-grounding-r1')
proposal=R/'docs/plans/jarvis-work-e02-source-grounding-and-coverage-proposal-20261108.md'
save(N/'inputs/scope.json',dict(work_order='wo-ultimaagent-20261101-0021',stage='T2',question_id=QUESTION,
    answer='授权离线审查、最小补修、必要独审与入口准备（推荐）',
    scope='Offline source-grounding expression and read-coverage review, evidence-led minimal repair, necessary independent reviews and controlled entry preparation',
    source_proposal=str(proposal),spec_sha256=sha(proposal),product_parent=BASE,
    actual_case_allocation=0,result_review_allocation=0,model_calls=0,retry=0,
    model='qwen3-8b-uncensored',model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',
    budgets=load(P/'inputs/input-manifest.json')['budgets'],original_question_and_full_acceptance_unchanged=True,
    service_operations=0,UI_operations=0,audio_operations=0,network_requests=0,
    implementation='root inline; independent reviewers only',new_actual_requires_explicit_allocation=True))
save(N/'inputs/worktree.json',dict(root=str(C),base=BASE,branch='codex/jarvis-e02-source-grounding-r1',native_created=True,operation_id='70b32860-f4d9-4a56-8eab-0c12cc852650'))
for target,source in [('accepted-dependency-pins.json',B/'inputs/accepted-dependency-pins.json'),('unrelated-working-tree.json',P/'inputs/unrelated-working-tree.json'),('previous-current-run.json',T/'current-run.json')]:
    with (N/'inputs'/target).open('xb') as f:f.write(source.read_bytes())
save(N/'inputs/predecessor.json',dict(root=str(P),candidate=BASE,candidate_root=str(OLD),manifest_sha256=sha(P/'manifest.json'),
    preparation_review_sha256=sha(P/'review/independent-preparation-review.json'),result_manifest_sha256=sha(P/'review/result-inputs/result-manifest.json'),
    result_review_sha256=sha(P/'review/independent-result-review.json'),final_readback_sha256=sha(P/'verification/result-final-readback.json'),
    result_publication_sha256=sha(P/'verification/result-publication-readback.json'),
    product_preparation=str(B),product_manifest_sha256=sha(B/'manifest.json'),product_review_sha256=sha(B/'review/independent-preparation-review.json')))
copied={}
for name in ('run_product_checks.py','product_pytest.py','compatibility_checks.py','grammar_checks.py','run_final_regressions.py'):
    src=B/'verification'/name
    value=src.read_text('utf8').replace('/jarvis-e02-claim-generation-r1/','/jarvis-e02-source-grounding-r1/')
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(value)
    copied[name]=dict(source_sha256=sha(src),current_sha256=sha(N/'verification'/name))
for sub in ('upstream','native-log-supplement'):
    (N/'inputs'/sub).mkdir()
    for src in (B/'inputs'/sub).iterdir():
        if src.is_file():
            with (N/'inputs'/sub/src.name).open('xb') as f:f.write(src.read_bytes())
save(N/'inputs/copied-test-tools.json',dict(source_root=str(B/'verification'),files=copied,change='Candidate path only at bootstrap; focused groups and exact reference checks will be added before use'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
(N/'inputs/registration-before').mkdir()
before={str(p):p.read_bytes() for p in paths}
for i,p in enumerate(paths):(N/'inputs/registration-before'/str(i)).write_bytes(before[str(p)])
state=load(paths[0]);assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['last_actual_result']['run_id']=='1496a844-668d-407a-a91b-89be246ba05b'
state.update(phase='SOURCE36_E02_SOURCE_GROUNDING_COVERAGE_OFFLINE_INVESTIGATION',workflow_status='executing',stage_queue_state='EXECUTING',
    active_evidence=str(N),active_implementation_root=str(C),active_review_agent=None,active_plan=str(proposal),active_spec=str(proposal),
    source36_offline=dict(status='AUTHORIZED_OFFLINE_INVESTIGATION',root=str(N),parent=BASE,model_calls=0,actual_cases=0,actual_case_allocation=0,result_review_allocation=0),
    next_action_scope=dict(authorized=True,question_id=QUESTION,scope='Offline review, minimal repair, necessary preparation reviews and controlled entry preparation; no model calls or actual allocation',actual_case_allocation=0,result_review_allocation=0),
    new_live_cases_this_execution=0,new_work_cli_submissions_this_execution=0,new_completed_native_posts_this_execution=0,
    next_work='Review evidence-first schema representation and read coverage offline; plan review, minimal repair, preparation review and controlled entry',
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
summary='E02已明确授权离线审查逐来源证据表达与选页覆盖、最小补修、必要独审及入口准备；保留d8f8d97已写文件但事实/覆盖失败，当前8B/原预算/完整原题保持，实跑额度0。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
note='\n\n## 2026-11-08 SOURCE36 source grounding and coverage offline scope\n\n'+summary+'\n授权：'+QUESTION+'；提案：'+str(proposal)+'\n'
texts[str(paths[1])]=wo+note;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+note
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1;texts[str(paths[3])]=index
for p in paths:assert p.read_bytes()==before[str(p)]
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/registration.json',dict(question_id=QUESTION,files={str(p):sha(p) for p in paths},scope_sha256=sha(N/'inputs/scope.json'),actual_allocation=0))
(N/'progress.md').write_text('# SOURCE36 offline source grounding and coverage progress\n\n- Explicit offline review, minimal repair, necessary independent reviews and entry preparation authorized; actual0/model0.\n- Previous actual artifact and FAIL_CONFIRMED remain immutable; new native worktree created.\n- Ruling: approved concrete proposal and root-inline method supersede repeated skill handoff questions; necessary plan/preparation independent reviews remain.\n- Ruling: create a new worktree despite existing isolation because the existing candidate and its actual evidence are frozen; native tool used. No installs, service operations, remote push or scratch deletion.\n',encoding='utf8')
print(json.dumps(dict(status='REGISTERED_OFFLINE_ONLY',root=str(C),parent=BASE,actual_allocation=0)))
