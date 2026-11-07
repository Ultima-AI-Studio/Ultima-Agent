"""Retain every first validation receipt before correcting a Markdown test expectation."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rows=[]
for p in sorted((N/'code').glob('harness-preparation-*/receipt.json')):
    receipt=json.loads(p.read_bytes());tree=ET.parse(p.parent/'harness/adapter.xml')
    failed=[c for c in tree.findall('.//testcase') if c.find('failure') is not None]
    assert not tree.findall('.//error') and not tree.findall('.//skipped')
    if receipt['group']=='export-green':
        assert receipt['exit_code']==1 and len(failed)==1
        assert failed[0].get('name')=='test_export_diagnostics_current_sampler_contract[quoted_write]'
        assert "assert claim in artifact.decode('utf8')" in failed[0].find('failure').text
    else:assert receipt['exit_code']==0 and not failed
    files={str(x.relative_to(N)):sha(x) for x in p.parent.rglob('*') if x.is_file() and 'temp' not in x.relative_to(p.parent).parts}
    rows.append(dict(receipt=str(p.relative_to(N)),group=receipt['group'],exit_code=receipt['exit_code'],files=files))
assert len(rows)==5
value=dict(reason='Product writes Markdown-escaped backslash correctly; new test compared raw claim to rendered Markdown',
    failed_cases=1,product_failure=False,changed_product_sources=[],run_receipts=rows,actual_cases=0,model_calls=0)
with (N/'verification/first-validation-draft.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(preserved_runs=len(rows),failed_cases=1,product_failure=False)))
