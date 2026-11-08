"""Publish only this allocated result and verify exact Git/disk evidence bytes."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo');A=N/'actual/E02-controlled-1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
HEAD='43da3f014a763b8ea3963872a8f1ce8ebea77531'
RUN='d0109d12-520f-4f92-88a3-938e69905ba2'
TAG='ultimaagent-e02-source-grounding-controlled-result-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def names(raw):return {x.decode('utf8') for x in raw.split(b'\0') if x}
def git_bytes(root,head,paths):
    paths=sorted(paths);queries=[(head+':'+p.relative_to(root).as_posix()).encode('utf8') for p in paths]
    result=subprocess.run(['git','-C',str(root),'cat-file','--batch'],input=b'\n'.join(queries)+b'\n',capture_output=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    offset=0
    for p in paths:
        end=result.stdout.index(b'\n',offset);header=result.stdout[offset:end].split()
        assert len(header)==3 and header[1]==b'blob',p
        size=int(header[2]);start=end+1
        assert result.stdout[start:start+size]==p.read_bytes() and result.stdout[start+size:start+size+1]==b'\n',p
        offset=start+size+1
    assert offset==len(result.stdout)
def verify_members(root,path):
    for name,h in load(path)['files'].items():assert sha(root/name)==h,name

assert not (N/'verification/result-publication-readback.json').exists()
review=load(N/'review/independent-result-review.json');closeout=load(N/'verification/result-closeout-registration.json')
manifest=load(N/'review/result-inputs/result-manifest.json');prep=load(N/'verification/publication-readback.json')
assert review['reviewer']=='root-independent' and review['candidate']==HEAD and review['run_id']==RUN
assert review['result_manifest_sha256']==sha(N/'review/result-inputs/result-manifest.json')==closeout['result_manifest_sha256']
assert closeout['review_sha256']==sha(N/'review/independent-result-review.json')
assert closeout['review_markdown_sha256']==sha(N/'review/independent-result-review.md')
assert review['actual_run_authorized'] is False and review['acceptance_credit'] in (0,1)
for root,path in ((N,N/'manifest.json'),(N,N/'review/result-inputs/result-manifest.json'),(A,A/'seal-index.json')):verify_members(root,path)
spec=importlib.util.spec_from_file_location('result_preservation',N/'verification/verify_result_preservation.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
preserved=v.verify()
assert not git(C,'status','--porcelain').strip() and git(C,'rev-parse','HEAD').decode().strip()==HEAD
for root in (R,M):
    assert not git(root,'diff','--cached','--name-only','-z')
    assert not git(root,'tag','--list',TAG).strip()
project={N/name for name in manifest['files']}
project.update(p for p in (N/'verification').iterdir() if p.is_file())
project.update(p for p in (N/'review').iterdir() if p.is_file())
project.add(N/'review/result-inputs/result-manifest.json')
for folder in ('allocation-before','result-audit-before','result-closeout-before','skill-ledger-closeout'):
    project.update(p for p in (N/'verification'/folder).iterdir() if p.is_file())
project.update((N.parent/'current-run.json',N/'progress.md',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'))
project.update(Path(x['source']) for x in closeout['mirror']);mirror={Path(x['target']) for x in closeout['mirror']}
for row in closeout['mirror']:assert sha(Path(row['source']))==sha(Path(row['target']))==row['sha256']
pathspec=N/'verification/result-publication-pathspec.txt';project.add(pathspec)
for root,paths in ((R,project),(M,mirror)):
    assert all(p.resolve().is_relative_to(root.resolve()) for p in paths)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
before={key:git(root,'rev-parse','HEAD').decode().strip() for root,key in ((R,'project'),(M,'mirror'))}
concurrent={}
for root,key,paths in ((R,'project',project),(M,'mirror',mirror)):
    git(root,'merge-base','--is-ancestor',prep['heads'][key],before[key])
    changed=names(git(root,'diff','--name-only','-z',prep['heads'][key],before[key]))
    assert not changed & {p.relative_to(root).as_posix() for p in paths},key
    concurrent[key]=sorted(changed)
hashes={str(p):sha(p) for p in project|mirror};heads={'candidate':HEAD}
for root,key,paths in ((R,'project',project),(M,'mirror',mirror)):
    if root==R:git(root,'add','-f','--pathspec-from-file='+str(pathspec))
    else:git(root,'add','--',*[p.relative_to(root).as_posix() for p in sorted(paths)])
    staged=names(git(root,'diff','--cached','--name-only','-z'))
    assert staged and staged<={p.relative_to(root).as_posix() for p in paths}
    docs=[Path(row['source' if root==R else 'target']).relative_to(root).as_posix() for row in closeout['mirror']]
    git(root,'diff','--cached','--check','--',*docs)
    assert git(root,'rev-parse','HEAD').decode().strip()==before[key]
    git_bytes(root,'',paths)
    assert names(git(root,'diff','--cached','--name-only','-z'))==staged
    git(root,'commit','-q','-m','docs(e02): preserve single source-grounding result and independent review')
    head=git(root,'rev-parse','HEAD').decode().strip()
    assert git(root,'rev-parse',head+'^').decode().strip()==before[key]
    assert names(git(root,'diff-tree','--no-commit-id','--name-only','-r','-z',head))==staged
    git(root,'tag',TAG,head);heads[key]=head
    git_bytes(root,head,paths)
    for p in paths:assert sha(p)==hashes[str(p)],str(p)
publication=dict(verdict='PASS_LOCAL_RESULT_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,concurrent_nonoverlapping_changes=concurrent,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=hashes,result_manifest_sha256=sha(N/'review/result-inputs/result-manifest.json'),review_sha256=sha(N/'review/independent-result-review.json'),result_verdict=review['verdict'],acceptance_credit=review['acceptance_credit'],actual_case_invocations=1,retry=0,actual_remaining=0,result_review_remaining=0,model_calls_by_publication=0,global_aggregate_refreshed=False,remote_synced=False)
save(N/'verification/result-publication-readback.json',publication)
state=load(N.parent/'current-run.json');actual=state['last_actual_result']
assert actual['run_id']==RUN and actual['candidate']==HEAD and actual['question_id']=='call_7004c6eafaca48e3a6f19dd87f59d024'
assert actual['independent_review']==review['verdict'] and actual['acceptance_credit']==review['acceptance_credit']
assert state['previous_actual_result']==load(N/'verification/result-closeout-before/0-current-run.json')['last_actual_result']
assert state['previous_actual_result']['run_id']=='1496a844-668d-407a-a91b-89be246ba05b'
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
assert not state['live_gate_released'] and not state['next_stage_released'] and state['active_review_agent'] is None
assert state['goal_status']=='none' and state['goal_registry_status']=='cleared_by_user'
assert load(N/'release/tool-execution-receipt.json')['invocations']==1
assert load(N/'release/consumed.json')['retry']==0 and load(N/'review/result-review-allocation.json')['remaining']==0
assert state['queue_status_refresh']['aggregate_regenerated'] is False
for root,path in ((N,N/'manifest.json'),(N,N/'review/result-inputs/result-manifest.json'),(A,A/'seal-index.json')):verify_members(root,path)
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
assert not git(C,'status','--porcelain').strip()
for root,key,paths in ((R,'project',project),(M,'mirror',mirror)):
    assert git(root,'rev-parse',TAG).decode().strip()==heads[key]
    git(root,'merge-base','--is-ancestor',heads[key],'HEAD')
    assert not names(git(root,'diff','--name-only','-z',heads[key],'HEAD')) & {p.relative_to(root).as_posix() for p in paths}
    assert not git(root,'diff','--cached','--name-only','-z')
    git_bytes(root,heads[key],paths)
value=dict(verdict='PASS_POST_COMMIT_RESULT_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,tag=TAG,run_id=RUN,result=review['verdict'],result_manifest_sha256=sha(N/'review/result-inputs/result-manifest.json'),review_sha256=sha(N/'review/independent-result-review.json'),publication_receipt_sha256=sha(N/'verification/result-publication-readback.json'),result_members=len(manifest['files']),actual_seal_members=len(load(A/'seal-index.json')['files']),preparation_preserved=True,previous_actual_preserved=True,preservation_counts=preserved['member_counts'],entry_invocations=1,retry=0,actual_case_allocation=0,result_review_allocation=0,acceptance_credit=review['acceptance_credit'],E02=state['e02'],T2=state['t2'],Owner='NOT_PASSED',global_aggregate_refreshed=False,remote_synced=False,model_or_runtime_calls_by_readback=0)
save(N/'verification/result-final-readback.json',value)
print(json.dumps(value,ensure_ascii=False))
