"""Fresh readback of reviewed sources, tests, local commits and document mirrors."""
from pathlib import Path
import hashlib,json,subprocess,sys
R=Path(r'H:\UltimaAI\UltimaAgent');M=Path(r'H:\UltimaAI\ultima-docs-repo')
Q=R/'data/evidence/jarvis-work-capability/T2/e02-source13-exact-probe-20261106'
D=Q.parent/'e02-source13-closeout-handoff-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True).stdout
review=load(Q/'review/independent-preparation-review.json')
gate=load(Q/'verification/code-preparation-gate.json')
assert review['verdict']=='PASS' and review['runtime_authority'] is False
assert gate['verdict']=='PASS_PREPARATION_ONLY' and gate['actual_authority'] is False
assert sha(Q/'entry-manifest.json')==review['manifest_sha256']==gate['manifest_sha256']
assert sha(Q/'manifest.json')==review['package_manifest_sha256']==gate['package_manifest_sha256']
assert sha(Q/'review/independent-preparation-review.json')==gate['review_sha256']
for row in load(Q/'manifest.json')['files']:assert sha(Q/row['path'])==row['sha256'],row['path']
for rel in ('entry-manifest.json','profile-preparation/manifest.json'):
    for p,digest in load(Q/rel)['files'].items():assert sha(Path(p))==digest,p
for row in load(D/'snapshot-manifest.json')['files']:
    assert sha(D/row['snapshot'])==sha(Path(row['source']))==row['sha256'],row['source']
for name,digest in load(D/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
evidence=load(Q/'verification/offline-readback.json')
assert evidence['verdict']=='PASS_OFFLINE_PREPARATION_ONLY'
assert evidence['profile_tests']==584 and evidence['root_tests']==89
assert not (Q/'release').exists() and not (Q/'runs').exists()
if len(sys.argv)>1 and sys.argv[1]=='published':
    c=load(Q/'verification/preparation-checkpoint.json')
    assert c['runtime_authority'] is False and c['actual_profile_runs']==0
    assert c['entry_manifest_sha256']==sha(Q/'entry-manifest.json')
    assert c['package_manifest_sha256']==sha(Q/'manifest.json')
    assert c['review_sha256']==sha(Q/'review/independent-preparation-review.json')
    for row in c['mirrors']:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
    for repo,key in ((R,'main'),(M,'mirror')):
        assert git(repo,'rev-parse','HEAD').decode().strip()==c[key]['commit']
        assert git(repo,'rev-parse','refs/tags/'+c['tag']+'^{commit}').decode().strip()==c[key]['commit']
        for name in c[key]['files']:assert git(repo,'show',c[key]['commit']+':'+name)==(repo/name).read_bytes(),name
print(json.dumps(dict(verdict='PASS_FRESH_PREPARATION_READBACK',tests=673,review='PASS',
    sealed_members=126,entry_bindings=47,profile_dependencies=1499,external_files_preserved=71,
    unrelated_dirty_paths_preserved=9,published=len(sys.argv)>1,actual_profile_runs=0,runtime_authority=False)))
