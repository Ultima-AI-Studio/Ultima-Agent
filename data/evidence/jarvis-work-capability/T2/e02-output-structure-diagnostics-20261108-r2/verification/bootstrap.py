"""One bounded closure of PREP-STATE-01; preserve the r1 worktree and evidence."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4];P=T/'e02-output-structure-diagnostics-20261108-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure/UltimaAgent')
PARENT='47ac3a464ca15e01311d5739eda53b2a32d8783c'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
review=P/'review/independent-preparation-review.json';assert sha(review)=='43b4a9af797f991625a7844b39ed21c5630987ecae59668fd34d6d36d2ec040c'
assert load(review)['verdict']=='NEEDS_FIXES'
assert sha(P/'manifest.json')=='05b21259b4ebdf52b987b8a49a3063cc4c6cb642b726d204744c358bcf6f7bf8'
for name,h in load(P/'manifest.json')['files'].items():assert sha(P/name)==h,name
assert git(OLD,'rev-parse','HEAD')==PARENT and not git(OLD,'status','--porcelain')
assert git(C,'rev-parse','HEAD')==PARENT and not git(C,'status','--porcelain')
git(C,'switch','-c','codex/jarvis-e02-output-structure-r2')
for folder in ('inputs','offline','review'):(N/folder).mkdir(exist_ok=False)
for name in ('accepted-dependency-pins.json','unrelated-working-tree.json','DoR.json'):
    (N/'inputs'/name).write_bytes((P/'inputs'/name).read_bytes())
for name in ('independent-plan-review.json','independent-plan-review.md','independent-plan-review-closure.json','independent-plan-review-closure.md'):
    (N/'review'/name).write_bytes((P/'review'/name).read_bytes())
(N/'plan.md').write_bytes((P/'plan.md').read_bytes())
save(N/'inputs/predecessor.json',dict(root=str(P),candidate=PARENT,root_candidate=str(OLD),manifest_sha256=sha(P/'manifest.json'),review_sha256=sha(review),finding='PREP-STATE-01'))
scope=load(P/'inputs/scope.json');scope.update(scope='OFFLINE_PREP_STATE_01_CLOSURE',
    authority='Original exact plan Task2 bounded Important review fix; original goal remains active; no new actual allocation',
    product_parent=PARENT,plan_sha256=sha(N/'plan.md'),actual_case_allocation=0,result_review_allocation=0,model_calls=0)
save(N/'inputs/scope.json',scope)
save(N/'inputs/worktree.json',dict(root=str(C),base=PARENT,branch='codex/jarvis-e02-output-structure-r2',native_created=True,
    operation_id='3581ff49-d7e3-488b-a074-0f5930275336'))
copied={}
for name in ('product_pytest.py','run_product_checks.py','run_final_regressions.py','compatibility_checks.py','verify_offline.py'):
    source=P/'verification'/name;text=source.read_text('utf8').replace('/jarvis-e02-output-structure/','/jarvis-e02-output-structure-r2/')
    (N/'verification'/name).write_text(text,encoding='utf8',newline='\n');copied[name]=sha(source)
save(N/'inputs/copied-tools.json',dict(source_root=str(P/'verification'),source_sha256=copied,change='Only explicit candidate path; dependency guard, budgets and groups unchanged'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
(N/'inputs/registration-before').mkdir()
for i,p in enumerate(paths):(N/'inputs/registration-before'/str(i)).write_bytes(p.read_bytes())
state=load(paths[0]);assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(phase='SOURCE32_R2_E02_OUTPUT_STRUCTURE_REVIEW_FIX',active_evidence=str(N),active_implementation_root=str(C),active_review_agent=None,
    source32_offline=dict(status='NEEDS_FIXES_PREP_STATE_01',frozen_candidate=PARENT,frozen_root=str(OLD),review_sha256=sha(review),
        repair_root=str(N),model_calls=0,actual_case_allocation=0,result_review_allocation=0),
    next_work='RED-to-GREEN minimal diagnostic-state fix, covering suite and exact preparation closure; no actual case')
paths[0].write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note='E02输出结构准备独审发现1项P2诊断状态矛盾；r1/47ac3a4保留，新隔离r2仅补状态关联并验证。当前8B/原预算/完整原题保持，actual/model0。'
for p in paths[1:3]:p.write_bytes(p.read_bytes()+('\n\n## SOURCE32 r2 独审定点补修\n\n'+note+'\n').encode())
lines=paths[3].read_bytes().splitlines(keepends=True);hits=[i for i,line in enumerate(lines) if line.startswith(b'| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(hits)==1
i=hits[0];ending=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n';lines[i]=('| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |').encode()+ending;paths[3].write_bytes(b''.join(lines))
save(N/'verification/registration.json',dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files={str(p):sha(p) for p in paths},scope_sha256=sha(N/'inputs/scope.json'),actual_allocation=0))
print(json.dumps(dict(status='REGISTERED_BOUNDED_REVIEW_FIX',root=str(C),parent=PARENT,actual_allocation=0)))
