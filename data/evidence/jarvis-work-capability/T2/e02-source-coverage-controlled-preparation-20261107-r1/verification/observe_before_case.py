"""Read protected identities and two fixed metadata GETs; never infer or operate services."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json
N=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
e=module('http_controlled_readiness_entry',N/'code/entry.py');a=module('http_controlled_readiness_adapter',N/'harness/adapter.py')
a.check_inputs();b=a.Deadline();p4=a.load_p4()
with a.PrivateIO(p4,b):
    identities=p4.protected();a.validate_protected_members(identities,p4)
    expected=p4.old.protected_entries(a.load(a.PROTECTED_BASELINE))[0]['pid']
    e.require(p4.listener_owner(11434)==[expected],'Protected native listener drift')
    e.require(not p4.listener_owner(18799),'Isolated case port is occupied')
version=e.native_metadata(a,b,'/api/version');tags=e.native_metadata(a,b,'/api/tags')
inputs=a.bindings.load_inputs(a.INPUTS_PATH)
p4.old.metadata_valid(dict(ok=True,model=e.MODEL,agent='native_react'),version,tags,Path(inputs['model_manifest_path']).read_bytes())
value=dict(verdict='PASS_READONLY_RUNTIME_IDENTITY',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),candidate_base=e.CANDIDATE,
    protected=identities,protected_baseline_sha256=a.sha(a.PROTECTED_BASELINE),version=version,model=e.MODEL,model_digest=e.DIGEST,
    isolated_port_free=True,actual_calls=0,model_calls=0,service_operations=0,
    checker_sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (Path(__file__),N/'code/entry.py',N/'harness/adapter.py')})
e.save_new(N/'verification/runtime-before-allocated-case.json',value)
print(json.dumps({k:v for k,v in value.items() if k not in ('protected','checker_sources')}))
