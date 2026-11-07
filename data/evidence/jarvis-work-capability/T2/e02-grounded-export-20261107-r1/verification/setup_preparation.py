"""Prepare fresh copies, preserving all predecessor evidence and source paths."""
from pathlib import Path
import hashlib,json,subprocess
N=Path(__file__).resolve().parents[1]; OLD=N.parent/'e02-code-claim-schema-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-grounded-export/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-code-claim/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
for folder in ('harness','tests'):
    for source in (OLD/folder).glob('*'):
        if source.is_file():
            target=N/folder/source.name;target.parent.mkdir(exist_ok=True)
            with target.open('xb') as f:f.write(source.read_bytes())
for folder,names in {
    'code':['bindings.py','entry.py'],
    'inputs':['input-manifest.json','candidate-runtime-manifest.json','unrelated-working-tree.json','scope.json'],
    'verification':['offline_pytest.py','product_pytest.py','run_product_checks.py','run_binding_checks.py','run_entry_checks.py','run_boundary_checks.py','grammar_checks.py']}.items():
    for name in names:
        target=N/folder/name;target.parent.mkdir(exist_ok=True)
        with target.open('xb') as f:f.write((OLD/folder/name).read_bytes())
for source in (OLD/'verification/upstream').glob('*'):
    if source.is_file():
        target=N/'verification/upstream'/source.name;target.parent.mkdir(exist_ok=True)
        with target.open('xb') as f:f.write(source.read_bytes())
# Path changes are preparation wiring only; final hashes are sealed after implementation.
for folder in ('harness','code','tests','verification'):
    for p in (N/folder).glob('*.py'):
        if p.name in ('setup_preparation.py','register_progress.py'):continue
        text=p.read_text('utf8').replace('jarvis-e02-code-claim/UltimaAgent','jarvis-e02-grounded-export/UltimaAgent').replace('jarvis-e02-code-claim\\UltimaAgent','jarvis-e02-grounded-export\\UltimaAgent')
        p.write_text(text,encoding='utf8')
save(N/'inputs/predecessor.json',dict(root=str(OLD),candidate='1ecd75d061fd20e78c790c506cac76847f8e63bf',
    manifest_sha256=sha(OLD/'manifest.json'),result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),
    result_review_sha256=sha(OLD/'review/independent-result-review.json'),original_outcome='FAIL_CONFIRMED',credit=0))
save(N/'inputs/setup.json',dict(old_root=str(P),new_root=str(C),base=subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip(),
    rationale='New worktree preserves predecessor source files pinned by immutable evidence; no existing workspace is disposable'))
print('Fresh preparation source copies created; not sealed or released.')
