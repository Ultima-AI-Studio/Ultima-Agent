"""Bind only the new candidate; keep all predecessor and protected records."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-source13-native-metadata-20261107-r1';Q=T/'e02-source13-exact-probe-20261106'
OLD=T/'e02-source13-child-admission-20261107-r1'
BASE='269aca511d88412dbb9c15d23911138469a37aa2'
OC=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-metadata/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()
assert candidate!=BASE and subprocess.check_output(['git','rev-parse','HEAD^'],cwd=C,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
assert not (N/'inputs/candidate-runtime-manifest.json').exists()
manifest=load(Q/'inputs/candidate-runtime-manifest.json')
manifest.update(candidate=candidate,candidate_root=str(C),branch='codex/jarvis-e02-native-metadata',scope='New candidate: strict optional capabilities compatibility; pinned dependencies copied verbatim from 269aca5 runtime')
manifest['source_files']={str(C/Path(p).relative_to(OC)):sha(C/Path(p).relative_to(OC)) for p in manifest['source_files']}
for rel in ('src/brain/tests/test_native_metadata_compat.py','src/brain/tests/fixtures/native_metadata_0_32_15.json'):
    manifest['source_files'][str(C/rel)]=sha(C/rel)
save(N/'inputs/candidate-runtime-manifest.json',manifest)
inputs=load(N/'inputs/input-manifest.json');inputs.update(candidate=candidate,candidate_root=str(C),source_files=manifest['source_files'])
files={}
for p,digest in inputs['files'].items():
    path=Path(p)
    if path.is_relative_to(OC):path=C/path.relative_to(OC);digest=sha(path)
    files[str(path)]=digest
files.update(manifest['source_files']);files[str(N/'inputs/candidate-runtime-manifest.json')]=sha(N/'inputs/candidate-runtime-manifest.json')
inputs['files']=files;save(N/'inputs/input-manifest.json',inputs)
for rel in ('code/bindings.py','code/entry.py','harness/adapter.py','tests/test_live_boundary.py'):
    p=N/rel;text=p.read_text('utf8').replace(BASE,candidate).replace('jarvis-e03-source13','jarvis-e02-native-metadata')
    if rel=='code/bindings.py':
        text=text.replace("CANDIDATE_MANIFEST=Q/'inputs/candidate-runtime-manifest.json'","CANDIDATE_MANIFEST=N/'inputs/candidate-runtime-manifest.json'")
        text=text.replace('957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3',sha(N/'inputs/candidate-runtime-manifest.json'))
    if rel=='harness/adapter.py':text=text.replace('5badf78414d3cb6a13145b98dbc1e3fa0ce08e4e5f79fc2948244e2118f16121',sha(N/'inputs/input-manifest.json'))
    p.write_text(text,encoding='utf8')
p=N/'harness/adapter.py';p.write_text(p.read_text('utf8').replace('831c1b303c55e77fcfcd9e9742e1e4bd9995b553df36848e067fc3da84526c45',sha(N/'code/bindings.py')),encoding='utf8')
hm=load(N/'harness/manifest.json');hm.update(candidate=candidate,candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'))
hm['files']={name:sha(N/'harness'/name) for name in hm['files']};save(N/'harness/manifest.json',hm)
before=load(Q/'inputs/candidate-runtime-manifest.json')['source_files']
changed=[str(Path(p).relative_to(OC)) for p,d in before.items() if manifest['source_files'][str(C/Path(p).relative_to(OC))]!=d]
assert changed==['src\\brain\\work_research.py'],changed
save(N/'inputs/candidate-transition.json',dict(base=BASE,candidate=candidate,old_root=str(OC),new_root=str(C),previous_runtime_sources=len(before),current_sources=len(manifest['source_files']),
    changed_existing_sources=changed,added_tests=['src/brain/tests/test_native_metadata_compat.py','src/brain/tests/fixtures/native_metadata_0_32_15.json'],
    dependency_copy_record_sha256=sha(N/'inputs/copied-frozen-dependencies.json'),input_manifest_sha256=sha(N/'inputs/input-manifest.json'),
    prior_E01_E03_credit='old candidate only; new candidate actual E01/E03 not run',shared_P4_P1_changed=False,model_or_budget_changed=False))
s=load(T/'current-run.json');s.update(active_candidate=candidate,active_candidate_root=str(C));save(T/'current-run.json',s)
print(json.dumps(dict(candidate=candidate,sources=len(manifest['source_files']),inputs=len(files),changed=changed)))
