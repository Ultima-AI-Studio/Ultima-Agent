from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1];old=N.parent/'navigation-source10-validation-20261103-inert2/harness'
assert not (N/'harness').exists();(N/'harness').mkdir()
rows=[]
for name in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md'):
    raw=(old/name).read_bytes();(N/'harness'/name).write_bytes(raw)
    rows.append(dict(name=name,source=str(old/name),sha256=hashlib.sha256(raw).hexdigest()))
with (N/'inputs/harness-copy.json').open('x',encoding='utf-8') as f:json.dump(rows,f,indent=2)
print(json.dumps(dict(copied=len(rows),actual_product_runs=0)))
