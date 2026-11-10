"""Preserve expected RED and incompatible fixture results without rerunning."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
red=next((N/'offline').glob('evidence-first-red-*/receipt.json'))
r=json.loads(red.read_bytes());a=json.loads((red.parent/'offline-audit.json').read_bytes())
tree=ET.parse(red.parent/'junit.xml');cases=tree.findall('.//testcase')
fails=[c for c in cases if c.find('failure') is not None]
assert len(cases)==14 and len(fails)==12 and not tree.findall('.//error')
assert r['sources_unchanged'] and r['exit_code']==1 and not a['denied'] and a['python_operations_clean']
assert all('AssertionError' in c.find('failure').text for c in fails)
parents=json.loads((N/'inputs/plan-reviewed-parent-snapshots.json').read_bytes())['files']
for name,data in parents.items():assert r['source_sha256'][name]==data['sha256']
old=N/'verification/final-regression-batch.json';batch=json.loads(old.read_bytes())
assert batch['totals']==dict(tests=1022,failures=10,errors=0,skipped=0)
value=dict(red_receipt=str(red),red_sha256=sha(red),red_tests=14,expected_failures=12,parent_sources_verified=True,
    first_full_batch_sha256=sha(old),first_full_failures=10,failed_groups={k:v['failures'] for k,v in batch['groups'].items() if v['failures']},
    cause='Old fixture property access and source-selection/budget assumptions; migrate only those expressions and preserve all rejection tests',
    additional_test_paths=['src/brain/tests/test_work_failure_diagnostics.py','src/brain/tests/test_work_source_reference_schema.py'],
    scope_ruling='Necessary direct test fixture compatibility within approved offline minimal repair; no extra production files',
    actual_cases=0,model_calls=0)
with (N/'verification/tdd-and-fixture-readback.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
print(json.dumps({k:v for k,v in value.items() if k not in ('cause','scope_ruling')}))
