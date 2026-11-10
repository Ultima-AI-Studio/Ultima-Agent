"""Local baseline checkpoint for the fixed runner and next entry plan, not runtime release."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess

E = Path(__file__).resolve().parents[1]
B = E.parent/'e02-source13-profile-binding-20261106'
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
TAG = 'ultimaagent-t2-e02-source13-root-entry-baseline-20261106'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save_new(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2)+'\n')


def git(repo, *args, data=None):
    return subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','-c','core.quotepath=false',*args],
        input=data,capture_output=True,check=True).stdout


def gt(repo, *args):
    return git(repo,*args).decode('utf-8').strip()


def checkpoint(repo, paths, expected_head, message):
    assert gt(repo,'rev-parse','HEAD') == expected_head and not gt(repo,'diff','--cached','--name-only')
    names=sorted(path.relative_to(repo).as_posix() for path in paths)
    git(repo,'add','-f','--pathspec-from-file=-','--pathspec-file-nul',data=('\0'.join(names)+'\0').encode('utf-8'))
    staged=gt(repo,'diff','--cached','--name-only','--no-renames').splitlines()
    assert staged and set(staged).issubset(names)
    for name in staged:
        assert git(repo,'show',':'+name)==(repo/name).read_bytes(),name
    git(repo,'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check','--','docs','tasks')
    assert gt(repo,'rev-parse','HEAD')==expected_head
    git(repo,'commit','-m',message)
    commit=gt(repo,'rev-parse','HEAD')
    assert gt(repo,'rev-parse',commit+'^')==expected_head
    assert set(gt(repo,'diff-tree','--no-commit-id','--name-only','-r',commit).splitlines())==set(staged)
    for name in staged:
        assert git(repo,'show',commit+':'+name)==(repo/name).read_bytes(),name
    git(repo,'tag',TAG,commit)
    assert gt(repo,'rev-parse','refs/tags/'+TAG+'^{commit}')==commit
    return dict(commit=commit,parent=expected_head,files=staged,exact_blob_readback=True,tag=TAG)


assert not (E/'verification/task1-local-checkpoint.json').exists()
readback=load(E/'verification/fixed-runner-readback.json')
assert readback['verdict']=='PASS_OFFLINE_FIXED_RUNNER_ONLY' and readback['exact_test_ids']==557
assert readback['fixed_runner_invocations']==1 and readback['actual_profile_runs']==readback['model_calls']==0
for row in readback['files']+load(E/'inputs/source-bindings.json')['files']:
    assert sha(Path(row['path']))==row['sha256'] and Path(row['path']).stat().st_size==row['bytes'],row['path']
for row in load(B/'manifest.json')['files']:
    assert sha(B/row['path'])==row['sha256'],row['path']
pins=load(B/'profile-preparation/manifest.json')
for name,digest in pins['files'].items():
    assert sha(Path(name))==digest,name
candidate=Path(pins['candidate_root'])
assert gt(candidate,'rev-parse','HEAD')=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
state=load(E.parent/'current-run.json')
assert state['e02_root_entry_implemented'] is False and state['next_action_scope']['next_task']==2
assert state['next_action_scope']['actual_case_allocation']==state['next_action_scope']['actual_result_review_allocation']==0
mirrors=load(E/'verification/task1-document-mirror-readback.json')['mirrors']
for row in mirrors:
    assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
evidence={E/'plan.md'}
evidence.update(p for folder in ('inputs','verification') for p in (E/folder).iterdir() if p.is_file())
evidence.update(Path(row['path']) for row in readback['files'])
evidence.add(B/'verification/preparation-local-checkpoint.json')
manifest=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),scope='ROOT_ENTRY_TASK1_OFFLINE_BASELINE',
    runtime_authority=False,entry_implemented=False,
    files=[dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(evidence)])
save_new(E/'verification/task1-evidence-manifest.json',manifest)
paths=evidence|{E/'verification/task1-evidence-manifest.json',E.parent/'current-run.json',
    REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'}|{Path(row['source']) for row in mirrors}
mirror_paths={Path(row['mirror']) for row in mirrors}
owned={REPO:paths,MIRROR:mirror_paths}
heads={str(repo):gt(repo,'rev-parse','HEAD') for repo in owned}
foreign={}
for repo,members in owned.items():
    assert not gt(repo,'diff','--cached','--name-only') and not gt(repo,'tag','--list',TAG)
    names={p.relative_to(repo).as_posix() for p in members}
    foreign[str(repo)]={name:sha(repo/name) for name in gt(repo,'diff','--name-only').splitlines() if name not in names}
receipt=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),before_heads=heads,
    evidence_manifest_sha256=sha(E/'verification/task1-evidence-manifest.json'),sealed_task1_files=len(manifest['files']),
    fixed_runner_readback_sha256=sha(E/'verification/fixed-runner-readback.json'),fixed_runner_invocations=1,tests=557,
    original_profile_runs=0,model_calls=0,entry_implemented=False,next_task=2,actual_authority=False,
    E01='PASS_CURRENT_CANDIDATE_FIXED_CORPUS',E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS',E02='NOT_PASSED',T2='NOT_PASSED',
    mirrors=mirrors,unrelated_files_preserved=foreign,new_push_attempted=False,remote_synced=False)
save_new(E/'verification/task1-precommit-readback.json',receipt)
paths.add(E/'verification/task1-precommit-readback.json')
main=checkpoint(REPO,paths,heads[str(REPO)],'Record E02 fixed-runner baseline and concrete root-entry plan')
mirror=checkpoint(MIRROR,mirror_paths,heads[str(MIRROR)],'Mirror E02 root-entry baseline and offline plan')
for row in manifest['files']:
    assert sha(Path(row['path']))==row['sha256'],row['path']
for repo,items in foreign.items():
    for name,digest in items.items():assert sha(Path(repo)/name)==digest,name
receipt.update(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG)
save_new(E/'verification/task1-local-checkpoint.json',receipt)
print(json.dumps(dict(main=main['commit'],main_files=len(main['files']),mirror=mirror['commit'],mirror_files=len(mirror['files']),tag=TAG,next_task=2,actual_authority=False,remote_synced=False)))
