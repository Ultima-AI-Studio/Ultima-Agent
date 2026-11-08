"""Rebind frozen entry only; no actual release or product changes."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
B=T/'e02-source-grounding-coverage-20261108-r2'
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
HEAD='43da3f014a763b8ea3963872a8f1ce8ebea77531'
PLAN=R/'docs/plans/jarvis-work-e02-source-grounding-controlled-entry-plan-20261108.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def copy(a,b):
    with b.open('xb') as f:f.write(a.read_bytes())
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
pr=load(N/'review/independent-plan-review.json')
assert pr['reviewer']=='root-independent' and pr['verdict']=='PASS_PLAN_ONLY' and pr['plan_sha256']==sha(PLAN)==sha(N/'plan.md')
review=load(B/'review/independent-preparation-review.json');published=load(B/'verification/publication-readback.json')
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['actual_run_authorized'] is False
assert review['manifest_sha256']==sha(B/'manifest.json') and review['candidate']==HEAD
assert published['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and published['heads']['candidate']==HEAD
assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-source-grounding-candidate-20261108-r1')==HEAD and not git('status','--porcelain')
for name,h in load(B/'manifest.json')['files'].items():assert sha(B/name)==h,name
for name,h in load(B/'inputs/current-inputs.json')['files'].items():assert sha(Path(name))==h,name
for folder in ('code','harness','tests','offline'):(N/folder).mkdir(exist_ok=False)
save(N/'inputs/predecessor.json',dict(root=str(B),candidate=HEAD,manifest_sha256=sha(B/'manifest.json'),review_sha256=sha(B/'review/independent-preparation-review.json'),publication_sha256=sha(B/'verification/publication-readback.json'),entry_predecessor=str(O),entry_manifest_sha256=sha(O/'manifest.json'),last_result_manifest_sha256=sha(O/'review/result-inputs/result-manifest.json'),last_result_review_sha256=sha(O/'review/independent-result-review.json')))
foreign=load(B/'inputs/unrelated-working-tree.json');observed=load(B/'inputs/unrelated-change-observation.json')
for name,data in observed['observed_changes'].items():
    foreign['files'][name]=data['observed_sha256']
save(N/'inputs/unrelated-working-tree.json',foreign)
save(N/'inputs/unrelated-baseline-provenance.json',dict(original=str(B/'inputs/unrelated-working-tree.json'),original_sha256=sha(B/'inputs/unrelated-working-tree.json'),observation=str(B/'inputs/unrelated-change-observation.json'),observation_sha256=sha(B/'inputs/unrelated-change-observation.json'),original_unchanged=14,out_of_scope_observed=1,files_written_by_task=0))
save(N/'inputs/product-closeout-supplements.json',dict(root=str(B),files={str(B/'verification'/name):sha(B/'verification'/name) for name in ('publication-readback.json','final-readback.json')}))
answer='授权离线审查、最小补修、必要独审与入口准备（推荐）'
decision_id='user-message:sha256:'+hashlib.sha256(answer.encode('utf8')).hexdigest()
save(N/'inputs/direct-user-decision.json',dict(source='user_question_reply',source_question_id='call_3d33440cc40c401ea7a2cf11c8bc2bcf',question_id=decision_id,decision_id=decision_id,identifier_is_platform_message_id=False,decision_id_note='Content-derived preparation binding, not a platform id; source_question_id preserves the actual offline answer; allocations remain zero',answer=answer,plan_sha256=sha(PLAN),scope='Already authorized Task3 offline controlled entry preparation only; explicit new actual allocation still required',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,service_operations=0,retry=0,UI=False,audio=False))
save(N/'inputs/scope.json',dict(source='call_3d33440cc40c401ea7a2cf11c8bc2bcf',scope='Frozen evidence-first and source-reserve candidate controlled entry preparation, offline only',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,UI=False,audio=False,service_operations=False))
worker=load(N/'inputs/worker-observation.json');assert worker['this_order_worker_count']==0 and worker['count']==worker['foreign_worker_count']==1
save(N/'inputs/implementation-admission.json',dict(plan_sha256=sha(PLAN),plan_review_sha256=sha(N/'review/independent-plan-review.json'),DoR_sha256=sha(N/'inputs/DoR.json'),worker_observation_sha256=sha(N/'inputs/worker-observation.json'),product_frozen=True,actual_case_allocation=0,result_review_allocation=0,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
groups={'harness':('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'),'code':('entry.py','bindings.py'),'tests':('test_bindings.py','test_entry.py','test_live_boundary.py','test_plumbing_replay.py'),'verification':('offline_pytest.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py','prepare_review.py','run_preparation_checks.py','refresh_queue.py')}
copied={}
for folder,names in groups.items():
    for name in names:
        src=O/folder/name;dst=N/folder/name;raw=src.read_bytes()
        if dst.suffix=='.py':raw=raw.decode('utf8').replace('jarvis-e02-claim-generation-r1','jarvis-e02-source-grounding-r1').encode('utf8')
        with dst.open('xb') as f:f.write(raw)
        copied[str(src)]=sha(src)
old=load(O/'inputs/input-manifest.json');base=load(B/'inputs/current-inputs.json');sources=base['source_files']
assert len(sources)==79
for p,h in sources.items():assert Path(p).is_relative_to(C) and sha(Path(p))==h==base['files'][p]
runtime=load(O/'inputs/candidate-runtime-manifest.json');runtime.update(candidate=HEAD,candidate_root=str(C),branch='codex/jarvis-e02-source-grounding-r1',source_files=sources,scope='Frozen evidence-first and source-reserve candidate; offline controlled entry preparation',code_gate='FROZEN_N36_PASS_PREPARATION_ONLY',final_code_tests=1022,final_code_test_scope='N36 frozen1008 product plus4 compatibility plus10 official reference; not rerun in entry preparation',source_revision=HEAD,actual_cases=0,actual_release=False,acceptance_credit=False)
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
(N/'harness/README.md').write_text('# Frozen claim-generation entry\n\nProduct '+HEAD+'; current8B, original corpus/budgets/cleanup unchanged. Actual/model/network requests0. Existing v5 export unchanged. Live runtime freshness pending original actual preflight.\n',encoding='utf8',newline='\n')
functions=lambda p:{x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_bytes()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
for name in ('harness/adapter.py','code/bindings.py','code/entry.py'):assert functions(N/name)==functions(O/name),name
# Same negative export purpose; reserve now rejects third repeated read.
test=N/'harness/test_adapter.py';text=test.read_text('utf8')
assert text.count('reads,posts,validated=4,5,False')==1
assert text.count("len(packet['pages'])==4")==1
text=text.replace('reads,posts,validated=4,5,False','reads,posts,validated=2,3,False').replace("len(packet['pages'])==4","len(packet['pages'])==2")
test.write_text(text,encoding='utf8',newline='\n')
hm=load(N/'harness/manifest.json');hm.update(candidate=HEAD,candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'),files={name:sha(N/'harness'/name) for name in hm['files']})
(N/'harness/manifest.json').write_text(json.dumps(hm,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
save(N/'inputs/candidate-transition.json',dict(base=old['candidate'],candidate=HEAD,old_root=str(P),new_root=str(C),current_sources=len(sources),protected_baseline_sha256=files[old['protected_baseline_path']],changed_existing_sources=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h],changed_product_sources_this_turn=[],model_or_budget_changed=False,shared_P4_P1_changed=False,old_credit_transferred=False))
save(N/'verification/source-copy.json',dict(source_files=copied,actual_artifacts_copied=False,actual_allocation=0,core_function_class_AST_unchanged=True))
with (N/'progress.md').open('x',encoding='utf8',newline='\n') as f:f.write('# Controlled entry progress — '+str(PLAN)+'\n\n- Task 1: IN_PROGRESS; independent plan PASS, frozen 43da3f0, 79 sources bound, original core AST unchanged.\n- Task 2: PENDING; actual/model/result-review allocation0.\n')
print(json.dumps(dict(candidate=HEAD,sources=len(sources),inputs=len(files),actual_allocation=0)))

state=load(T/'current-run.json');assert state['last_actual_result']==load(N/'inputs/previous-current-run.json')['last_actual_result']
state.update(active_review_agent=None,phase='SOURCE37_E02_SOURCE_GROUNDING_ENTRY_OFFLINE_CHECKS')
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
