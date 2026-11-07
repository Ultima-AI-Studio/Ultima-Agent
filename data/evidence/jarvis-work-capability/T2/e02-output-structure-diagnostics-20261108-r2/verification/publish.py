"""Local exact-path publication and batch blob readback, with no push."""
from pathlib import Path
import datetime as dt,importlib.util,json,subprocess
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,R,T,C,git,sha,load,save=v.N,v.R,v.T,v.C,v.git,v.sha,v.load,v.save
M=Path('H:/UltimaAI/ultima-docs-repo');TAG='ultimaagent-e02-output-structure-ready-20261108-r2'
manifest=load(N/'manifest.json');close=load(N/'verification/closeout-registration.json')
review=load(N/'review/independent-preparation-review.json')
assert close['candidate']==manifest['candidate']==review['candidate'] and review['verdict']=='PASS_PREPARATION_ONLY'
assert close['manifest_sha256']==review['manifest_sha256']==sha(N/'manifest.json')
for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
for name,h in close['after'].items():assert sha(name)==h,name
for item in close['mirror']:assert sha(item['source'])==sha(item['target'])==item['sha256']
assert not git(C,'status','--porcelain').strip()
for root in (R,M):
    assert not git(root,'diff','--cached','--name-only').strip()
    assert not git(root,'tag','--list',TAG).strip()
project={N/name for name in manifest['files']}
prior=Path(load(N/'inputs/predecessor.json')['root'])
for name,h in load(prior/'manifest.json')['files'].items():assert sha(prior/name)==h,name
project.update(prior/name for name in load(prior/'manifest.json')['files'])
project.update([prior/'manifest.json',prior/'review/independent-preparation-review.json',prior/'review/independent-preparation-review.md'])
project.update(p for p in (N/'review').iterdir() if p.is_file())
project.update(p for p in (N/'verification').rglob('*') if p.is_file() and '__pycache__' not in p.parts)
project.update([N/'manifest.json',N/'completion-report.md',T/'current-run.json',
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
project.update(Path(item['source']) for item in close['mirror']);mirror={Path(item['target']) for item in close['mirror']}
for p in project:assert p.resolve().is_relative_to(R.resolve())
supplement=N/'verification/publication-supplement.json'
save(supplement,dict(files={str(p):sha(p) for p in project|mirror},manifest_sha256=sha(N/'manifest.json'),
    reviewed_candidate=manifest['candidate'],review_sha256=sha(N/'review/independent-preparation-review.json'),
    scope='local bookkeeping and mirror only; no new product/actual authority'))
project.add(supplement)
pathspec=N/'verification/publication-pathspec.txt';project.add(pathspec)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
hashes={str(p):sha(p) for p in project|mirror}
before={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M)]}
assert before==dict(project='568b759ca57ab8b4969392eea8c9827a1047d8fb',mirror='6850e6d813e56d72459ad29aedb4f848aa8b07d3'),before
git(R,'--literal-pathspecs','add','-f','--pathspec-from-file='+str(pathspec))
staged=set(git(R,'diff','--cached','--name-only').decode().splitlines());expected={p.relative_to(R).as_posix() for p in project}
assert staged<=expected and staged
# Historical snapshots retain their original bytes and whitespace.
git(R,'-c','core.whitespace=cr-at-eol','diff','--cached','--check','--',*[Path(x['source']).relative_to(R).as_posix() for x in close['mirror']])
git(R,'commit','-m','docs(e02): seal bounded output structure diagnostics preparation');git(R,'tag',TAG)
git(M,'--literal-pathspecs','add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
assert set(git(M,'diff','--cached','--name-only').decode().splitlines())=={p.relative_to(M).as_posix() for p in mirror}
git(M,'-c','core.whitespace=cr-at-eol','diff','--cached','--check')
git(M,'commit','-m','docs(e02): mirror output structure diagnostic preparation');git(M,'tag',TAG)
heads={label:git(root,'rev-parse','HEAD').decode().strip() for label,root in [('project',R),('mirror',M),('candidate',C)]}
def readback(root,paths,head):
    paths=sorted(paths);requests=''.join(head+':'+p.relative_to(root).as_posix()+'\n' for p in paths).encode('utf8')
    result=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=requests,capture_output=True,
        timeout=60,creationflags=subprocess.CREATE_NO_WINDOW)
    assert result.returncode==0,result.stderr
    output=result.stdout;cursor=0
    for p in paths:
        end=output.index(b'\n',cursor);header=output[cursor:end].split();assert len(header)==3 and header[1]==b'blob',p
        size=int(header[2]);start=end+1;data=output[start:start+size];assert data==p.read_bytes() and sha(p)==hashes[str(p)],p
        cursor=start+size;assert output[cursor:cursor+1]==b'\n';cursor+=1
    assert cursor==len(output)
for root,paths,key in [(R,project,'project'),(M,mirror,'mirror')]:
    assert git(root,'rev-parse',TAG).decode().strip()==heads[key]
    readback(root,paths,heads[key])
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
state=load(T/'current-run.json');assert state['last_actual_result']==load(N/'inputs/registration-before/0')['last_actual_result']
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert heads['candidate']==manifest['candidate'] and not git(C,'status','--porcelain').strip()
save(N/'verification/publication-readback.json',dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,tag=TAG,
    project_members=len(project),mirror_members=len(mirror),file_sha256=hashes,candidate_clean=True,
    manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),
    last_actual_result_unchanged=True,foreign_files_unchanged=15,actual_cases=0,model_calls=0,
    remote_synced=False,new_push_attempted=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry'))
print(json.dumps(dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',heads=heads,tag=TAG,project_members=len(project),mirror_members=len(mirror))))
