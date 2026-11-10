"""Reconcile only current preparation aliases; never create execution authority."""
from pathlib import Path
import copy
import datetime as dt
import hashlib
import json

N = Path(__file__).resolve().parents[1]
HEAD = 'd860b2ab4e4d9974e33c96472e4ea15abb807280'
TAG = 'ultimaagent-e02-native-rejection-controlled-ready-20261107'
MANIFEST = '6bdbff35be5d300ae82fc36c9f8a3098781872923882d3e855cd87e6cf1171d7'
PHASE = 'SOURCE29_E02_NATIVE_REJECTION_CONTROLLED_READY_AWAITING_ALLOCATION'
KEYS = ('preparation_review_path', 'preparation_tests_passed', 'preparation_sync',
        'local_checkpoint_tag', 'remote_sync', 'next_action', 'next_offline_plan')
HISTORY = 'source29_superseded_preparation_aliases'

def reconcile(state):
    assert state['phase'] == PHASE
    assert state['active_candidate'] == HEAD
    assert state['actual_case_allocation_remaining'] == state['result_review_allocation_remaining'] == 0
    assert state['live_gate_released'] is False and state['next_stage_released'] is False
    assert state['t2'] == state['owner_gate'] == 'NOT_PASSED'
    assert HISTORY not in state
    result = copy.deepcopy(state)
    result[HISTORY] = {key:copy.deepcopy(state[key]) for key in KEYS}
    result.update(
        preparation_review_path=state['preparation_review_receipt'],
        preparation_tests_passed=state['preparation_test_count'],
        preparation_sync=dict(status='REFER_TO_LOCAL_PUBLICATION_READBACK_REMOTE_BLOCKED',
            local_tag=TAG, publication_receipt=str(N / 'verification/publication-readback.json'),
            new_push_attempted=False, remote_synced=False),
        local_checkpoint_tag=TAG,
        remote_sync=dict(status='EXISTING_AUTOMATIC_APPROVAL_BLOCK',
            new_push_attempted=False, remote_synced=False),
        next_action=state['next_work'], next_offline_plan=None)
    return result

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save_new(path, value):
    with path.open('xb') as stream:
        stream.write((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf8'))

def main():
    supplement_path = N / 'review/registration-aliases-supplement.json'
    spec = json.loads(supplement_path.read_bytes())
    assert sha(Path(__file__)) == spec['script_sha256']
    assert sha(N / 'manifest.json') == spec['manifest_sha256'] == MANIFEST
    review_path = N / 'review/independent-preparation-review.json'
    review = json.loads(review_path.read_bytes())
    assert review['verdict'] == 'PASS_PREPARATION_ONLY'
    assert review['manifest_sha256'] == MANIFEST and review['actual_run_authorized'] is False
    assert review['registration_aliases_supplement_sha256'] == sha(supplement_path)
    for folder in ('release', 'actual', 'controller-authority', 'native-preflight'):
        assert not (N / folder).exists()
    state_path = N.parent / 'current-run.json'
    before = state_path.read_bytes()
    original = json.loads(before)
    updated = reconcile(original)
    with (N / 'review/registration-before-alias-reconcile.raw').open('xb') as stream:
        stream.write(before)
    assert state_path.read_bytes() == before
    state_path.write_bytes((json.dumps(updated, ensure_ascii=False, indent=2) + '\n').encode('utf8'))
    assert json.loads(state_path.read_bytes()) == updated
    assert updated['last_actual_result'] == original['last_actual_result']
    save_new(N / 'review/registration-alias-reconcile-receipt.json', dict(
        verdict='PASS_CURRENT_PREPARATION_ALIASES', manifest_sha256=MANIFEST,
        supplement_sha256=sha(supplement_path), review_sha256=sha(review_path),
        before_sha256=hashlib.sha256(before).hexdigest(), after_sha256=sha(state_path),
        changed_keys=[*KEYS, HISTORY], historical_actual_unchanged=True,
        actual_case_allocation=0, result_review_allocation=0, model_calls=0,
        recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
    print(json.dumps(dict(verdict='PASS_CURRENT_PREPARATION_ALIASES', actual_case_allocation=0)))

if __name__ == '__main__':
    main()
