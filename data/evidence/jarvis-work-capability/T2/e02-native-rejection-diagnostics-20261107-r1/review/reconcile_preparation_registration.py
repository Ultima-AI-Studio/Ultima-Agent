"""Point current preparation aliases at reviewed evidence; preserve actual history."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];state_path=N.parent/'current-run.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
supplement=N/'review/registration-reconcile-supplement.json'
spec=json.loads(supplement.read_bytes())
assert sha(Path(__file__))==spec['script_sha256']
assert sha(N/'manifest.json')==spec['manifest_sha256']=='5ecc68ffa1e4828c81d778a02e1ae9664bd692efbbd7073c9bc4ef13481fbf4b'
manifest=json.loads((N/'manifest.json').read_bytes());review=N/'review/independent-preparation-review.json'
assert json.loads(review.read_bytes())['verdict']=='PASS_PREPARATION_ONLY'
before=state_path.read_bytes();state=json.loads(before)
assert state['phase']=='SOURCE28_E02_NATIVE_REJECTION_OFFLINE_PREPARATION_PASS'
assert state['active_candidate']==state['active_preparation']['candidate']==manifest['candidate']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert state['live_gate_released'] is False and state['next_stage_released'] is False
changes=dict(preparation_review_receipt=str(review),preparation_review_sha256=sha(review),
    preparation_manifest_sha256=sha(N/'manifest.json'),
    next_work='Prepare the current frozen candidate controlled entry offline; explicit new one-case allocation required before any model request',
    next_action_scope=dict(authorized=True,scope='OFFLINE_CONTROLLED_ENTRY_PREPARATION_ONLY_UNDER_CONTINUING_GOAL',
        actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0,
        actual_released=False,reason='Continuing original work order; completed one-case grant is not reused'))
with (N/'review/registration-before-reconcile.raw').open('xb') as f:f.write(before)
state.update(changes)
state_path.write_bytes((json.dumps(state,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
readback=json.loads(state_path.read_bytes());original=json.loads(before)
assert readback==dict(original,**changes)
assert readback['last_actual_result']==original['last_actual_result']
assert readback['actual_case_allocation_remaining']==readback['result_review_allocation_remaining']==0
assert readback['live_gate_released'] is False and readback['t2']=='NOT_PASSED' and readback['owner_gate']=='NOT_PASSED'
save(N/'review/registration-reconcile-receipt.json',dict(verdict='PASS_CURRENT_PREPARATION_POINTERS',
    supplement_sha256=sha(supplement),before_sha256=hashlib.sha256(before).hexdigest(),after_sha256=sha(state_path),
    changed_keys=sorted(changes),historical_actual_unchanged=True,actual_case_allocation=0,result_review_allocation=0,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
print(json.dumps(dict(verdict='PASS_CURRENT_PREPARATION_POINTERS',changed_keys=sorted(changes),actual_case_allocation=0)))
