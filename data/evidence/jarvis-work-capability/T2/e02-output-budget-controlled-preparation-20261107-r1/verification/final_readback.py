"""Final exact local readback; no tests, model calls or actual entry invocation."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
publication=load(N/'verification/publication-readback.json');manifest=load(N/'manifest.json');review=load(N/'review/independent-preparation-review.json');inputs=load(N/'inputs/input-manifest.json')
assert publication['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==inputs['candidate']==manifest['candidate']==publication['heads']['candidate']
assert review['manifest_sha256']==sha(N/'manifest.json')==publication['manifest_sha256']
assert sha(N/'review/independent-preparation-review.json')==publication['review_sha256']
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in inputs['files'].items():assert sha(Path(name))==h,name
for name,h in publication['file_sha256'].items():
    p=Path(name);root=R if p.is_relative_to(R) else M;head=publication['heads']['project' if root==R else 'mirror']
    assert sha(p)==h and git(root,'show',head+':'+p.relative_to(root).as_posix())==p.read_bytes(),name
for root,key in ((R,'project'),(M,'mirror')):assert git(root,'rev-parse',publication['tag']).decode().strip()==git(root,'rev-parse','HEAD').decode().strip()==publication['heads'][key]
C=Path(inputs['candidate_root']);assert not git(C,'status','--porcelain').strip()
assert git(C,'rev-parse','HEAD').decode().strip()==git(C,'rev-parse','ultimaagent-e02-output-budget-candidate-20261107').decode().strip()==inputs['candidate']
state=load(N.parent/'current-run.json');ready=load(N/'verification/ready-readback.json')
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['preparation_test_count']==state['preparation_tests_passed']==manifest['test_count']==346
for key in ('active_evidence','active_preparation_root'):assert Path(state[key])==N,key
for key in ('preparation_review_path','preparation_review_receipt'):assert Path(state[key])==N/'review/independent-preparation-review.json',key
assert state['preparation_review_sha256']==sha(N/'review/independent-preparation-review.json') and state['preparation_manifest_sha256']==sha(N/'manifest.json')
assert state['active_candidate']==state['active_product_candidate']==inputs['candidate']
assert state['local_checkpoint_tag']==state['preparation_sync']['local_tag']==publication['tag']
assert state['source_candidate_tag']=='ultimaagent-e02-output-budget-candidate-20261107'
assert Path(state['next_proposal']['path'])==N/'execution-proposal.md'
assert ready['missing_grant_rejected'] and not ready['run_once_called']
assert '- Task 2: COMPLETE;' in (N/'progress.md').read_text('utf8') and '- Task 2: IN_PROGRESS;' not in (N/'progress.md').read_text('utf8')
before=load(N/'inputs/previous-current-run.json');assert state['last_actual_result']==before['last_actual_result']
for name in ('actual','release','controller-authority','native-preflight','controller-ledger.json'):assert not (N/name).exists(),name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
value=dict(verdict='PASS_FINAL_LOCAL_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=inputs['candidate'],heads=publication['heads'],tag=publication['tag'],manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),publication_sha256=sha(N/'verification/publication-readback.json'),members=len(manifest['files']),input_pins=len(inputs['files']),source_pins=len(inputs['source_files']),entry_checks=346,product_checks=927,current_aliases_match=True,last_actual_preserved=True,foreign_preserved=15,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,remote_synced=False)
with (N/'verification/final-readback.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
