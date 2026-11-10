"""Record only static preflight preservation and historical evidence; perform no live request."""
from pathlib import Path
import ast,datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
O=T/'e02-output-structure-controlled-preparation-20261108-r1';B=T/'e02-claim-generation-contract-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
assert funcs(N/'code/entry.py')==funcs(O/'code/entry.py')
assert funcs(N/'harness/adapter.py')==funcs(O/'harness/adapter.py')
historical=[O/'verification/runtime-readiness-final.json',B/'verification/protected-seven-after.json']
value=dict(status='PENDING_FRESH_ACTUAL_PREFLIGHT',candidate='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b',current_runtime_verified=False,actual_preflight_unchanged=True,
    historical_files={str(p):sha(p) for p in historical},historical_evidence_is_current_proof=False,
    reason='Current authorization is offline. Original run_released performs fresh protected identities/listener/native metadata validation after a future explicit grant; this receipt cannot replace it.',
    actual_cases=0,model_calls=0,network_requests=0,service_operations=0,os_packets=None,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
with (N/'verification/runtime-readiness-pending.json').open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(status=value['status'],live_observation=False,actual=0,network_requests=0)))
