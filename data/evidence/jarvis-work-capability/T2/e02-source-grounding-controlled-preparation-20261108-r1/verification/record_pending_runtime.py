from pathlib import Path
import ast,datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
O=T/'e02-claim-generation-controlled-preparation-20261108-r1';B=T/'e02-source-grounding-coverage-20261108-r2'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def funcs(p):return {x.name:ast.dump(x,include_attributes=False) for x in ast.parse(p.read_bytes()).body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
for name in ('code/entry.py','code/bindings.py','harness/adapter.py'):assert funcs(N/name)==funcs(O/name)
base=json.loads((B/'inputs/current-inputs.json').read_bytes())
historical=[O/'verification/runtime-readiness-pending.json',Path(base['protected_baseline_path'])]
value=dict(status='PENDING_FRESH_ACTUAL_PREFLIGHT',candidate='43da3f014a763b8ea3963872a8f1ce8ebea77531',current_runtime_verified=False,actual_preflight_unchanged=True,historical_files={str(p):sha(p) for p in historical},historical_evidence_is_current_proof=False,reason='Offline authorization; only future allocated original preflight may establish current runtime readiness',actual_cases=0,model_calls=0,network_requests=0,service_operations=0,os_packets=None,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
with (N/'verification/runtime-readiness-pending.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
print(json.dumps(dict(status=value['status'],current_runtime_verified=False,actual=0)))
