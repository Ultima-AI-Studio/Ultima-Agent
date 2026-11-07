"""Publish only exact reviewed/offline evidence paths, then read both commits."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent')
TAG='ultimaagent-e02-native-rejection-ready-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
manifest=json.loads((N/'manifest.json').read_bytes());closeout=json.loads((N/'verification/closeout-registration.json').read_bytes())
assert closeout['candidate']==manifest['candidate']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in json.loads((N/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==digest,name
assert not git(C,'status','--porcelain').strip()
assert not git(R,'diff','--cached','--name-only').strip() and not git(M,'diff','--cached','--name-only').strip()
project={N/name for name in manifest['files']}
project.update(p for p in (N/'review').iterdir() if p.is_file())
project.update([N/'manifest.json',N/'completion-report.md',N/'verification/closeout.py',Path(__file__),N/'verification/closeout-registration.json'])
project.update([N/'verification/queue-refresh.json',N/'verification/queue-status-after.json'])
project.update(p for p in (N/'verification/closeout-before').iterdir() if p.is_file())
project.update([R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',N/'progress.md'])
project.update(Path(v['source']) for v in closeout['mirror'])
mirror={Path(v['target']) for v in closeout['mirror']}
pathspec=N/'verification/publication-pathspec.txt';project.add(pathspec)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
for v in closeout['mirror']:assert sha(Path(v['source']))==sha(Path(v['target']))==v['sha256']
before=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip())
assert before['project']=='808ed5ca844f8b15afdcf3615bf4e3c16ea3f6a9'
assert before['mirror']=='1cfcff15f640fbdffe8a041360ea28ac1db3a36a'
file_hashes={str(p):sha(p) for p in project|mirror}
git(R,'add','-f','--pathspec-from-file='+str(pathspec))
expected={p.relative_to(R).as_posix() for p in project}
actual=set(git(R,'diff','--cached','--name-only').decode().splitlines())
# Some byte-identical already tracked inputs may legitimately not appear in diff.
assert actual<=expected and actual
# Preserve exact raw receipts/upstream snapshots, including their original whitespace.
git(R,'diff','--cached','--check','--',*[Path(v['source']).relative_to(R).as_posix() for v in closeout['mirror']])
git(R,'commit','-m','docs(e02): seal bounded native response rejection diagnostics')
git(R,'tag',TAG)
git(M,'add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
assert set(git(M,'diff','--cached','--name-only').decode().splitlines())=={p.relative_to(M).as_posix() for p in mirror}
git(M,'diff','--cached','--check')
git(M,'commit','-m','docs(e02): mirror bounded native response rejection diagnostics')
git(M,'tag',TAG)
heads=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip(),candidate=git(C,'rev-parse','HEAD').decode().strip())
for root,paths,head in [(R,project,heads['project']),(M,mirror,heads['mirror'])]:
    assert git(root,'rev-parse',TAG).decode().strip()==head
    for p in paths:
        assert sha(p)==file_hashes[str(p)],str(p)
        assert git(root,'show',head+':'+p.relative_to(root).as_posix())==p.read_bytes(),str(p)
assert not git(C,'status','--porcelain').strip()
for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():assert sha(R/name)==digest,name
save(N/'verification/publication-readback.json',dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=file_hashes,manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),candidate_clean=True,foreign_files_unchanged=9,actual_cases=0,model_calls=0,remote_synced=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry this turn'))
print(json.dumps(dict(heads=heads,tag=TAG,project_members=len(project),mirror_members=len(mirror),verdict='PASS_LOCAL_PUBLICATION_READBACK',remote_synced=False)))
