"""Read-only final delivery checks; no test rerun or runtime release."""
from pathlib import Path
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1];repo=E.parents[4]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True).stdout
receipt=load(E/'verification/handoff-pass-checkpoint.json')
manifest=load(E/'manifest.json');entry=load(E/'entry-manifest.json')
review=load(E/'review/independent-handoff-source-review.json');gate=load(E/'verification/code-preparation-gate.json')
assert sha(E/'manifest.json')==receipt['published_manifest_sha256']
assert sha(E/'entry-manifest.json')==receipt['entry_manifest_sha256']==review['manifest_sha256']
for row in manifest['files']:assert sha(E/row['path'])==row['sha256'],row['path']
for path,digest in entry['files'].items():assert sha(Path(path))==digest,path
archive=Path(manifest['reviewed_prepublication_archive'])
assert sha(archive/'manifest.json')==review['package_manifest_sha256']==manifest['reviewed_prepublication_manifest_sha256']
for row in load(archive/'manifest.json')['files']:assert sha(archive/row['path'])==row['sha256'],row['path']
canonical=E/'review/independent-preparation-review.json'
assert canonical.read_bytes()==(E/'review/independent-handoff-source-review.json').read_bytes()
assert sha(canonical)==receipt['review_sha256']==gate['review_sha256']
assert gate['verdict']=='PASS_PREPARATION_ONLY' and gate['actual_authority'] is False
assert gate['manifest_sha256']==review['manifest_sha256']
assert not (E/'release').exists() and not (E/'runs').exists()
final=load(E/'offline/handoff-full-green/receipt.json')
assert final['counts']==dict(tests=89,failures=0,errors=0,skipped=0)
assert {p.name:sha(p) for p in (E/'code').glob('*.py')}==final['package_after']
assert set(load(E/'offline/review-r1-full-green/inventory.json')).issubset(load(E/'offline/handoff-full-green/inventory.json'))
for item in receipt['mirrors']:assert sha(Path(item['source']))==sha(Path(item['mirror']))==item['sha256']
for root,key in ((repo,'main'),(Path(r'H:\UltimaAI\ultima-docs-repo'),'mirror')):
    assert git(root,'rev-parse','HEAD').decode().strip()==receipt[key]['commit']
    assert git(root,'rev-parse','refs/tags/'+receipt['tag']+'^{commit}').decode().strip()==receipt[key]['commit']
for name,digest in receipt['unrelated_files_preserved'].items():assert sha(repo/name)==digest
state=load(E.parent/'current-run.json')
assert state['preparation_status']=='PASS_PREPARATION_ONLY' and state['e02_execution_released'] is False
assert state['e02_root_entry_current_source_review']=='PASS' and state['active_review_agent'] is None
assert state['next_action_scope']['actual_case_allocation']==state['next_action_scope']['actual_result_review_allocation']==0
print(json.dumps(dict(verdict='PASS_FINAL_PREPARATION_READBACK',tests=89,review='PASS',runtime_bindings=len(entry['files']),
    reviewed_members=len(load(archive/'manifest.json')['files']),published_members=len(manifest['files']),
    mirrors_exact=True,commits_tags_exact=True,runtime_authority=False,E02='NOT_PASSED',T2='NOT_PASSED')))
