"""Read existing receipts and sources; create a new observation, never a case."""
from pathlib import Path
import collections
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parent
T2 = ROOT.parent
R31 = T2 / 'e03-source12-20261105-r31-preflight-log-isolation'
HEAD = '7975e477665c02820fa235b73d203718bd33b2c9'

def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))

def save_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')

manifest_path = R31 / 'preparation/manifest.json'
assert sha(manifest_path) == '7e988afb8e279caac6e0fe1605bbce3c27cb08e68ad4f6356dc89df4a8fcdb81'
manifest = load(manifest_path)
artifact_checks = []
for item in manifest['review_artifacts']:
    path = R31 / item['path']
    assert path.resolve().is_relative_to(R31.resolve())
    assert path.stat().st_size == item['bytes'] and sha(path) == item['sha256'], item['path']
    artifact_checks.append(item)
candidate_path = R31 / 'candidate-manifest-r13.json'
candidate = load(candidate_path)
for path, expected in candidate['source_files'].items():
    assert sha(path) == expected, path
assert subprocess.check_output(['git', '-C', candidate['candidate_root'], 'rev-parse', 'HEAD'], text=True).strip() == HEAD
assert subprocess.check_output(['git', '-C', candidate['candidate_root'], 'branch', '--show-current'], text=True).strip() == candidate['branch']

case = R31 / 'actual/e03-round2'
terminal = load(case / 'terminal.json')
execution = load(R31 / 'verification/controller-execution-r31.json')
assert sha(case / 'terminal.json') == execution['terminal_sha256']
events = [json.loads(line) for line in (case / 'fixture-events.jsonl').read_text().splitlines()]
assert sha(case / 'fixture-events.jsonl') == terminal['fixture_audit_sha256']
fixture, initial, baseline = (load(case / name) for name in ('fixture.json', 'fixture-initial-readback.json', 'baseline.json'))
timing = load(case / 'baseline-timing.json')
edits = [row for row in events if row['type'] == 'edit-message']
changes = [row for row in edits if row['before'] != row['after']]
assert len(changes) == 1
change = changes[0]
assert change['message_id'] == 0xC2 and change['before']['utf16_units'] == 41 and change['after']['utf16_units'] == 0
assert initial['targets'][0]['after_activation']['utf16_units'] == 41 and baseline[0]['text'] == ''
assert fixture['targets'][0]['control_hwnd'] == baseline[0]['control_hwnd'] == change['hwnd']
assert load(R31 / 'controller-ledger.json')['consumed'] == ['e03-round2']
assert terminal['work_cli_count'] == 0 and terminal['product_result_sha256'] is None

receipts = []
inherited_receipts = []
for path in sorted(T2.glob('e03-source12*/actual/*/terminal.json')):
    folder = path.parent
    value = load(path)
    admission_path = folder / 'admission.json'
    if not admission_path.exists():
        # This directory is a two-file mirror, not a fresh source12 execution.
        original_root = T2 / 'e03-source10-20261103-recovery2'
        original_case = original_root / 'actual' / value['case']
        original_authority_path = original_root / 'controller-authority' / (value['case'] + '.json')
        original_authority = load(original_authority_path)
        assert original_authority['candidate'] != HEAD
        assert sha(path) == sha(original_case / 'terminal.json')
        assert sha(folder / 'independent-review.json') == sha(original_case / 'independent-review.json')
        inherited_receipts.append(dict(mirror=str(path), terminal_sha256=sha(path),
                                       original_case=str(original_case),
                                       original_candidate=original_authority['candidate'],
                                       original_authority=str(original_authority_path),
                                       original_authority_sha256=sha(original_authority_path),
                                       review_sha256=sha(folder / 'independent-review.json'),
                                       current_candidate_credit=False,
                                       reason='byte-identical source10 PASS mirror; original authority binds another candidate'))
        continue
    admission = load(admission_path)
    authority = admission['authority']
    assert authority['candidate'] == HEAD, str(path)
    review_path = folder / 'independent-review.json'
    review = load(review_path) if review_path.exists() else None
    bound_review = False
    if review:
        evidence = review.get('evidence_sha256', {})
        bound_review = review.get('terminal_sha256', evidence.get('terminal.json')) == sha(path)
        if value.get('product_result_sha256'):
            assert sha(folder / 'product-result.json') == value['product_result_sha256']
            if 'product-result.json' in evidence:
                bound_review = bound_review and evidence['product-result.json'] == sha(folder / 'product-result.json')
        for rel in ('cleanup.json', 'boundaries.json'):
            if rel in evidence:
                bound_review = bound_review and sha(folder / rel) == evidence[rel]
    identity = hashlib.sha256(json.dumps(authority, sort_keys=True).encode()).hexdigest()
    receipts.append(dict(path=str(path), terminal_sha256=sha(path), candidate=authority['candidate'],
                         case=value['case'], authority_identity_sha256=identity,
                         overall=value['overall'], mechanical=value['mechanical'],
                         work_cli_count=value['work_cli_count'], acceptance_credit=value.get('acceptance_credit'),
                         review_path=str(review_path) if review else None,
                         review_sha256=sha(review_path) if review else None,
                         review_bound=bound_review, review_verdict=review.get('verdict') if review else None,
                         review_facts=review.get('facts') if review else None))
assert len({(x['authority_identity_sha256'], x['case']) for x in receipts}) == len(receipts), 'duplicate case receipts need explicit reconciliation'
reviewed_pass = [x for x in receipts if x['overall'] == x['mechanical'] == 'PASS'
                and x['review_bound'] and x['review_verdict'] == x['review_facts'] == 'PASS']
counts = dict(distinct_same_candidate_terminals=len(receipts),
              work_cli_submissions=sum(x['work_cli_count'] for x in receipts),
              reviewed_positive_cases=sum(x['case'] != 'e03-negative' for x in reviewed_pass),
              reviewed_negative_cases=sum(x['case'] == 'e03-negative' for x in reviewed_pass),
              consecutive_three_and_negative_gate='NOT_PASSED')
artifacts = ['preparation/manifest.json', 'review/independent-review.json', 'candidate-manifest-r13.json',
             'authorization.json', 'controller-ledger.json', 'verification/controller-execution-r31.json',
             'actual/e03-round2/terminal.json', 'actual/e03-round2/fixture-initial-readback.json',
             'actual/e03-round2/baseline.json', 'actual/e03-round2/baseline-timing.json',
             'actual/e03-round2/fixture-events.jsonl', 'actual/e03-round2/cleanup.json',
             'actual/e03-round2/boundaries.json', 'preparation/fixture_adapter.py', 'preparation/controller.py']
report = dict(schema=1, work_order='wo-ultimaagent-20261101-0021',
              recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), action='read-only existing-evidence diagnosis',
              r31_sealed_artifacts_verified=len(artifact_checks), candidate_sources_verified=len(candidate['source_files']),
              candidate=HEAD, model=manifest['model'],
              source_hashes={rel: sha(R31 / rel) for rel in artifacts},
              terminal=terminal, observed_counts=dict(collections.Counter(row['category'] for row in edits)),
              changed_record=change, baseline_observer_interval=timing,
              change_record_time_offset_ms=(dt.datetime.fromisoformat(change['received_at_utc'])-dt.datetime.fromisoformat(timing['started_at'])).total_seconds()*1000,
              interpretation=dict(source='UNCONFIRMED', category_is_message_class_not_actor=True,
                                  legacy_timestamps_sampled_after_original_wndproc=True,
                                  nesting_not_recorded=True, input_origin_not_recorded=True,
                                  user_context='User could not confirm whether typing during 14:54:36-38'),
              same_candidate_case_receipts=receipts, inherited_receipts_excluded=inherited_receipts,
              derived_counts=counts,
              new_live_cases=0, new_model_calls=0, current_authority_consumed=True,
              old_failures_preserved=True, t2_status='NOT_PASSED')
save_new(ROOT / 'verification/r31-readback.json', report)
print(json.dumps({'sealed_artifacts': len(artifact_checks), 'candidate_sources': len(candidate['source_files']),
                  'counts': counts, 'r31_terminal': terminal['overall'], 'output_sha256': sha(ROOT / 'verification/r31-readback.json')}))
