"""Register exact independently reviewed offline preparation; keep actual credit zero."""
from pathlib import Path
import datetime as dt,importlib.util,json,re,subprocess,sys
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
R,T,C=v.R,v.T,v.C
review=N/'review/independent-preparation-review.json';r=v.load(review);manifest=v.load(N/'manifest.json')
assert r['reviewer']=='root-independent' and r['verdict']=='PASS_PREPARATION_ONLY'
assert r['manifest_sha256']==v.sha(N/'manifest.json') and r['candidate']==manifest['candidate']
assert r['actual_run_authorized'] is False and r['acceptance_credit']==0
for name,h in manifest['files'].items():assert v.sha(N/name)==h,name
v.verify()
report=R/'docs/reports/jarvis-work-t2-e02-source-grounding-coverage-preparation-20261108.md'
plan=R/'docs/plans/jarvis-work-e02-source-grounding-coverage-plan-20261108.md'
text=(N/'preparation-report.md').read_text('utf8')+'\n\n## 精确独立准备审核\n\nPASS_PREPARATION_ONLY；JSON SHA256 '+v.sha(review)+'。只准进入已授权Task3受控入口准备，不授予实际研究或结果复核。\n'
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability');mirror=[]
for p,kind in ((report,'reports'),(plan,'plans')):
    target=M/kind/p.name
    with target.open('xb') as f:f.write(p.read_bytes())
    mirror.append(dict(source=str(p),target=str(target),sha256=v.sha(p)))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
head=manifest['candidate'];tag=v.load(N/'verification/candidate-freeze.json')['tag']
ready=dict(root=str(N),candidate=head,parent=v.BASE,status='PASS_OFFLINE_PRODUCT_ONLY_ENTRY_NOT_PREPARED',tests=1022,manifest_sha256=v.sha(N/'manifest.json'),review_sha256=v.sha(review),actual_authority=False,model_calls=0,actual_cases=0)
next_work='Continue authorized Task3 controlled entry preparation for '+head+'; actual and result review allocations remain zero'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE36_E02_SOURCE_GROUNDING_OFFLINE_READY',workflow_status='executing',stage_queue_state='EXECUTING',active_review_agent=None,
    active_evidence=str(N),active_implementation_root=str(C),active_candidate_root=str(C),active_product_root=str(C),active_candidate=head,active_product_candidate=head,
    active_report=str(report),active_plan=str(plan),active_preparation=ready,active_preparation_root=str(N),source36_offline=ready,
    active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False),
    preparation_review_path=str(review),preparation_tests_passed=1022,source_candidate_tag=tag,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    next_work=next_work,next_action=next_work,next_offline_plan=str(plan),
    next_action_scope=dict(authorized=True,question_id='call_3d33440cc40c401ea7a2cf11c8bc2bcf',scope='Remaining approved Task3 controlled entry preparation and necessary reviews only',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(plan),status='TASK3_ENTRY_PREPARATION_AUTHORIZED_NO_ACTUAL',actual_case_allocation=0,result_review_allocation=0))
summary='E02证据优先与未读来源机会候选'+head[:7]+'：1022项离线检查及准备独审PASS；保留事实/引用/原题覆盖待验证风险与旧FAIL，继续已授权入口准备，actual/model0。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
note='\n\n## 2026-11-08 SOURCE36 offline preparation\n\n'+summary+'\n报告：'+str(report)+'\n'
texts[str(paths[1])]=wo+note;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+note
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1;texts[str(paths[3])]=index
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+'\n- Frozen '+head+'; 1022 offline checks; independent preparation PASS; Task3 authorized, actual0/model0.\n'
(N/'verification/closeout-before').mkdir()
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(N/'verification/closeout-before'/str(i)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
v.save(N/'verification/closeout-registration.json',dict(candidate=head,review_sha256=v.sha(review),manifest_sha256=v.sha(N/'manifest.json'),mirror=mirror,files={str(p):v.sha(p) for p in paths},actual_allocation=0))
q=Path('H:/UltimaAI/_shared/queue');assert v.sha(q/'queue-status-gen.py')=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
proc=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
v.save(N/'verification/queue-refresh.json',dict(exit_code=proc.returncode,stdout=proc.stdout.decode('utf8'),stderr=proc.stderr.decode('utf8'),queue_sha256=v.sha(q/'queue-status.json')));assert proc.returncode==0
with (N/'verification/queue-status-after.json').open('xb') as f:f.write((q/'queue-status.json').read_bytes())
print(json.dumps(dict(candidate=head,verdict='PASS_OFFLINE_PREPARATION_REGISTERED',next='AUTHORIZED_TASK3',actual=0)))
