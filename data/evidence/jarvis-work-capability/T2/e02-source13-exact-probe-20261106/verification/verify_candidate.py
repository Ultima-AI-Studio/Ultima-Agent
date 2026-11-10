from pathlib import Path
import hashlib,json,sys
Q=Path(__file__).resolve().parents[1];R=Q.parents[4];T=Q.parent;D=T/'e02-source13-closeout-handoff-20261106';S=T/'e02-source13-audit-closeout-20261106';B=T/'e02-source13-cold-import-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
mode=sys.argv[1]
pins=load(Q/'profile-preparation/manifest.json')
for name,h in pins['members'].items():assert sha(Q/'profile-preparation'/name)==h,name
for name,h in pins['files'].items():assert sha(Path(name))==h,name
snapshot=load(D/'snapshot-manifest.json')
assert len(snapshot['files'])==71 and all(sha(Path(r['source']))==r['sha256']==sha(D/r['snapshot']) for r in snapshot['files'])
for name,h in load(D/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
assert not (Q/'release').exists() and not (Q/'runs').exists()
if mode=='inputs':
    print(json.dumps(dict(verdict='PASS_ISOLATED_INPUTS',profile_dependencies=len(pins['files']),external_snapshot_unchanged=71,unrelated_dirty_paths=9,actual_profile_runs=0)));raise SystemExit(0)
red=load(Q/'offline/exact-red-native/receipt.json');green=load(Q/'offline/exact-final-green/receipt.json')
assert red['counts']==dict(tests=18,failures=16,errors=0,skipped=0) and red['sources_unchanged']
assert green['counts']==dict(tests=18,failures=0,errors=0,skipped=0) and green['sources_unchanged']
fulls=list((Q/'code').glob('profile-preparation-contracts-*/receipt.json'));assert len(fulls)==1
full=load(fulls[0]);assert full['exit_code']==0 and full['actual_count']==584 and full['allowlist_exact'] and full['package_unchanged'] and full['dependencies_unchanged']
assert set(load(S/'profile-preparation/manifest.json')['test_ids']).issubset(full['actual_test_ids'])
assert len(set(full['actual_test_ids']))==584
native=list((fulls[0].parent/'temp').rglob('probe.json'));assert len(native)==1
n=load(native[0]);assert n['outcome']=='PASS' and n['closed_at_return']==[True] and n['unclean_before_close']==[True]
if mode=='probe':
    print(json.dumps(dict(verdict='PASS_EXACT_PROBE_REGRESSIONS',red_failures=16,green_tests=18,full_profile_tests=584,original_ids_retained=566,real_local_probe='PASS',actual_profile_runs=0)));raise SystemExit(0)
assert mode=='full'
root=Q/'offline/exact-root89';r=load(root/'receipt.json');assert r['counts']==dict(tests=89,failures=0,errors=0,skipped=0) and r['exit_code']==0 and r['package_unchanged'] and r['sources_unchanged'] and not r['denied_python_io']
assert load(root/'inventory.json')==load(B/'offline/cold-binding-final89/inventory.json')
assert {p.name:sha(p) for p in (Q/'code').glob('*.py')}==r['package_after']
entry=load(Q/'entry-manifest.json')
for p,h in entry['files'].items():assert sha(Path(p))==h,p
for p in (Q/'code').glob('*.py'):
    original=(B/'code'/p.name).read_text('utf-8')
    if p.name in ('entry.py','controls.py'):original=original.replace(str(B),str(Q))
    if p.name=='controls.py':original=original.replace(sha(B/'profile-preparation/profile.py'),sha(Q/'profile-preparation/profile.py'))
    assert original==p.read_text('utf-8'),p.name
value=dict(verdict='PASS_OFFLINE_PREPARATION_ONLY',profile_tests=584,original_profile_ids=566,root_tests=89,
    profile_receipt=str(fulls[0]),root_receipt=str(root/'receipt.json'),entry_manifest_sha256=sha(Q/'entry-manifest.json'),
    profile_manifest_sha256=sha(Q/'profile-preparation/manifest.json'),dependencies=len(pins['files']),
    external_snapshot_unchanged=71,unrelated_dirty_paths=9,actual_profile_runs=0,model_calls=0,runtime_authority=False)
with (Q/'verification/offline-readback.json').open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(value))
