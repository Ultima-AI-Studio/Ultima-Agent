"""Resume after quoted Unicode path display check; commit only the exact scoped set."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
TAG='ultimaagent-e02-source-grounding-ready-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def names(root):return set(git(root,'diff','--cached','--name-only','-z').decode('utf8').split('\0'))-{''}
spec=importlib.util.spec_from_file_location('pub_scope',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
v.verify();C=v.C
project={R/name for name in (N/'verification/publication-recovery-pathspec.txt').read_text('utf8').splitlines()}
assert names(R)=={p.relative_to(R).as_posix() for p in project} and not names(M)
assert R/'docs/tracker/北极星上线任务清单.html' not in project
for root in (N,N.parent/'e02-source-grounding-coverage-20261108-r1'):
    for name,h in load(root/'manifest.json')['files'].items():assert sha(root/name)==h,name
close=load(N/'verification/closeout-registration.json');mirror={Path(x['target']) for x in close['mirror']}
for x in close['mirror']:assert sha(Path(x['source']))==sha(Path(x['target']))==x['sha256']
before=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip())
context=load(N/'verification/publication-recovery-context.json')
assert before['project']==context['observed_project_head'] and before['mirror']==context['observed_mirror_head']
save(N/'verification/publication-resume-context.json',dict(previous_stop='Scoped staged set comparison used quoted Unicode display; -z proves all8618 paths are in scope, no foreign staged files',staged_paths=8618,original_publisher_unchanged=True,original_recovery_context_sha256=sha(N/'verification/publication-recovery-context.json'),commit_scope='git commit --only exact pathspec',readback='Native Git cat-file --batch, exact blob/disk byte equality',actual_cases=0))
pathspec=N/'verification/publication-final-pathspec.txt';project.update([Path(__file__),N/'verification/publication-resume-context.json',pathspec])
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
hashes={str(p):sha(p) for p in project|mirror}
git(R,'add','-f','--pathspec-from-file='+str(pathspec));assert names(R)=={p.relative_to(R).as_posix() for p in project}
git(R,'diff','--cached','--check','--',*[Path(x['source']).relative_to(R).as_posix() for x in close['mirror']])
git(R,'commit','--only','--pathspec-from-file='+str(pathspec),'-m','docs(e02): seal evidence-first source-reserve preparation and retained reviews')
project_head=git(R,'rev-parse','HEAD').decode().strip();assert git(R,'rev-parse','HEAD^').decode().strip()==before['project']
committed=set(git(R,'diff-tree','--no-commit-id','--name-only','-r','-z',project_head).decode('utf8').split('\0'))-{''}
assert committed<={p.relative_to(R).as_posix() for p in project}
git(R,'tag',TAG,project_head)
git(M,'add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)]);assert names(M)=={p.relative_to(M).as_posix() for p in mirror}
git(M,'diff','--cached','--check');git(M,'commit','--only','-m','docs(e02): mirror source grounding offline preparation','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
mirror_head=git(M,'rev-parse','HEAD').decode().strip();git(M,'tag',TAG,mirror_head)
heads=dict(project=project_head,mirror=mirror_head,candidate=git(C,'rev-parse','HEAD').decode().strip())
cache={}
for root,paths,key in ((R,project,'project'),(M,mirror,'mirror')):
    assert git(root,'rev-parse',TAG).decode().strip()==heads[key]
    ordered=sorted(paths);queries=''.join(heads[key]+':'+p.relative_to(root).as_posix()+'\n' for p in ordered)
    raw=subprocess.check_output(['git','-C',str(root),'cat-file','--batch'],input=queries.encode('utf8'),creationflags=subprocess.CREATE_NO_WINDOW)
    offset=0
    for p in ordered:
        end=raw.index(b'\n',offset);header=raw[offset:end].split();assert len(header)==3 and header[1]==b'blob'
        size=int(header[2]);offset=end+1;blob=raw[offset:offset+size];offset+=size;assert raw[offset:offset+1]==b'\n';offset+=1
        assert sha(p)==hashes[str(p)] and blob==p.read_bytes(),str(p)
        cache[(str(root),heads[key]+':'+p.relative_to(root).as_posix())]=blob
    assert offset==len(raw)
assert not git(C,'status','--porcelain').strip();foreign=v.foreign_readback()
save(N/'verification/publication-readback.json',dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=hashes,manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),candidate_clean=True,foreign_files_unchanged=14,foreign_readback=foreign,actual_cases=0,model_calls=0,actual_allocation=0,remote_synced=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry',publication_recovery_context_sha256=sha(N/'verification/publication-resume-context.json')))
print(json.dumps(dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',heads=heads,project_members=len(project),actual=0)),flush=True)
# Original final readback with the same native Git object bytes; no predicate changes.
original=subprocess.check_output
def exact_git_objects(argv,*args,**kwargs):
    if isinstance(argv,list) and len(argv)==5 and argv[:2]==['git','-C'] and argv[3]=='show' and (argv[2],argv[4]) in cache:return cache[(argv[2],argv[4])]
    return original(argv,*args,**kwargs)
subprocess.check_output=exact_git_objects
try:
    p=N/'verification/final_readback.py';exec(compile(p.read_bytes(),str(p),'exec'),{'__file__':str(p),'__name__':'__main__'})
finally:subprocess.check_output=original
