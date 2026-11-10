"""Publish only exact reviewed preparation and its local documentation mirrors."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True,encoding='utf8').strip()
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
spec=importlib.util.spec_from_file_location('prep_publish_entry',N/'code/entry.py');e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
package=e.read_ready(N);manifest=load(N/'manifest.json');
assert load(N/'verification/runtime-readiness-final.json')['candidate']==e.CANDIDATE
assert not (N/'release').exists() and not (N/'actual').exists()
for p,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==h
report=R/'docs/reports/jarvis-work-t2-e02-failure-state-preparation-20261107.md'
assert not report.exists()
report.write_text((N/'preparation-report.md').read_text(encoding='utf8')+'\n\n独立准备审查 PASS_PREPARATION_ONLY；准备 manifest SHA256 '+package['manifest_sha256']+'，审查 SHA256 '+package['review_sha256']+'。封存成员 1058。新提交的只读七保护身份、原生版本和模型核对通过，实际入口未调用。\n',encoding='utf8')
summary='E02候选22653fb：失败终态和选页诊断完成，965项离线与独立准备PASS；已授权诊断单例待执行，随后按证据决定后继修复；原8B/时限保持、失败不重试、旧信用不转移。'
subprocess.run([str(e.PY),'-I','-B','-X','utf8',str(N/'verification/register_progress.py'),'ready','ready_for_one_authorized_case',summary],check=True,stdout=subprocess.DEVNULL)
statepath=N.parent/'current-run.json';state=load(statepath)
state.update(active_candidate=e.CANDIDATE,active_candidate_root='C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent',
    current_e02_controlled_passed=0,active_review_agent=None,
    active_preparation=dict(root=str(N),candidate=e.CANDIDATE,status='PASS_PREPARATION_ONLY',tests=965,product_tests=631,harness_unique_tests=275,interface_tests=59,**package),
    e02_failure_state_preparation=dict(root=str(N),candidate=e.CANDIDATE,status='PASS_PREPARATION_ONLY',tests=965,**package),
    active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False))
state.update(active_report=str(report),active_preparation_root=str(N),preparation_test_count=965,preparation_tests_passed=965,preparation_test_scope='631 product + 275 unique harness + 59 interface',preparation_review_receipt=str(N/'review/independent-preparation-review.json'),preparation_review_sha256=package['review_sha256'],preparation_manifest_sha256=package['manifest_sha256'],updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),next_work='Run the one authorized diagnostic case, review its preserved final branch and selected pages, then decide evidence-based repair.')
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
base=M/'docs/shared/research/ultimaagent-work-capability';mirrors=[]
for src,dst in [(R/'docs/plans/jarvis-work-e02-failure-state-and-handoff-plan-20261107.md',base/'plans/jarvis-work-e02-failure-state-and-handoff-plan-20261107.md'),
    (report,base/'reports'/report.name),(N/'execution-proposal.md',base/'execution-proposals'/f'{N.name}.md')]:
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());assert sha(src)==sha(dst)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save(N/'verification/ready-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
paths={N/name for name in manifest['files']}
paths.update([N/'manifest.json',N/'review/independent-preparation-review.json',N/'harness-approval.json',report,
    R/'docs/plans/jarvis-work-e02-failure-state-and-handoff-plan-20261107.md',statepath,
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(p for p in (N/'verification').iterdir() if p.is_file())
sources={str(p.relative_to(R)).replace('\\','/'):sha(p) for p in paths}
pathlist=N/'verification/preparation-pathspec.txt';pathlist.write_bytes(b'\0'.join(p.encode('utf8') for p in sorted(sources))+b'\0')
subprocess.run(['git','-C',str(R),'-c','core.autocrlf=false','add','-f','--pathspec-from-file='+str(pathlist),'--pathspec-file-nul'],check=True)
staged=set(git(R,'diff','--cached','--name-only','-z').strip('\0').split('\0'));assert staged==set(sources)
subprocess.run(['git','-C',str(R),'commit','-m','Prepare failure branch and selected-page diagnostic for current 8B'],check=True,stdout=subprocess.DEVNULL)
main=git(R,'rev-parse','HEAD');tag='ultimaagent-e02-failure-state-ready-20261107';subprocess.run(['git','-C',str(R),'tag',tag,main],check=True)
mirrorpaths=[str(Path(x['mirror']).relative_to(M)).replace('\\','/') for x in mirrors]
subprocess.run(['git','-C',str(M),'-c','core.autocrlf=false','add','--',*mirrorpaths],check=True)
assert set(git(M,'diff','--cached','--name-only','-z').strip('\0').split('\0'))==set(mirrorpaths)
subprocess.run(['git','-C',str(M),'commit','-m','Mirror failure-state diagnostic preparation and ordered handoff plan'],check=True,stdout=subprocess.DEVNULL)
mirror=git(M,'rev-parse','HEAD');subprocess.run(['git','-C',str(M),'tag',tag,mirror],check=True)
for name,h in sources.items():assert hashlib.sha256(subprocess.check_output(['git','-C',str(R),'show',main+':'+name])).hexdigest()==h,name
for item,name in zip(mirrors,mirrorpaths):assert hashlib.sha256(subprocess.check_output(['git','-C',str(M),'show',mirror+':'+name])).hexdigest()==item['sha256']
assert e.read_ready(N)==package
for p,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==h
result=dict(verdict='PASS_LOCAL_PREPARATION_PUBLICATION',project_commit=main,mirror_commit=mirror,tag=tag,project_members=len(sources),mirrors=mirrors,
    package=package,actual_invocations=0,remote_synced=False,remote_reason='Earlier automatic approval blocked by policy; no retry',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'verification/final-ready-readback.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ('mirrors','package')}))
