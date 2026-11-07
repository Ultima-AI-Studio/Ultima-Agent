"""Copy source only and bind the frozen HTTP diagnostic candidate; never release."""
from pathlib import Path
import hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-unique-sections-20261107-r1'
BASE=N.parent/'e02-native-http-diagnostics-20261107-r1'
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-unique-sections/UltimaAgent')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent')
HEAD='ee1bef61f04169c64978538dbc4ba799ef7be6c0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert load(N/'review/independent-plan-review.json')['verdict']=='PASS_PLAN_ONLY'
assert load(N/'review/independent-plan-review.json')['plan_sha256']==sha(N/'plan.md')
assert subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip()==HEAD
assert not subprocess.check_output(['git','-C',str(C),'status','--porcelain'],text=True).strip()
groups={'harness':('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'),
        'code':('entry.py','bindings.py'),
        'tests':('test_bindings.py','test_entry.py','test_live_boundary.py','test_plumbing_replay.py'),
        'verification':('offline_pytest.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py','prepare_review.py')}
copied={}
for folder,names in groups.items():
    for name in names:
        source=OLD/folder/name;target=N/folder/name
        assert not target.exists()
        data=source.read_bytes()
        if target.suffix=='.py':
            data=data.decode('utf8').replace('jarvis-e02-unique-sections','jarvis-e02-http-diagnostics').encode('utf8')
        target.write_bytes(data);copied[str(source)]=sha(source)
old=load(OLD/'inputs/input-manifest.json')
sources={str(C/Path(p).relative_to(P)):sha(C/Path(p).relative_to(P)) for p in old['source_files']}
sources[str(C/'src/brain/tests/test_work_http_failure_diagnostics.py')]=sha(C/'src/brain/tests/test_work_http_failure_diagnostics.py')
runtime=load(OLD/'inputs/candidate-runtime-manifest.json')
runtime.update(candidate=HEAD,candidate_root=str(C),branch='codex/jarvis-e02-http-diagnostics',source_files=sources,
    scope='Frozen product HTTP diagnostics; current entry preparation only',code_gate='FROZEN_N12_PASS_PREPARATION_ONLY',
    final_code_tests=706,final_code_test_scope='N12 frozen prior product700 plus export6; not rerun in N13',
    source_revision=HEAD,actual_cases=0,actual_release=False,acceptance_credit=False)
save(N/'inputs/candidate-runtime-manifest.json',runtime)
files={p:h for p,h in old['files'].items() if not Path(p).is_relative_to(P) and p!=str(OLD/'inputs/candidate-runtime-manifest.json')}
files.update(sources)
for p in [N/'inputs/candidate-runtime-manifest.json',BASE/'manifest.json',BASE/'review/independent-preparation-review.json',BASE/'verification/publication-readback.json']:
    files[str(p)]=sha(p)
save(N/'inputs/input-manifest.json',dict(old,candidate=HEAD,candidate_root=str(C),source_files=sources,files=files))
def constants(path,values):
    text=path.read_text('utf8');previous={}
    for key,value in values.items():
        match=re.search(r"(?m)^"+key+r"='([^']*)'",text);assert match,key
        previous[key]=match[1]
        text,count=re.subn(r"(?m)^"+key+r"='[^']*'",key+'='+repr(value),text);assert count==1
    path.write_text(text,encoding='utf8');return previous
constants(N/'code/bindings.py',dict(CANDIDATE=HEAD,CANDIDATE_MANIFEST_SHA=sha(N/'inputs/candidate-runtime-manifest.json')))
previous=constants(N/'harness/adapter.py',dict(CANDIDATE=HEAD,MANIFEST_SHA=sha(N/'inputs/input-manifest.json'),BINDINGS_SHA=sha(N/'code/bindings.py'),PREPARATION_SHA=sha(N/'inputs/scope.json')))
constants(N/'code/entry.py',dict(CANDIDATE=HEAD,DIRECT_USER_DECISION_SHA=sha(N/'inputs/direct-user-decision.json')))
for p in [N/'harness/test_adapter.py',N/'tests/test_live_boundary.py']:
    p.write_text(p.read_text('utf8').replace(previous['CANDIDATE'],HEAD).replace(previous['MANIFEST_SHA'],sha(N/'inputs/input-manifest.json')),encoding='utf8')
(N/'harness/README.md').write_text('# Frozen C12 controlled-entry preparation\n\nProduct '+HEAD+'; current 8B and original budgets/corpus/cleanup unchanged.\nNo actual grant, model call or acceptance credit is allocated by this package.\nOnly the adapter path/candidate/input digest constants are rebound from N11.\nHTTP diagnostic export is verified with the current SDK MockTransport.\n',encoding='utf8')
hm=load(N/'harness/manifest.json');hm.update(candidate=HEAD,candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'),files={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file() and p.name!='manifest.json'})
(N/'harness/manifest.json').write_text(json.dumps(hm,indent=2),encoding='utf8')
save(N/'inputs/candidate-transition.json',dict(base=old['candidate'],candidate=HEAD,old_root=str(P),new_root=str(C),current_sources=len(sources),
    protected_baseline_sha256=files[old['protected_baseline_path']],
    changed_existing_sources=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h],
    changed_product_sources_this_turn=[],model_or_budget_changed=False,shared_P4_P1_changed=False,old_credit_transferred=False))
save(N/'verification/source-copy.json',dict(source_files=copied,actual_artifacts_copied=False,actual_allocation=0))
p=N/'verification/prepare_review.py';text=p.read_text('utf8').replace("('independent-plan-review.json','independent-clock-plan-review.json')","('independent-plan-review.json','independent-plan-review.md')").replace("('plan.md','diagnostic-clock-amendment.md','execution-proposal.md','preparation-report.md')","('plan.md','execution-proposal.md','preparation-report.md')")
p.write_text(text,encoding='utf8')
print(json.dumps(dict(candidate=HEAD,sources=len(sources),inputs=len(files),actual_allocation=0)))
