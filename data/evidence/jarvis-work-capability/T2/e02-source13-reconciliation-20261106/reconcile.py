"""Read saved E02 evidence and compare it with the frozen source13 candidate.

This script does not import product modules, run tests, or contact any service.
It writes only new readback receipts below its own evidence directory.
"""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

HERE = Path(__file__).resolve().parent
REPO = Path(r'H:\UltimaAI\UltimaAgent')
T2 = REPO / 'data/evidence/jarvis-work-capability/T2'
OLD = T2 / 'navigation-source10-validation-20261103-inert2'
PACKAGE = OLD / 'profile-preparation'
CANDIDATE = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
CANDIDATE_COMMIT = '269aca511d88412dbb9c15d23911138469a37aa2'
OLD_COMMIT = '118ba152b007c30d358c8bc44c51aabe8ae820f0'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), *args])


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


manifest_path = PACKAGE / 'manifest.json'
manifest = load(manifest_path)
old_root = Path(manifest['candidate_root'])
runtime_path = T2 / 'e01-source13-round3-20261106/inputs/candidate-runtime-manifest.json'
runtime = load(runtime_path)
assert git(CANDIDATE, 'rev-parse', 'HEAD').decode().strip() == CANDIDATE_COMMIT
assert not git(CANDIDATE, 'status', '--porcelain', '--untracked-files=no').strip()
for name, digest in runtime['source_files'].items():
    assert sha(Path(name)) == digest, name

members = []
for name, digest in manifest['members'].items():
    current = sha(PACKAGE / name)
    members.append(dict(path=name, expected=digest, observed=current, match=current == digest))
assert all(row['match'] for row in members)

old_inputs = []
mapped_source = []
for name, digest in manifest['files'].items():
    path = Path(name)
    observed = sha(path) if path.is_file() else None
    old_inputs.append(dict(path=name, expected=digest, observed=observed, match=observed == digest))
    try:
        relative = path.relative_to(old_root)
    except ValueError:
        continue
    if relative.parts[0] != 'src':
        continue
    current_path = CANDIDATE / relative
    current = sha(current_path) if current_path.is_file() else None
    mapped_source.append(dict(path=relative.as_posix(), old_expected=digest,
                              current_path=str(current_path), current_sha256=current,
                              same=current == digest))

diff_paths = ['src/brain/work_context.py', 'src/brain/work_service.py']
diff = git(CANDIDATE, 'diff', OLD_COMMIT, CANDIDATE_COMMIT, '--', *diff_paths)
with (HERE / 'product-source-delta.patch').open('xb') as stream:
    stream.write(diff)
report = old_root / '.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-4-original-profile-code-preparation-report.md'
input_paths = [
    manifest_path, PACKAGE / 'README.md', report,
    OLD / 'original-profile-code-preparation-authority.json',
    OLD / 'original-profile-root-interface-supplement.json',
    OLD / 'original-profile-design-review-3/verdict.json',
    Path(manifest['corpus_path']), Path(manifest['readback_path']), runtime_path,
    REPO / 'docs/specs/jarvis-work-capability-contract-20261101.md',
    REPO / 'docs/plans/jarvis-work-research-source-navigation-implementation-20261102.md',
    HERE / 'reconcile.py', HERE / 'product-source-delta.patch',
]
inputs = [dict(path=str(path), bytes=path.stat().st_size, sha256=sha(path)) for path in input_paths]
receipt = dict(
    recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), controller='root',
    scope='E02_READ_ONLY_HISTORY_AND_CANDIDATE_RECONCILIATION',
    candidate=CANDIDATE_COMMIT, prior_candidate=OLD_COMMIT,
    candidate_runtime_manifest_sha256=sha(runtime_path),
    current_source_files_rehashed=len(runtime['source_files']),
    old_manifest_sha256=sha(manifest_path), old_package_members=members,
    old_inputs=old_inputs, old_input_count=len(old_inputs),
    old_input_matches=sum(row['match'] for row in old_inputs),
    old_input_mismatches=[row for row in old_inputs if not row['match']],
    mapped_current_sources=mapped_source,
    mapped_current_source_count=len(mapped_source),
    mapped_current_source_differences=[row for row in mapped_source if not row['same']],
    historical_fix6_state=manifest['review_fix_6'],
    historical_test_inventory_count=len(manifest['test_ids']),
    historical_unique_test_ids=len(set(manifest['test_ids'])),
    historical_test_note='Saved inventory and author report only; no fresh test or current-candidate qualification.',
    historical_root_control_implementation=manifest['control_implementation'],
    historical_final_contract_run=manifest['full_contract_run'],
    original_corpus_sha256=sha(Path(manifest['corpus_path'])),
    inputs=inputs, product_delta_paths=diff_paths,
    product_delta_meaning='Current committed delta reobserves E03 selection and replaces unverified failure completion text; the E02 SourceNavigation implementation already exists.',
    conclusion='OLD_PACKAGE_IS_NOT_A_CURRENT_CANDIDATE_RELEASE',
    required_next='Prepare a bounded source13 reuse/delta plan and independent preparation review before any new runtime proposal; retain original query, four sources, gates and all failures.',
    product_imports=0, new_tests_run=0, product_cli_runs=0, model_inferences=0,
    network_or_metadata_requests=0, audio_or_UI_actions=0, service_mutations=0,
    actual_authority_issued=False, existing_closed_allocations_reopened=False,
    E02='NOT_PASSED', T2='NOT_PASSED',
)
save(HERE / 'reconciliation.json', receipt)
print(json.dumps(dict(receipt_sha256=sha(HERE / 'reconciliation.json'),
                     old_input_count=len(old_inputs), old_input_matches=receipt['old_input_matches'],
                     mapped_current_source_count=len(mapped_source),
                     mapped_source_differences=[row['path'] for row in receipt['mapped_current_source_differences']],
                     product_calls=0, new_tests=0, E02='NOT_PASSED')))
