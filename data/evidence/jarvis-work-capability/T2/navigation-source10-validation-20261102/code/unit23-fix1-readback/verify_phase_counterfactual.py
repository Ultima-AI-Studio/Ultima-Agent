"""Read-only ACK suffix mutation outside the sealed prewrite prefix."""
import hashlib
import json
from pathlib import Path
import socket
import sys

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
sys.path.insert(0,str(C))
def deny(*a,**kw): raise AssertionError('network forbidden in replay probe')
socket.socket.connect=deny
socket.getaddrinfo=deny
from src.brain.work_navigation import IssuedSnapshotV3
from src.brain.work_tools import WorkBinding,ResearchRuntimeInputs
from src.brain.work_research import ResearchCollection,verify_runtime_packet

HERE=Path(__file__).resolve().parent
external=json.loads((HERE/'external-verification.json').read_bytes())
case=next(c for c in external['cases'] if c['variant']=='text')
folder=Path(case['folder'])
raw=(folder/'runtime-replay.json').read_bytes();packet=json.loads(raw)
issued=(folder/'issued-snapshot.json').read_bytes();pure=json.loads(issued)
inputs=json.loads((folder/'runtime-inputs.json').read_bytes());inputs['binding_key']=tuple(inputs['binding_key'])
frozen=ResearchRuntimeInputs(**inputs)
binding=WorkBinding(Path(frozen.root),*frozen.binding_key)
snapshot=IssuedSnapshotV3(frozen.binding_key,pure['nonce'],pure['catalogue_sha256'],pure['generation'],
    (folder/'issued-views.json').read_bytes(),issued,hashlib.sha256(issued).hexdigest())
collection=dict(pure['collection']);collection['ignored_failure_ids']=tuple(collection['ignored_failure_ids']);collection=ResearchCollection(**collection)
J=lambda value:json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':')).encode()
H=lambda value:hashlib.sha256(value).hexdigest()
wire=packet['wires'][-1];wire['secured_messages'][0]['content']+='\nInjected ACK phase override.'
request=json.loads(wire['entity']);request['messages']=wire['secured_messages'];entity=J(request);wire['entity']=entity.decode()
wire['hashes']['messages']=H(J(request['messages']));wire['hashes']['entity']=H(entity)
receipt=packet['transport']['receipts'][-1];receipt['entity_sha256']=H(entity);receipt['entity_bytes']=len(entity)
packet['transport']['post_bytes']=sum(len(w['entity'].encode()) for w in packet['wires'])
assert packet['prewrite_packet']==json.loads(raw)['prewrite_packet']
try:
    verify_runtime_packet(binding,snapshot,collection,J(packet),require_ack=True,runtime_inputs=frozen)
except ValueError as exc:
    assert str(exc)=='Runtime exact phase system drift',str(exc)
    error=str(exc)
else: raise AssertionError('coherent ACK suffix was accepted')
paths={n:str(Path(m.__file__).resolve()) for n,m in tuple(sys.modules.items()) if getattr(m,'__file__',None) and n.startswith(('src.brain.','openjarvis.'))}
sdk=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages')
assert all(Path(p).is_relative_to(sdk if n.startswith('openjarvis.') else C) for n,p in paths.items())
out=dict(result='REJECTED_AT_INTENDED_EXACT_PHASE_GATE',error=error,original_runtime_sha256=H(raw),mutated_runtime_sha256=H(J(packet)),
    prewrite_unchanged=True,entity_message_hashes_and_send_bytes_recomputed=True,raw_envelope_unchanged=True,
    artifact_unchanged=H(Path(case['artifact']).read_bytes())==case['artifact_sha256'],loaded_paths=paths,
    argv=sys.argv,interpreter=sys.executable,script_sha256=H(Path(__file__).read_bytes()))
(HERE/'phase-counterfactual.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps({k:out[k] for k in ('result','error','prewrite_unchanged','artifact_unchanged')}))
