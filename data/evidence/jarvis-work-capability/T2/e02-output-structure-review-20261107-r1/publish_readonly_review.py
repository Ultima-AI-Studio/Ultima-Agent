"""Publish only this audit's local files and verify exact byte readback."""
from pathlib import Path
import datetime, hashlib, json, subprocess

R=Path('H:/UltimaAI/UltimaAgent')
M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-output-structure-review-20261107-r1'
TAG='ultimaagent-e02-output-structure-review-20261107'
HEAD='0421a54cab572be013c3f7ad562e86406bfe8e52'
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path):return json.loads(Path(path).read_bytes())
def save(path,value):
    with Path(path).open('x',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
def git(root,*args):
    p=subprocess.run(['git','-C',str(root),*args],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=60)
    if p.returncode:raise RuntimeError(p.stderr.decode('utf8','replace'))
    return p.stdout

assert git(C,'rev-parse','HEAD').decode().strip()==HEAD
assert not git(C,'status','--porcelain=v1','--untracked-files=normal').strip()
assert not git(R,'diff','--cached','--name-only').strip()
assert not git(M,'diff','--cached','--name-only').strip()
for root in (R,M):assert not git(root,'tag','--list',TAG).strip()
for name,h in load(N/'input-hashes.json')['files'].items():assert sha(name)==h,name
close=load(N/'closeout.json')
for name,h in close['files'].items():assert sha(name)==h,name
for name,h in close['mirrors'].items():assert sha(name)==h,name
foreign=load(T/'e02-output-budget-controlled-preparation-20261107-r1/inputs/unrelated-working-tree.json')['files']
for name,h in foreign.items():assert sha(R/name)==h,name
save(N/'current-run-at-closeout.json',load(T/'current-run.json'))
docs=[Path(name) for name in close['files'] if '/docs/' in name.replace('\\','/')]
audit_files=sorted(p for p in N.rglob('*') if p.is_file())
for p in audit_files:assert p.resolve().is_relative_to(N.resolve())
manifest=dict(kind='ROOT_READONLY_OUTPUT_STRUCTURE_REVIEW',independent_review=False,
    candidate=HEAD,recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    files={str(p):sha(p) for p in audit_files+docs},
    product_changes=0,actual_cases=0,model_calls=0,acceptance_credit=0)
save(N/'manifest.json',manifest)
project_files=audit_files+[N/'manifest.json']+docs+[
    T/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
project_rel=sorted({p.relative_to(R).as_posix() for p in project_files})
mirror_rel=sorted(Path(p).relative_to(M).as_posix() for p in close['mirrors'])
heads_before={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M)]}
for root,paths in [(R,project_rel),(M,mirror_rel)]:
    git(root,'--literal-pathspecs','add','--',*paths)
    staged={p for p in git(root,'diff','--cached','--name-only','-z').decode('utf8').split('\0') if p}
    assert staged==set(paths),(root,staged.symmetric_difference(paths))
    git(root,'diff','--cached','--check')
git(R,'commit','-m','docs: audit E02 output structure and bounded diagnostics')
git(M,'commit','-m','docs: mirror E02 output structure audit and diagnostic proposal')
heads={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M)]}
for root in (R,M):git(root,'tag',TAG)
for root,paths in [(R,project_rel),(M,mirror_rel)]:
    assert git(root,'rev-parse',TAG).decode().strip()==git(root,'rev-parse','HEAD').decode().strip()
    for name in paths:assert git(root,'show','HEAD:'+name)==(root/name).read_bytes(),name
for name,h in manifest['files'].items():assert sha(name)==h,name
for name,h in foreign.items():assert sha(R/name)==h,name
assert git(C,'rev-parse','HEAD').decode().strip()==HEAD
assert not git(C,'status','--porcelain=v1','--untracked-files=normal').strip()
state=load(T/'current-run.json'); old=load(N/'history/current-run-before.json')
assert state['last_actual_result']==old['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
save(N/'publication-readback.json',dict(status='PASS_LOCAL_AUDIT_PUBLICATION_READBACK',
    recorded_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    heads=heads,heads_before=heads_before,tag=TAG,manifest_sha256=sha(N/'manifest.json'),
    project_members=len(project_rel),mirror_members=len(mirror_rel),
    candidate=HEAD,candidate_clean=True,foreign_tracked_files_preserved=len(foreign),
    last_actual_result_unchanged=True,new_product_changes=0,new_actual_cases=0,new_model_calls=0,
    independent_review=False,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED',
    remote_synced=False,remote_reason='Previous automatic approval rejected push; not retried'))
print(json.dumps(dict(status='PASS_LOCAL_AUDIT_PUBLICATION_READBACK',heads=heads,tag=TAG,
    project_members=len(project_rel),mirror_members=len(mirror_rel),candidate_clean=True),ensure_ascii=False))
