"""Publish the reviewed product preparation while preserving the spent actual."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path(json.loads((N/'inputs/worktree.json').read_bytes())['root'])
PLAN=R/'docs/plans/jarvis-work-e02-writer-output-budget-alignment-plan-20261107.md'
REPORT=R/'docs/reports/jarvis-work-t2-e02-writer-output-budget-preparation-20261107.md'
TAG='ultimaagent-e02-output-budget-ready-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review_path=N/'review/independent-preparation-review.json';review=json.loads(review_path.read_bytes())
manifest=json.loads((N/'manifest.json').read_bytes());HEAD=manifest['candidate'];MH=sha(N/'manifest.json');RH=sha(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['manifest_sha256']==MH and review['candidate']==HEAD and review['actual_run_authorized'] is False
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in json.loads((N/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==h,name
text=(N/'preparation-report.md').read_text('utf8').replace('状态：PASS_FRESH_OFFLINE_CURRENT_BYTES；独立准备审查待完成。','状态：PASS_OFFLINE_AND_INDEPENDENT_PREPARATION_REVIEW；仅离线准备通过。',1)
text+='\n独立准备审查PASS_PREPARATION_ONLY；manifest '+MH+'；review '+RH+'。\n'
for p in (N/'completion-report.md',REPORT):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={}
for i,p in enumerate(paths):
    before[str(p)]=sha(p);q=N/'verification/closeout-before'/str(i);q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(p.read_bytes())
s=json.loads(paths[0].read_bytes());last=s['last_actual_result']
assert s['actual_case_allocation_remaining']==s['result_review_allocation_remaining']==0
alias_names=('preparation_review_path','preparation_tests_passed','preparation_sync','local_checkpoint_tag','remote_sync','next_action','next_offline_plan','source_candidate_tag','goal_status','goal_registry_status')
s['source30_superseded_preparation_aliases']={k:s.get(k) for k in alias_names}
prep=dict(root=str(N),candidate=HEAD,status='PASS_OFFLINE_PRODUCT_ONLY_CONTROLLED_ENTRY_NOT_PREPARED',tests=manifest['tests'],manifest_sha256=MH,review_sha256=RH,actual_authority=False)
s.update(phase='SOURCE30_E02_OUTPUT_BUDGET_OFFLINE_PREPARATION_PASS',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    active_candidate=HEAD,active_candidate_root=str(C),active_product_candidate=HEAD,active_product_root=str(C),
    active_evidence=str(N),active_preparation_root=str(N),active_preparation=prep,active_plan=str(PLAN),active_report=str(REPORT),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',
    preparation_review_receipt=str(review_path),preparation_review_path=str(review_path),preparation_review_sha256=RH,preparation_manifest_sha256=MH,
    preparation_test_count=manifest['tests'],preparation_tests_passed=manifest['tests'],preparation_test_scope='Fresh product regression plus 3 legacy/current observer compatibility checks; zero actual',
    local_checkpoint_tag=TAG,source_candidate_tag='ultimaagent-e02-output-budget-candidate-20261107',
    preparation_sync=dict(status='REFER_TO_LOCAL_PUBLICATION_READBACK_REMOTE_BLOCKED',local_tag=TAG,publication_receipt=str(N/'verification/publication-readback.json'),new_push_attempted=False,remote_synced=False),
    remote_sync=dict(status='PRIOR_AUTOMATIC_APPROVAL_BLOCK_NO_RETRY',local_tag=TAG,new_push_attempted=False,remote_synced=False),
    next_work='Continue authorized controlled entry preparation; do not execute a model case',next_action='Prepare N21 entry under the approved Task2; actual allocation remains zero',next_offline_plan=str(PLAN),
    next_proposal=dict(path=str(PLAN),status='CONTROLLED_ENTRY_PREPARATION_NEXT_NO_ACTUAL_ALLOCATION',actual_case_allocation=0,result_review_allocation=0),
    source30_offline=dict(prep,parent=manifest['parent'],model_calls=0,actual_cases=0),
    workflow_status='blocked',stage_queue_state='BLOCKED',goal_status='blocked',goal_registry_status='blocked',goal_registry_note='Fresh goal tool observation remains blocked; authorized offline work continues; this is not a new blocking audit or completed goal',
    live_gate_released=False,next_stage_released=False,active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False))
assert s['last_actual_result']==last
paths[0].write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note='E02候选'+HEAD[:7]+'输出预算提示对齐：'+str(manifest['tests'])+'项离线检查和产品准备独审PASS；继续已授权入口准备，actual/model0，E02仍0/3。'
addition='\n\n## SOURCE30 输出预算对齐产品准备收口\n\n'+note+'\n报告：'+str(REPORT)+'\n'
for p in paths[1:3]:
    text=p.read_text('utf8')
    if p==paths[1]:
        line=next(l for l in text.splitlines() if l.startswith('- 状态：'));text=text.replace(line,'- 状态：'+note,1)
    p.write_text(text+addition,encoding='utf8',newline='\n')
text=paths[3].read_text('utf8');rows=[l for l in text.splitlines() if l.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(rows)==1
paths[3].write_text(text.replace(rows[0],'| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |',1),encoding='utf8',newline='\n')
mirrors=[]
for p,kind in ((PLAN,'plans'),(REPORT,'reports')):
    target=M/'docs/shared/research/ultimaagent-work-capability'/kind/p.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(p.read_bytes())
    mirrors.append(dict(source=str(p),target=str(target),sha256=sha(p)))
save(N/'verification/closeout-registration.json',dict(candidate=HEAD,before=before,after={str(p):sha(p) for p in paths},mirror=mirrors,last_actual_unchanged=True,actual_cases=0))
generator=Path('H:/UltimaAI/_shared/queue/queue-status-gen.py');assert sha(generator)=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
r=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',str(generator)],capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/queue-refresh.json',dict(exit_code=r.returncode,stdout=r.stdout.decode('utf8','replace'),stderr=r.stderr.decode('utf8','replace'),generator_sha256=sha(generator),registered_state='blocked'));assert r.returncode==0
with (N/'verification/queue-status-after.json').open('xb') as f:f.write(Path('H:/UltimaAI/_shared/queue/queue-status.json').read_bytes())
with (N/'progress.md').open('a',encoding='utf8') as f:f.write('\nTask1: independent preparation PASS; local publication is recorded by its separate readback. Task2 entry preparation next.\n')
print(json.dumps(dict(candidate=HEAD,tests=manifest['tests'],actual_cases=0)))
