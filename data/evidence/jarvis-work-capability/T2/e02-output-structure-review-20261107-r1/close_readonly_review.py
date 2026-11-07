"""Persist the completed root audit without releasing code or a model case."""
from pathlib import Path
import datetime, hashlib, json, subprocess, sys

R=Path('H:/UltimaAI/UltimaAgent')
T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-output-structure-review-20261107-r1'
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
STATE=T/'current-run.json'
WO=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
STAGE=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
G=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
PLAN=R/'docs/plans/jarvis-work-e02-output-structure-review-plan-20261107.md'
PROPOSAL=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md'
REPORT=R/'docs/reports/jarvis-work-t2-e02-output-structure-review-20261107.md'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')

assert not (N/'manifest.json').exists()
for name,expected in load(N/'input-hashes.json')['files'].items():
    assert sha(name)==expected,name
analysis=load(N/'analysis.json')
assert analysis['product_changes']==analysis['generation_calls_by_this_audit']==0
save(N/'scope-addendum.json',dict(recorded_utc=NOW,previous_scope_sha256=sha(N/'scope.json'),
    original_plan_sha256=load(N/'scope.json')['plan_sha256'],current_plan_sha256=sha(PLAN),
    clarification='Add the concrete diagnostic proposal to documentation write scope; no product/runtime scope change',
    actual_case_allocation=0,model_calls=0,independent_review_allocation=0))

state=load(STATE);before=load(N/'history/current-run-before.json')
assert state['last_actual_result']==before['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
save(N/'history/current-run-before-closeout.json',state)
state.update(updated_utc=NOW,phase='SOURCE31_E02_OUTPUT_STRUCTURE_READONLY_REVIEW_COMPLETE',
    active_report=str(REPORT),active_plan=str(PLAN),next_offline_plan=str(PROPOSAL),
    source_implementation_released=False,live_gate_released=False,
    readonly_review=dict(status='COMPLETE_ROOT_READONLY_AUDIT',independent=False,root=str(N),
        report=str(REPORT),report_sha256=sha(REPORT),analysis_sha256=sha(N/'analysis.json'),
        decision='Bounded rejection diagnostics first; functional output/delivery change deferred pending actual content evidence',
        product_changes=0,model_calls=0,actual_case_allocation=0,independent_review_allocation=0),
    next_action_scope=dict(authorized=False,scope='Concrete diagnostics-only proposal; no implementation or new actual release issued by this read-only audit',
        actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(PROPOSAL),sha256=sha(PROPOSAL),kind='ROOT_READONLY_DIAGNOSTIC_SCOPE_PROPOSAL',
        status='NOT_IMPLEMENTED_NOT_INDEPENDENTLY_APPROVED',actual_case_allocation=0,result_review_allocation=0),
    next_work='Prepare bounded native-output structure diagnostics before choosing functional changes; preserve current8B, original budgets and complete original-task acceptance',
    next_action='Diagnostics proposal is concrete; no new actual case allocated')
assert state['last_actual_result']==before['last_actual_result']
STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
status='E02 输出结构只读审查完成：两例length/2048且正文缺失；已形成16KiB内结构诊断提案，功能修复待证据；当前8B/原预算/原题保持，新增产品与实跑0。'
raw=WO.read_bytes();lines=raw.splitlines(keepends=True)
needle='- 状态：'.encode('utf8')
hits=[i for i,line in enumerate(lines) if line.startswith(needle)]
assert len(hits)==1
i=hits[0];nl=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
lines[i]=('- 状态：'+status).encode('utf8')+nl
WO.write_bytes(b''.join(lines))
addition=('\n\n## 2026-11-07 E02 output structure read-only review complete\n\n'+status+
    '\n报告：'+str(REPORT)+'\n具体提案：'+str(PROPOSAL)+'\n本次是root只读审查，非新增独审PASS；原FAIL和已消费额度不改。\n').encode('utf8')
for path in (WO,STAGE):path.write_bytes(path.read_bytes()+addition)
raw=G.read_bytes();lines=raw.splitlines(keepends=True)
hits=[i for i,line in enumerate(lines) if line.startswith(b'| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(hits)==1
i=hits[0];nl=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
lines[i]=('| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |').encode('utf8')+nl
G.write_bytes(b''.join(lines))
mirrors={}
for path in (PLAN,PROPOSAL,REPORT):
    target=M/path.parent.name/path.name
    with target.open('xb') as f:f.write(path.read_bytes())
    assert sha(target)==sha(path)
    mirrors[str(target)]=sha(target)

q=G.parent; generator=q/'queue-status-gen.py'
assert sha(generator)=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(generator)],capture_output=True,
    creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
save(N/'queue-refresh.json',dict(exit_code=run.returncode,stdout=run.stdout.decode('utf8'),stderr=run.stderr.decode('utf8'),
    generator_sha256=sha(generator),queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True))
assert run.returncode==0
save(N/'closeout.json',dict(recorded_utc=NOW,status='ROOT_READONLY_REVIEW_COMPLETE',independent_review=False,
    candidate='0421a54cab572be013c3f7ad562e86406bfe8e52',
    original_actual_result_preserved=state['last_actual_result']==before['last_actual_result'],
    files={str(p):sha(p) for p in (PLAN,PROPOSAL,REPORT,STATE,WO,STAGE,G)},mirrors=mirrors,
    acceptance_credit=0,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',product_changes=0,actual_cases=0,model_calls=0,
    remote_synced=False,remote_reason='Previous automatic approval rejected push; no retry or alternate channel'))
print(json.dumps(dict(status='ROOT_READONLY_REVIEW_COMPLETE',mirror_documents=len(mirrors),queue_refresh_exit=run.returncode,
    product_changes=0,actual_cases=0,model_calls=0),ensure_ascii=False))
