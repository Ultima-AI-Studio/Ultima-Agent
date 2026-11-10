"""Register controlled-entry preparation; the continuing goal allocates no case."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];T=N.parent
B=T/'e02-native-rejection-diagnostics-20261107-r1';O=T/'e02-json-string-controlled-preparation-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
PLAN=R/'docs/plans/jarvis-work-e02-native-rejection-controlled-entry-plan-20261107.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
for folder in ('inputs','code','harness','tests','offline','review','verification'):(N/folder).mkdir(exist_ok=True)
expected={'manifest.json':'5ecc68ffa1e4828c81d778a02e1ae9664bd692efbbd7073c9bc4ef13481fbf4b',
    'review/independent-preparation-review.json':'b66d78f6eab63cbbfc03ff2f9cff884e1298ff842e8d612610d325c1dd2da3c7',
    'verification/publication-readback.json':'5fd086520e950b924f50be5dea9f19f9ac42878deab0914f9ef8433ea1a364e9'}
for name,h in expected.items():assert sha(B/name)==h
for name,h in json.loads((B/'manifest.json').read_bytes())['files'].items():assert sha(B/name)==h,name
for name,h in json.loads((B/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==h,name
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-native-rejection-candidate-20261107')=='d860b2ab4e4d9974e33c96472e4ea15abb807280'
assert not git('status','--porcelain')
save(N/'inputs/predecessor.json',dict(root=str(B),candidate=git('rev-parse','HEAD'),
    manifest_sha256=expected['manifest.json'],review_sha256=expected['review/independent-preparation-review.json'],
    publication_sha256=expected['verification/publication-readback.json'],entry_predecessor=str(O),
    entry_manifest_sha256=sha(O/'manifest.json'),last_result_manifest_sha256=sha(O/'review/result-inputs/result-manifest.json'),
    last_result_review_sha256=sha(O/'review/independent-result-review.json')))
foreign=dict(files={Path(name).relative_to(R).as_posix():h for name,h in json.loads((B/'review/unrelated-before-publication.json').read_bytes())['files'].items()})
for name,h in foreign['files'].items():assert sha(R/name)==h,name
save(N/'inputs/unrelated-working-tree.json',foreign)
supplements=json.loads((B/'review/independent-preparation-review.json').read_bytes())['supplement_sha256']
for name,h in supplements.items():assert sha(B/'review'/name)==h,name
save(N/'inputs/product-closeout-supplements.json',dict(root=str(B),files={str(B/'review'/name):h for name,h in supplements.items()}))
decision=json.loads((O/'inputs/direct-user-decision.json').read_bytes())
decision['plan_sha256']=sha(PLAN)
decision['scope']='Continue current goal through native-rejection diagnostic controlled-entry preparation; separate explicit one-case allocation remains required'
assert decision['actual_case_allocation']==decision['result_review_allocation']==0
save(N/'inputs/direct-user-decision.json',decision)
save(N/'inputs/scope.json',dict(source='Active goal continuation with existing explicit-case gate',
    scope='Prepare frozen d860b2a controlled entry and bindings; offline verification and necessary independent reviews',
    actual_case_allocation=0,result_review_allocation=0,model_calls=0,UI=False,audio=False,service_operations=False))
save(N/'inputs/DoR.json',dict(original_order='wo-ultimaagent-20261101-0021',stage='T2',
    objective=True,exact_write_domain=True,acceptance=True,forbidden=True,history_and_budget=True,
    independent_plan_review_required=True,actual_case_allocation=0,result_review_allocation=0,
    product_frozen=True,actual_codex_exec_workers_observed=json.loads((N/'inputs/worker-observation.json').read_text(encoding='utf-8-sig'))['count'],reasoning_effort='high'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
       R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={}
for i,p in enumerate(paths):
    before[str(p)]=sha(p);q=N/'verification/registration-plan-before'/str(i);q.parent.mkdir(parents=True,exist_ok=True)
    with q.open('xb') as f:f.write(p.read_bytes())
with (N/'inputs/previous-current-run.json').open('xb') as f:f.write(paths[0].read_bytes())
state=json.loads(paths[0].read_bytes())
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(phase='SOURCE29_E02_NATIVE_REJECTION_CONTROLLED_PLAN_REVIEW',active_evidence=str(N),active_plan=str(PLAN),
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    source29_preparation=dict(status='PLAN_REVIEW_PENDING',candidate=git('rev-parse','HEAD'),
        actual_case_allocation=0,result_review_allocation=0,plan_sha256=sha(PLAN)))
paths[0].write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note='E02候选d860b2a受控入口/完整绑定准备：精确计划独审中，产品冻结、8B/原预算保持，actual与结果复核分配0，旧实际FAIL保留。'
addition='\n\n## SOURCE29 原生拒绝诊断候选受控入口准备\n\n'+note+'\n\n计划：'+str(PLAN)+'；证据：'+str(N)+'。本登记只允许离线准备，不释放真实研究。\n'
for p in paths[1:3]:p.write_bytes(p.read_bytes()+addition.encode('utf8'))
raw=paths[3].read_bytes().decode('utf8');row=[l for l in raw.splitlines() if l.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(row)==1
paths[3].write_bytes(raw.replace(row[0],'| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |',1).encode('utf8'))
save(N/'verification/registration-plan.json',dict(before=before,after={str(p):sha(p) for p in paths},plan_sha256=sha(PLAN),actual_allocation=0))
print(json.dumps(dict(plan_sha256=sha(PLAN),registered='SOURCE29_PREPARATION_ONLY',candidate=git('rev-parse','HEAD'),actual_allocation=0)))
