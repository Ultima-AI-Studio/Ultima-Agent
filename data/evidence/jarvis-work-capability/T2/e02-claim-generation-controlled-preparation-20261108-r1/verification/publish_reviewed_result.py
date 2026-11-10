"""Local exact-path publication of the single reviewed case; no runtime action."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess

N = Path(__file__).resolve().parents[1]
R = N.parents[4]
M = Path('H:/UltimaAI/ultima-docs-repo')
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
HEAD = 'd8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
RUN = '1496a844-668d-407a-a91b-89be246ba05b'
TAG = 'ultimaagent-e02-claim-generation-controlled-result-20261108-r1'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], creationflags=subprocess.CREATE_NO_WINDOW)

def save(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

def main():
    receipt = N / 'verification/result-publication-readback.json'
    assert not receipt.exists()
    closeout = load(N / 'verification/result-closeout-registration.json')
    review = load(N / 'review/independent-result-review.json')
    assert review['verdict'] == 'FAIL_CONFIRMED' and review['acceptance_credit'] == 0
    assert review['candidate'] == HEAD and review['run_id'] == RUN
    assert closeout['review_sha256'] == sha(N / 'review/independent-result-review.json')
    assert closeout['review_markdown_sha256'] == sha(N / 'review/independent-result-review.md')
    manifest = load(N / 'review/result-inputs/result-manifest.json')
    assert closeout['result_manifest_sha256'] == review['result_manifest_sha256'] == sha(N / 'review/result-inputs/result-manifest.json')
    for rel, digest in manifest['files'].items():
        assert sha(N / rel) == digest, rel
    for rel, digest in load(N / 'manifest.json')['files'].items():
        assert sha(N / rel) == digest, rel
    spec = importlib.util.spec_from_file_location('readonly_preservation', N / 'verification/verify_result_preservation.py')
    preservation = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(preservation)
    preserved = preservation.verify()
    assert preserved['verdict'] == 'PASS_PRODUCT_AND_PREDECESSOR_PRESERVATION'
    assert not git(R, 'diff', '--cached', '--name-only').strip()
    assert not git(M, 'diff', '--cached', '--name-only').strip()
    before = dict(project=git(R, 'rev-parse', 'HEAD').decode().strip(), mirror=git(M, 'rev-parse', 'HEAD').decode().strip())
    assert before == dict(project='13699f8d7b523b420cd5c67f0a992e5e581a0125', mirror='1de72daea741ceb9623a6750027ddbf378684442')
    for root in (R, M):
        assert not git(root, 'tag', '--list', TAG).strip()
    project = {N / name for name in manifest['files']}
    supplements = (
        'review/result-inputs/result-manifest.json',
        'review/independent-result-review.json', 'review/independent-result-review.md',
        'review/result-review-allocation.json', 'review/result-registration.json',
        'review/result-final-registration.json',
        'review/result-audit-queue-refresh.json',
        'verification/register_result_audit.py', 'verification/result-audit-registration.json',
        'verification/allocation-queue-refresh.json',
        'verification/authorized-scope-completion.json', 'verification/final-readback.json',
        'verification/skill-contract-ledger-final.md', 'verification/skill-controlled-entry-ledger-final.md',
        'verification/register_reviewed_result.py', 'verification/result-closeout-registration.json',
        'verification/result-source-analysis.json', 'verification/result-goal-registry-observation.json',
        'verification/result-queue-refresh.json', 'verification/result-queue-status.json',
        'verification/publish_reviewed_result.py', 'verification/result_final_readback.py',
    )
    project.update(N / rel for rel in supplements)
    for directory in ('allocation-before', 'result-audit-before', 'result-closeout-before'):
        project.update(p for p in (N / 'verification' / directory).iterdir() if p.is_file())
    project.update([N.parent / 'current-run.json', R / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
                    R / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md', N / 'progress.md'])
    project.update(Path(row['source']) for row in closeout['mirror'])
    mirror = {Path(row['target']) for row in closeout['mirror']}
    for row in closeout['mirror']:
        assert sha(Path(row['source'])) == sha(Path(row['target'])) == row['sha256']
    for p in project:
        assert p.is_file() and p.resolve().is_relative_to(R.resolve()), str(p)
    for p in mirror:
        assert p.is_file() and p.resolve().is_relative_to(M.resolve()), str(p)
    pathspec = N / 'verification/result-publication-pathspec.txt'
    project.add(pathspec)
    with pathspec.open('x', encoding='utf8', newline='\n') as f:
        f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project)) + '\n')
    hashes = {str(p): sha(p) for p in project | mirror}
    git(R, 'add', '-f', '--pathspec-from-file=' + str(pathspec))
    expected = {p.relative_to(R).as_posix() for p in project}
    staged = set(git(R, 'diff', '--cached', '--name-only').decode().splitlines())
    assert staged and staged <= expected
    git(R, 'diff', '--cached', '--check', '--', *[Path(row['source']).relative_to(R).as_posix() for row in closeout['mirror']])
    git(R, 'commit', '-m', 'docs(e02): preserve delivered artifact and failed factual review')
    git(R, 'tag', TAG)
    git(M, 'add', '--', *sorted(p.relative_to(M).as_posix() for p in mirror))
    assert set(git(M, 'diff', '--cached', '--name-only').decode().splitlines()) == {p.relative_to(M).as_posix() for p in mirror}
    git(M, 'diff', '--cached', '--check')
    git(M, 'commit', '-m', 'docs(e02): mirror factual review and source grounding proposal')
    git(M, 'tag', TAG)
    heads = dict(project=git(R, 'rev-parse', 'HEAD').decode().strip(), mirror=git(M, 'rev-parse', 'HEAD').decode().strip(),
                 candidate=git(C, 'rev-parse', 'HEAD').decode().strip())
    assert heads['candidate'] == HEAD and not git(C, 'status', '--porcelain').strip()
    for root, paths, head in ((R, project, heads['project']), (M, mirror, heads['mirror'])):
        assert git(root, 'rev-parse', TAG).decode().strip() == head
        for p in paths:
            assert sha(p) == hashes[str(p)] and git(root, 'show', head + ':' + p.relative_to(root).as_posix()) == p.read_bytes(), str(p)
    for rel, digest in load(N / 'inputs/unrelated-working-tree.json')['files'].items():
        assert sha(R / rel) == digest, rel
    value = dict(verdict='PASS_LOCAL_RESULT_PUBLICATION_READBACK', recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        heads=heads, previous_heads=before, tag=TAG, project_members=len(project), mirror_members=len(mirror), file_sha256=hashes,
        result_manifest_sha256=sha(N / 'review/result-inputs/result-manifest.json'), review_sha256=sha(N / 'review/independent-result-review.json'),
        candidate_clean=True, foreign_files_unchanged=15, actual_case_invocations=1, native_post_attempts=8, completed_native_posts=8,
        actual_native_start_count=None, research_files=1, successful_write_count=1, ack_confirmed=True,
        model_calls_by_publication=0, actual_remaining=0, result_review_remaining=0, acceptance_credit=0, E02='NOT_PASSED', T2='NOT_PASSED',
        remote_synced=False, remote_reason='Prior automatic approval rejected push: blocked by policy; no retry or alternate channel')
    save(receipt, value)
    print(json.dumps({k: value[k] for k in ('verdict', 'heads', 'tag', 'project_members', 'mirror_members', 'acceptance_credit', 'remote_synced')}))

if __name__ == '__main__':
    main()
