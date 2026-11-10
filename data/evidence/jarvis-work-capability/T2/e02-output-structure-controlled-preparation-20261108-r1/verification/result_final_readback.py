"""Post-commit result readback, preserving every consumed-case boundary."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo');A=N/'actual/E02-controlled-1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
publication=load(N/'verification/result-publication-readback.json');review=load(N/'review/independent-result-review.json');manifest=load(N/'review/result-inputs/result-manifest.json');state=load(N.parent/'current-run.json')
assert publication['verdict']=='PASS_LOCAL_RESULT_PUBLICATION_READBACK' and review['verdict']=='FAIL_CONFIRMED'
assert publication['result_manifest_sha256']==review['result_manifest_sha256']==sha(N/'review/result-inputs/result-manifest.json')
assert publication['review_sha256']==sha(N/'review/independent-result-review.json')
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in load(A/'seal-index.json')['files'].items():assert sha(A/name)==h,name
for name,h in load(N/'manifest.json')['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
for name,h in publication['file_sha256'].items():
    p=Path(name);root=R if p.is_relative_to(R) else M;head=publication['heads']['project' if root==R else 'mirror']
    assert sha(p)==h and git(root,'show',head+':'+p.relative_to(root).as_posix())==p.read_bytes(),name
for root,key in ((R,'project'),(M,'mirror')):assert git(root,'rev-parse','HEAD').decode().strip()==git(root,'rev-parse',publication['tag']).decode().strip()==publication['heads'][key]
C=Path(load(N/'inputs/input-manifest.json')['candidate_root']);assert not git(C,'status','--porcelain').strip()
assert git(C,'rev-parse','HEAD').decode().strip()==publication['heads']['candidate']==review['candidate']
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
actual=state['last_actual_result'];previous=load(N/'verification/result-closeout-before/0-current-run.json')['last_actual_result']
assert state['previous_actual_result']==previous and previous['run_id']=='9dbe192a-3bc1-4a4d-a218-581846d5f654'
assert actual['run_id']==review['run_id']==manifest['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'
assert actual['question_id']==manifest['user_question_id']=='call_5c06d21b59b8475b873814f857990cc3'
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==actual['acceptance_credit']==0
assert actual['research_artifacts']==actual['successful_write_count']==0 and not actual['write_confirmed'] and not actual['ack_confirmed']
assert state['active_preparation']['status']=='COMPLETED_ACTUAL_CONSUMED' and not state['live_gate_released'] and not state['next_stage_released']
assert actual['native_response']['done_reason']=='length' and actual['native_response']['eval_count']==actual['native_response']['max_tokens']==2048
assert actual['timing_eligibility']=='UNOBSERVED_NEVER_TIMED_PASS' and actual['root_witness_eligible'] is False
assert actual['output_structure']==review['output_structure']
assert actual['output_structure']['mode']=='FULL' and actual['output_structure']['omitted_chars']==0
assert sorted(actual['output_structure']['literal_repeat_counts'].values())==[49,50]
assert state['next_proposal']['status']=='PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED'
value=dict(verdict='PASS_POST_COMMIT_RESULT_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=publication['heads'],tag=publication['tag'],result='FAIL_CONFIRMED',run_id=actual['run_id'],question_id=actual['question_id'],result_manifest_sha256=sha(N/'review/result-inputs/result-manifest.json'),review_sha256=sha(N/'review/independent-result-review.json'),publication_receipt_sha256=sha(N/'verification/result-publication-readback.json'),result_members=len(manifest['files']),actual_seal_members=len(load(A/'seal-index.json')['files']),project_members=publication['project_members'],mirror_members=publication['mirror_members'],preparation_preserved=True,old_failure_preserved=True,candidate_clean=True,foreign_files_unchanged=15,entry_invocations=1,retry=0,application_native_POST_attempts=7,completed_native_posts=7,server_native_start_count=None,outer_elapsed_seconds=actual['outer_elapsed_seconds'],native_response=actual['native_response'],research_files=0,write_confirmed=False,ack_confirmed=False,cleanup='PASS_AT_RECORDED_OBSERVATIONS',protected='SEVEN_IDENTITIES_MATCH_AT_RECORDED_POINTS',continuous_liveness_measured=False,timing_eligibility=actual['timing_eligibility'],root_witness_observation_error=actual['root_witness_observation_error'],actual_remaining=0,result_review_remaining=0,acceptance_credit=0,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',Owner='NOT_PASSED',new_case_authorized=False,model_or_runtime_calls_by_readback=0,remote_synced=False,remote_reason='Existing automatic push approval block; no retry')
value['output_structure']=actual['output_structure']
value['next_proposal']=state['next_proposal']
with (N/'verification/result-final-readback.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(value))
