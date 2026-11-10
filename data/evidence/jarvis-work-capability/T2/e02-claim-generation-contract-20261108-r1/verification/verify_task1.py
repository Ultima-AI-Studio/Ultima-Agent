"""Read back fresh RED/GREEN source-bound receipts; do not repeat model or tests."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
expected={'contract-red-20261107T175153861414Z':(19,14,0),'contract-green-20261107T175224033143Z':(19,0,0),'json-green-20261107T175224031092Z':(35,0,0)}
for name,counts in expected.items():
    root=N/'offline'/name;r=json.loads((root/'receipt.json').read_bytes());a=json.loads((root/'offline-audit.json').read_bytes())
    suites=list(ET.parse(root/'junit.xml').getroot().iter('testsuite'))
    assert tuple(sum(int(s.attrib[k]) for s in suites) for k in ('tests','failures','errors'))==counts
    assert r['sources_unchanged'] and a['python_operations_clean'] and not a['denied']
    if counts[1]==0:
        assert r['exit_code']==0
        for p,h in r['source_sha256'].items():assert hashlib.sha256(Path(p).read_bytes()).hexdigest()==h,p
print('PASS_TASK1_RECEIPT_READBACK: RED14/19, GREEN19+35; unchanged tested source; no new test/runtime execution')
