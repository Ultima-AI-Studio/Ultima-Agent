"""Offline fixed-path rebinding only. Do not run after preparation sealing."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
B=T/'e02-source13-profile-binding-20261106';E=T/'e02-source13-root-entry-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def write(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf-8')
assert not (N/'review/independent-preparation-review.json').exists(),'Sealed candidate cannot be rebound'
manifest=N/'profile-preparation/manifest.json';m=load(manifest)
m['import_path'][0]=load(B/'profile-preparation/manifest.json')['import_path'][0]
m['members']={name:sha(manifest.parent/name) for name in m['members']}
m['files'][str(N/'cold/cold_import_probe.py')]=sha(N/'cold/cold_import_probe.py')
write(manifest,m)
root=load(E/'entry-manifest.json');mapped={}
for key,value in root['files'].items():
    p=Path(key)
    if p.is_relative_to(E):q=N/p.relative_to(E)
    elif p.is_relative_to(B/'profile-preparation'):q=N/'profile-preparation'/p.relative_to(B/'profile-preparation')
    elif p.is_relative_to(B/'inputs'):q=N/'inputs'/p.relative_to(B/'inputs')
    else:q=p
    assert q.is_file(),str(q)
    mapped[str(q)]=sha(q)
for p in [N/'profile-preparation/test_profile.py',N/'profile-preparation/README.md',N/'cold/cold_import_probe.py',N/'profile-adapter.py',N/'inputs/authorization.json',N.parents[4]/'docs/plans/jarvis-work-e02-source13-sdk-cold-import-fix-plan-20261106.md']:
    mapped[str(p)]=sha(p)
root.update(base_profile_manifest_path=str(manifest),base_profile_manifest_sha256=sha(manifest),import_path=[str(manifest.parent),*m['import_path'][1:]],protected_baseline_path=str(N/'inputs/protected-baseline.json'),files=mapped)
write(N/'entry-manifest.json',root)
bindings=load(E/'inputs/source-bindings.json');bindings['scope']='HISTORICAL_INPUTS_AND_NEW_COLD_IMPORT_BINDINGS'
for p in [manifest,N/'profile-preparation/profile.py',N/'profile-preparation/test_profile.py',N/'profile-preparation/run_checks.py',N/'profile-preparation/README.md',N/'cold/cold_import_probe.py',N/'entry-manifest.json']:
    bindings['files'].append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
write(N/'inputs/source-bindings.json',bindings)
print(json.dumps(dict(entry_manifest_sha256=sha(N/'entry-manifest.json'),profile_manifest_sha256=sha(manifest),root_bindings=len(mapped),profile_test_count=len(m['test_ids']))))
