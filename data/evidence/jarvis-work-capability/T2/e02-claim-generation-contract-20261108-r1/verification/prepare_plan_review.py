"""Bind exact offline plan and register the authorized independent plan review."""
from pathlib import Path
import datetime as dt,hashlib,json,re
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
plan=R/'docs/plans/jarvis-work-e02-claim-generation-contract-plan-20261108.md'
assert sha(plan)==sha(N/'plan.md')=='1e26155fc2bf9a256d9cd4ed694a3537ad9deca6f7915381f2412ad41d09c0ea'
scope=load(N/'inputs/scope.json');assert scope['question_id']=='call_5411de619a6c4de0bab414126a228c7d'
files={str(p):sha(p) for p in (plan,N/'plan.md',Path(scope['source_proposal']),N/'inputs/scope.json',N/'inputs/predecessor.json',N/'exploration/probe.py',N/'exploration/receipt.json')}
files.update(load(N/'exploration/receipt.json')['inputs'])
for name,h in files.items():assert sha(Path(name))==h,name
save(N/'review/plan-inputs.json',dict(plan_sha256=sha(plan),scope_sha256=sha(N/'inputs/scope.json'),files=files,actual_run_authorized=False,actual_case_allocation=0,result_review_allocation=0))
state_path=T/'current-run.json';index_path=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
before={str(p):p.read_bytes() for p in (state_path,index_path)}
state=load(state_path);state.update(phase='SOURCE34_E02_CLAIM_GENERATION_PLAN_REVIEW',workflow_status='audit',stage_queue_state='AUDIT',active_plan=str(plan),active_review_agent='/root/review_e02_claim_generation_plan',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | audit | E02代码事实生成契约离线计划独审；当前8B、原预算、完整验收，actual/model0。 |',before[str(index_path)].decode('utf8'));assert count==1
(N/'review/plan-registration-before').mkdir()
for i,(p,b) in enumerate(before.items()):(N/'review/plan-registration-before'/str(i)).write_bytes(b)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');index_path.write_text(index,encoding='utf8',newline='\n')
print(json.dumps(dict(plan_sha256=sha(plan),members=len(files),actual=0,model=0)))
