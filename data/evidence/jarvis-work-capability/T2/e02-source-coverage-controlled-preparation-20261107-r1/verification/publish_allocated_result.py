"""Commit exact first-result and reviewed conclusion paths; local-only publication."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')
TAG='ultimaagent-e02-source-coverage-controlled-result-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
closeout=load(N/'verification/result-closeout-registration.json');review=load(N/'review/independent-result-review.json')
assert review['verdict']=='FAIL_CONFIRMED' and closeout['review_sha256']==sha(N/'review/independent-result-review.json')
manifest=load(N/'review/result-inputs/result-manifest.json')
assert closeout['result_manifest_sha256']==sha(N/'review/result-inputs/result-manifest.json')==review['result_manifest_sha256']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
module('final_current_entry',N/'code/entry.py').read_ready(N)
preservation=module('final_current_preservation',N/'verification/verify_preservation.py').verify()
assert not git(R,'diff','--cached','--name-only').strip() and not git(M,'diff','--cached','--name-only').strip()
project={N/name for name in manifest['files']}
project.update(N/name for name in ('verification/allocation-program-bindings.json','review/result-audit-queue-refresh.json'))
project.update(N/name for name in ('review/result-inputs/result-manifest.json','review/independent-result-review.json',
    'review/independent-result-review.md','review/result-review-allocation.json','review/result-registration.json',
    'verification/register_reviewed_result.py','verification/result-closeout-registration.json','verification/publish_allocated_result.py',
    'verification/allocation-queue-refresh.json','verification/result-audit-registration.json',
    'verification/result-queue-refresh.json','verification/result-queue-status.json'))
for directory in ('allocation-before','result-audit-before','result-closeout-before'):
    project.update(p for p in (N/'verification'/directory).iterdir() if p.is_file())
project.update([R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',R/'.superpowers/sdd/jarvis-work-e02-source-coverage-controlled-entry-plan-20261107/progress.md'])
project.update(Path(row['source']) for row in closeout['mirror'])
mirror={Path(row['target']) for row in closeout['mirror']}
for row in closeout['mirror']:assert sha(Path(row['source']))==sha(Path(row['target']))==row['sha256']
pathspec=N/'verification/result-publication-pathspec.txt';project.add(pathspec)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
before=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip())
assert before==dict(project='a963581887529175b5cf4be4c7db547e32cf0e57',mirror='a74d0921b7d96eff7b7737e073cf2e24ad0c8679')
hashes={str(p):sha(p) for p in project|mirror}
git(R,'add','-f','--pathspec-from-file='+str(pathspec))
expected={p.relative_to(R).as_posix() for p in project};actual=set(git(R,'diff','--cached','--name-only').decode().splitlines())
assert actual and actual<=expected
git(R,'diff','--cached','--check','--',*[Path(row['source']).relative_to(R).as_posix() for row in closeout['mirror']])
git(R,'commit','-m','docs(e02): preserve coverage repair outcome and native HTTP500 review')
git(R,'tag',TAG)
git(M,'add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
assert set(git(M,'diff','--cached','--name-only').decode().splitlines())=={p.relative_to(M).as_posix() for p in mirror}
git(M,'diff','--cached','--check')
git(M,'commit','-m','docs(e02): mirror coverage result and native HTTP500 follow-up')
git(M,'tag',TAG)
heads=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip(),candidate=git(C,'rev-parse','HEAD').decode().strip())
assert heads['candidate']=='e40a55b40c223181040dbb6a09d0c4d2da5026cf' and not git(C,'status','--porcelain').strip()
for root,paths,head in [(R,project,heads['project']),(M,mirror,heads['mirror'])]:
    assert git(root,'rev-parse',TAG).decode().strip()==head
    for p in paths:
        assert sha(p)==hashes[str(p)] and git(root,'show',head+':'+p.relative_to(root).as_posix())==p.read_bytes(),str(p)
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
save(N/'verification/result-publication-readback.json',dict(verdict='PASS_LOCAL_RESULT_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    heads=heads,previous_heads=before,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=hashes,
    result_manifest_sha256=sha(N/'review/result-inputs/result-manifest.json'),review_sha256=sha(N/'review/independent-result-review.json'),
    candidate_clean=True,foreign_files_unchanged=9,actual_case_invocations=1,native_post_attempts=7,actual_native_start_count=None,
    model_calls_by_publication=0,actual_remaining=0,result_review_remaining=0,acceptance_credit=0,E02='NOT_PASSED',T2='NOT_PASSED',
    remote_synced=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry this turn'))
print(json.dumps(dict(verdict='PASS_LOCAL_RESULT_PUBLICATION_READBACK',heads=heads,tag=TAG,project_members=len(project),mirror_members=len(mirror),actual_remaining=0,result_review_remaining=0,remote_synced=False)))
