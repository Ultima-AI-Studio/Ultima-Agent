"""Seal the offline-only candidate; this creates no actual-run authority."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent')
HEAD=None
BASE='ee1bef61f04169c64978538dbc4ba799ef7be6c0'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW)
HEAD=git('rev-parse','HEAD').decode().strip()
assert HEAD!=BASE and git('rev-parse','HEAD').decode().strip()==HEAD and git('rev-parse','HEAD^').decode().strip()==BASE
assert not git('status','--porcelain').strip()
assert git('rev-parse','ultimaagent-e02-source-coverage-candidate-20261107').decode().strip()==HEAD
spec=importlib.util.spec_from_file_location('verify_current_offline',N/'verification/verify_offline.py')
verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
checked=verify.verify();assert checked['candidate_head']==HEAD
save(N/'verification/offline-post-commit-readback.json',checked)
for name in checked['changed_files']:assert git('show',HEAD+':'+name)==(C/name).read_bytes(),name
sources={str(p):sha(p) for p in [*C.glob('src/brain/*.py'),*C.glob('src/brain/tests/test_work*.py'),C/'src/brain/tests/test_native_metadata_compat.py',C/'src/brain/tests/fixtures/native_metadata_0_32_15.json']}
save(N/'verification/candidate-freeze.json',dict(candidate=HEAD,parent=BASE,tag='ultimaagent-e02-source-coverage-candidate-20261107',working_tree_clean=True,changed_files=checked['changed_files'],source_sha256=sources,exact_committed_changed_bytes=True))
oldpins=json.loads((N/'inputs/accepted-dependency-pins.json').read_bytes())
files={}
for name,digest in oldpins['files'].items():
    p=Path(name);current=C/p.relative_to(OLD) if p.is_relative_to(OLD) else p
    if current==p:assert sha(p)==digest,name
    files[str(current)]=sha(current)
files.update(sources)
save(N/'inputs/current-inputs.json',dict(kind='OFFLINE_COVERAGE_CANDIDATE_BINDINGS',candidate=HEAD,root=str(C),actual_authority=False,files=files))
members=set()
for folder in ('inputs','code','verification'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file())
for run in (N/'offline').iterdir():
    if not run.is_dir():continue
    members.update(p for p in run.iterdir() if p.is_file())
    members.update(p for p in (run/'snapshot').rglob('*') if p.is_file())
members.update([N/'plan.md',N/'preparation-report.md',N/'review/independent-plan-review.json',N/'review/independent-plan-review.md'])
assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
value=dict(kind='OFFLINE_SOURCE_COVERAGE_PREPARATION',candidate=HEAD,parent=BASE,model='qwen3-8b-uncensored',model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',tests=checked['tests'],product_tests=checked['product_tests'],export_interface_tests=checked['export_interface_tests'],actual_authority=False,actual_cases=0,model_calls=0,acceptance_credit=0,created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)})
save(N/'manifest.json',value)
print(json.dumps(dict(candidate=HEAD,manifest_sha256=sha(N/'manifest.json'),members=len(members),current_input_files=len(files),tests=checked['tests'],actual_cases=0)))
