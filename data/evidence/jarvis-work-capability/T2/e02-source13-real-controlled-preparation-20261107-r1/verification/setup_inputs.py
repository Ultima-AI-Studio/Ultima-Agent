"""Snapshot current read-only inputs for a future real8B case; grants nothing."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
Q=T/'e02-source13-exact-probe-20261106';OLD=T/'navigation-source10-validation-20261103-inert2'
E01=T/'e01-source13-round3-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert not (N/'inputs').exists() and not (N/'actual').exists() and not (N/'release').exists()
pins=load(Q/'profile-preparation/manifest.json');candidate=load(Q/'inputs/candidate-runtime-manifest.json')
assert candidate['candidate']=='269aca511d88412dbb9c15d23911138469a37aa2'
assert load(Q/'execution/final-readback.json')['verdict']=='PASS_ZERO_INFERENCE_RESULT_FINAL_READBACK'
reg=Q/'execution/result-registration.json';review=Q/'review/independent-exact-probe-result-review.json'
assert load(reg)['execution']==load(review)['verdict']=='PASS_ZERO_INFERENCE_PLUMBING_ONLY'
assert load(reg)['actual_research_credit']==0
files={}
def add(path,digest=None):
    path=Path(path);actual=sha(path)
    assert digest is None or digest==actual,str(path)
    assert str(path) not in files or files[str(path)]==actual,str(path)
    files[str(path)]=actual
for p,digest in pins['files'].items():add(p,digest)
for p,digest in load(Q/'entry-manifest.json')['files'].items():add(p,digest)
for p,digest in candidate['source_files'].items():add(p,digest)
for p in (reg,review,Q/'execution/final-readback.json',Q/'inputs/e01-registration.json',Q/'inputs/e03-registration.json',
          Q/'inputs/candidate-runtime-manifest.json',Q/'profile-preparation/manifest.json',Q/'entry-manifest.json',
          OLD/'harness/manifest.json',OLD/'harness-approval.json',OLD/'harness-deadline-design/root-decision.json',
          OLD/'source10-candidate-manifest.json',OLD/'harness-preparation-authority.json'):
    add(p)
for p in (OLD/'harness').iterdir():
    if p.is_file():add(p)
source_before=load(OLD/'source10-candidate-manifest.json')
differences=[];oldroot=Path(source_before['candidate_root']);newroot=Path(candidate['candidate_root'])
for p,digest in source_before['source_files'].items():
    old=Path(p);new=newroot/old.relative_to(oldroot)
    assert new.exists(),str(new)
    differences.append(dict(old_path=str(old),old_expected=digest,current_path=str(new),current_sha256=sha(new),changed=sha(new)!=digest))
functions=[n.name for n in ast.parse((OLD/'harness/test_adapter.py').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')]
assert len(functions)==len(set(functions))
manifest=dict(schema=1,kind='SOURCE13_CURRENT8B_REAL_CONTROLLED_PREPARATION',candidate=candidate['candidate'],
    candidate_root=str(newroot),model='qwen3-8b-uncensored',model_digest=pins['model_digest'],model_manifest_path=pins['model_manifest_path'],
    corpus_path=pins['corpus_path'],corpus_sha256=pins['corpus_sha256'],protected_baseline_path=str(Q/'inputs/protected-baseline.json'),protected_count=7,
    budgets=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,
        work_seconds=275,cleanup_seconds=310,outer_seconds=315,retry=0),actual_released=False,
    source_files=dict(candidate['source_files']),previous_plumbing=dict(registration_path=str(reg),registration_sha256=sha(reg),
        review_path=str(review),review_sha256=sha(review),run_id=load(reg)['run_id'],real_research_credit=0),files=dict(sorted(files.items())))
save(N/'inputs/input-manifest.json',manifest)
save(N/'inputs/reuse-audit.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),previous_goal_turn='PROGRESS: independently verified zero-inference plumbing pass',
    candidate=candidate['candidate'],old_candidate=source_before['candidate'],source_comparisons=differences,
    old_harness_test_function_ids=functions,old_test_function_count=len(functions),
    live_harness= dict(path=str(OLD/'harness/adapter.py'),sha256=sha(OLD/'harness/adapter.py')),
    current_helper=dict(controller=str(E01/'code/controller.py'),controller_sha256=sha(E01/'code/controller.py'),
        adapter=str(E01/'preparation-support/acceptance_adapter.py'),adapter_sha256=sha(E01/'preparation-support/acceptance_adapter.py')),
    adaptation_required=['Current source13 input pins and paths','Current seven protected identities including parent and command hash',
        'Fresh one-shot actual root allocation under existing RootInvocation','Current SDK byte-compatible export replay'],
    native_model_transport='Keep actual product/SDK transport; only original browser search/GET fixture is injected',
    actual_model_calls=0,actual_product_runs=0,runtime_authority=False))
save(N/'inputs/scope.json',dict(source='User resumed persistent original delivery goal',
    scope='Original reentry plan step5: inline offline preparation of current8B real controlled first case',
    actual_case_allocation=0,result_review_allocation=0,model_calls=0,UI=False,audio=False,service_operations=False))
save(N/'inputs/state-before.json',load(T/'current-run.json'))
git=subprocess.run(['git','-C',str(R),'-c','core.quotepath=false','diff','--name-only'],capture_output=True,check=True).stdout.decode('utf-8').splitlines()
save(N/'inputs/unrelated-working-tree.json',dict(files={p:sha(R/p) for p in git if p!='data/evidence/jarvis-work-capability/T2/current-run.json'}))
state=load(T/'current-run.json');state.update(phase='SOURCE13_E02_REAL_CONTROLLED_OFFLINE_PREPARATION',
    active_preparation_root=str(N),active_report=str(R/'docs/plans/jarvis-work-e02-source13-real-controlled-preparation-plan-20261106.md'),
    preparation_status='IN_PROGRESS',preparation_review='PENDING',e02_execution_released=False,live_gate_released=False,
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),next_work='Bind current inputs and adapt existing real research harness; no live allocation')
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(dict(input_bindings=len(files),current_source_files=len(candidate['source_files']),old_source_comparisons=len(differences),
    source_differences=sum(x['changed'] for x in differences),old_test_functions=len(functions),actual_model_calls=0,runtime_authority=False)))
