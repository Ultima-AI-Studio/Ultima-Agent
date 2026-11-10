"""Publish only exact reviewed/offline evidence paths, then read both commits."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
TAG='ultimaagent-e02-source-grounding-controlled-ready-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)

def names(raw):return {name.decode('utf8') for name in raw.split(b'\0') if name}

def git_bytes(root,head,paths):
    paths=sorted(paths)
    queries=[(head+':'+p.relative_to(root).as_posix()).encode('utf8') for p in paths]
    result=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=b'\n'.join(queries)+b'\n',capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    offset=0
    for p in paths:
        end=result.stdout.index(b'\n',offset);header=result.stdout[offset:end].split()
        assert len(header)==3 and header[1]==b'blob',p
        size=int(header[2]);start=end+1;raw=result.stdout[start:start+size]
        assert result.stdout[start+size:start+size+1]==b'\n' and raw==p.read_bytes(),str(p)
        offset=start+size+1
    assert offset==len(result.stdout)
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
manifest=json.loads((N/'manifest.json').read_bytes());closeout=json.loads((N/'verification/closeout-registration.json').read_bytes())
assert closeout['candidate']==manifest['candidate']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in json.loads((N/'inputs/input-manifest.json').read_bytes())['files'].items():assert sha(Path(name))==digest,name
assert not git(C,'status','--porcelain').strip()
assert not git(R,'diff','--cached','--name-only','-z') and not git(M,'diff','--cached','--name-only','-z')
project={N/name for name in manifest['files']}
project.update(p for p in (N/'review').iterdir() if p.is_file())
project.update([N/'manifest.json',N/'completion-report.md',N/'verification/closeout.py',Path(__file__),N/'verification/closeout-registration.json',N/'harness-approval.json',N/'verification/ready-readback.json'])
project.update([N/'verification/queue-refresh.json',N/'verification/queue-status-after.json'])
project.update(p for p in (N/'verification/closeout-before').iterdir() if p.is_file())
project.update([R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',N/'progress.md'])
project.update(Path(v['source']) for v in closeout['mirror'])
mirror={Path(v['target']) for v in closeout['mirror']}
pathspec=N/'verification/publication-pathspec.txt';project.add(pathspec)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
for v in closeout['mirror']:assert sha(Path(v['source']))==sha(Path(v['target']))==v['sha256']
before=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip())
product_heads=json.loads((N.parent/'e02-source-grounding-coverage-20261108-r2/verification/publication-readback.json').read_bytes())['heads']
concurrent_changes={}
for root,key,paths in ((R,'project',project),(M,'mirror',mirror)):
    git(root,'merge-base','--is-ancestor',product_heads[key],before[key])
    changed=names(git(root,'diff','--name-only','-z',product_heads[key],before[key]))
    assert not changed & {p.relative_to(root).as_posix() for p in paths},(key,'Concurrent overlapping publication')
    concurrent_changes[key]=sorted(changed)
file_hashes={str(p):sha(p) for p in project|mirror}
git(R,'add','-f','--pathspec-from-file='+str(pathspec))
expected={p.relative_to(R).as_posix() for p in project}
actual=names(git(R,'diff','--cached','--name-only','-z'))
# Some byte-identical already tracked inputs may legitimately not appear in diff.
assert actual<=expected and actual
# Preserve exact raw receipts/upstream snapshots, including their original whitespace.
git(R,'diff','--cached','--check','--',*[Path(v['source']).relative_to(R).as_posix() for v in closeout['mirror']])
assert git(R,'rev-parse','HEAD').decode().strip()==before['project']
assert names(git(R,'diff','--cached','--name-only','-z'))==actual
git_bytes(R,'',project)
git(R,'commit','-q','-m','docs(e02): bind evidence-first source-reserve candidate without actual allocation')
project_head=git(R,'rev-parse','HEAD').decode().strip()
assert git(R,'rev-parse',project_head+'^').decode().strip()==before['project']
assert names(git(R,'diff-tree','--no-commit-id','--name-only','-r','-z',project_head))==actual
git(R,'tag',TAG,project_head)
git(M,'add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
mirror_staged=names(git(M,'diff','--cached','--name-only','-z'))
assert mirror_staged and mirror_staged<={p.relative_to(M).as_posix() for p in mirror}
git(M,'diff','--cached','--check')
assert git(M,'rev-parse','HEAD').decode().strip()==before['mirror']
assert names(git(M,'diff','--cached','--name-only','-z'))==mirror_staged
git_bytes(M,'',mirror)
git(M,'commit','-q','-m','docs(e02): mirror source grounding controlled entry and proposal')
mirror_head=git(M,'rev-parse','HEAD').decode().strip()
assert git(M,'rev-parse',mirror_head+'^').decode().strip()==before['mirror']
assert names(git(M,'diff-tree','--no-commit-id','--name-only','-r','-z',mirror_head))==mirror_staged
git(M,'tag',TAG,mirror_head)
heads=dict(project=project_head,mirror=mirror_head,candidate=git(C,'rev-parse','HEAD').decode().strip())
for root,paths,head in [(R,project,heads['project']),(M,mirror,heads['mirror'])]:
    assert git(root,'rev-parse',TAG).decode().strip()==head
    for p in paths:
        assert sha(p)==file_hashes[str(p)],str(p)
    git_bytes(root,head,paths)
assert not git(C,'status','--porcelain').strip()
for name,digest in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():
    if name!='docs/tracker/北极星上线任务清单.html':assert sha(R/name)==digest,name
save(N/'verification/publication-readback.json',dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,concurrent_nonoverlapping_changes=concurrent_changes,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=file_hashes,manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),candidate_clean=True,foreign_files_unchanged=14,unowned_dynamic_file_excluded_from_write=True,actual_cases=0,model_calls=0,remote_synced=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry this turn'))
print(json.dumps(dict(heads=heads,tag=TAG,project_members=len(project),mirror_members=len(mirror),verdict='PASS_LOCAL_PUBLICATION_READBACK',remote_synced=False)))
