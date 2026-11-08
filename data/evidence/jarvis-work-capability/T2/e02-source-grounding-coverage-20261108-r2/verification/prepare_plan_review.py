"""Bind the authorized offline plan to exact read-only review inputs."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
P=T/'e02-claim-generation-controlled-preparation-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
plan=R/'docs/plans/jarvis-work-e02-source-grounding-coverage-plan-20261108.md'
with (N/'plan.md').open('xb') as f:f.write(plan.read_bytes())
scope=load(N/'inputs/scope.json');assert scope['question_id']=='call_3d33440cc40c401ea7a2cf11c8bc2bcf'
paths=[plan,N/'plan.md',Path(scope['source_proposal']),N/'inputs/scope.json',N/'inputs/predecessor.json',N/'inputs/worktree.json',
    N/'exploration/ordered-schema-probe.py',N/'exploration/receipt.json',N/'exploration/original-writer.gbnf',N/'exploration/ordered-writer.gbnf',
    N/'inputs/upstream/json_schema_to_grammar.py',N/'inputs/upstream/json-schema-to-grammar.cpp',N/'inputs/upstream/provenance.json',
    P/'review/independent-result-review.json',P/'review/independent-result-review.md',P/'review/result-inputs/result-manifest.json',
    P/'actual/E02-controlled-1/trusted-runtime.raw',P/'actual/E02-controlled-1/trusted-views.raw',Path(load(P/'review/independent-result-review.json')['artifact']['path'])]
paths += [C/'src/brain'/p for p in ['agent_server.py','work_navigation.py','work_research.py','tests/test_work_sampler_json_strings.py','tests/test_work_source_coverage_budget.py','tests/test_work_research.py','tests/test_work_claim_generation_contract.py']]
paths += [R/'docs'/p for p in ['specs/jarvis-work-capability-contract-20261101.md','specs/jarvis-work-research-evidence-protocol-20261102.md','specs/jarvis-work-research-navigation-v3-20261102.md','plans/jarvis-work-research-source-navigation-design-20261102.md']]
files={str(p):sha(p) for p in paths}
save(N/'review/plan-inputs.json',dict(plan_sha256=sha(plan),scope_sha256=sha(N/'inputs/scope.json'),candidate_root=str(C),parent=scope['product_parent'],files=files,
    actual_run_authorized=False,actual_case_allocation=0,result_review_allocation=0,review_scope='Plan-only independent audit; no tests, model, runtime or product edits'))
git=lambda *args:subprocess.check_output(['git','-C',str(C),*args],text=True,creationflags=subprocess.CREATE_NO_WINDOW).strip()
assert git('rev-parse','HEAD')==scope['product_parent'] and not git('status','--porcelain')
state_path=T/'current-run.json';index_path=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
before={str(p):p.read_bytes() for p in (state_path,index_path)}
state=load(state_path);state.update(phase='SOURCE36_E02_SOURCE_GROUNDING_PLAN_REVIEW',workflow_status='audit',stage_queue_state='AUDIT',active_plan=str(plan),
    active_review_agent='/root/review_e02_source_grounding_plan',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | audit | E02证据优先生成/来源读取余量计划独审；当前8B、原预算、完整验收，actual/model0。 |',before[str(index_path)].decode('utf8'));assert count==1
(N/'review/plan-registration-before').mkdir()
for i,(p,b) in enumerate(before.items()):(N/'review/plan-registration-before'/str(i)).write_bytes(b)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n');index_path.write_text(index,encoding='utf8',newline='\n')
print(json.dumps(dict(plan_sha256=sha(plan),members=len(files),actual=0,model=0)))
