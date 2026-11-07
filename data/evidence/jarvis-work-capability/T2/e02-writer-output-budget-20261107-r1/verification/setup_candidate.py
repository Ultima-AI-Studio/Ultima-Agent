"""Set up the authorized offline candidate after exact independent plan PASS."""
from pathlib import Path
import hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];T=N.parent;OLD=T/'e02-native-rejection-diagnostics-20261107-r1'
C=Path(sys.argv[1]).resolve();BASE='d860b2ab4e4d9974e33c96472e4ea15abb807280'
OLD_C='C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent'
ALLOWED={'src/brain/work_navigation.py','src/brain/agent_server.py','src/brain/work_research.py','src/brain/tests/test_work_grounding_context.py','src/brain/tests/test_work_output_budget_guidance.py'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
review=N/'review/independent-plan-review-closure.json';r=json.loads(review.read_bytes())
assert r['verdict']=='PASS_PLAN_ONLY' and r['plan_sha256']==sha(N/'plan.md') and r['actual_run_authorized'] is False
for ext in ('json','md'):
    source=N/('review/independent-plan-review-closure.'+ext);target=N/('review/independent-plan-review.'+ext)
    assert sha(target)==sha(N/('review/independent-plan-review-first-needs-fixes.'+ext))
    target.write_bytes(source.read_bytes())
save(N/'verification/plan-review-promotion.json',dict(plan_sha256=sha(N/'plan.md'),closure_sha256=sha(review),generic_sha256=sha(N/'review/independent-plan-review.json'),first_preserved=True))
assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
git('switch','-c','codex/jarvis-e02-output-budget')
save(N/'inputs/worktree.json',dict(root=str(C),base=BASE,branch=git('branch','--show-current'),native_created=True,review_sha256=sha(review)))
for name in ('product_pytest.py','run_product_checks.py','run_final_regressions.py','verify_offline.py','compatibility_checks.py','verify_preservation.py','read_runtime_after.py'):
    s=(OLD/'verification'/name).read_text('utf8').replace(OLD_C,C.as_posix())
    if name=='run_product_checks.py':
        s=s.replace('GROUPS={',"GROUPS={'budget-red':['test_work_output_budget_guidance.py'],'budget-green':['test_work_output_budget_guidance.py'],")
    if name=='run_final_regressions.py':
        s=s.replace("GROUPS=[", "GROUPS=['native-green','compatibility',")
    if name=='verify_offline.py':
        s=s.replace('6d758d9c3961f156a062e349ec4a949e2ee7a9a9',BASE).replace("GROUPS=[", "GROUPS=['budget-green',")
        start=s.index('ALLOWED=');end=s.index('\n',start)
        s=s[:start]+'ALLOWED='+repr(ALLOWED)+s[end:]
        s=s.replace('jarvis-work-e02-native-response-rejection-diagnostics-plan-20261107.md','jarvis-work-e02-writer-output-budget-alignment-plan-20261107.md').replace("glob('native-red-*')","glob('budget-red-*')")
    if name=='verify_preservation.py':
        s=s.replace('e02-json-string-controlled-preparation-20261107-r1','e02-native-rejection-controlled-preparation-20261107-r1')
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
state=json.loads((T/'current-run.json').read_bytes());state.update(active_review_agent=None,phase='SOURCE30_E02_WRITER_OUTPUT_BUDGET_IMPLEMENTATION',active_implementation_root=str(C))
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
with (N/'progress.md').open('a',encoding='utf8') as f:f.write('\nTask 1: revised exact plan PASS; implementation starts at '+BASE+' in '+str(C)+'. Five changed files, full source set76, actual/model0.\n')
print(json.dumps(dict(root=str(C),base=BASE,branch=git('branch','--show-current'))))
