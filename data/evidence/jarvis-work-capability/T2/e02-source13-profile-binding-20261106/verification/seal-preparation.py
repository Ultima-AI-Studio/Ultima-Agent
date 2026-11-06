"""Seal the current offline package and all retained stages for independent review."""
from pathlib import Path
import ast
import datetime as dt
import difflib
import hashlib
import json
import xml.etree.ElementTree as ET

B = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
PKG = B / 'profile-preparation'
OLD = B.parent / 'navigation-source10-validation-20261103-inert2'
PLAN = REPO / 'docs/plans/jarvis-work-e02-source13-profile-binding-plan-20261106.md'
OLD_ROOT = 'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent'
CURRENT_ROOT = 'C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def save(p, d):
    with p.open('x', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')


old_manifest = load(B / 'history/manifest.json')
manifest = load(PKG / 'manifest.json')
for name, digest in old_manifest['members'].items():
    assert sha(OLD / 'profile-preparation' / name) == sha(B / 'history' / name) == digest
assert sha(OLD / 'profile-preparation/manifest.json') == sha(B / 'history/manifest.json')
for name, digest in manifest['members'].items(): assert sha(PKG / name) == digest
for name, digest in manifest['files'].items(): assert sha(Path(name)) == digest, name

old_source = (B / 'history/profile.py').read_text(encoding='utf-8')
new_source = (PKG / 'profile.py').read_text(encoding='utf-8')
expected_source = old_source.replace("CANDIDATE = '118ba152b007c30d358c8bc44c51aabe8ae820f0'",
    "CANDIDATE = '269aca511d88412dbb9c15d23911138469a37aa2'").replace(OLD_ROOT, CURRENT_ROOT)
assert new_source == expected_source
old_tests = (B / 'history/test_profile.py').read_text(encoding='utf-8')
normalized_tests = old_tests.replace(OLD_ROOT, CURRENT_ROOT).replace("HERE.parent/'harness/adapter.py'", 'binding_adapter().LEGACY')
expected_nodes = [ast.dump(node, include_attributes=False) for node in ast.parse(normalized_tests).body]
current_nodes = [ast.dump(node, include_attributes=False) for node in ast.parse((PKG / 'test_profile.py').read_text(encoding='utf-8')).body]
cursor = 0
for node in current_nodes:
    if cursor < len(expected_nodes) and node == expected_nodes[cursor]: cursor += 1
assert cursor == len(expected_nodes), 'Original test statement removed or changed beyond path adaptation'
assert (PKG / 'run_checks.py').read_bytes() == (B / 'history/run_checks.py').read_bytes()
for name in ('profile.py', 'test_profile.py', 'README.md'):
    before = (B / 'history' / name).read_text(encoding='utf-8').splitlines(keepends=True)
    after = (PKG / name).read_text(encoding='utf-8').splitlines(keepends=True)
    (B / 'verification' / (name + '.diff')).write_text(''.join(difflib.unified_diff(before, after, fromfile='historical/' + name, tofile='current/' + name)), encoding='utf-8')

stages = []
for folder in sorted((B / 'code').iterdir()):
    if not folder.is_dir(): continue
    receipt = load(folder / 'receipt.json')
    assert receipt['dependencies_unchanged'] and receipt['package_unchanged'] and not receipt['io_guard']['denied']
    for name, digest in receipt['raw_sha256'].items(): assert sha(folder / name) == digest
    stages.append(dict(stage=folder.name, counts=receipt['counts'], exit_code=receipt['exit_code'],
                       receipt_sha256=sha(folder / 'receipt.json')))
final = load(B / 'code/binding-full-green2/receipt.json')
assert final['counts'] == dict(tests=557, failures=0, errors=0, skipped=0) and final['exit_code'] == 0
actual = ['test_profile.py::' + case.attrib['name'] for case in ET.parse(B / 'code/binding-full-green2/junit.xml').findall('.//testcase')]
assert len(actual) == len(set(actual)) == 557 and set(actual) == set(manifest['test_ids'])
assert set(old_manifest['test_ids']).issubset(actual) and len(set(actual) - set(old_manifest['test_ids'])) == 17
assert len(load(B / 'inputs/e01-registration.json')['same_candidate_e01_terminal_bindings']) == 3

(B / 'plan.md').write_bytes(PLAN.read_bytes())
author = Path(OLD_ROOT) / '.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-4-original-profile-code-preparation-report.md'
(B / 'history/original-author-report.md').write_bytes(author.read_bytes())
save(B / 'verification/preparation-readback.json', dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    controller='root', scope='OFFLINE_BINDING_PREPARATION_PENDING_INDEPENDENT_REVIEW',
    candidate='269aca511d88412dbb9c15d23911138469a37aa2',
    package_manifest_sha256=sha(PKG / 'manifest.json'), source13_runtime_manifest_sha256=sha(B / 'inputs/candidate-runtime-manifest.json'),
    original_manifest_sha256=sha(B / 'history/manifest.json'), original_author_report_sha256=sha(author),
    pinned_files=len(manifest['files']), original_test_statements_preserved=cursor,
    original_test_ids_preserved=540, current_test_ids=557, new_test_ids=17,
    profile_diff='Candidate constant and one fixed preflight source-origin path only; no algorithm change.',
    old_test_diff='13 source-root literals and three pinned legacy helper source references only; original AST statements retained.',
    historical_repairs=6, historical_review_status='NOT_READY_PENDING_NEW_REVIEW',
    historical_sequence_reopened=False, stages=stages, current_full_contracts=final['counts'],
    original_fixed_runner_actual_invocations=0, original_profile_runs=0, product_cli_runs=0, model_calls=0,
    root_controls_implementation=False, runtime_authority_issued=False, E02='NOT_PASSED', T2='NOT_PASSED'))

brief = '''# Independent preparation review: E02 source13 original-profile binding

Review this offline binding package against plan.md and the original work-capability contract. This is the single whole-package preparation review required by the inline plan, not an actual-result review or new runtime authority. Product candidate remains 269aca511d88412dbb9c15d23911138469a37aa2 and only current8B is allowed. Main repository base is 2bd15bfa70146d19f934141ed84091db0b059ce3; current additions are sealed by manifest.json, not yet committed. Do not review unrelated checkout changes.

Read profile-preparation, profile-adapter.py, verification/preparation-readback.json and all six retained stage receipts/JUnit/inventories; rehash the seal and relevant bound inputs. Inspect the two-literal profile diff and retained original test AST/540 IDs, 17 new cases, 8 behavioral RED, the failed full557 (79 failures/8 errors), focused138 correction and final557 PASS. Original source10 fix-6 and its report are preserved under history; its final review was NOT_READY. Do not assume the old profile algorithm was independently accepted. Judge reusable profile and helper behavior needed for this preparation, including the last R14c real service-handler order and currently pinned WorkService failure content. Important residual bugs must be reported even if inherited.

The new seven-method adapter rehashes current57/7/1346 bindings and uses a private pinned legacy module for five helpers plus SDK origin validation. It changes the private module candidate root/check_inputs only. Assess namespace/origin binding, no accidental old authority/CLI path, signature compatibility, export/readback state and restored monkeypatches. Private legacy definitions are trusted reuse, not an OS/Python security boundary. Original corpus/query/persona/scanners/SDK protocols remain fixed.

Review Focus from plan: (1) old candidate acceptance; (2) old workspace/authority fallback; (3) code PASS misread as runtime authority; (4) WorkService failure content and R14c classification; (5) omitted old tests or drift. Read plan's implementation ruling for three location/documentation omissions; judge the fix by its effect, not just test count. All findings need severity, exact path/line, consequence and correction. List every declined-to-judge item explicitly for root disposition.

Readonly only: standard-library parsing/hashing and readonly Git/file inspection. No audited-module imports, tests, product/model/service/network calls, UI/audio, process operations, source/Git mutations or subagents. The sole permitted write is review/independent-preparation-review.json. Include reviewer=root-independent, agent_identity, scope=e02-source13-profile-binding-preparation, manifest_sha256, verdict (PASS/NEEDS_FIXES), evidence/plan/code judgments, findings and declined_to_judge. State zero actual/model/runtime authority. The original fixed run_checks.py runner was not invoked; named run-stage.py ran all557 selected contracts. Concrete outer RootControls/worker/reader entry and actual SDK/profile/native timing integration remain future gates, not implemented or proved here. E02/T2/Owner remain NOT_PASSED.
'''
(B / 'review/brief.md').write_text(brief, encoding='utf-8')
paths = []
for directory in ('profile-preparation', 'inputs', 'history', 'verification'):
    paths += [p for p in (B / directory).iterdir() if p.is_file()]
paths += [B / 'profile-adapter.py', B / 'plan.md', B / 'review/brief.md']
for folder in (B / 'code').iterdir():
    if folder.is_dir():
        paths += [p for p in folder.iterdir() if p.is_file()]
        paths += [p for p in (folder / 'snapshot').iterdir() if p.is_file()]
rows = [dict(path=p.relative_to(B).as_posix(), bytes=p.stat().st_size, sha256=sha(p)) for p in sorted(set(paths))]
save(B / 'manifest.json', dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    scope='E02_SOURCE13_PROFILE_BINDING_PREPARATION_ONLY', candidate='269aca511d88412dbb9c15d23911138469a37aa2',
    product_or_model_or_actual_authority=False, files=rows))
print(json.dumps(dict(sealed_files=len(rows), manifest_sha256=sha(B / 'manifest.json'),
                     tests=557, original_tests_retained=540, model_calls=0, E02='NOT_PASSED')))
