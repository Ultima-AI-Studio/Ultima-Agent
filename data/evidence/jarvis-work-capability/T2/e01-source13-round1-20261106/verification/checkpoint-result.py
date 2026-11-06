"""Commit the independently reviewed E01 result, preserving raw pending terminal and sealed evidence."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e01-source13-round1-result-20261106'


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


assert not (ROOT/'verification/result-local-checkpoint.json').exists()
manifest = seal()
result_manifest = load(ROOT/'verification/result-evidence-manifest.json')
for row in result_manifest['files']:
    path = ROOT/row['path']
    assert path.stat().st_size == row['bytes'] and sha(path) == row['sha256'], str(path)
review_path = ROOT/'review/independent-result-review.json'
review = load(review_path)
registration = load(ROOT/'verification/result-registration.json')
assert registration['result_review_sha256'] == sha(review_path)
assert registration['terminal_sha256'] == sha(ROOT/'actual/e01-round1/terminal.json')
assert registration['case_verdict'] == registration['facts'] == 'PASS' and registration['acceptance_credit'] is True
assert registration['positive_passed'] == 1 and registration['positive_required'] == 3
assert registration['current_case_work_cli_count'] == 1 and registration['current_case_completed_inference_events'] == 2
state = load(ROOT.parent/'current-run.json')
assert state['e01_current_candidate_positive_passed'] == 1
assert state['next_action_scope']['actual_case_allocation'] == state['next_action_scope']['actual_result_review_allocation'] == 0
assert state['e03_positive_passed'] == 3 and state['e03_negative_passed'] is True
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
mirrors = load(ROOT/'verification/result-document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source'])) == sha(Path(row['mirror'])) == row['sha256']
    text = Path(row['source']).read_text(encoding='utf-8')
    assert all(line.rstrip() == line for line in text.splitlines()) and not text.endswith('\n\n')
unrelated = load(ROOT/'verification/result-unrelated-current-snapshot.json')['preserved_sha256']
for name,digest in unrelated.items():
    assert sha(REPO/name) == digest, name
heads = {str(p):gt(p,'rev-parse','HEAD') for p in (REPO,MIRROR)}
for p in (REPO,MIRROR):
    assert not gt(p,'diff','--cached','--name-only')
    assert subprocess.run(['git','-C',str(p),'rev-parse','--verify','--quiet','refs/tags/'+TAG],capture_output=True).returncode != 0
external = gt(REPO,'diff','--name-only','57a0e0d153328751393d68fadfc8bac41527befd..HEAD').splitlines()
assert all(name.startswith('docs/') for name in external), external
receipt = {'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'preparation_manifest_sha256':sha(ROOT/'manifest.json'),'preparation_sealed_files':len(manifest['files']),
    'result_manifest_sha256':sha(ROOT/'verification/result-evidence-manifest.json'),'result_sealed_files':len(result_manifest['files']),
    'review_sha256':sha(review_path),'registration_sha256':sha(ROOT/'verification/result-registration.json'),
    'review':'PASS','candidate':manifest['candidate'],'actual_cases':1,'work_cli_count':1,'completed_inference_events':2,
    'actual_native_start_count':None,'audio_actions':0,'next_case_authority_issued':False,'new_tests_run':0,
    'E01_current_candidate_positive_passed':1,'E01_positive_required':3,'T2':'NOT_PASSED',
    'unrelated_files_preserved':unrelated,'external_docs_commits_preserved':external,
    'authored_documents_whitespace':'PASS','sealed_raw_evidence_bytes':'PRESERVED',
    'before_heads':heads,'mirrors':mirrors,'new_push_attempted':False,'remote_synced':False}
save(ROOT/'verification/result-precommit-readback.json',receipt)
paths = {ROOT/row['path'] for row in result_manifest['files']}
paths.update([review_path])
paths.update(p for d in ('verification','history','review') for p in (ROOT/d).iterdir() if p.is_file())
paths.update([ROOT.parent/'current-run.json',REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(Path(row['source']) for row in mirrors)
assert all(path.is_file() for path in paths) and not any(REPO/name in paths for name in unrelated)
main = checkpoint(REPO,paths,'Record E01 source13 round1 actual and independent facts pass',heads[str(REPO)])
mirror = checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'Mirror E01 round1 result and round2 preparation plan',heads[str(MIRROR)])
seal()
for row in result_manifest['files']:
    assert sha(ROOT/row['path']) == row['sha256']
for name,digest in unrelated.items():
    assert sha(REPO/name) == digest, name
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG)
save(ROOT/'verification/result-local-checkpoint.json',receipt)
print(json.dumps({'main':main['commit'],'main_files':len(main['files']),'mirror':mirror['commit'],
    'mirror_files':len(mirror['files']),'tag':TAG,'E01_positive_passed':1,'E01_required':3,'remote_synced':False}))
