"""Immutable bytes and previous-result preservation after allocation; no obsolete zero-allocation test."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
B=T/'e02-source-grounding-coverage-20261108-r2'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def members(root,manifest):
    values=load(manifest)['files']
    for name,h in values.items():assert sha(root/name)==h,name
    return len(values)
def verify():
    pred=load(N/'inputs/predecessor.json')
    for name,key in [('manifest.json','manifest_sha256'),('review/independent-preparation-review.json','review_sha256'),('verification/publication-readback.json','publication_sha256')]:assert sha(B/name)==pred[key]
    counts=dict(current_entry=members(N,N/'manifest.json'),product_preparation=members(B,B/'manifest.json'))
    for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(name)==h,name
    for name,h in load(B/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
    prior=load(B/'inputs/predecessor.json');old=Path(prior['root'])
    for name,key in [('manifest.json','manifest_sha256'),('review/independent-preparation-review.json','preparation_review_sha256'),('review/result-inputs/result-manifest.json','result_manifest_sha256'),('review/independent-result-review.json','result_review_sha256')]:assert sha(old/name)==prior[key]
    counts.update(previous_entry=members(old,old/'manifest.json'),previous_result=members(old,old/'review/result-inputs/result-manifest.json'),previous_actual_seal=members(old/'actual/E02-controlled-1',old/'actual/E02-controlled-1/seal-index.json'))
    parent_product=Path(prior['product_preparation']);assert sha(parent_product/'manifest.json')==prior['product_manifest_sha256']
    counts['parent_product']=members(parent_product,parent_product/'manifest.json')
    pins=load(B/'inputs/accepted-dependency-pins.json')['files']
    for name,h in pins.items():assert sha(name)==h,name
    for name,h in load(N/'inputs/product-closeout-supplements.json')['files'].items():assert sha(name)==h,name
    for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():
        if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==h,name
    git=lambda *args:subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
    assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-source-grounding-candidate-20261108-r1')==pred['candidate'] and not git('status','--porcelain')
    s=load(T/'current-run.json');previous=load(N/'inputs/previous-current-run.json')['last_actual_result']
    assert (s.get('previous_actual_result') if s.get('last_actual_result',{}).get('run_id')!='1496a844-668d-407a-a91b-89be246ba05b' else s['last_actual_result'])==previous
    decision=load(N/'verification/allocated-user-decision.json')
    assert decision['question_id']=='call_7004c6eafaca48e3a6f19dd87f59d024' and decision['actual_case_allocation']==decision['result_review_allocation']==1 and decision['retry']==0
    return dict(verdict='PASS_PRODUCT_AND_PREDECESSOR_PRESERVATION',candidate=pred['candidate'],product_clean=True,member_counts=counts,dependency_pins=len(pins),foreign_files=15,strict_foreign_files=14,dynamic_observation_only=1,previous_actual_preserved=True,checker_sha256=sha(Path(__file__)),actual_cases=0,model_calls=0,scope='Readback only; counters do not refer to the separately allocated real case',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
