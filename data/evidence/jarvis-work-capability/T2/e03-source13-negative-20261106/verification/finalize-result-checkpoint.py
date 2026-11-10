"""Local result checkpoint; preserve sealed bytes and unrelated working files."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e03-source13-negative-result-20261106'
CANDIDATE = '269aca511d88412dbb9c15d23911138469a37aa2'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    assert not path.exists(), str(path)
    path.write_bytes((json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))


def git(repo, *args):
    return subprocess.check_output(['git', '-C', str(repo), '-c', 'core.quotepath=false', *args])


def git_text(repo, *args):
    return git(repo, *args).decode('utf-8').strip()


def verify_manifest(name):
    manifest = load(ROOT / name)
    for row in manifest['files']:
        path = ROOT / row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
    return manifest


def stage_commit(repo, paths, message, expected_head):
    assert git_text(repo, 'rev-parse', 'HEAD') == expected_head
    assert not git_text(repo, 'diff', '--cached', '--name-only')
    names = sorted(p.relative_to(repo).as_posix() for p in paths)
    subprocess.run(['git', '-C', str(repo), '-c', 'core.autocrlf=false', 'add', '-f', '--', *names], check=True, capture_output=True)
    staged = git_text(repo, 'diff', '--cached', '--name-only', '--no-renames').splitlines()
    assert staged and set(staged).issubset(names), staged
    for name in staged:
        assert git(repo, 'show', ':' + name) == (repo / name).read_bytes(), name
    subprocess.run(['git', '-C', str(repo), 'commit', '-m', message], check=True, capture_output=True)
    commit = git_text(repo, 'rev-parse', 'HEAD')
    assert git_text(repo, 'rev-parse', commit + '^') == expected_head
    committed = git_text(repo, 'diff-tree', '--no-commit-id', '--name-only', '-r', commit).splitlines()
    assert set(committed) == set(staged)
    for name in staged:
        assert git(repo, 'show', commit + ':' + name) == (repo / name).read_bytes(), name
    subprocess.run(['git', '-C', str(repo), 'tag', TAG, commit], check=True, capture_output=True)
    assert git_text(repo, 'rev-parse', 'refs/tags/' + TAG + '^{commit}') == commit
    return {'commit': commit, 'parent': expected_head, 'files': staged, 'exact_blob_readback': True, 'tag': TAG}


assert not (ROOT / 'verification/result-local-checkpoint.json').exists()
heads = {str(p): git_text(p, 'rev-parse', 'HEAD') for p in (REPO, MIRROR)}
for p in (REPO, MIRROR):
    assert not git_text(p, 'diff', '--cached', '--name-only')
    assert subprocess.run(['git', '-C', str(p), 'rev-parse', '--verify', '--quiet', 'refs/tags/' + TAG], capture_output=True).returncode != 0
prep = verify_manifest('manifest.json')
result = verify_manifest('verification/result-evidence-manifest.json')
assert len(prep['files']) == 80 and len(result['files']) == 61
review = load(ROOT / 'independent-result-review.json')
review_sha = sha(ROOT / 'independent-result-review.json')
assert review_sha == 'a4f5efc616ea83ab30c5752bd9fae914dda684a8222b7a1c3a9a630d4979b6c5'
assert review['verdict'] == 'PASS'
registration = load(ROOT / 'verification/result-registration.json')
assert registration['result_review_sha256'] == review_sha
assert registration['terminal_sha256'] == sha(ROOT / 'actual/e03-negative/terminal.json')
assert registration['result_manifest_sha256'] == sha(ROOT / 'verification/result-evidence-manifest.json')
assert registration['E03'] == 'PASS_CURRENT_CANDIDATE_FIXED_CORPUS'
assert registration['positive_passed'] == 3 and registration['negative_cases_passed'] == 1
assert registration['cumulative_work_cli_count'] == 3 and registration['cumulative_completed_inference_events'] == 9
assert registration['candidate'] == CANDIDATE and not registration['goal_complete']
state = load(ROOT.parent / 'current-run.json')
assert state['e03_negative_passed'] and state['e03_positive_passed'] == 3
assert state['next_action_scope']['actual_case_allocation'] == state['next_action_scope']['actual_result_review_allocation'] == 0
assert not state['next_action_scope']['authority_issued']
runtime = load(ROOT / 'inputs/candidate-runtime-manifest.json')
candidate = Path(runtime['candidate_root'])
assert git_text(candidate, 'rev-parse', 'HEAD') == CANDIDATE
assert not git_text(candidate, 'status', '--porcelain', '--untracked-files=no')
for group in ('source_files', 'dependencies'):
    for name, digest in runtime[group].items():
        assert sha(Path(name)) == digest, name
for component in runtime['sdk_components'].values():
    for name, digest in component['files'].items():
        assert sha(Path(component['root']) / name) == digest, name
unrelated = {
    'docs/reports/jarvis-work-t2-current8b-interface-resume-20261102.md': 'a610c3bffdf3595ba35057de6c7302385f6b8013f5cb7dbc211c449f6ad36715',
    'tasks/events/wo-ultimaagent-20261101-0021-t2.jsonl': '5c99b1f63fa0a49584ffbbf986f6bed19d0022fd3d1ecc2f5f820723717a675c',
    'tasks/tasks.json': '6dd19c7762f164e1e19b5b6971149890b9f1d9750ef6f8f02f050bc48284bb0d',
    'docs/references/lessons-log.md': '89fe849a71e91a05d2241db4690f3333c5e2d3e71aa8e6cc0e29399258f0bcd7',
}
for name, digest in unrelated.items():
    assert sha(REPO / name) == digest, name
mirrors = load(ROOT / 'verification/result-document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source'])) == sha(Path(row['mirror'])) == row['sha256']
    text = Path(row['source']).read_text(encoding='utf-8')
    assert all(line.rstrip() == line for line in text.splitlines())
    assert not text.endswith('\n\n')
receipt = {
    'recorded_at': dt.datetime.now(dt.timezone.utc).isoformat(),
    'preparation_sealed_files': 80, 'result_sealed_files': 61, 'seal_mismatches': 0,
    'review_sha256': review_sha, 'registration_sha256': sha(ROOT / 'verification/result-registration.json'),
    'candidate': CANDIDATE, 'candidate_tracked_clean': True, 'source_files': len(runtime['source_files']),
    'dependency_files': len(runtime['dependencies']),
    'sdk_files': sum(len(x['files']) for x in runtime['sdk_components'].values()),
    'new_tests_run': 0, 'new_live_cases': 0, 'model_calls': 0, 'audio_actions': 0,
    'E03': registration['E03'], 'T2': 'NOT_PASSED', 'E01_actual_allocation': 0,
    'unrelated_files_preserved': unrelated, 'before_heads': heads, 'mirrors': mirrors,
    'authored_documents_whitespace': 'PASS',
    'raw_evidence_whitespace': 'NOT_REWRITTEN; prior full-check warnings retained',
    'remote_synced': False, 'new_push_attempted': False,
}
precommit = ROOT / 'verification/result-precommit-readback.json'
save(precommit, receipt)
paths = {ROOT / 'manifest.json', ROOT / 'independent-result-review.json', ROOT / 'user-approval.json'}
paths.update(ROOT / row['path'] for row in prep['files'])
paths.update(ROOT / row['path'] for row in result['files'])
paths.update(p for folder in ('history', 'verification') for p in (ROOT / folder).iterdir() if p.is_file())
paths.update([ROOT.parent / 'current-run.json', REPO / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md', REPO / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(Path(row['source']) for row in mirrors)
assert not any(REPO / name in paths for name in unrelated)
assert all(p.is_file() for p in paths)
main_result = stage_commit(REPO, paths, 'Record E03 source13 negative pass and next E01 preparation plan', heads[str(REPO)])
mirror_result = stage_commit(MIRROR, {Path(row['mirror']) for row in mirrors}, 'Mirror E03 negative result and E01 source13 preparation plan', heads[str(MIRROR)])
verify_manifest('manifest.json')
verify_manifest('verification/result-evidence-manifest.json')
for name, digest in unrelated.items():
    assert sha(REPO / name) == digest, name
assert not git_text(candidate, 'status', '--porcelain', '--untracked-files=no')
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), main=main_result, mirror=mirror_result, tag=TAG)
save(ROOT / 'verification/result-local-checkpoint.json', receipt)
print(json.dumps({'main': main_result['commit'], 'main_files': len(main_result['files']), 'mirror': mirror_result['commit'], 'mirror_files': len(mirror_result['files']), 'tag': TAG, 'sealed_files_verified': 141, 'unrelated_preserved': len(unrelated), 'remote_synced': False}))
