"""Release only the reviewed offline implementation, never a real case."""
from pathlib import Path
import datetime as dt,hashlib,json,re
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
review=N/'review/independent-plan-review.json'
assert sha(review)=='7ea4b91b21285088f05e1219303d2d39a47cf8d402fc08306e3377ccc0d44a2c'
r=load(review);assert r['verdict']=='PASS_PLAN_ONLY' and r['plan_sha256']==sha(N/'plan.md')
state_path=T/'current-run.json';index=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
before={str(p):p.read_bytes() for p in (state_path,index)}
state=load(state_path);assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(phase='SOURCE34_E02_CLAIM_GENERATION_OFFLINE_IMPLEMENTATION',workflow_status='executing',stage_queue_state='EXECUTING',active_review_agent=None,
    source34_plan_review=dict(path=str(review),sha256=sha(review),verdict='PASS_PLAN_ONLY'),updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state['source34_offline']['status']='PLAN_PASS_OFFLINE_IMPLEMENTATION'
text,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | E02代码事实生成契约计划独审PASS，root离线TDD最小补修；当前8B/原预算/完整验收保持，actual/model0。 |',before[str(index)].decode('utf8'));assert count==1
folder=N/'verification/implementation-before';folder.mkdir()
for i,(name,data) in enumerate(before.items()):(folder/str(i)).write_bytes(data)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');index.write_text(text,encoding='utf8',newline='\n')
with (N/'verification/implementation-registration.json').open('x',encoding='utf8') as f:json.dump(dict(review_sha256=sha(review),plan_sha256=sha(N/'plan.md'),files={str(p):sha(p) for p in (state_path,index)},actual=0,model=0),f,indent=2)
print('PASS_PLAN_BOUND_OFFLINE_ONLY')
