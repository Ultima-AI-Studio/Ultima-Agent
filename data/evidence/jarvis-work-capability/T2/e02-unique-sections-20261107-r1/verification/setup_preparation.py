"""Fresh source-only successor preparation; no copied authority or actual result."""
from pathlib import Path
import hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];OLD=N.parent/'e02-failure-state-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-unique-sections/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
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
        if source.suffix=='.py':raw=raw.decode('utf8').replace('jarvis-e02-failure-state/UltimaAgent','jarvis-e02-unique-sections/UltimaAgent').replace('jarvis-e02-failure-state\\UltimaAgent','jarvis-e02-unique-sections\\UltimaAgent').encode('utf8')
        with target.open('xb') as f:f.write(raw)
for source in (OLD/'verification/upstream').iterdir():
    if source.is_file():
        target=N/'verification/upstream'/source.name;target.parent.mkdir(exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
for folder in ('offline','review'):(N/folder).mkdir(exist_ok=True)
save(N/'inputs/predecessor.json',dict(root=str(OLD),candidate='22653fb77445bad4f5b9d9ae789cd35972dcc984',manifest_sha256=sha(OLD/'manifest.json'),
    result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(OLD/'review/independent-result-review.json'),outcome='FAIL_CONFIRMED',credit=0))
decision=json.loads((OLD/'inputs/direct-user-decision.json').read_bytes())
decision.update(plan_sha256=sha(N/'plan.md'),purpose='post_repair_verification',
    parent_plan_sha256=decision['plan_sha256'],diagnostic_case_consumed=dict(root=str(OLD),run_id='963f8bf5-1a85-49ce-ae9f-19d503b9ff65',
    result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),result_review_sha256=sha(OLD/'review/independent-result-review.json')),
    remaining_purpose_case_limits=dict(diagnostic=0,post_repair_verification=1))
save(N/'inputs/direct-user-decision.json',decision)
p=N/'code/entry.py';s=p.read_text(encoding='utf8');s,n=re.subn(r"(?m)^DIRECT_USER_DECISION_SHA='[^']*'",'DIRECT_USER_DECISION_SHA='+repr(sha(N/'inputs/direct-user-decision.json')),s);assert n==1;p.write_text(s,encoding='utf8')
save(N/'inputs/setup.json',dict(old_root=str(P),new_root=str(C),base=subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip(),
    worktree_operation='4182f169-8906-4661-9d5a-d31e50cfd7e9',reason='Prior actual candidate source paths remain immutable'))
save(N/'inputs/previous-current-run.json',json.loads((N.parent/'current-run.json').read_bytes()))
print('Source-only successor preparation copied; no runtime allocation or product test yet. Decision SHA256 '+sha(N/'inputs/direct-user-decision.json'))
