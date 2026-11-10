"""Freeze the offline compatibility candidate without creating run authority."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
P=N.parent/'e02-json-string-controlled-preparation-20261107-r1'
BASE='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
TAG='ultimaagent-e02-native-rejection-candidate-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
head=git('rev-parse','HEAD').decode().strip()
assert head!=BASE and git('rev-parse','HEAD^').decode().strip()==BASE
assert not git('status','--porcelain').strip()
assert git('rev-parse',TAG).decode().strip()==head
checked=module('verify_json_compat_offline',N/'verification/verify_offline.py').verify()
assert checked['candidate_head']==head
save(N/'verification/offline-post-commit-readback.json',checked)
preserved=module('verify_json_compat_preservation',N/'verification/verify_preservation.py').verify()
save(N/'verification/preservation-post-commit.json',preserved)
for name in checked['changed_files']:assert git('show',head+':'+name)==(C/name).read_bytes()
sources={str(p):sha(p) for p in [*C.glob('src/brain/*.py'),*C.glob('src/brain/tests/test_work*.py'),
    C/'src/brain/tests/test_native_metadata_compat.py',C/'src/brain/tests/fixtures/native_metadata_0_32_15.json']}
save(N/'verification/candidate-freeze.json',dict(candidate=head,parent=BASE,tag=TAG,root=str(C),working_tree_clean=True,
    changed_files=checked['changed_files'],source_sha256=sources,exact_committed_changed_bytes=True))
oldinputs=json.loads((P/'inputs/input-manifest.json').read_bytes())
files={}
for name,h in oldinputs['files'].items():
    p=Path(name);assert sha(p)==h,name
    target=C/p.relative_to(OLD) if p.is_relative_to(OLD) else p
    files[str(target)]=sha(target)
files.update(sources)
complete_sources={name:h for name,h in files.items() if Path(name).is_relative_to(C)}
save(N/'inputs/current-inputs.json',dict(kind='OFFLINE_NATIVE_REJECTION_DIAGNOSTICS_CANDIDATE',candidate=head,root=str(C),
    actual_authority=False,source_files=complete_sources,model=oldinputs['model'],model_digest=oldinputs['model_digest'],
    protected_baseline_path=oldinputs['protected_baseline_path'],corpus_path=oldinputs['corpus_path'],budgets=oldinputs['budgets'],files=files))
runtime=json.loads((N/'verification/runtime-after.json').read_bytes())
assert runtime['verdict']=='PASS_READONLY_RUNTIME_IDENTITY' and runtime['version']=={'version':'0.32.15'}
assert len(runtime['protected'])==7
save(N/'verification/runtime-readback.json',dict(kind='READBACK_OF_READONLY_OBSERVATION',observation_sha256=sha(N/'verification/runtime-after.json'),
    observer_candidate=runtime['frozen_checker_candidate'],observation_field_note='Inherited current_candidate_base names the frozen observer, not the new product.',
    product_candidate=head,product_parent=BASE,protected_count=7,continuous_liveness_measured=False,model_calls=0,service_operations=0))
members=set()
for folder in ('inputs','verification','diagnosis'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file())
for run in (N/'offline').iterdir():
    if not run.is_dir():continue
    members.update(p for p in run.iterdir() if p.is_file())
    members.update(p for p in (run/'snapshot').rglob('*') if p.is_file())
members.update([N/'plan.md',N/'preparation-report.md',N/'review/independent-plan-review.json',N/'review/independent-plan-review.md'])
for name in ('actual','release','controller-authority'):assert not (N/name).exists()
save(N/'manifest.json',dict(kind='OFFLINE_NATIVE_REJECTION_DIAGNOSTICS_PREPARATION',candidate=head,parent=BASE,
    tests=checked['tests'],product_tests=checked['product_tests'],reference_converter_tests=checked['reference_converter_tests'],compatibility_tests=checked['compatibility_tests'],
    actual_cases=0,model_calls=0,acceptance_credit=0,actual_authority=False,
    created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)}))
print(json.dumps(dict(candidate=head,manifest_sha256=sha(N/'manifest.json'),members=len(members),current_input_files=len(files),tests=checked['tests'],actual_cases=0)))
