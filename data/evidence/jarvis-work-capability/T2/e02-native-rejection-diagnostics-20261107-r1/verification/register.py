"""Register one bounded offline compatibility correction, no actual allocation."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4];P=N.parent/'e02-json-string-controlled-preparation-20261107-r1'
PLAN=R/'docs/plans/jarvis-work-e02-native-response-rejection-diagnostics-plan-20261107.md'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
assert git('rev-parse','HEAD')=='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
assert not git('status','--porcelain','--untracked-files=no')
for name,digest in [('manifest.json','ac1fba00bd3af0cb0e16a5736d8ac6c8ec3ffd1949b0383d0bdc7a2275c90b97'),('review/result-inputs/result-manifest.json','3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b')]:
    assert sha(P/name)==digest
    files=json.loads((P/name).read_bytes())['files']
    for member,h in files.items():assert sha(P/member)==h,member
foreign=json.loads((P/'inputs/unrelated-working-tree.json').read_bytes())
for name,h in foreign['files'].items():assert sha(R/name)==h,name
save(N/'inputs/unrelated-working-tree.json',foreign)
pins=P.parent/'e02-native-pattern-json-20261107-r1/inputs/accepted-dependency-pins.json'
with (N/'inputs/accepted-dependency-pins.json').open('xb') as f:f.write(pins.read_bytes())
for name,h in json.loads(pins.read_bytes())['files'].items():assert sha(Path(name))==h,name
save(N/'inputs/predecessor.json',dict(candidate=git('rev-parse','HEAD'),root=str(P),
    manifest_sha256=sha(P/'manifest.json'),result_manifest_sha256=sha(P/'review/result-inputs/result-manifest.json'),
    result_review_sha256=sha(P/'review/independent-result-review.json'),
    publication_sha256=sha(P/'verification/result-publication-readback.json'),frozen_product=str(C),frozen_product_clean=True))
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={}
for i,p in enumerate(paths):
    before[str(p)]=sha(p);d=N/'inputs/registration-before'/str(i);d.parent.mkdir(exist_ok=True)
    with d.open('xb') as f:f.write(p.read_bytes())
current=json.loads(paths[0].read_bytes())
assert current['actual_case_allocation_remaining']==current['result_review_allocation_remaining']==0
current.update(phase='SOURCE28_E02_NATIVE_REJECTION_PLAN_REVIEW',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    active_evidence=str(N),active_plan=str(PLAN),active_review_agent=None,
    source28_offline=dict(status='PLAN_REVIEW_PENDING',actual_case_allocation=0,result_review_allocation=0,
      product_parent=git('rev-parse','HEAD'),plan_sha256=sha(PLAN),previous_actual_preserved=True,model_calls=0,
      previous_current_run=str(N/'inputs/registration-before/0')))
paths[0].write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note='E02 6d758d9实际FAIL保留；HTTP200原生响应拒绝的具体谓词未知，新增受限原因诊断进入计划独审；新actual=0，保持8B及原预算。'
addition='\n\n## SOURCE28 原生响应拒绝诊断离线补修登记\n\n'+note+'\n\n计划：'+str(PLAN)+'；证据：'+str(N)+'。DoR：目标、精确写域、离线验收、禁止、原单继承均明确；独立计划PASS后方改新候选。原单与T2/Owner保持未通过，本登记不扩大实际额度。\n'
for p in paths[1:3]:
    raw=p.read_bytes();p.write_bytes(raw+addition.encode('utf8'))
g=paths[3].read_bytes().decode('utf8')
old=[line for line in g.splitlines() if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(old)==1
g=g.replace(old[0],'| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |',1)
paths[3].write_bytes(g.encode('utf8'))
save(N/'inputs/DoR.json',dict(original_order='wo-ultimaagent-20261101-0021',stage='T2',
    objective=True,write_domain=True,offline_acceptance=True,forbidden=True,history_and_budget=True,
    actual_case_allocation=0,result_review_allocation=0,scope='OFFLINE_BOUNDED_REJECTION_DIAGNOSTICS_ONLY',
    reasoning_effort='high',independent_review_limit=1,actual_exec_workers_observed=json.loads((N/'inputs/worker-observation.json').read_text(encoding='utf-8-sig'))['count']))
save(N/'verification/registration.json',dict(before=before,after={str(p):sha(p) for p in paths},plan_sha256=sha(PLAN),actual_allocation=0))
print(json.dumps(dict(plan_sha256=sha(PLAN),registered='SOURCE28_OFFLINE',foreign_preserved=len(foreign['files']),actual_allocation=0)))
