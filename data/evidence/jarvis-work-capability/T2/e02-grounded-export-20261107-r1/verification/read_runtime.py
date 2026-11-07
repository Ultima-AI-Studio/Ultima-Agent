"""Read-only current identity and native metadata check; never allocate or run."""
from pathlib import Path
import datetime as dt,importlib.util,json
N=Path(__file__).resolve().parents[1]
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
e=module('readiness_entry',N/'code/entry.py');a=module('readiness_adapter',N/'harness/adapter.py')
a.check_inputs();b=a.Deadline();p4=a.load_p4()
with a.PrivateIO(p4,b):
    identities=p4.protected();a.validate_protected_members(identities,p4)
    expected=p4.old.protected_entries(a.load(a.PROTECTED_BASELINE))[0]['pid']
    e.require(p4.listener_owner(11434)==[expected],'Protected native listener drift')
    e.require(not p4.listener_owner(18799),'Isolated case port is occupied')
version=e.native_metadata(a,b,'/api/version');tags=e.native_metadata(a,b,'/api/tags')
inputs=a.bindings.load_inputs(a.INPUTS_PATH)
p4.old.metadata_valid(dict(ok=True,model=e.MODEL,agent='native_react'),version,tags,Path(inputs['model_manifest_path']).read_bytes())
value=dict(verdict='PASS_READONLY_RUNTIME_IDENTITY',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=e.CANDIDATE,
    protected=identities,protected_baseline_sha256=a.sha(a.PROTECTED_BASELINE),version=version,model=e.MODEL,model_digest=e.DIGEST,
    isolated_port_free=True,actual_calls=0,model_calls=0,service_operations=0)
e.save_new(N/'verification/runtime-readiness.json',value)
print(json.dumps({k:v for k,v in value.items() if k!='protected'}))
