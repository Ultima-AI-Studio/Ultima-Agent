from pathlib import Path
import datetime, hashlib, json, subprocess, sys
N=Path(__file__).resolve().parents[1];R=N.parents[4];T=N.parent
P=T/'e02-output-budget-controlled-preparation-20261107-r1'
PLAN=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md'
SPEC=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
for part in ('inputs','review','offline'): (N/part).mkdir(exist_ok=False)
assert sha(P/'review/result-inputs/result-manifest.json')=='3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61'
for name,h in json.loads((P/'review/result-inputs/result-manifest.json').read_bytes())['files'].items():assert sha(P/name)==h,name
foreign=json.loads((P/'inputs/unrelated-working-tree.json').read_bytes())
for name,h in foreign['files'].items():assert sha(R/name)==h,name
save(N/'inputs/unrelated-working-tree.json',foreign)
pins=T/'e02-writer-output-budget-20261107-r1/inputs/accepted-dependency-pins.json'
(N/'inputs/accepted-dependency-pins.json').write_bytes(pins.read_bytes())
now=datetime.datetime.now(datetime.timezone.utc).isoformat()
save(N/'inputs/scope.json',dict(original_order='wo-ultimaagent-20261101-0021',recorded_utc=now,
    authority='User resumed active original delivery goal after completed output-structure review; routine offline diagnosis implementation and necessary preparation reviews only',
    previous_turn='PROGRESS: output-structure audit and evidence gaps determined',
    scope='OFFLINE_OUTPUT_STRUCTURE_DIAGNOSTICS',product_parent='0421a54cab572be013c3f7ad562e86406bfe8e52',
    plan=str(PLAN),plan_sha256=sha(PLAN),spec=str(SPEC),spec_sha256=sha(SPEC),
    actual_case_allocation=0,result_review_allocation=0,model_calls=0,implementation_method='root-inline',
    independent_preparation_reviews='exact plan and final frozen preparation; one reviewer active at a time',
    previous_one_case_and_result_review_consumed=True,old_review_receipts_reused=False))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
for i,p in enumerate(paths):
    out=N/'inputs/registration-before'/str(i);out.parent.mkdir(exist_ok=True);out.write_bytes(p.read_bytes())
state=json.loads(paths[0].read_bytes());assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(updated_utc=now,phase='SOURCE32_E02_OUTPUT_STRUCTURE_DIAGNOSTICS_PLAN_REVIEW',active_evidence=str(N),
    active_plan=str(PLAN),active_review_agent='/root/review_e02_output_structure_plan',
    source32_offline=dict(status='PLAN_REVIEW_PENDING',parent='0421a54cab572be013c3f7ad562e86406bfe8e52',
        plan_sha256=sha(PLAN),actual_case_allocation=0,result_review_allocation=0,model_calls=0),
    next_work='Exact preparation plan review, then isolated offline diagnostic implementation; actual allocation stays zero')
paths[0].write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note='E02输出结构诊断接续：当前8B/原预算/原题保持，精确计划独审后新隔离候选离线实现；旧失败保留，实际与结果独审分配0。'
addition=('\n\n## SOURCE32 输出结构诊断离线准备\n\n'+note+'\n计划：'+str(PLAN)+'；证据：'+str(N)+'。\n').encode('utf8')
for p in paths[1:3]:p.write_bytes(p.read_bytes()+addition)
g=paths[3].read_bytes();lines=g.splitlines(keepends=True)
hits=[i for i,line in enumerate(lines) if line.startswith(b'| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(hits)==1
i=hits[0];nl=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
lines[i]=('| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |').encode('utf8')+nl;paths[3].write_bytes(b''.join(lines))
save(N/'inputs/DoR.json',dict(original_order='wo-ultimaagent-20261101-0021',objective=True,write_domain=True,
    offline_acceptance=True,forbidden=True,history_and_budget=True,actual_case_allocation=0,result_review_allocation=0,
    plan_review_required=True,independent_reviewer_concurrency_limit=1,live_worker_readonly_observation_count=0,
    worker_observation_scope='codex.exe exec excluding app-server/exec-server; current collaboration reviewers completed'))
save(N/'verification/registration.json',dict(recorded_utc=now,files={str(p):sha(p) for p in paths},
    plan_sha256=sha(PLAN),scope_sha256=sha(N/'inputs/scope.json'),actual_allocation=0))
print(json.dumps(dict(status='SOURCE32_REGISTERED_OFFLINE',plan_sha256=sha(PLAN),actual_allocation=0)))
