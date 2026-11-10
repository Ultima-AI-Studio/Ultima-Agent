"""Checkpoint the reviewed package and exact mirrors, preserving other work."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e01-source13-round3-prep-20261106'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, data):
    assert not path.exists(), str(path)
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def git(repo, *args):
    return subprocess.check_output(['git','-C',str(repo),'-c','core.quotepath=false',*args])


def gt(repo, *args):
    return git(repo,*args).decode('utf-8').strip()


def seal():
    manifest = load(ROOT/'manifest.json')
    for row in manifest['files']:
        path=ROOT/row['path']
        assert path.stat().st_size==row['bytes'] and sha(path)==row['sha256'],str(path)
    return manifest


def checkpoint(repo, paths, message, expected_head):
    assert gt(repo,'rev-parse','HEAD')==expected_head
    assert not gt(repo,'diff','--cached','--name-only')
    names=sorted(path.relative_to(repo).as_posix() for path in paths)
    subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','add','-f','--',*names],check=True,capture_output=True)
    staged=gt(repo,'diff','--cached','--name-only','--no-renames').splitlines()
    assert staged and set(staged).issubset(names)
    for name in staged:
        assert git(repo,'show',':'+name)==(repo/name).read_bytes(),name
    assert gt(repo,'rev-parse','HEAD')==expected_head
    subprocess.run(['git','-C',str(repo),'commit','-m',message],check=True,capture_output=True)
    commit=gt(repo,'rev-parse','HEAD')
    assert gt(repo,'rev-parse',commit+'^')==expected_head
    assert set(gt(repo,'diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())==set(staged)
    for name in staged:
        assert git(repo,'show',commit+':'+name)==(repo/name).read_bytes(),name
    subprocess.run(['git','-C',str(repo),'tag',TAG,commit],check=True,capture_output=True)
    assert gt(repo,'rev-parse','refs/tags/'+TAG+'^{commit}')==commit
    return {'commit':commit,'parent':expected_head,'files':staged,'exact_blob_readback':True,'tag':TAG}


assert not (ROOT/'verification/local-checkpoint.json').exists()
manifest=seal()
review_path=ROOT/'review/independent-preparation-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['scope']==manifest['scope']+'-package'
assert review['verdict']=='PASS' and review['preparation_only'] is True
assert review['manifest_sha256']==sha(ROOT/'manifest.json') and review['candidate']==manifest['candidate']
disposition=load(ROOT/'verification/review-disposition.json')
assert disposition['review_sha256']==sha(review_path) and disposition['decision']=='ACCEPT_PREPARATION_PASS'
assert not (ROOT/'actual').exists() and not (ROOT/'release').exists()
state=load(ROOT.parent/'current-run.json')
assert state['next_action_scope']['actual_case_allocation']==state['next_action_scope']['actual_result_review_allocation']==0
assert state['e01_current_candidate_positive_passed']==2 and state['e01_preparation_tests_passed']==306
runtime=load(ROOT/'inputs/candidate-runtime-manifest.json');candidate=Path(runtime['candidate_root'])
assert gt(candidate,'rev-parse','HEAD')==manifest['candidate']
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
for group in ('source_files','dependencies'):
    for name,digest in runtime[group].items():
        assert sha(Path(name))==digest,name
for component in runtime['sdk_components'].values():
    for name,digest in component['files'].items():
        assert sha(Path(component['root'])/name)==digest,name
mirrors=load(ROOT/'verification/document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
    text=Path(row['source']).read_text(encoding='utf-8')
    assert all(line.rstrip()==line for line in text.splitlines()) and not text.endswith('\n\n')
paths={ROOT/row['path'] for row in manifest['files']}
paths.update([ROOT/'manifest.json',ROOT/'execution-proposal.md'])
paths.update(p for d in ('verification','history','review') for p in (ROOT/d).iterdir() if p.is_file())
paths.update([ROOT.parent/'current-run.json',REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
    ROOT.parent/'e01-source13-round2-20261106/verification/result-local-checkpoint.json'])
paths.update(Path(row['source']) for row in mirrors)
assert all(p.is_file() for p in paths)
names={p.relative_to(REPO).as_posix() for p in paths}
unrelated={name:sha(REPO/name) for name in gt(REPO,'diff','--name-only').splitlines() if name not in names}
heads={str(p):gt(p,'rev-parse','HEAD') for p in (REPO,MIRROR)}
for p in (REPO,MIRROR):
    assert not gt(p,'diff','--cached','--name-only')
    assert subprocess.run(['git','-C',str(p),'rev-parse','--verify','--quiet','refs/tags/'+TAG],capture_output=True).returncode!=0
external=gt(REPO,'log','--format=%H %s','462e3fb064d33f880fd76c268a41a9fbb1ed64f1..HEAD').splitlines()
receipt=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),manifest_sha256=sha(ROOT/'manifest.json'),
    sealed_files=len(manifest['files']),review_sha256=sha(review_path),review='PASS',tests=306,
    candidate=manifest['candidate'],actual_cases=0,product_model_calls=0,audio_actions=0,
    authority_issued=False,result_review_allocated=False,E01='PARTIAL_2_OF_3',T2='NOT_PASSED',
    unrelated_files_preserved=unrelated,external_commits_preserved=external,before_heads=heads,mirrors=mirrors,
    new_push_attempted=False,remote_synced=False)
save(ROOT/'verification/precommit-readback.json',receipt);paths.add(ROOT/'verification/precommit-readback.json')
for name,digest in unrelated.items():
    assert sha(REPO/name)==digest,name
main=checkpoint(REPO,paths,'Prepare same-candidate E01 round3 after two reviewed deliveries',heads[str(REPO)])
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'Mirror E01 source13 round3 preparation',heads[str(MIRROR)])
seal()
for name,digest in unrelated.items():
    assert sha(REPO/name)==digest,name
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG)
save(ROOT/'verification/local-checkpoint.json',receipt)
print(json.dumps({'main':main['commit'],'main_files':len(main['files']),'mirror':mirror['commit'],
    'mirror_files':len(mirror['files']),'tag':TAG,'tests':306,'remote_synced':False,'actual_cases':0}))
