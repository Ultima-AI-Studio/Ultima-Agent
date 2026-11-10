"""Verify the bounded payload and stage explicit paths, never unrelated work."""
from pathlib import Path
import json,hashlib,datetime as dt,subprocess
repo=Path(r'H:\UltimaAI\UltimaAgent')
root=Path(__file__).resolve().parents[1]
recovery=root.parent/'runtime-reconcile-20261106-after-round3'
mirror=Path(r'H:\UltimaAI\ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(cwd,*args):return subprocess.check_output(['git','-C',str(cwd),'-c','core.quotepath=false',*args],text=True,encoding='utf-8').strip()
def load(p):return json.loads(p.read_bytes())
assert not git(repo,'diff','--cached','--name-only') and not git(mirror,'diff','--cached','--name-only')
review=load(root/'independent-preparation-review.json');manifest=load(root/'manifest.json')
assert review['manifest_sha256']==sha(root/'manifest.json') and review['verdict']=='PASS'
assert review['original_review_sha256']==sha(root/'independent-preparation-review-original.json')
for row in manifest['files']:
    p=root/row['path'];assert p.stat().st_size==row['bytes'] and sha(p)==row['sha256'],str(p)
assert not (root/'actual').exists() and not (root/'release').exists()
parent=root.parent/'e03-source13-round3-20261106';pm=load(parent/'manifest.json')
for row in pm['files']:
    p=parent/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes']
source=load(root/'inputs/candidate-runtime-manifest.json');candidate=Path(source['candidate_root'])
assert git(candidate,'rev-parse','HEAD')==source['candidate'] and not git(candidate,'status','--porcelain','--untracked-files=no')
for group in ('source_files','dependencies'):
    for name,digest in source[group].items():assert sha(Path(name))==digest
for c in source['sdk_components'].values():
    for name,digest in c['files'].items():assert sha(Path(c['root'])/name)==digest
unrelated={
 'docs/reports/jarvis-work-t2-current8b-interface-resume-20261102.md':'a610c3bffdf3595ba35057de6c7302385f6b8013f5cb7dbc211c449f6ad36715',
 'tasks/events/wo-ultimaagent-20261101-0021-t2.jsonl':'5c99b1f63fa0a49584ffbbf986f6bed19d0022fd3d1ecc2f5f820723717a675c',
 'tasks/tasks.json':'6dd19c7762f164e1e19b5b6971149890b9f1d9750ef6f8f02f050bc48284bb0d'}
for name,digest in unrelated.items():assert sha(repo/name)==digest
mirror_rows=load(root/'verification/document-mirror-readback.json')['mirrors']
for row in mirror_rows:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
state=load(root.parent/'current-run.json');assert state['e03_positive_passed']==3 and state['e03_negative_passed'] is False
assert state['next_action_scope']['actual_case_allocation']==state['next_action_scope']['actual_result_review_allocation']==0
assert state['preparation_tests_passed']==255 and state['preparation_review']=='PASS' and not state['acceptance_entry_authority_issued']
tag='ultimaagent-t2-e03-source13-negative-prep-20261106'
for checkout in (repo,mirror):
    assert subprocess.run(['git','-C',str(checkout),'rev-parse','--verify','--quiet','refs/tags/'+tag],capture_output=True).returncode!=0
main_before=git(repo,'rev-parse','HEAD');mirror_before=git(mirror,'rev-parse','HEAD')
external=git(repo,'diff','--name-only','650d09e2fb5c145214b1b28e74126ef264f8ecaf..HEAD').splitlines()
assert all(name.startswith('docs/') for name in external),external
receipt=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=source['candidate'],candidate_clean=True,
 main_before=main_before,mirror_before=mirror_before,external_commits_paths_preserved=external,unrelated_tracked_preserved=unrelated,
 manifest_sha256=sha(root/'manifest.json'),sealed_files=len(manifest['files']),seal_mismatches=0,parent_seal_unchanged=True,
 review_sha256=sha(root/'independent-preparation-review.json'),original_review_sha256=review['original_review_sha256'],review_verdict='PASS',
 current_tests=255,model_calls=0,actual_cases=0,audio_actions=0,authority_issued=False,positive=3,negative_passed=False,T2='NOT_PASSED',
 mirrors=mirror_rows,tag=tag,remote_synced=False,new_push_attempted=False,
 finishing_ruling='Existing local checkpoint and preserved candidate are the integration choice; no repeat merge/PR menu or worktree cleanup. Relevant isolated full suite255 passed; unchanged product485/8 gates not rerun.')
p=root/'verification/precommit-readback.json';assert not p.exists();p.write_bytes((json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
paths={root/'manifest.json',root/'independent-preparation-review-original.json',root/'independent-preparation-review.json'}
paths.update(root/row['path'] for row in manifest['files'])
paths.update(p for directory in ('history','verification') for p in (root/directory).iterdir() if p.is_file())
paths.update(p for p in recovery.rglob('*') if p.is_file())
paths.update([root.parent/'current-run.json',repo/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',repo/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(Path(row['source']) for row in mirror_rows)
relative=sorted(p.relative_to(repo).as_posix() for p in paths)
assert all(p.is_file() for p in paths) and not any(name in unrelated for name in relative)
assert git(repo,'rev-parse','HEAD')==main_before and git(mirror,'rev-parse','HEAD')==mirror_before
p=root/'verification/staging-paths.json';assert not p.exists();p.write_bytes((json.dumps(relative,ensure_ascii=False,indent=2)+'\n').encode('utf-8'))
relative.append(p.relative_to(repo).as_posix())
subprocess.run(['git','-C',str(repo),'-c','core.autocrlf=false','add','-f','--',*relative],check=True)
actual=git(repo,'diff','--cached','--name-only','--no-renames').splitlines();assert set(actual)==set(relative),set(actual)^set(relative)
check=subprocess.run(['git','-C',str(repo),'-c','core.whitespace=blank-at-eol,blank-at-eof,space-before-tab,cr-at-eol','diff','--cached','--check'],capture_output=True,text=True,encoding='utf-8')
print(json.dumps({'main_before':main_before,'files_staged':len(actual),'whitespace_exit':check.returncode,'whitespace_output':check.stdout[:2500]},ensure_ascii=False))
assert check.returncode==0
