"""Post-closeout readback: immutable predecessor checks plus exact reviewed-result state."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
B=T/'e02-output-structure-diagnostics-20261108-r2'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def members(root,manifest):
    values=load(manifest)['files']
    for name,h in values.items():assert sha(root/name)==h,name
    return len(values)
def verify():
    predecessor=load(N/'inputs/predecessor.json')
    for name,key in [('manifest.json','manifest_sha256'),('review/independent-preparation-review.json','review_sha256'),('verification/publication-readback.json','publication_sha256')]:assert sha(B/name)==predecessor[key]
    counts={str(B):members(B,B/'manifest.json')}
    for name,h in load(B/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
    old=load(B/'inputs/predecessor.json');root=Path(old['root'])
    assert sha(root/'manifest.json')==old['manifest_sha256'] and sha(root/'review/independent-preparation-review.json')==old['review_sha256']
    counts[str(root)]=members(root,root/'manifest.json')
    for name,h in load(root/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
    pins=load(B/'inputs/accepted-dependency-pins.json')['files']
    for name,h in pins.items():assert sha(name)==h,name
    historical={}
    for name,expected in [('e02-native-rejection-controlled-preparation-20261107-r1','9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6'),('e02-output-budget-controlled-preparation-20261107-r1','3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61')]:
        p=T/name;assert sha(p/'review/result-inputs/result-manifest.json')==expected
        historical[name]=dict(preparation=members(p,p/'manifest.json'),result=members(p,p/'review/result-inputs/result-manifest.json'),actual_seal=members(p/'actual/E02-controlled-1',p/'actual/E02-controlled-1/seal-index.json'))
    for name,h in load(N/'inputs/product-closeout-supplements.json')['files'].items():assert sha(name)==h,name
    for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
    git=lambda root,*args:subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
    assert git(C,'rev-parse','HEAD')==git(C,'rev-parse','ultimaagent-e02-output-structure-candidate-20261108-r2')==predecessor['candidate']
    assert not git(C,'status','--porcelain')
    s=load(T/'current-run.json');assert s['previous_actual_result']==load(N/'inputs/previous-current-run.json')['last_actual_result']
    actual=s['last_actual_result'];review=load(N/'review/independent-result-review.json')
    assert actual['run_id']==review['run_id']=='c4caa739-c466-44f3-866b-0c57ea8c5e40'
    assert actual['result_manifest_sha256']==review['result_manifest_sha256']==sha(N/'review/result-inputs/result-manifest.json')
    assert actual['review_sha256']==sha(N/'review/independent-result-review.json')
    assert actual['independent_review']=='FAIL_CONFIRMED' and actual['acceptance_credit']==0
    assert s['actual_case_allocation_remaining']==s['result_review_allocation_remaining']==0
    decision=load(N/'verification/allocated-user-decision.json')
    assert decision['question_id']=='call_5c06d21b59b8475b873814f857990cc3' and decision['actual_case_allocation']==decision['result_review_allocation']==1 and decision['retry']==0
    return dict(verdict='PASS_PRODUCT_AND_PREDECESSOR_PRESERVATION',candidate=predecessor['candidate'],product_clean=True,product_preparation_members=counts,dependency_pins=len(pins),historical_actual_failures=historical,foreign_files=15,last_actual_preserved=True,actual_cases=0,model_calls=0,scope='Readback only; counters refer to this preservation check, not the separately allocated case',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
