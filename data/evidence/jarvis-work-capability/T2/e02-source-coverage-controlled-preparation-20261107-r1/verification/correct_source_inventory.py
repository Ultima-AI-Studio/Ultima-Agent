"""Restore full inherited inventory plus current frozen source additions before final tests."""
from pathlib import Path
import hashlib,json,re
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-native-http-controlled-preparation-20261107-r1';B=N.parent/'e02-source-coverage-budget-20261107-r1'
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
paths=['inputs/input-manifest.json','inputs/candidate-runtime-manifest.json','inputs/candidate-transition.json','code/bindings.py','harness/adapter.py','harness/test_adapter.py','harness/manifest.json','tests/test_live_boundary.py','verification/prepare_sources.py']
snap=N/'verification/rebinding-attempt1';snap.mkdir(exist_ok=False)
before={name:sha(N/name) for name in paths}
for name in paths:
    dst=snap/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes((N/name).read_bytes())
old=load(O/'inputs/input-manifest.json');current=load(N/'inputs/input-manifest.json')
sources={str(C/Path(path).relative_to(P)):sha(C/Path(path).relative_to(P)) for path in old['source_files']}
sources.update(load(B/'verification/candidate-freeze.json')['source_sha256'])
frozen=load(B/'inputs/current-inputs.json')['files']
assert all(frozen.get(path)==digest==sha(Path(path)) for path,digest in sources.items())
assert {str(C/Path(path).relative_to(P)) for path in old['source_files']}<=sources.keys()
runtime=load(N/'inputs/candidate-runtime-manifest.json');runtime['source_files']=sources
write(N/'inputs/candidate-runtime-manifest.json',runtime)
files={path:digest for path,digest in old['files'].items() if not Path(path).is_relative_to(P) and path!=str(O/'inputs/candidate-runtime-manifest.json')}
files.update(sources)
for p in [N/'inputs/candidate-runtime-manifest.json',B/'manifest.json',B/'review/independent-preparation-review.json',B/'verification/publication-readback.json']:files[str(p)]=sha(p)
current.update(source_files=sources,files=files);old_input_hash=sha(N/'inputs/input-manifest.json')
write(N/'inputs/input-manifest.json',current)
def constant(path,key,value):
    s=path.read_text('utf8');s,count=re.subn(r"(?m)^"+key+r"='[^']*'",key+'='+repr(value),s);assert count==1
    path.write_text(s,encoding='utf8',newline='\n')
constant(N/'code/bindings.py','CANDIDATE_MANIFEST_SHA',sha(N/'inputs/candidate-runtime-manifest.json'))
constant(N/'harness/adapter.py','MANIFEST_SHA',sha(N/'inputs/input-manifest.json'))
constant(N/'harness/adapter.py','BINDINGS_SHA',sha(N/'code/bindings.py'))
for p in [N/'harness/test_adapter.py',N/'tests/test_live_boundary.py']:
    p.write_text(p.read_text('utf8').replace(old_input_hash,sha(N/'inputs/input-manifest.json')),encoding='utf8',newline='\n')
transition=load(N/'inputs/candidate-transition.json');transition['current_sources']=len(sources)
transition['changed_existing_sources']=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h]
write(N/'inputs/candidate-transition.json',transition)
p=N/'verification/prepare_sources.py';s=p.read_text('utf8')
s=s.replace("sources=load(BASE/'verification/candidate-freeze.json')['source_sha256']", "sources={str(C/Path(path).relative_to(P)):sha(C/Path(path).relative_to(P)) for path in old['source_files']}\nsources.update(load(BASE/'verification/candidate-freeze.json')['source_sha256'])")
p.write_text(s,encoding='utf8',newline='\n')
hm=load(N/'harness/manifest.json');hm.update(candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'),files={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file() and p.name!='manifest.json'})
write(N/'harness/manifest.json',hm)
write(N/'verification/inventory-correction.json',dict(reason='Top-level frozen source snapshot alone omits inherited nested modules/contracts; use union required by plan',before=before,after={name:sha(N/name) for name in paths},old_inventory=len(old['source_files']),complete_current_inventory=len(sources),current_inputs=len(files),all_current_sources_pinned_by_frozen_product=True,product_changes=0,actual_cases=0,model_calls=0))
print(json.dumps(dict(sources=len(sources),inputs=len(files),prior_inventory_fully_preserved=True,actual_cases=0)))
