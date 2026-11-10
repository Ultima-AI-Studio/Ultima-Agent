"""Close offline preparation only; retain the spent actual result unchanged."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
P=N.parent/'e02-source-coverage-controlled-preparation-20261107-r1'
PLAN=R/'docs/plans/jarvis-work-e02-json-string-sampler-plan-20261107.md'
REPORT=R/'docs/reports/jarvis-work-t2-e02-json-string-sampler-preparation-20261107.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review=json.loads((N/'review/independent-preparation-review.json').read_bytes())
assert review['verdict']=='PASS_PREPARATION_ONLY'
manifest=json.loads((N/'manifest.json').read_bytes())
for name,h in manifest['files'].items():assert sha(N/name)==h,name
assert manifest['candidate']=='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
for name,h in json.loads((N/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==h,name
assert json.loads((P/'review/independent-result-review.json').read_bytes())['verdict']=='FAIL_CONFIRMED'
text=(N/'preparation-report.md').read_text(encoding='utf8')
text=text.replace('状态：PASS_FRESH_OFFLINE_CURRENT_BYTES；独立准备审查待完成。','状态：PASS_OFFLINE_AND_INDEPENDENT_PREPARATION_REVIEW；仅离线准备通过。',1)
text+='\n独立准备审查：PASS_PREPARATION_ONLY。manifest SHA256 '+sha(N/'manifest.json')+'；review SHA256 '+sha(N/'review/independent-preparation-review.json')+'。\n'
for p in [N/'completion-report.md',REPORT]:
    with p.open('x',encoding='utf8') as f:f.write(text)
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
       R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={}
for i,p in enumerate(paths):
    before[str(p)]=sha(p);q=N/'verification/closeout-before'/str(i);q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(p.read_bytes())
state=json.loads(paths[0].read_bytes());last_actual=state['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
prep=dict(root=str(N),candidate=manifest['candidate'],status='PASS_OFFLINE_PRODUCT_ONLY_CONTROLLED_ENTRY_NOT_PREPARED',
    tests=manifest['tests'],manifest_sha256=sha(N/'manifest.json'),
    review_sha256=sha(N/'review/independent-preparation-review.json'),actual_authority=False)
state.update(phase='SOURCE26_E02_JSON_STRING_OFFLINE_PREPARATION_PASS',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    active_product_candidate=manifest['candidate'],active_product_root=str(C),
    active_candidate=manifest['candidate'],active_candidate_root=str(C),
    active_evidence=str(N),active_preparation_root=str(N),active_preparation=prep,
    active_plan=str(PLAN),active_report=str(REPORT),active_review_agent=None,
    active_result_review=dict(verdict='FAIL_CONFIRMED',path=str(P/'review/independent-result-review.json'),
        sha256=sha(P/'review/independent-result-review.json'),scope='LATEST_ACTUAL_ON_FROZEN_PREDECESSOR_E40'),
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',
    preparation_test_count=manifest['tests'],preparation_test_scope='775 fresh product + 6 pinned reference converter; zero actual',
    next_proposal=dict(path=str(PLAN),status='CONTROLLED_ENTRY_PREPARATION_NEXT_NO_ACTUAL_ALLOCATION',
        actual_case_allocation=0,result_review_allocation=0),
    source26_offline=dict(prep,model_calls=0,actual_cases=0,parent=manifest['parent'],
        previous_current_run=str(N/'verification/closeout-before/0')),
    stage_queue_state='BLOCKED',workflow_status='blocked',goal_status='active',
    live_gate_released=False,next_stage_released=False,
    active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',
        E02_controlled_passed=0,required=3,old_credit_transferred=False))
assert state['last_actual_result']==last_actual
paths[0].write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note='E02新候选6d758d9：原生JSON字符串采样兼容补修，781离线检查与准备独审PASS；旧e40实际FAIL保留，未运行新模型，实际0/3；待准备受控入口并明确分配单例。'
addition='\n\n## SOURCE26 离线字符串兼容修复收口\n\n'+note+'\n\n报告：'+str(REPORT)+'；证据：'+str(N)+'。8B、原预算、来源/事实/ACK/时限门保持；新actual/resultreview额度0，T2/Owner未通过。\n'
for p in paths[1:3]:
    raw=p.read_bytes().decode('utf8')
    if p==paths[1]:
        lines=[l for l in raw.splitlines() if l.startswith('- 状态：')]
        assert lines
        raw=raw.replace(lines[0],'- 状态：'+note,1)
    p.write_bytes((raw+addition).encode('utf8'))
g=paths[3].read_bytes().decode('utf8')
rows=[l for l in g.splitlines() if l.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(rows)==1
paths[3].write_bytes(g.replace(rows[0],'| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |',1).encode('utf8'))
mirrors=[]
for p,kind in [(PLAN,'plans'),(REPORT,'reports')]:
    target=M/'docs/shared/research/ultimaagent-work-capability'/kind/p.name
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(p.read_bytes())
    mirrors.append(dict(source=str(p),target=str(target),sha256=sha(p)))
save(N/'verification/closeout-registration.json',dict(candidate=manifest['candidate'],before=before,
    after={str(p):sha(p) for p in paths},mirror=mirrors,last_actual_unchanged=True,actual_cases=0))
generator=Path('H:/UltimaAI/_shared/queue/queue-status-gen.py')
assert sha(generator)=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
r=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',str(generator)],
    capture_output=True,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/queue-refresh.json',dict(exit_code=r.returncode,stdout=r.stdout.decode('utf8','replace'),
    stderr=r.stderr.decode('utf8','replace'),generator_sha256=sha(generator),registered_state='blocked'))
assert r.returncode==0
with (N/'verification/queue-status-after.json').open('xb') as f:f.write(Path('H:/UltimaAI/_shared/queue/queue-status.json').read_bytes())
print(json.dumps(dict(candidate=manifest['candidate'],phase=state['phase'],tests=manifest['tests'],mirrors=2,actual_cases=0)))
