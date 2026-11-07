"""Fresh bounded offline covering suite; no model, profile or service launch."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
GROUPS=['contract-green','grammar','structure-green','native-green','compatibility','budget-green','json-green','coverage-green',
    'failure-green','http-green','unique-green','grounding-green','metadata-green','claim-green',
    'reference-green','target-green','diagnostics-green','research-a','research-b','navigation','transport','delivery']
OUT=N/'verification/final-regression-batch.json'
assert not OUT.exists()
def run(group):
    p=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(N/'verification/run_product_checks.py'),group],
        capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with (N/'verification'/('final-batch-'+group+'.log')).open('xb') as f:f.write(p.stdout+p.stderr)
    lines=p.stdout.decode('utf8','replace').splitlines()
    receipts=[Path(line[8:]) for line in lines if line.startswith('RECEIPT ')]
    assert len(receipts)==1,(group,p.returncode)
    receipt=receipts[0];r=json.loads(receipt.read_bytes());audit=json.loads((receipt.parent/'offline-audit.json').read_bytes())
    assert r['exit_code']==p.returncode and r['sources_unchanged'] and not audit['denied'] and audit['python_operations_clean']
    root=ET.parse(receipt.parent/'junit.xml').getroot();suites=list(root.iter('testsuite'))
    cases=[(x.attrib.get('classname',''),x.attrib['name']) for x in root.iter('testcase')]
    return group,dict(exit_code=p.returncode,receipt=str(receipt),receipt_sha256=hashlib.sha256(receipt.read_bytes()).hexdigest(),
        tests=sum(int(s.attrib['tests']) for s in suites),failures=sum(int(s.attrib['failures']) for s in suites),
        errors=sum(int(s.attrib['errors']) for s in suites),skipped=sum(int(s.attrib['skipped']) for s in suites),
        cases=cases,source_sha256=r['source_sha256'])
results={}
with ThreadPoolExecutor(max_workers=2) as pool:
    for future in as_completed([pool.submit(run,g) for g in GROUPS]):
        group,result=future.result();results[group]=result
        print(json.dumps(dict(group=group,**{k:result[k] for k in ('exit_code','tests','failures','errors','skipped')})),flush=True)
sources=[r.pop('source_sha256') for r in results.values()]
assert all(s==sources[0] for s in sources)
cases=[tuple(case) for r in results.values() for case in r.pop('cases')]
assert len(cases)==len(set(cases)), 'duplicate collected JUnit identities'
totals={k:sum(r[k] for r in results.values()) for k in ('tests','failures','errors','skipped')}
summary=dict(groups=results,totals=totals,distinct_cases=len(set(cases)),same_source_bytes=True,
    source_sha256=sources[0],actual_cases=0,model_calls=0,acceptance_credit=0,
    exclusions=['test_http_work_legacy_and_cli','test_reparse_rejected'])
with OUT.open('x',encoding='utf8') as f:json.dump(summary,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(totals=totals,groups=len(results),same_source_bytes=True,model_calls=0)),flush=True)
raise SystemExit(int(any(r['exit_code'] for r in results.values()) or totals['failures'] or totals['errors']))
