"""Initialize only the new managed worktree after exact plan review closure."""
from pathlib import Path
import hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path(sys.argv[1]).resolve();BASE='0421a54cab572be013c3f7ad562e86406bfe8e52'
PLAN=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
review_path=N/'review/independent-plan-review-closure.json';review=json.loads(review_path.read_bytes())
assert review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(PLAN) and review['actual_run_authorized'] is False
assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
git('switch','-c','codex/jarvis-e02-output-structure')
with (N/'inputs/worktree.json').open('x',encoding='utf8') as f:json.dump(dict(root=str(C),base=BASE,
    branch=git('branch','--show-current'),native_created=True,review_sha256=sha(review_path)),f,indent=2)
expected='C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure/UltimaAgent'
for name in ('product_pytest.py','run_product_checks.py'):
    p=N/'verification'/name;s=p.read_text('utf8');assert expected in s
    p.write_text(s.replace(expected,C.as_posix()),encoding='utf8',newline='\n')
(N/'plan.md').write_bytes(PLAN.read_bytes())
state=json.loads((T/'current-run.json').read_bytes())
state.update(phase='SOURCE32_E02_OUTPUT_STRUCTURE_DIAGNOSTICS_IMPLEMENTATION',active_review_agent=None,
    active_implementation_root=str(C),source_implementation_released=True,
    next_work='Implement and verify bounded structure diagnostics offline; actual allocation remains zero')
state['source32_offline'].update(status='PLAN_PASS_IMPLEMENTATION',plan_sha256=sha(PLAN),plan_review_sha256=sha(review_path))
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(root=str(C),base=BASE,branch=git('branch','--show-current'),actual=0)))
