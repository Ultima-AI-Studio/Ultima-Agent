from pathlib import Path
import hashlib,json
Q=Path(__file__).resolve().parents[1];T=Q.parent;B=T/'e02-source13-cold-import-20261106';R=Q.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert not (Q/'entry-manifest.json').exists() and not (Q/'review/independent-preparation-review.json').exists()
profile=Q/'profile-preparation/manifest.json';m=load(profile)
assert sha(profile.parent/'profile.py') in (Q/'code/controls.py').read_text('utf-8')
for name,h in m['members'].items():assert sha(profile.parent/name)==h,name
root=load(B/'entry-manifest.json');files={}
for name in root['files']:
    source=Path(name);target=Q/source.relative_to(B) if source.is_relative_to(B) else source
    if not target.is_file():target=source  # historical evidence remains historical
    files[str(target)]=sha(target)
for p in (Q/'profile-preparation').iterdir():
    if p.is_file():files[str(p)]=sha(p)
for p in [Q/'inputs/scope.json',Q/'cold/cold_import_probe.py',Q/'cold/urllib3_probe.py',R/'docs/plans/jarvis-work-e02-source13-exact-probe-repair-plan-20261106.md']:
    files[str(p)]=sha(p)
root.update(base_profile_manifest_path=str(profile),base_profile_manifest_sha256=sha(profile),import_path=[str(profile.parent),*m['import_path'][1:]],protected_baseline_path=str(Q/'inputs/protected-baseline.json'),files=files)
save(Q/'entry-manifest.json',root)
bindings=load(B/'inputs/source-bindings.json');bindings['scope']='EXACT_PROBE_AND_UNCHANGED_ROOT_INPUTS'
for p in [profile,profile.parent/'profile.py',profile.parent/'test_profile.py',Q/'cold/urllib3_probe.py',Q/'entry-manifest.json']:
    bindings['files'].append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
(Q/'inputs/source-bindings.json').write_text(json.dumps(bindings,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(dict(entry_manifest_sha256=sha(Q/'entry-manifest.json'),entry_bindings=len(files),profile_manifest_sha256=sha(profile))))
