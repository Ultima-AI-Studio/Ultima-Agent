"""Finish publication; byte-preserved historical snapshots are not reformatted."""
from pathlib import Path
import datetime, hashlib, json, subprocess

R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
T=R/'data/evidence/jarvis-work-capability/T2';N=T/'e02-output-structure-review-20261107-r1'
TAG='ultimaagent-e02-output-structure-review-20261107';HEAD='0421a54cab572be013c3f7ad562e86406bfe8e52'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(root,*args):
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
    if p.returncode:raise RuntimeError((p.stderr+p.stdout)[-2000:].decode('utf8','replace'))
    return p.stdout
def staged(root):return {p for p in git(root,'diff','--cached','--name-only','-z').decode('utf8').split('\0') if p}

manifest=load(N/'manifest.json');close=load(N/'closeout.json')
for name,h in manifest['files'].items():assert sha(name)==h,name
for name,h in load(N/'input-hashes.json')['files'].items():assert sha(name)==h,name
for name,h in close['files'].items():assert sha(name)==h,name
for name,h in close['mirrors'].items():assert sha(name)==h,name
before_heads={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M)]}
assert before_heads==dict(project='ab4b5209656437153e41b9437190c48ab2b3f321',mirror='5925b3c757ba96673d2b59c42b9282d02d1a57bb')
original_files=[Path(p) for p in manifest['files']]+[N/'manifest.json',T/'current-run.json',
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
assert staged(R)=={p.relative_to(R).as_posix() for p in original_files}
assert not staged(M)
for root in (R,M):assert not git(root,'tag','--list',TAG).strip()
# These are original bytes pinned before this audit, not authored whitespace.
prior=load(N/'scope.json')['registration_before']
for label,p in [('global',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')),
    ('work-order',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'),
    ('stage',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md')]:
    assert sha(N/'history'/f'{label}-before{p.suffix}')==prior[str(p)]
save(N/'publication-preflight-note.json',dict(recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    initial_status='STOPPED_BEFORE_COMMIT_AT_GIT_DIFF_CHECK',
    cause='Byte-identical historical snapshots contain CRLF and historical blank EOF lines; original bytes deliberately preserved',
    correction='Verify snapshot hashes; check all authored and current changed paths with CR recognized as line ending, excluding history copies only',
    source_or_product_change=False,initial_commits=0,remote_attempts=0))
save(N/'publication-supplement.json',dict(manifest_sha256=sha(N/'manifest.json'),
    files={str(p):sha(p) for p in (N/'resume_local_publication.py',N/'publication-preflight-note.json')}))
files=original_files+[N/'resume_local_publication.py',N/'publication-preflight-note.json',N/'publication-supplement.json']
project_rel=sorted({p.relative_to(R).as_posix() for p in files})
mirror_rel=sorted(Path(p).relative_to(M).as_posix() for p in close['mirrors'])
for root,paths in [(R,project_rel),(M,mirror_rel)]:
    git(root,'--literal-pathspecs','add','--',*paths)
    assert staged(root)==set(paths)
    authored=[p for p in paths if '/history/' not in p]
    git(root,'-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',*authored)
git(R,'commit','-m','docs: audit E02 output structure and bounded diagnostics')
git(M,'commit','-m','docs: mirror E02 output structure audit and diagnostic proposal')
heads={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M)]}
for root in (R,M):git(root,'tag',TAG)
for root,paths in [(R,project_rel),(M,mirror_rel)]:
    assert git(root,'rev-parse',TAG).decode().strip()==git(root,'rev-parse','HEAD').decode().strip()
    for name in paths:assert git(root,'show','HEAD:'+name)==(root/name).read_bytes(),name
for name,h in manifest['files'].items():assert sha(name)==h,name
foreign=load(T/'e02-output-budget-controlled-preparation-20261107-r1/inputs/unrelated-working-tree.json')['files']
for name,h in foreign.items():assert sha(R/name)==h,name
assert git(C,'rev-parse','HEAD').decode().strip()==HEAD
assert not git(C,'status','--porcelain=v1','--untracked-files=normal').strip()
state=load(T/'current-run.json');old=load(N/'history/current-run-before.json')
assert state['last_actual_result']==old['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
value=dict(status='PASS_LOCAL_AUDIT_PUBLICATION_READBACK',recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    heads=heads,heads_before=before_heads,tag=TAG,manifest_sha256=sha(N/'manifest.json'),
    publication_supplement_sha256=sha(N/'publication-supplement.json'),
    project_members=len(project_rel),mirror_members=len(mirror_rel),candidate=HEAD,candidate_clean=True,
    foreign_tracked_files_preserved=len(foreign),last_actual_result_unchanged=True,
    new_product_changes=0,new_actual_cases=0,new_model_calls=0,independent_review=False,
    E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',remote_synced=False,
    remote_reason='Previous automatic approval rejected push; no retry or alternate channel')
save(N/'publication-readback.json',value)
print(json.dumps(dict(status=value['status'],heads=heads,tag=TAG,project_members=len(project_rel),mirror_members=len(mirror_rel),candidate_clean=True),ensure_ascii=False))
