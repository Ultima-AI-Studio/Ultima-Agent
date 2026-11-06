"""Commit exactly the reviewed preparation and its receipts; no remote operations."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

B = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e02-source13-binding-prep-20261106'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save_new(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def git(repo, *args, data=None):
    return subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','-c','core.quotepath=false',*args],
        input=data, capture_output=True, check=True).stdout


def gt(repo, *args):
    return git(repo, *args).decode('utf-8').strip()


def seal():
    assert sha(B/'manifest.json') == 'ec15aa82ee9ef72ff366c33eb997307e8151a97957eaa6d3f8544dc555424382'
    manifest = load(B/'manifest.json')
    for row in manifest['files']:
        path = B/row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
    bound = load(B/'profile-preparation/manifest.json')['files']
    assert len(bound) == 1461
    for name, digest in bound.items():
        assert sha(Path(name)) == digest, name
    return manifest


def checkpoint(repo, paths, expected_head, message):
    assert gt(repo,'rev-parse','HEAD') == expected_head
    assert not gt(repo,'diff','--cached','--name-only')
    names = sorted(path.relative_to(repo).as_posix() for path in paths)
    assert all(path.is_file() for path in paths)
    git(repo,'add','-f','--pathspec-from-file=-','--pathspec-file-nul', data=('\0'.join(names)+'\0').encode('utf-8'))
    staged = gt(repo,'diff','--cached','--name-only','--no-renames').splitlines()
    assert staged and set(staged).issubset(names)
    for name in staged:
        assert git(repo,'show',':'+name) == (repo/name).read_bytes(), name
    # Raw historical snapshots and runner stdout remain exact evidence, including whitespace.
    git(repo,'diff','--cached','--check','--','docs','tasks')
    assert gt(repo,'rev-parse','HEAD') == expected_head
    git(repo,'commit','-m',message)
    commit = gt(repo,'rev-parse','HEAD')
    assert gt(repo,'rev-parse',commit+'^') == expected_head
    assert set(gt(repo,'diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()) == set(staged)
    for name in staged:
        assert git(repo,'show',commit+':'+name) == (repo/name).read_bytes(), name
    git(repo,'tag',TAG,commit)
    assert gt(repo,'rev-parse','refs/tags/'+TAG+'^{commit}') == commit
    return dict(commit=commit, parent=expected_head, files=staged, exact_blob_readback=True, tag=TAG)


assert not (B/'verification/preparation-local-checkpoint.json').exists()
manifest = seal()
review = load(B/'review/independent-preparation-review.json')
gate = load(B/'verification/code-preparation-gate.json')
assert review['verdict'] == 'PASS' and review['findings'] == []
assert gate['independent_review_sha256'] == sha(B/'review/independent-preparation-review.json')
assert gate['root_disposition_sha256'] == sha(B/'verification/root-review-disposition.json')
assert gate['verdict'] == 'PASS_PREPARATION_ONLY' and gate['actual_authority'] is False
state = load(B.parent/'current-run.json')
assert state['e02_preparation_review'] == 'PASS' and state['e01_current_candidate_positive_passed'] == 3
assert state['next_action_scope']['actual_case_allocation'] == state['next_action_scope']['actual_result_review_allocation'] == 0
candidate = Path(load(B/'inputs/candidate-runtime-manifest.json')['candidate_root'])
assert gt(candidate,'rev-parse','HEAD') == manifest['candidate']
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
mirrors = load(B/'verification/reviewed-document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source'])) == sha(Path(row['mirror'])) == row['sha256']

paths = {B/row['path'] for row in manifest['files']}
paths.add(B/'manifest.json')
paths.update(p for folder in ('verification','review') for p in (B/folder).iterdir() if p.is_file())
paths.update(Path(row['source']) for row in mirrors)
paths.update([B.parent/'current-run.json', REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
    B.parent/'e01-source13-round3-20261106/verification/result-local-checkpoint.json'])
mirror_paths = {Path(row['mirror']) for row in mirrors}
owned = {REPO:paths, MIRROR:mirror_paths}
heads={str(repo):gt(repo,'rev-parse','HEAD') for repo in owned}
unrelated={}
for repo, members in owned.items():
    assert not gt(repo,'diff','--cached','--name-only')
    assert not gt(repo,'tag','--list',TAG)
    names = {path.relative_to(repo).as_posix() for path in members}
    unrelated[str(repo)] = {name:sha(repo/name) for name in gt(repo,'diff','--name-only').splitlines() if name not in names}
receipt=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), scope='REVIEWED_OFFLINE_PREPARATION_CHECKPOINT',
    manifest_sha256=sha(B/'manifest.json'), sealed_files=len(manifest['files']), bound_inputs=1461,
    review_sha256=sha(B/'review/independent-preparation-review.json'),
    code_gate_sha256=sha(B/'verification/code-preparation-gate.json'),
    candidate=manifest['candidate'], named_runner_tests=557, old_test_ids=540, new_test_ids=17,
    original_profile_runs=0, fixed_runner_runs=0, model_calls=0, runtime_authority=False,
    E01='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', E02='NOT_PASSED', T2='NOT_PASSED',
    before_heads=heads, unrelated_files_preserved=unrelated, mirrors=mirrors,
    new_push_attempted=False, remote_synced=False, automatic_review_block='Prior push rejected: blocked by policy; no alternative channel attempted')
save_new(B/'verification/preparation-precommit-readback.json', receipt)
paths.add(B/'verification/preparation-precommit-readback.json')
for repo_name, items in unrelated.items():
    for name, digest in items.items():
        assert sha(Path(repo_name)/name) == digest, name
main = checkpoint(REPO, paths, heads[str(REPO)], 'Record reviewed E02 source13 offline profile binding preparation')
mirror = checkpoint(MIRROR, mirror_paths, heads[str(MIRROR)], 'Mirror reviewed E02 source13 binding preparation')
seal()
for repo_name, items in unrelated.items():
    for name, digest in items.items():
        assert sha(Path(repo_name)/name) == digest, name
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(), main=main, mirror=mirror, tag=TAG)
save_new(B/'verification/preparation-local-checkpoint.json', receipt)
print(json.dumps(dict(main=main['commit'], main_files=len(main['files']), mirror=mirror['commit'],
    mirror_files=len(mirror['files']), tag=TAG, remote_synced=False, actual_authority=False)))
