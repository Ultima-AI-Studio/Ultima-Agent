"""Read committed bytes and bindings; never infer acceptance from file existence."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess

N = Path(__file__).resolve().parents[1]
R = N.parents[4]
M = Path('H:/UltimaAI/ultima-docs-repo')
A = N / 'actual/E02-controlled-1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], creationflags=subprocess.CREATE_NO_WINDOW)

def main():
    publication = load(N / 'verification/result-publication-readback.json')
    review = load(N / 'review/independent-result-review.json')
    manifest = load(N / 'review/result-inputs/result-manifest.json')
    state = load(N.parent / 'current-run.json')
    assert publication['verdict'] == 'PASS_LOCAL_RESULT_PUBLICATION_READBACK'
    assert review['verdict'] == 'FAIL_CONFIRMED' and review['acceptance_credit'] == 0
    assert publication['result_manifest_sha256'] == review['result_manifest_sha256'] == sha(N / 'review/result-inputs/result-manifest.json')
    assert publication['review_sha256'] == sha(N / 'review/independent-result-review.json')
    for root, source in ((N, manifest), (A, load(A / 'seal-index.json')), (N, load(N / 'manifest.json'))):
        for name, digest in source['files'].items():
            assert sha(root / name) == digest, name
    for name, digest in load(N / 'inputs/input-manifest.json')['files'].items():
        assert sha(Path(name)) == digest, name
    for name, digest in publication['file_sha256'].items():
        p = Path(name)
        root = R if p.is_relative_to(R) else M
        head = publication['heads']['project' if root == R else 'mirror']
        assert sha(p) == digest and git(root, 'show', head + ':' + p.relative_to(root).as_posix()) == p.read_bytes(), name
    for root, key in ((R, 'project'), (M, 'mirror')):
        assert git(root, 'rev-parse', 'HEAD').decode().strip() == git(root, 'rev-parse', publication['tag']).decode().strip() == publication['heads'][key]
        assert not git(root, 'diff', '--cached', '--name-only').strip()
    C = Path(load(N / 'inputs/input-manifest.json')['candidate_root'])
    assert not git(C, 'status', '--porcelain').strip()
    assert git(C, 'rev-parse', 'HEAD').decode().strip() == publication['heads']['candidate'] == review['candidate']
    spec = importlib.util.spec_from_file_location('readonly_preservation', N / 'verification/verify_result_preservation.py')
    preservation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preservation)
    preserved = preservation.verify()
    actual = state['last_actual_result']
    previous = load(N / 'verification/result-closeout-before/0-current-run.json')['last_actual_result']
    assert state['previous_actual_result'] == previous and previous['run_id'] == 'c4caa739-c466-44f3-866b-0c57ea8c5e40'
    assert actual['run_id'] == review['run_id'] == manifest['run_id'] == '1496a844-668d-407a-a91b-89be246ba05b'
    assert actual['question_id'] == manifest['user_question_id'] == 'call_c910dd9e4819410492607baac9ed63bf'
    assert state['actual_case_allocation_remaining'] == state['result_review_allocation_remaining'] == actual['acceptance_credit'] == 0
    assert actual['research_artifacts'] == actual['successful_write_count'] == 1 and actual['write_confirmed'] and actual['ack_confirmed']
    assert actual['root_witness_eligible'] is True and actual['timing_eligibility'] == 'UNOBSERVED_NEVER_TIMED_PASS'
    assert actual['application_native_POST_attempts'] == actual['completed_native_posts'] == 8
    assert actual['actual_native_start_count'] is None and actual['facts'] == actual['original_question_coverage'] == 'FAIL'
    assert state['current_e02_controlled_passed'] == 0
    assert state['active_preparation']['status'] == 'COMPLETED_ACTUAL_CONSUMED'
    assert not state['live_gate_released'] and not state['next_stage_released'] and 'pending_actual_result' not in state
    assert state['next_proposal']['status'] == 'PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED'
    effects = load(A / 'accepted-effects.json')
    assert len(effects) == 1 and sha(Path(effects[0]['path'])) == effects[0]['sha256'] == actual['artifact_sha256']
    assert actual['product_status'] == load(A / 'product-result.json')['status'] == 'succeeded'
    assert actual['independent_review'] == 'FAIL_CONFIRMED' and actual['result'] == 'FAIL'
    value = dict(verdict='PASS_POST_COMMIT_RESULT_READBACK', recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        heads=publication['heads'], tag=publication['tag'], result='FAIL_CONFIRMED', run_id=actual['run_id'], question_id=actual['question_id'],
        result_manifest_sha256=sha(N / 'review/result-inputs/result-manifest.json'), review_sha256=sha(N / 'review/independent-result-review.json'),
        publication_receipt_sha256=sha(N / 'verification/result-publication-readback.json'), result_members=len(manifest['files']),
        actual_seal_members=len(load(A / 'seal-index.json')['files']), project_members=publication['project_members'], mirror_members=publication['mirror_members'],
        preparation_preserved=True, old_failure_preserved=True, preservation_counts=preserved['member_counts'], candidate_clean=True, foreign_files_unchanged=15,
        entry_invocations=1, retry=0, application_native_POST_attempts=8, completed_native_posts=8, actual_native_start_count=None,
        research_files=1, artifact_sha256=actual['artifact_sha256'], write_confirmed=True, ack_confirmed=True,
        raw_research_write_success_rows=2, physical_write_effects=1,
        cleanup='PASS_AT_RECORDED_OBSERVATIONS', protected='SEVEN_IDENTITIES_MATCH_AT_RECORDED_POINTS', continuous_liveness_measured=False,
        outer_elapsed_seconds=actual['outer_elapsed_seconds'], terminal_timing_eligibility=actual['timing_eligibility'], root_witness_eligible=True,
        facts='FAIL', original_question_coverage='FAIL', actual_remaining=0, result_review_remaining=0, acceptance_credit=0,
        E02='NOT_PASSED_0_OF_3', T2='NOT_PASSED', Owner='NOT_PASSED', new_case_authorized=False, model_or_runtime_calls_by_readback=0,
        next_proposal=state['next_proposal'], remote_synced=False, remote_reason='Existing automatic push approval block; no retry')
    with (N / 'verification/result-final-readback.json').open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
    print(json.dumps(value, ensure_ascii=False))

if __name__ == '__main__':
    main()
