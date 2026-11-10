"""Final readonly publication verification, not another product or test invocation."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-code-claim-schema-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])
cp=load(N/'verification/result-checkpoint.json')
for root,key in ((R,'main'),(M,'mirror')):
    item=cp[key];assert git(root,'rev-parse','HEAD').decode().strip()==item['commit']
    assert git(root,'rev-parse','refs/tags/'+item['tag']+'^{commit}').decode().strip()==item['commit']
    for name in item['files']:assert git(root,'show',item['commit']+':'+name)==(root/name).read_bytes(),name
for row in load(N/'verification/result-mirror-readback.json')['mirrors']:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
for manifest in (N/'manifest.json',N/'review/result-inputs/result-manifest.json'):
    for name,digest in load(manifest)['files'].items():assert sha(N/name)==digest,name
inputs=load(N/'inputs/input-manifest.json')
for name,digest in inputs['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
C=Path(inputs['candidate_root']);assert git(C,'rev-parse','HEAD').decode().strip()==inputs['candidate'] and not git(C,'status','--porcelain')
old=Path(load(N/'inputs/predecessor.json')['root'])
for manifest in (old/'manifest.json',old/'review/result-inputs/result-manifest.json'):
    for name,digest in load(manifest)['files'].items():assert sha(old/name)==digest,name
registration=load(N/'review/result-registration.json');review=load(N/'review/independent-result-review.json')
assert review['verdict']==registration['independent_review']
assert review['verdict'] in ('PASS_CONTROLLED_CASE','FAIL_CONFIRMED')
accepted=review['verdict']=='PASS_CONTROLLED_CASE'
assert registration['actual_case_allocation_remaining']==registration['result_review_allocation_remaining']==0
assert registration['retry']==0 and registration['current_controlled_passed']==int(accepted) and registration['acceptance_credit'] is accepted
assert sha(N/'review/independent-result-review.json')==cp['review_sha256']==registration['review_sha256']
assert sha(N/'review/result-inputs/result-manifest.json')==cp['result_manifest_sha256']==registration['result_manifest_sha256']
value=dict(verdict='PASS_REVIEWED_SINGLE_CASE_PUBLICATION_ONLY',run_id=registration['run_id'],candidate=inputs['candidate'],main=cp['main']['commit'],mirror=cp['mirror']['commit'],tag=cp['tag'],
    independent_result=review['verdict'],actual_case_invocations=1,actual_remaining=0,result_review_remaining=0,research_credit=int(accepted),new_runtime_calls=0,new_tests=0,remote_synced=False,E02='NOT_PASSED',T2='NOT_PASSED')
with (N/'verification/final-result-readback.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
