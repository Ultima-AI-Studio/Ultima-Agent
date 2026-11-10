"""Bind a frozen candidate to the existing entry; never copy an actual grant."""
from pathlib import Path
import ast,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent
OLD=T/'e02-json-string-controlled-preparation-20261107-r1'
BASE=T/'e02-native-rejection-diagnostics-20261107-r1'
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
HEAD='d860b2ab4e4d9974e33c96472e4ea15abb807280'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def write(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
review=load(N/'review/independent-plan-review.json')
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PLAN_ONLY'
assert review['actual_run_authorized'] is False and review['plan_sha256']==sha(N/'plan.md')=='9c306c5db7b26d0af7d33530fcae711fa56fbfd7489aa9430c6d1e4b2445520f'
git=lambda *args:subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-native-rejection-candidate-20261107')==HEAD and not git('status','--porcelain')
groups={'harness':('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'),
    'code':('entry.py','bindings.py'),'tests':('test_bindings.py','test_entry.py','test_live_boundary.py','test_plumbing_replay.py'),
    'verification':('offline_pytest.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py',
        'prepare_review.py','read_runtime.py','verify_preservation.py','verify_preparation.py','run_preparation_checks.py','refresh_queue.py')}
copied={}
for folder,names in groups.items():
    for name in names:
        source=OLD/folder/name;target=N/folder/name;raw=source.read_bytes()
        if target.suffix=='.py':raw=raw.decode('utf8').replace('jarvis-e02-json-string-projection','jarvis-e02-native-rejection').encode('utf8')
        with target.open('xb') as f:f.write(raw)
        copied[str(source)]=sha(source)
old=load(OLD/'inputs/input-manifest.json');base=load(BASE/'inputs/current-inputs.json')
sources={str(C/Path(p).relative_to(P)):sha(C/Path(p).relative_to(P)) for p in old['source_files']}
sources.update(base['source_files']);sources.update(load(BASE/'verification/candidate-freeze.json')['source_sha256'])
assert len(sources)==75 and set(sources)==set(base['source_files'])
for p,h in sources.items():assert Path(p).is_relative_to(C) and sha(Path(p))==h==base['files'][p]
runtime=load(OLD/'inputs/candidate-runtime-manifest.json')
runtime.update(candidate=HEAD,candidate_root=str(C),branch='codex/jarvis-e02-native-rejection',source_files=sources,
    scope='Frozen bounded native-response refusal diagnosis; controlled entry preparation only',code_gate='FROZEN_N18_PASS_PREPARATION_ONLY',
    final_code_tests=909,final_code_test_scope='N18 frozen 906 product plus 3 compatibility; not rerun in N19',
    source_revision=HEAD,actual_cases=0,actual_release=False,acceptance_credit=False)
save(N/'inputs/candidate-runtime-manifest.json',runtime)
files={p:h for p,h in old['files'].items() if not Path(p).is_relative_to(P) and p!=str(OLD/'inputs/candidate-runtime-manifest.json')}
files.update(sources)
extra=[N/'inputs/candidate-runtime-manifest.json',BASE/'manifest.json',BASE/'review/independent-preparation-review.json',BASE/'verification/publication-readback.json']
extra.extend(Path(p) for p in load(N/'inputs/product-closeout-supplements.json')['files'])
extra.extend(BASE/p for p in ('review/output-normalization-receipt.json','review/registration-reconcile-receipt.json','verification/final-readback.json'))
for p in extra:files[str(p)]=sha(p)
save(N/'inputs/input-manifest.json',dict(old,candidate=HEAD,candidate_root=str(C),source_files=sources,files=files))
def constants(p,values):
    text=p.read_text('utf8');previous={}
    for key,value in values.items():
        match=re.search(r"(?m)^"+key+r"='([^']*)'",text);assert match,key;previous[key]=match[1]
        text,count=re.subn(r"(?m)^"+key+r"='[^']*'",key+'='+repr(value),text);assert count==1
    p.write_text(text,encoding='utf8',newline='\n');return previous
constants(N/'code/bindings.py',dict(CANDIDATE=HEAD,CANDIDATE_MANIFEST_SHA=sha(N/'inputs/candidate-runtime-manifest.json')))
previous=constants(N/'harness/adapter.py',dict(CANDIDATE=HEAD,MANIFEST_SHA=sha(N/'inputs/input-manifest.json'),BINDINGS_SHA=sha(N/'code/bindings.py'),PREPARATION_SHA=sha(N/'inputs/scope.json')))
constants(N/'code/entry.py',dict(CANDIDATE=HEAD,DIRECT_USER_DECISION_SHA=sha(N/'inputs/direct-user-decision.json')))
for p in (N/'harness/test_adapter.py',N/'tests/test_live_boundary.py'):
    text=p.read_text('utf8').replace(previous['CANDIDATE'],HEAD).replace(previous['MANIFEST_SHA'],sha(N/'inputs/input-manifest.json'))
    if p.name=='test_adapter.py':
        assert text.count("packet['kind']=='research_failure_diagnostic_v3'")==1
        text=text.replace("packet['kind']=='research_failure_diagnostic_v3'","packet['kind']=='research_failure_diagnostic_v4'")
    p.write_text(text,encoding='utf8',newline='\n')
(N/'harness/README.md').write_text('# Frozen native-rejection controlled-entry preparation\n\nProduct '+HEAD+'; current 8B, original corpus/budgets/cleanup unchanged.\nNo actual allocation or model call. Current v4 observer checks preserve no-delivery and committed-write distinctions.\n',encoding='utf8',newline='\n')
p=N/'verification/verify_preservation.py';s=p.read_text('utf8').replace('e02-native-pattern-json-20261107-r1',BASE.name).replace('ultimaagent-e02-json-string-candidate-20261107','ultimaagent-e02-native-rejection-candidate-20261107')
point="    spec=importlib.util.spec_from_file_location"
assert point in s
s=s.replace(point,"    for name,h in json.loads((N/'inputs/product-closeout-supplements.json').read_bytes())['files'].items():assert sha(Path(name))==h,name\n    for name,h in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():assert sha(N.parents[4]/name)==h,name\n"+point,1)
p.write_text(s,encoding='utf8',newline='\n')
p=N/'verification/verify_preparation.py';s=p.read_text('utf8').replace('e02-source-coverage-controlled-preparation-20261107-r1',OLD.name).replace('e02-native-pattern-json-20261107-r1',BASE.name).replace(previous['CANDIDATE'],HEAD)
start=s.index("    draft=load(N/'verification/first-validation-draft.json')");end=s.index('    groups={}',start)
s=s[:start]+"    # No new product behavior: prior RED/GREEN and prior failed validation remain under their old roots.\n    historical=set()\n"+s[end:]
s=s.replace('initial_validation_failed_cases=1,initial_validation_preserved=True,','initial_validation_failed_cases=0,initial_validation_preserved=True,')
s=s.replace('product_baseline_tests=781','product_baseline_tests=909')
p.write_text(s,encoding='utf8',newline='\n')
for name in ('harness/adapter.py','code/bindings.py','code/entry.py'):
    functions=lambda path:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
    assert functions(N/name)==functions(OLD/name),name
save(N/'inputs/candidate-transition.json',dict(base=old['candidate'],candidate=HEAD,old_root=str(P),new_root=str(C),current_sources=len(sources),
    protected_baseline_sha256=files[old['protected_baseline_path']],changed_existing_sources=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h],
    changed_product_sources_this_turn=[],model_or_budget_changed=False,shared_P4_P1_changed=False,old_credit_transferred=False))
save(N/'verification/source-copy.json',dict(source_files=copied,actual_artifacts_copied=False,actual_allocation=0))
write(N/'progress.md','# SDD ledger — plan: H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-native-rejection-controlled-entry-plan-20261107.md\n\n- Task 1: IN_PROGRESS; plan PASS, 75 sources rebound; core AST unchanged.\n- Task 2: PENDING; final fresh checks, preparation review, local publication.\n- Pre-flight: Task 2 consumes Task 1 final hashes; no conflicting interface.\n- Ruling: native Windows ledger and preserved evidence, no installation or worktree cleanup.\n- Ruling: frozen product has existing RED/GREEN; no fabricated product RED for entry rebinding.\n- Actual/result-review allocation 0; explicit one-case gate retained.\n')
print(json.dumps(dict(candidate=HEAD,sources=len(sources),inputs=len(files),actual_allocation=0)))
