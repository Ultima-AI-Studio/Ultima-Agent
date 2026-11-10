"""Record a reviewed offline candidate; do not grant a research execution."""
from pathlib import Path
import datetime as dt,importlib.util,json,subprocess
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,R,T,C,git,sha,load,save=v.N,v.R,v.T,v.C,v.git,v.sha,v.load,v.save
M=Path('H:/UltimaAI/ultima-docs-repo')
PLAN=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md'
REPORT=R/'docs/reports/jarvis-work-t2-e02-output-structure-diagnostics-preparation-20261108-r2.md'
TAG='ultimaagent-e02-output-structure-ready-20261108-r2'
manifest=load(N/'manifest.json');head=manifest['candidate'];review_path=N/'review/independent-preparation-review.json';review=load(review_path)
mh=sha(N/'manifest.json');rh=sha(review_path)
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['candidate']==head
assert review['manifest_sha256']==mh and review['actual_run_authorized'] is False
for name,h in manifest['files'].items():assert sha(N/name)==h,name
assert git(C,'rev-parse','HEAD').decode().strip()==head and not git(C,'status','--porcelain').strip()
text=(N/'preparation-report.md').read_text('utf8')
old='独立准备审查尚待精确本包复核，下一步只有其PASS后才准备新入口'
assert old in text;text=text.replace(old,'独立准备审查已对本包给出PASS_PREPARATION_ONLY，下一步准备新入口',1)
text+='\n独立审查：'+str(review_path)+'；manifest SHA256 '+mh+'；review SHA256 '+rh+'。本地提交/镜像状态由 publication-readback.json 单独证明。\n'
for p in (N/'completion-report.md',REPORT):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
for i,p in enumerate(paths):
    backup=N/'verification/closeout-before'/str(i);backup.parent.mkdir(exist_ok=True)
    with backup.open('xb') as f:f.write(p.read_bytes())
state=load(paths[0]);last=state['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
prep=dict(root=str(N),candidate=head,status='PASS_OFFLINE_PRODUCT_ONLY_CONTROLLED_ENTRY_NOT_PREPARED',tests=manifest['tests'],
    manifest_sha256=mh,review_sha256=rh,actual_authority=False)
state.update(phase='SOURCE32_R2_E02_OUTPUT_STRUCTURE_DIAGNOSTICS_PREPARATION_PASS',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    active_candidate=head,active_candidate_root=str(C),active_product_candidate=head,active_product_root=str(C),
    active_evidence=str(N),active_preparation_root=str(N),active_preparation=prep,active_plan=str(PLAN),active_report=str(REPORT),active_review_agent=None,
    source32_offline=dict(prep,parent=manifest['parent'],model_calls=0,actual_cases=0),
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',
    preparation_review_path=str(review_path),preparation_review_receipt=str(review_path),preparation_review_sha256=rh,preparation_manifest_sha256=mh,
    preparation_test_count=manifest['tests'],preparation_tests_passed=manifest['tests'],preparation_test_scope=f'Fresh{manifest["tests"]-4} product plus4 compatibility; zero actual',
    local_checkpoint_tag=TAG,source_candidate_tag='ultimaagent-e02-output-structure-candidate-20261108-r2',
    preparation_sync=dict(status='REFER_TO_LOCAL_PUBLICATION_READBACK_REMOTE_BLOCKED',local_tag=TAG,
        publication_receipt=str(N/'verification/publication-readback.json'),remote_synced=False,new_push_attempted=False),
    remote_sync=dict(status='PRIOR_AUTOMATIC_APPROVAL_BLOCK_NO_RETRY',remote_synced=False,new_push_attempted=False),
    next_work='Prepare a new controlled entry bound to this frozen diagnostic candidate; actual allocation stays zero',
    next_action='Complete controlled entry preparation before requesting one-case allocation',next_offline_plan=str(PLAN),
    next_proposal=dict(path=str(PLAN),status='CONTROLLED_ENTRY_PREPARATION_NEXT_NO_ACTUAL_ALLOCATION',actual_case_allocation=0,result_review_allocation=0),
    workflow_status='OFFLINE_PREPARATION_COMPLETE_E02_PENDING',stage_queue_state='BLOCKED',goal_status='active',goal_registry_status='active',
    goal_registry_note='Current goal tool reports active; T2 exit is not passed and actual allocation is zero',
    live_gate_released=False,next_stage_released=False,active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',
        E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False))
assert state['last_actual_result']==last
paths[0].write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note=f'E02候选{head[:7]}输出结构诊断：{manifest["tests"]}项离线检查与独立准备审查PASS；真实截断正文仍待新入口与明确单例分配。当前8B/原预算/完整原题保持，actual/model0，E02仍0/3。'
addition=('\n\n## SOURCE32 输出结构诊断准备收口\n\n'+note+'\n报告：'+str(REPORT)+'\n').encode('utf8')
for p in paths[1:3]:
    raw=p.read_bytes()
    if p==paths[1]:
        lines=raw.splitlines(keepends=True);hits=[i for i,line in enumerate(lines) if line.startswith('- 状态：'.encode())];assert len(hits)==1
        i=hits[0];ending=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n';lines[i]=('- 状态：'+note).encode()+ending;raw=b''.join(lines)
    p.write_bytes(raw+addition)
lines=paths[3].read_bytes().splitlines(keepends=True)
hits=[i for i,line in enumerate(lines) if line.startswith(b'| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(hits)==1
i=hits[0];ending=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
lines[i]=('| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |').encode()+ending;paths[3].write_bytes(b''.join(lines))
mirrors=[]
for p,kind in ((PLAN,'plans'),(REPORT,'reports')):
    target=M/'docs/shared/research/ultimaagent-work-capability'/kind/p.name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(p.read_bytes())
    mirrors.append(dict(source=str(p),target=str(target),sha256=sha(p)))
save(N/'verification/closeout-registration.json',dict(candidate=head,manifest_sha256=mh,review_sha256=rh,
    after={str(p):sha(p) for p in paths},mirror=mirrors,last_actual_unchanged=True,actual_cases=0,model_calls=0))
generator=Path('H:/UltimaAI/_shared/queue/queue-status-gen.py')
assert sha(generator)=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
r=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',str(generator)],
    capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/queue-refresh.json',dict(exit_code=r.returncode,stdout=r.stdout.decode('utf8','replace'),
    stderr=r.stderr.decode('utf8','replace'),generator_sha256=sha(generator),registered_state='blocked'))
assert r.returncode==0
with (N/'verification/queue-status-after.json').open('xb') as f:f.write(Path('H:/UltimaAI/_shared/queue/queue-status.json').read_bytes())
print(json.dumps(dict(candidate=head,tests=manifest['tests'],actual_cases=0,goal_status='active')))
