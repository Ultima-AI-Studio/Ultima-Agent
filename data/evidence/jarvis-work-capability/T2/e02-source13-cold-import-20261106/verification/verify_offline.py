"""Read back exact test identities, current bindings and preserved history."""
from pathlib import Path
import ast,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
B=T/'e02-source13-profile-binding-20261106';E=T/'e02-source13-root-entry-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
profile=N/'profile-preparation/manifest.json';pins=load(profile)
for name,digest in pins['files'].items():assert sha(Path(name))==digest,name
for name,digest in pins['members'].items():assert sha(profile.parent/name)==digest,name
entry=load(N/'entry-manifest.json')
assert entry['base_profile_manifest_sha256']==sha(profile)
for name,digest in entry['files'].items():assert sha(Path(name))==digest,name
baseline=load(N/'inputs/preserved-before.json')['files']
for name,digest in baseline.items():assert sha(Path(name))==digest,name
receipts=[]
for path in (N/'code').glob('profile-preparation-contracts-*/receipt.json'):
    d=load(path)
    if d.get('package_unchanged') and load(path.parent/'package-after.json')[str(profile)]==sha(profile):receipts.append((path,d))
assert len(receipts)==1,'Exactly one current-manifest full profile suite'
path,full=receipts[0]
assert full['exit_code']==0 and full['actual_count']==561 and full['allowlist_exact'] and full['dependencies_unchanged']
old_ids=load(B/'profile-preparation/manifest.json')['test_ids']
assert len(old_ids)==557 and set(old_ids).issubset(full['actual_test_ids'])
assert set(full['actual_test_ids'])==set(pins['test_ids'])
root=N/'offline/cold-binding-final89';r=load(root/'receipt.json')
assert r['exit_code']==0 and r['counts']==dict(tests=89,failures=0,errors=0,skipped=0)
assert r['sources_unchanged'] and r['package_unchanged'] and r['denied_python_io']==[]
assert load(root/'inventory.json')==load(E/'offline/handoff-full-green/inventory.json')
assert {p.name:sha(p) for p in (N/'code').glob('*.py')}==r['package_after']
for stage,expected in [('red-2',2),('green-2',0)]:
    v=load(N/'cold-evidence'/stage/'receipt.json');assert v['counts']==dict(tests=4,failures=expected,errors=0,skipped=0) and v['sources_unchanged']
    assert len(v['probe_results'])==2
    for row in v['probe_results']:
        probe=row['result'];assert probe['audit_events']==['socket.gethostname'] and probe['refused_io']==[]
        assert probe['outcome']==('FAIL' if expected else 'PASS')
        if not expected:
            assert probe['profile_manifest_sha256']==sha(profile) and probe['eager_audit']['eager']['clean']
            assert probe['real_sdk_not_preloaded'] and probe['platform_cache_cold'] and probe['boundary_stopped']
assert not (N/'release').exists() and not (N/'runs').exists()
old=(B/'profile-preparation/profile.py').read_text('utf-8');new=(N/'profile-preparation/profile.py').read_text('utf-8')
change="        # platform.machine() reads local Windows metadata during cold SDK import.\n        if event=='socket.gethostname':\n            return\n"
assert new.replace(change,'',1)==old and new.count(change)==1
for p in (N/'code').glob('*.py'):
    value=(E/'code'/p.name).read_text('utf-8')
    if p.name=='controls.py':value=value.replace(str(B/'profile-preparation/manifest.json'),str(profile)).replace(sha(B/'profile-preparation/profile.py'),sha(N/'profile-preparation/profile.py'))
    elif p.name=='entry.py':value=value.replace(str(E),str(N))
    assert value==p.read_text('utf-8'),p.name+' unauthorized semantic change'
for p in (N/'verification').glob('*.py'):ast.parse(p.read_bytes(),filename=str(p))
receipt=dict(verdict='PASS_OFFLINE_PREPARATION_ONLY',profile_test_count=561,original_profile_test_ids_retained=557,
    new_tests=4,root_test_count=89,original_root_test_ids_exact=True,profile_receipt=str(path),root_receipt=str(root/'receipt.json'),
    entry_manifest_sha256=sha(N/'entry-manifest.json'),profile_manifest_sha256=sha(profile),preserved_old_bindings=540,
    actual_profile_invocations=0,model_calls=0,runtime_authority=False)
out=N/'verification/offline-readback.json'
with out.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(receipt))
