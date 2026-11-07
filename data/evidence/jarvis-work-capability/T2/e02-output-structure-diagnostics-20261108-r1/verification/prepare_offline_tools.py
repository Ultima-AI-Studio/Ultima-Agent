"""Prepare offline-only runner copies; no test or product execution."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-writer-output-budget-20261107-r1'
old_c='C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent'
new_c='C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure/UltimaAgent'
record={}
for name in ('product_pytest.py','run_product_checks.py'):
    p=OLD/'verification'/name;raw=p.read_bytes();s=raw.decode('utf8').replace(old_c,new_c)
    if name=='run_product_checks.py':
        s=s.replace('GROUPS={',"GROUPS={'structure-red':['test_work_output_structure_diagnostics.py'],'structure-green':['test_work_output_structure_diagnostics.py'],")
    target=N/'verification'/name
    with target.open('x',encoding='utf8',newline='\n') as f:f.write(s)
    record[name]=dict(source=str(p),source_sha256=hashlib.sha256(raw).hexdigest(),prepared_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
with (N/'verification/offline-tool-preparation.json').open('x',encoding='utf8') as f:json.dump(dict(files=record,actual=0,model_calls=0),f,indent=2)
print(json.dumps(dict(status='OFFLINE_RUNNERS_PREPARED_NOT_EXECUTED',files=len(record))))
