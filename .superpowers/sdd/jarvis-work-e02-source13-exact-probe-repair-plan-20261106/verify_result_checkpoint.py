from pathlib import Path
import datetime as dt,hashlib,json,subprocess
R=Path(r'H:\UltimaAI\UltimaAgent');M=Path(r'H:\UltimaAI\ultima-docs-repo')
Q=R/'data/evidence/jarvis-work-capability/T2/e02-source13-exact-probe-20261106'
D=Q.parent/'e02-source13-closeout-handoff-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.run(['git','-C',str(root),*args],capture_output=True,check=True).stdout
c=load(Q/'execution/result-checkpoint.json');r=load(Q/'review/independent-exact-probe-result-review.json');reg=load(Q/'execution/result-registration.json')
assert r['verdict']==reg['execution']=='PASS_ZERO_INFERENCE_PLUMBING_ONLY'
assert r['runtime_authority'] is False and r['real_research_acceptance_credit'] is False
assert c['remaining_runtime']==c['remaining_review']==0 and reg['root_invocations']==reg['profile_invocations']==reg['reader_invocations']==1
assert reg['original_readbacks']==2 and reg['E02']==reg['T2']=='NOT_PASSED'
assert sha(Q/'execution/result-manifest.json')==c['result_manifest_sha256']==r['result_manifest_sha256']
assert sha(Q/'review/independent-exact-probe-result-review.json')==c['review_sha256']
assert sha(Q/'execution/result-registration.json')==c['registration_sha256']
for rel in ('execution/result-manifest.json','manifest.json'):
    for row in load(Q/rel)['files']:assert sha(Q/row['path'])==row['sha256'],row['path']
for rel in ('entry-manifest.json','profile-preparation/manifest.json'):
    for p,digest in load(Q/rel)['files'].items():assert sha(Path(p))==digest,p
for row in load(D/'snapshot-manifest.json')['files']:
    assert sha(D/row['snapshot'])==sha(Path(row['source']))==row['sha256'],row['source']
for row in c['mirrors']:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
for repo,key in ((R,'main'),(M,'mirror')):
    assert git(repo,'rev-parse','HEAD').decode().strip()==c[key]['commit']
    assert git(repo,'rev-parse','refs/tags/'+c['tag']+'^{commit}').decode().strip()==c[key]['commit']
    for name in c[key]['files']:assert git(repo,'show',c[key]['commit']+':'+name)==(repo/name).read_bytes(),name
for name,digest in c['unrelated_files_preserved'].items():assert sha(R/name)==digest,name
pins=load(Q/'profile-preparation/manifest.json');candidate=Path(pins['candidate_root'])
assert git(candidate,'rev-parse','HEAD').decode().strip()=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not git(candidate,'status','--porcelain','--untracked-files=no').strip()
assert sha(Path(pins['model_manifest_path']))==pins['model_digest']=='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
state=load(Q.parent/'current-run.json')
assert state['phase']=='SOURCE13_E02_ZERO_INFERENCE_PLUMBING_REVIEWED_PASS' and state['active_review_agent'] is None
assert state['next_action_scope']['actual_case_allocation']==state['next_action_scope']['actual_result_review_allocation']==0
assert not state['e02_execution_released'] and not state['next_stage_released']
record=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),verdict='PASS_ZERO_INFERENCE_RESULT_FINAL_READBACK',
    run_id=c['run_id'],execution=reg['execution'],result_files=61,preparation_members=126,entry_bindings=47,profile_dependencies=1499,
    external_snapshot_unchanged=71,unrelated_dirty_paths_preserved=9,product_candidate_unchanged=True,current_8b_manifest_unchanged=True,
    commits_tags_mirrors_exact=True,remaining_runtime=0,remaining_review=0,E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False)
with (Q/'execution/final-readback.json').open('x',encoding='utf-8') as f:json.dump(record,f,ensure_ascii=False,indent=2)
print(json.dumps(record))
