"""Clone source-only preparation into a fresh evidence root; preserve all old runs."""
from pathlib import Path
import hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];OLD=N.parent/'e02-grounded-export-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-grounded-export/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
for folder,names in {
    'harness':[p.name for p in (OLD/'harness').iterdir() if p.is_file()],
    'tests':[p.name for p in (OLD/'tests').iterdir() if p.is_file()],
    'code':['bindings.py','entry.py'],
    'inputs':['input-manifest.json','candidate-runtime-manifest.json','unrelated-working-tree.json','scope.json'],
    'verification':['offline_pytest.py','product_pytest.py','run_product_checks.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py','grammar_checks.py']}.items():
    for name in names:
        source=OLD/folder/name;target=N/folder/name;target.parent.mkdir(parents=True,exist_ok=True)
        raw=source.read_bytes()
        if source.suffix=='.py':raw=raw.decode('utf8').replace('jarvis-e02-grounded-export/UltimaAgent','jarvis-e02-failure-state/UltimaAgent').replace('jarvis-e02-grounded-export\\UltimaAgent','jarvis-e02-failure-state\\UltimaAgent').encode('utf8')
        with target.open('xb') as f:f.write(raw)
for source in (OLD/'verification/upstream').iterdir():
    if source.is_file():
        target=N/'verification/upstream'/source.name;target.parent.mkdir(exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
for folder in ('offline','review'):(N/folder).mkdir(exist_ok=True)
save(N/'inputs/predecessor.json',dict(root=str(OLD),candidate='9e2716a6bc8dc1a51218257b89a581f968d8444a',manifest_sha256=sha(OLD/'manifest.json'),
    result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(OLD/'review/independent-result-review.json'),outcome='FAIL_CONFIRMED',credit=0))
text='先补齐失败时的最终分支和选页诊断，再针对证据修复“读取到交付”的衔接。'
plan=R/'docs/plans/jarvis-work-e02-failure-state-and-handoff-plan-20261107.md'
save(N/'inputs/direct-user-decision.json',dict(source='direct_user_message_in_current_chat',decision_id='user-message:sha256:'+hashlib.sha256(text.encode()).hexdigest(),
    answer=text,identifier_is_platform_message_id=False,plan_sha256=sha(plan),sequence=['failure diagnosis','evidence based minimal repair'],
    maximum_case_allocations=dict(diagnostic=1,post_repair_verification=1),retry_per_case=0,conditional_on_independent_preparation_PASS=True,production_service_operations=False,UI=False,audio=False))
save(N/'inputs/setup.json',dict(old_root=str(P),new_root=str(C),base=subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip(),
    worktree_operation='f2400b12-4853-4c48-b2df-60356a7e4959',reason='Old source paths are immutable evidence inputs'))
(N/'plan.md').write_bytes(plan.read_bytes())
save(N/'inputs/previous-current-run.json',json.loads((N.parent/'current-run.json').read_bytes()))
print('Fresh source copies and user decision recorded; no runtime allocation issued.')
