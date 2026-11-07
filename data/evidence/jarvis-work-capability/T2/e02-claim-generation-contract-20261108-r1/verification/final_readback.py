"""Post-commit point-in-time byte/state verification, without runtime execution."""
from pathlib import Path
import datetime as dt,importlib.util,json
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
publication=v.load(N/'verification/publication-readback.json');review=v.load(N/'review/independent-preparation-review.json');state=v.load(v.T/'current-run.json');M=Path('H:/UltimaAI/ultima-docs-repo')
assert publication['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and review['verdict']=='PASS_PREPARATION_ONLY'
assert publication['manifest_sha256']==review['manifest_sha256']==v.sha(N/'manifest.json')
assert publication['review_sha256']==v.sha(N/'review/independent-preparation-review.json')
for name,h in v.load(N/'manifest.json')['files'].items():assert v.sha(N/name)==h,name
for name,h in publication['file_sha256'].items():
    p=Path(name);root=v.R if p.is_relative_to(v.R) else M;key='project' if root==v.R else 'mirror'
    assert v.sha(p)==h and v.git(root,'show',publication['heads'][key]+':'+p.relative_to(root).as_posix())==p.read_bytes(),name
for root,key in ((v.R,'project'),(M,'mirror')):assert v.git(root,'rev-parse','HEAD').decode().strip()==v.git(root,'rev-parse',publication['tag']).decode().strip()==publication['heads'][key]
assert v.git(v.C,'rev-parse','HEAD').decode().strip()==review['candidate']==publication['heads']['candidate'] and not v.git(v.C,'status','--porcelain').strip()
v.verify()
assert state['active_candidate']==review['candidate'] and state['last_actual_result']['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'
assert state['active_candidate_acceptance']['old_credit_transferred'] is False
assert state['next_action_scope']['authorized'] and state['next_proposal']['status']=='TASK3_ENTRY_PREPARATION_AUTHORIZED_NO_ACTUAL'
value=dict(verdict='PASS_FINAL_LOCAL_READBACK',heads=publication['heads'],tag=publication['tag'],manifest_sha256=v.sha(N/'manifest.json'),review_sha256=v.sha(N/'review/independent-preparation-review.json'),publication_sha256=v.sha(N/'verification/publication-readback.json'),tests=1004,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,acceptance_credit=0,old_failure_preserved=True,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',next='AUTHORIZED_TASK3_ENTRY_PREPARATION',remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
v.save(N/'verification/final-readback.json',value);print(json.dumps(value))
