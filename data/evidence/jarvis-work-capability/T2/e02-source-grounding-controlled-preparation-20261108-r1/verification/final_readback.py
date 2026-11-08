"""Exact local readback; no tests, product import, actual case or inference."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)

def git_bytes(root,head,paths):
    paths=sorted(paths)
    queries=[(head+':'+p.relative_to(root).as_posix()).encode('utf8') for p in paths]
    result=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=b'\n'.join(queries)+b'\n',capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    offset=0
    for p in paths:
        end=result.stdout.index(b'\n',offset);header=result.stdout[offset:end].split()
        assert len(header)==3 and header[1]==b'blob',p
        size=int(header[2]);start=end+1;raw=result.stdout[start:start+size]
        assert result.stdout[start+size:start+size+1]==b'\n' and raw==p.read_bytes(),str(p)
        offset=start+size+1
    assert offset==len(result.stdout)
publication=load(N/'verification/publication-readback.json');manifest=load(N/'manifest.json');review=load(N/'review/independent-preparation-review.json');inputs=load(N/'inputs/input-manifest.json')
assert publication['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==inputs['candidate']==manifest['candidate']==publication['heads']['candidate']
assert review['manifest_sha256']==sha(N/'manifest.json')==publication['manifest_sha256']
assert sha(N/'review/independent-preparation-review.json')==publication['review_sha256']
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in inputs['files'].items():assert sha(Path(name))==h,name
groups={R:set(),M:set()}
for name,h in publication['file_sha256'].items():
    p=Path(name);root=R if p.is_relative_to(R) else M
    assert sha(p)==h,name
    groups[root].add(p)
current_heads={}
for root,key in ((R,'project'),(M,'mirror')):
    head=publication['heads'][key];assert git(root,'rev-parse',publication['tag']).decode().strip()==head
    current_heads[key]=git(root,'rev-parse','HEAD').decode().strip()
    git(root,'merge-base','--is-ancestor',head,current_heads[key])
    changed={p.decode('utf8') for p in git(root,'diff','--name-only','-z',head,current_heads[key]).split(b'\0') if p}
    assert not changed & {p.relative_to(root).as_posix() for p in groups[root]},key
    git_bytes(root,head,groups[root])
C=Path(inputs['candidate_root']);assert not git(C,'status','--porcelain').strip()
assert git(C,'rev-parse','HEAD').decode().strip()==git(C,'rev-parse','ultimaagent-e02-source-grounding-candidate-20261108-r1').decode().strip()==inputs['candidate']
state=load(N.parent/'current-run.json');ready=load(N/'verification/ready-readback.json')
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['preparation_test_count']==state['preparation_tests_passed']==manifest['test_count']==ready['verification']['tests']
for key in ('active_evidence','active_preparation_root'):assert Path(state[key])==N,key
for key in ('preparation_review_path','preparation_review_receipt'):assert Path(state[key])==N/'review/independent-preparation-review.json',key
assert state['preparation_review_sha256']==sha(N/'review/independent-preparation-review.json') and state['preparation_manifest_sha256']==sha(N/'manifest.json')
assert state['active_candidate']==state['active_product_candidate']==inputs['candidate']
assert state['local_checkpoint_tag']==state['preparation_sync']['local_tag']==publication['tag']
assert state['source_candidate_tag']=='ultimaagent-e02-source-grounding-candidate-20261108-r1'
assert state['goal_status']=='none' and state['goal_registry_status']=='cleared_by_user'
assert Path(state['next_proposal']['path'])==N/'execution-proposal.md'
assert ready['missing_grant_rejected'] and not ready['run_once_called']
assert ready['live_runtime_readiness']==state['live_runtime_readiness']=='PENDING_FRESH_ACTUAL_PREFLIGHT' and ready['current_runtime_verified'] is False
assert '- Task 2: PREPARATION_REVIEW_COMPLETE;' in (N/'progress.md').read_text('utf8')
before=load(N/'inputs/previous-current-run.json');assert state['last_actual_result']==before['last_actual_result']
for name in ('actual','release','controller-authority','native-preflight','controller-ledger.json'):assert not (N/name).exists(),name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():
    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==h,name
value=dict(verdict='PASS_FINAL_LOCAL_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=inputs['candidate'],heads=publication['heads'],observed_heads=current_heads,tag=publication['tag'],manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),publication_sha256=sha(N/'verification/publication-readback.json'),members=len(manifest['files']),input_pins=len(inputs['files']),source_pins=len(inputs['source_files']),entry_checks=manifest['test_count'],product_checks=1022,product_checks_rerun=False,current_aliases_match=True,live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',current_runtime_verified=False,last_actual_preserved=True,foreign_preserved=14,unowned_dynamic_file_not_written=True,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',Owner='NOT_PASSED',remote_synced=False)
with (N/'verification/final-readback.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
