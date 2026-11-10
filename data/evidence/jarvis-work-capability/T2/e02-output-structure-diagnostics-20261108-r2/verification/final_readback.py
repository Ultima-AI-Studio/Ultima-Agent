"""Final local publication readback without importing product or running tests."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,R,T,C,git,sha,load,save=v.N,v.R,v.T,v.C,v.git,v.sha,v.load,v.save
manifest=load(N/'manifest.json');review=load(N/'review/independent-preparation-review.json');published=load(N/'verification/publication-readback.json')
assert published['verdict']=='PASS_LOCAL_PUBLICATION_READBACK'
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['actual_run_authorized'] is False
assert review['candidate']==manifest['candidate']==published['heads']['candidate']
assert sha(N/'manifest.json')==review['manifest_sha256']==published['manifest_sha256']
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in published['file_sha256'].items():assert sha(name)==h,name
for key,root in [('project',R),('mirror',Path('H:/UltimaAI/ultima-docs-repo'))]:
    assert git(root,'rev-parse','HEAD').decode().strip()==published['heads'][key]
    assert git(root,'rev-parse',published['tag']).decode().strip()==published['heads'][key]
assert git(C,'rev-parse','HEAD').decode().strip()==manifest['candidate'] and not git(C,'status','--porcelain').strip()
state=load(T/'current-run.json');assert state['active_candidate']==manifest['candidate']
assert state['last_actual_result']==load(N/'inputs/registration-before/0')['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['active_preparation']['status']=='PASS_OFFLINE_PRODUCT_ONLY_CONTROLLED_ENTRY_NOT_PREPARED'
assert state['active_candidate_acceptance']['E02_controlled_passed']==0 and state['goal_status']=='active'
checked=v.verify()
save(N/'verification/final-readback.json',dict(verdict='PASS_FINAL_LOCAL_READBACK',candidate=manifest['candidate'],
    tests=checked['tests'],manifest_members=len(manifest['files']),published_members=len(published['file_sha256']),
    heads=published['heads'],tag=published['tag'],old_actual_result_preserved=True,actual_cases=0,model_calls=0,
    E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',Owner='NOT_PASSED',controlled_entry_prepared=False,
    actual_allocation=0,result_review_allocation=0,remote_synced=False,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
print(json.dumps(dict(verdict='PASS_FINAL_LOCAL_READBACK',heads=published['heads'],tests=checked['tests'],actual_allocation=0)))
