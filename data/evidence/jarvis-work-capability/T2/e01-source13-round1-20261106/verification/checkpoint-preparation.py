"""Commit only the reviewed preparation, local receipts and matching document mirrors."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e01-source13-round1-prep-20261106'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, data):
    assert not path.exists(), str(path)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),'-c','core.quotepath=false',*args])


def gt(repo, *args):
    return git(repo,*args).decode('utf-8').strip()


def seal():
    manifest = load(ROOT/'manifest.json')
    for row in manifest['files']:
        path = ROOT/row['path']
        assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], str(path)
    return manifest


def checkpoint(repo, paths, message, expected_head):
    assert gt(repo,'rev-parse','HEAD') == expected_head
    assert not gt(repo,'diff','--cached','--name-only')
    names = sorted(path.relative_to(repo).as_posix() for path in paths)
    subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','add','-f','--',*names],check=True,capture_output=True)
    staged = gt(repo,'diff','--cached','--name-only','--no-renames').splitlines()
    assert staged and set(staged).issubset(names)
    for name in staged:
        assert git(repo,'show',':'+name) == (repo/name).read_bytes(), name
    subprocess.run(['git','-C',str(repo),'commit','-m',message],check=True,capture_output=True)
    commit = gt(repo,'rev-parse','HEAD')
    assert gt(repo,'rev-parse',commit+'^') == expected_head
    assert set(gt(repo,'diff-tree','--no-commit-id','--name-only','-r',commit).splitlines()) == set(staged)
    for name in staged:
        assert git(repo,'show',commit+':'+name) == (repo/name).read_bytes(), name
    subprocess.run(['git','-C',str(repo),'tag',TAG,commit],check=True,capture_output=True)
    assert gt(repo,'rev-parse','refs/tags/'+TAG+'^{commit}') == commit
    return {'commit':commit,'parent':expected_head,'files':staged,'exact_blob_readback':True,'tag':TAG}


assert not (ROOT/'verification/local-checkpoint.json').exists()
manifest = seal()
review_path = ROOT/'review/independent-preparation-review.json'
review = load(review_path)
assert review['reviewer'] == 'root-independent' and review['scope'] == manifest['scope']+'-package'
assert review['verdict'] == 'PASS' and review['preparation_only'] is True
assert review['manifest_sha256'] == sha(ROOT/'manifest.json') and review['candidate'] == manifest['candidate']
disposition = load(ROOT/'verification/review-disposition.json')
assert disposition['review_sha256'] == sha(review_path) and disposition['decision'] == 'ACCEPT_PREPARATION_PASS'
assert not (ROOT/'actual').exists() and not (ROOT/'release').exists()
state = load(ROOT.parent/'current-run.json')
assert state['next_action_scope']['actual_case_allocation'] == state['next_action_scope']['actual_result_review_allocation'] == 0
assert state['e03_positive_passed'] == 3 and state['e03_negative_passed'] is True
assert state['e01_preparation_review'] == 'PASS' and state['e01_preparation_tests_passed'] == 208
runtime = load(ROOT/'inputs/candidate-runtime-manifest.json')
candidate = Path(runtime['candidate_root'])
assert gt(candidate,'rev-parse','HEAD') == manifest['candidate']
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
for group in ('source_files','dependencies'):
    for name,digest in runtime[group].items():
        assert sha(Path(name)) == digest, name
for component in runtime['sdk_components'].values():
    for name,digest in component['files'].items():
        assert sha(Path(component['root'])/name) == digest, name
mirrors = load(ROOT/'verification/document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source'])) == sha(Path(row['mirror'])) == row['sha256']
    text = Path(row['source']).read_text(encoding='utf-8')
    assert all(line.rstrip() == line for line in text.splitlines()) and not text.endswith('\n\n')
unrelated = {
    'docs/references/lessons-log.md':'89fe849a71e91a05d2241db4690f3333c5e2d3e71aa8e6cc0e29399258f0bcd7',
    'docs/reports/jarvis-work-t2-current8b-interface-resume-20261102.md':'a610c3bffdf3595ba35057de6c7302385f6b8013f5cb7dbc211c449f6ad36715',
    'tasks/events/wo-ultimaagent-20261101-0021-t2.jsonl':'5c99b1f63fa0a49584ffbbf986f6bed19d0022fd3d1ecc2f5f820723717a675c',
    'tasks/tasks.json':'6dd19c7762f164e1e19b5b6971149890b9f1d9750ef6f8f02f050bc48284bb0d'}
for name,digest in unrelated.items():
    assert sha(REPO/name) == digest, name
heads = {str(p):gt(p,'rev-parse','HEAD') for p in (REPO,MIRROR)}
for p in (REPO,MIRROR):
    assert not gt(p,'diff','--cached','--name-only')
    assert subprocess.run(['git','-C',str(p),'rev-parse','--verify','--quiet','refs/tags/'+TAG],capture_output=True).returncode != 0
external = gt(REPO,'diff','--name-only','c4c21b565686b15f7731fc6ecf59032a9bfe0934..HEAD').splitlines()
assert all(name.startswith('docs/') for name in external), external
receipt = {'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'manifest_sha256':sha(ROOT/'manifest.json'),'sealed_files':len(manifest['files']),
    'review_sha256':sha(review_path),'review':'PASS','tests':208,'candidate':manifest['candidate'],
    'actual_cases':0,'product_model_calls':0,'audio_actions':0,'authority_issued':False,'result_review_allocated':False,
    'T2':'NOT_PASSED','unrelated_files_preserved':unrelated,'external_docs_commits_preserved':external,
    'authored_documents_whitespace':'PASS','sealed_raw_test_logs_and_parent_EOF_bytes':'PRESERVED',
    'before_heads':heads,'mirrors':mirrors,'new_push_attempted':False,'remote_synced':False}
save(ROOT/'verification/precommit-readback.json',receipt)
paths = {ROOT/row['path'] for row in manifest['files']}
paths.update([ROOT/'manifest.json',review_path,ROOT/'execution-proposal.md'])
paths.update(p for d in ('verification','history','review') for p in (ROOT/d).iterdir() if p.is_file())
paths.update([ROOT.parent/'current-run.json',REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
    ROOT.parent/'e03-source13-negative-20261106/verification/result-local-checkpoint.json'])
paths.update(Path(row['source']) for row in mirrors)
assert all(path.is_file() for path in paths) and not any(REPO/name in paths for name in unrelated)
main = checkpoint(REPO,paths,'Prepare same-candidate E01 round1 file delivery after E03 pass',heads[str(REPO)])
mirror = checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'Mirror E01 source13 round1 preparation',heads[str(MIRROR)])
seal()
for name,digest in unrelated.items():
    assert sha(REPO/name) == digest, name
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG)
save(ROOT/'verification/local-checkpoint.json',receipt)
print(json.dumps({'main':main['commit'],'main_files':len(main['files']),'mirror':mirror['commit'],
                  'mirror_files':len(mirror['files']),'tag':TAG,'sealed_files':len(manifest['files']),
                  'tests':208,'remote_synced':False,'actual_cases':0}))
