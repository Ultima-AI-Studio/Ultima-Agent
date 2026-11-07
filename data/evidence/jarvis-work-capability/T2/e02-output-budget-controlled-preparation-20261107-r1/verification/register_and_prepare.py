"""Task2: rebind the original entry only after product review and local publication."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
B=T/'e02-writer-output-budget-20261107-r1';O=T/'e02-native-rejection-controlled-preparation-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
HEAD='0421a54cab572be013c3f7ad562e86406bfe8e52'
PLAN=R/'docs/plans/jarvis-work-e02-writer-output-budget-alignment-plan-20261107.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def write(p,s):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(s)
def copy(a,b):
    with b.open('xb') as f:f.write(a.read_bytes())
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
review=load(B/'review/independent-preparation-review.json');published=load(B/'verification/publication-readback.json')
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['actual_run_authorized'] is False
assert review['manifest_sha256']==sha(B/'manifest.json') and review['candidate']==HEAD
assert published['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and published['heads']['candidate']==HEAD
assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-output-budget-candidate-20261107')==HEAD and not git('status','--porcelain')
for name,h in load(B/'manifest.json')['files'].items():assert sha(B/name)==h,name
for name,h in load(B/'inputs/current-inputs.json')['files'].items():assert sha(Path(name))==h,name
for folder in ('inputs','code','harness','tests','offline','review','verification'):(N/folder).mkdir(exist_ok=True)
copy(PLAN,N/'plan.md')
for ext in ('json','md'):copy(B/('review/independent-plan-review.'+ext),N/('review/independent-plan-review.'+ext))
assert load(N/'review/independent-plan-review.json')['plan_sha256']==sha(N/'plan.md')
save(N/'inputs/predecessor.json',dict(root=str(B),candidate=HEAD,manifest_sha256=sha(B/'manifest.json'),review_sha256=sha(B/'review/independent-preparation-review.json'),publication_sha256=sha(B/'verification/publication-readback.json'),entry_predecessor=str(O),entry_manifest_sha256=sha(O/'manifest.json'),last_result_manifest_sha256=sha(O/'review/result-inputs/result-manifest.json'),last_result_review_sha256=sha(O/'review/independent-result-review.json')))
copy(B/'inputs/unrelated-working-tree.json',N/'inputs/unrelated-working-tree.json')
save(N/'inputs/product-closeout-supplements.json',dict(root=str(B),files={str(B/'verification/publication-readback.json'):sha(B/'verification/publication-readback.json')}))
decision=load(B/'inputs/direct-user-decision.json');decision.update(prior_plan_sha256=decision['plan_sha256'],plan_sha256=sha(PLAN),scope='Authorized offline Task2 controlled entry preparation; no actual case or result-review allocation',retry=0,UI=False,audio=False)
decision.update(decision_id='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest(),identifier_is_platform_message_id=False,decision_id_note='Content-derived identifier for the existing direct-message gate; question_id retains the actual user reply identity; allocation remains zero')
save(N/'inputs/direct-user-decision.json',decision)
save(N/'inputs/scope.json',dict(source='Explicit user call_4d19727901d9426786cc1f5fd01a3b64',scope='Prepare frozen0421a54 entry and complete bindings under approved Task2',actual_case_allocation=0,result_review_allocation=0,model_calls=0,UI=False,audio=False,service_operations=False))
worker=load(N/'inputs/worker-observation.json');assert worker['count']==0
save(N/'inputs/DoR.json',dict(original_order='wo-ultimaagent-20261101-0021',stage='T2',objective=True,exact_write_domain=True,acceptance=True,forbidden=True,history_and_budget=True,independent_plan_review_required=True,plan_sha256=sha(PLAN),plan_review_sha256=sha(N/'review/independent-plan-review.json'),actual_case_allocation=0,result_review_allocation=0,product_frozen=True,actual_codex_exec_workers_observed=worker['count'],reasoning_effort='high'))
paths=[T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={}
for i,p in enumerate(paths):
    before[str(p)]=sha(p);q=N/'verification/registration-plan-before'/str(i);q.parent.mkdir(parents=True,exist_ok=True);copy(p,q)
copy(paths[0],N/'inputs/previous-current-run.json')
s=load(paths[0]);assert s['actual_case_allocation_remaining']==s['result_review_allocation_remaining']==0
s.update(phase='SOURCE31_E02_OUTPUT_BUDGET_ENTRY_PREPARATION',active_evidence=str(N),active_plan=str(PLAN),active_review_agent=None,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),source31_preparation=dict(status='IMPLEMENTATION_AFTER_SHARED_PLAN_PASS',candidate=HEAD,actual_case_allocation=0,result_review_allocation=0,plan_sha256=sha(PLAN)))
paths[0].write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
note='E02候选0421a54受控入口准备：已授权Task2且同一精确计划PASS；产品冻结、8B/原预算保持，actual与结果复核分配0。'
addition='\n\n## SOURCE31 输出预算候选受控入口准备\n\n'+note+'\n计划：'+str(PLAN)+'；证据：'+str(N)+'。\n'
for p in paths[1:3]:p.write_bytes(p.read_bytes()+addition.encode('utf8'))
text=paths[3].read_text('utf8');rows=[l for l in text.splitlines() if l.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(rows)==1
paths[3].write_text(text.replace(rows[0],'| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+note+' |',1),encoding='utf8',newline='\n')
save(N/'verification/registration-plan.json',dict(before=before,after={str(p):sha(p) for p in paths},plan_sha256=sha(PLAN),actual_allocation=0))
groups={'harness':('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'),'code':('entry.py','bindings.py'),'tests':('test_bindings.py','test_entry.py','test_live_boundary.py','test_plumbing_replay.py'),'verification':('offline_pytest.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py','prepare_review.py','read_runtime.py','verify_preservation.py','verify_preparation.py','run_preparation_checks.py','refresh_queue.py')}
copied={}
for folder,names in groups.items():
    for name in names:
        src=O/folder/name;dst=N/folder/name;raw=src.read_bytes()
        if dst.suffix=='.py':raw=raw.decode('utf8').replace('jarvis-e02-native-rejection','jarvis-e02-output-budget').encode('utf8')
        with dst.open('xb') as f:f.write(raw)
        copied[str(src)]=sha(src)
old=load(O/'inputs/input-manifest.json');base=load(B/'inputs/current-inputs.json')
sources={str(C/Path(p).relative_to(P)):sha(C/Path(p).relative_to(P)) for p in old['source_files']}
sources.update(base['source_files']);sources.update(load(B/'verification/candidate-freeze.json')['source_sha256'])
assert len(sources)==76 and set(sources)==set(base['source_files'])
for p,h in sources.items():assert Path(p).is_relative_to(C) and sha(Path(p))==h==base['files'][p]
runtime=load(O/'inputs/candidate-runtime-manifest.json');runtime.update(candidate=HEAD,candidate_root=str(C),branch='codex/jarvis-e02-output-budget',source_files=sources,scope='Frozen actual output budget guidance; controlled entry preparation only',code_gate='FROZEN_N20_PASS_PREPARATION_ONLY',final_code_tests=927,final_code_test_scope='N20 frozen924 product plus3 compatibility; not rerun inN21',source_revision=HEAD,actual_cases=0,actual_release=False,acceptance_credit=False)
save(N/'inputs/candidate-runtime-manifest.json',runtime)
files={p:h for p,h in old['files'].items() if not Path(p).is_relative_to(P) and p!=str(O/'inputs/candidate-runtime-manifest.json')};files.update(sources)
for p in (N/'inputs/candidate-runtime-manifest.json',B/'manifest.json',B/'review/independent-preparation-review.json',B/'verification/publication-readback.json'):files[str(p)]=sha(p)
save(N/'inputs/input-manifest.json',dict(old,candidate=HEAD,candidate_root=str(C),source_files=sources,files=files))
def constants(p,values):
    text=p.read_text('utf8');previous={}
    for key,value in values.items():
        m=re.search(r'(?m)^'+key+r"='([^']*)'",text);assert m,key;previous[key]=m[1]
        text,count=re.subn(r'(?m)^'+key+r"='[^']*'",key+'='+repr(value),text);assert count==1
    p.write_text(text,encoding='utf8',newline='\n');return previous
constants(N/'code/bindings.py',dict(CANDIDATE=HEAD,CANDIDATE_MANIFEST_SHA=sha(N/'inputs/candidate-runtime-manifest.json')))
previous=constants(N/'harness/adapter.py',dict(CANDIDATE=HEAD,MANIFEST_SHA=sha(N/'inputs/input-manifest.json'),BINDINGS_SHA=sha(N/'code/bindings.py'),PREPARATION_SHA=sha(N/'inputs/scope.json')))
constants(N/'code/entry.py',dict(CANDIDATE=HEAD,DIRECT_USER_DECISION_SHA=sha(N/'inputs/direct-user-decision.json')))
for p in (N/'harness/test_adapter.py',N/'tests/test_live_boundary.py'):
    p.write_text(p.read_text('utf8').replace(previous['CANDIDATE'],HEAD).replace(previous['MANIFEST_SHA'],sha(N/'inputs/input-manifest.json')),encoding='utf8',newline='\n')
(N/'harness/README.md').write_text('# Frozen output-budget controlled-entry preparation\n\nProduct '+HEAD+'; current8B, original corpus/budgets/cleanup unchanged. Actual/model0. Existing v4 observer checks unchanged.\n',encoding='utf8',newline='\n')
for name in ('verify_preservation.py','verify_preparation.py'):
    p=N/'verification'/name;text=p.read_text('utf8').replace('e02-native-rejection-diagnostics-20261107-r1',B.name).replace('e02-json-string-controlled-preparation-20261107-r1',O.name).replace('ultimaagent-e02-native-rejection-candidate-20261107','ultimaagent-e02-output-budget-candidate-20261107').replace('d860b2ab4e4d9974e33c96472e4ea15abb807280',HEAD).replace('product_baseline_tests=909','product_baseline_tests=927')
    p.write_text(text,encoding='utf8',newline='\n')
for name in ('harness/adapter.py','code/bindings.py','code/entry.py'):
    functions=lambda p:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_bytes()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    assert functions(N/name)==functions(O/name),name
hm=load(N/'harness/manifest.json');hm.update(candidate=HEAD,candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'),files={name:sha(N/'harness'/name) for name in hm['files']})
(N/'harness/manifest.json').write_text(json.dumps(hm,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
save(N/'inputs/candidate-transition.json',dict(base=old['candidate'],candidate=HEAD,old_root=str(P),new_root=str(C),current_sources=len(sources),protected_baseline_sha256=files[old['protected_baseline_path']],changed_existing_sources=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h],changed_product_sources_this_turn=[],model_or_budget_changed=False,shared_P4_P1_changed=False,old_credit_transferred=False))
save(N/'verification/source-copy.json',dict(source_files=copied,actual_artifacts_copied=False,actual_allocation=0))
write(N/'progress.md','# SDD ledger — Task2 of '+str(PLAN)+'\n\n- Task 1: COMPLETE; N20 product927, frozen0421a54, independent product PASS.\n- Task 2: IN_PROGRESS; shared exact plan PASS, complete76 sources rebound, core AST unchanged.\n- Actual/result-review/model allocation0; no grant or actual root copied.\n')
print(json.dumps(dict(candidate=HEAD,sources=len(sources),inputs=len(files),actual_allocation=0)))
