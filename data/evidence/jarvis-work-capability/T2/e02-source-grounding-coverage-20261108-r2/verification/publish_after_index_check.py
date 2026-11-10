"""Use original staged-commit method after exact index readback; no process termination."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo');TAG='ultimaagent-e02-source-grounding-ready-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def names(root):return set(git(root,'diff','--cached','--name-only','-z').decode('utf8').split('\0'))-{''}
spec=importlib.util.spec_from_file_location('pub_scope_final',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);v.verify();C=v.C
project={R/name for name in (N/'verification/publication-final-pathspec.txt').read_text('utf8').splitlines()}
assert names(R)=={p.relative_to(R).as_posix() for p in project} and not names(M)
assert R/'docs/tracker/北极星上线任务清单.html' not in project
for root in (N,N.parent/'e02-source-grounding-coverage-20261108-r1'):
    for name,h in load(root/'manifest.json')['files'].items():assert sha(root/name)==h,name
close=load(N/'verification/closeout-registration.json');mirror={Path(x['target']) for x in close['mirror']}
for x in close['mirror']:assert sha(Path(x['source']))==sha(Path(x['target']))==x['sha256']
before=dict(project=git(R,'rev-parse','HEAD').decode().strip(),mirror=git(M,'rev-parse','HEAD').decode().strip())
prior=load(N/'verification/publication-recovery-context.json');assert before['project']==prior['observed_project_head'] and before['mirror']==prior['observed_mirror_head']
save(N/'verification/publication-index-recovery.json',dict(previous_failure='git commit --only failed with malloc allocation error, exit128; no commit created',head_unchanged=before,staged_paths_verified=len(project),foreign_staged_paths=[],system_free_physical_kib_observed=10964736,system_free_virtual_kib_observed=11264336,processes_terminated=0,method='Original reviewed publisher staged-commit method, exact NUL-delimited staged names immediately before commit and exact committed paths afterward',actual_cases=0))
pathspec=N/'verification/publication-commit-pathspec.txt';project.update([Path(__file__),N/'verification/publication-index-recovery.json',pathspec])
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
hashes={str(p):sha(p) for p in project|mirror}
git(R,'add','-f','--pathspec-from-file='+str(pathspec));assert names(R)=={p.relative_to(R).as_posix() for p in project}
assert git(R,'rev-parse','HEAD').decode().strip()==before['project']
tail=(N/'verification/finish_publication.py').read_text('utf8');tail=tail[tail.index("git(R,'commit',"):]
tail=tail.replace("git(R,'commit','--only','--pathspec-from-file='+str(pathspec),'-m'","git(R,'commit','--quiet','-m'",1)
exec(compile(tail,str(N/'verification/finish_publication.py'),'exec'))
