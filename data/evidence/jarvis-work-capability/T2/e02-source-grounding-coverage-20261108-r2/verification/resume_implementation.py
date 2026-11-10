"""Read back the exact independent plan approval before authorized offline edits."""
from pathlib import Path
import datetime as dt,hashlib,json,re
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review=load(N/'review/independent-plan-review.json');inputs=load(N/'review/plan-inputs.json')
assert sha(N/'review/independent-plan-review.json')=='82b7d2213526760e097563a775bc23210f26124ca93d9186818dcefcebebb14f'
assert sha(N/'review/independent-plan-review.md')=='63e6cfa8129947746942d7063c9f9b2fdaf031620fb635c51741bd4c74093fd6'
assert review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')==inputs['plan_sha256']
assert review['plan_inputs_sha256']==sha(N/'review/plan-inputs.json')
preserved={}
for name,h in inputs['files'].items():
    p=Path(name);assert sha(p)==h,name
    if p.is_relative_to(C):
        target=N/'inputs/reviewed-parent'/p.relative_to(C);target.parent.mkdir(parents=True,exist_ok=True)
        with target.open('xb') as f:f.write(p.read_bytes())
        preserved[name]=dict(snapshot=str(target),sha256=h)
save(N/'inputs/plan-reviewed-parent-snapshots.json',dict(parent=inputs['parent'],plan_inputs_sha256=sha(N/'review/plan-inputs.json'),files=preserved))
state_path=T/'current-run.json';index_path=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
before={str(p):p.read_bytes() for p in (state_path,index_path)}
(N/'inputs/implementation-before').mkdir()
for i,(name,raw) in enumerate(before.items()):(N/'inputs/implementation-before'/str(i)).write_bytes(raw)
state=load(state_path);state.update(phase='SOURCE36_E02_SOURCE_GROUNDING_OFFLINE_IMPLEMENTATION',workflow_status='executing',stage_queue_state='EXECUTING',active_review_agent=None,
    source36_plan_review=dict(verdict='PASS_PLAN_ONLY',path=str(N/'review/independent-plan-review.json'),sha256=sha(N/'review/independent-plan-review.json')),
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state['source36_offline']['status']='AUTHORIZED_OFFLINE_IMPLEMENTATION_PLAN_REVIEWED'
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | E02证据优先生成/读取余量计划独审PASS，75项父版基线通过；离线RED/GREEN实施，actual/model0。 |',before[str(index_path)].decode('utf8'));assert count==1
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');index_path.write_text(index,encoding='utf8',newline='\n')
save(N/'verification/implementation-registration.json',dict(plan_review_sha256=sha(N/'review/independent-plan-review.json'),plan_sha256=sha(N/'plan.md'),parent_sources_preserved=len(preserved),actual_allocation=0,
    before={name:hashlib.sha256(raw).hexdigest() for name,raw in before.items()},after={str(p):sha(p) for p in (state_path,index_path)}))
ledger=R/'.superpowers/sdd/jarvis-work-e02-source-grounding-coverage-plan-20261108/progress.md'
with ledger.open('a',encoding='utf8',newline='\n') as f:f.write('\n- Exact plan independent review PASS_PLAN_ONLY (82b7d221...), all 30 inputs read back; seven parent source snapshots preserved before edits. Task1 begins RED/GREEN; no actual/model authority.\n')
print(json.dumps(dict(status='OFFLINE_IMPLEMENTATION_REGISTERED',plan_review=review['verdict'],parent_snapshots=len(preserved),actual=0,model=0)))
