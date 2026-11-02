"""U2 SDK boundary tests. Confirmed fixture projections are not native wire proof."""
import dataclasses
import hashlib
import json
import socket
import threading
import time
import uuid
import pytest
from src.brain.tests.test_work_navigation import fixture, policy, j
from src.brain import work_tools as wt
from src.brain import work_navigation as nav

INSPECT = 'ultima_work_research_inspect'
WRITE = 'ultima_work_research_write'

@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*a, **kw): raise AssertionError('live network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)

def setup(tmp_path):
    c,b,r = fixture()
    binding = wt.WorkBinding(tmp_path, b.request_id, b.session_id, b.task_id)
    ledger = wt.WorkLedger(); ledger.deadline = time.monotonic()+260
    p = policy()
    cat = nav.prepare_navigation(c,b,p,get_records_json=r,deadline=ledger.deadline)
    assert hasattr(ledger, '_prepare_navigation'), 'trusted request preparation missing'
    ledger._prepare_navigation(binding,cat,c,r,p)
    caps = wt.WorkCapabilities(navigation=cat,research_json=c.catalogue_json)
    from openjarvis.cli.ask import _build_tools
    from openjarvis.core.config import JarvisConfig
    from openjarvis.core.events import EventBus,EventType
    from openjarvis.tools._stubs import ToolExecutor
    caller = threading.get_ident()
    ledger.open_enrollment(binding,caller)
    with wt.bind_work(binding,ledger,caps):
        tools = _build_tools([INSPECT,WRITE],JarvisConfig(),None,'unused')
    ledger.close_enrollment()
    bus = EventBus()
    for kind in (EventType.TOOL_CALL_START,EventType.TOOL_CALL_END,EventType.TOOL_TIMEOUT):
        bus.subscribe(kind,lambda e: ledger.observe_navigation(e,caller_id=caller,binding_key=cat.binding_key))
    executor = ToolExecutor(tools,bus=bus,agent_id=binding.task_id)
    return ledger,binding,c,cat,tools,executor,bus

def invoke(state, seq, name, args, promote=True):
    from openjarvis.core.types import ToolCall
    ledger,*_=state
    ledger.expect(seq,name,hashlib.sha256(j(args)).hexdigest())
    result=state[5].execute(ToolCall(id=str(uuid.uuid4()),name=name,arguments=json.dumps(args)))
    if result.success and name==INSPECT and promote:
        ledger.promote_visible(seq,hashlib.sha256(result.content.encode()).hexdigest())
    return result

def read_three(state):
    refs=[]
    for i in range(1,4):
        r=invoke(state,i,INSPECT,dict(source_id=f'S{i}',start_line=1))
        assert r.success,r.content
        refs.append(json.loads(r.content)['cards'][0][0])
    return dict(path='research.md',title='Report',sections=[dict(source_id=f'S{i}',heading=f'Section {i}',facts=[dict(claim='Source documents local usage',evidence_id=ref)]) for i,ref in enumerate(refs,1)])

def test_v3_writer_real_io_and_external_bytes(tmp_path):
    state=setup(tmp_path); data=read_three(state)
    result=invoke(state,4,WRITE,data)
    assert result.success,result.content
    ledger,b,c,*_=state
    resolved,bindings=nav.resolve_v3(data,ledger.issued_snapshot,c)
    oracle=nav.render_v3(resolved,c.catalogue_json,bindings=bindings).content.encode()
    raw=(tmp_path/'research.md').read_bytes()
    assert raw==oracle and hashlib.sha256(raw).hexdigest()==json.loads(result.content)['sha256']
    assert len(result.content.encode())<=3072
    assert len([r for r in ledger.snapshot() if r['tool_name']=='ultima_work_file_write'])==1
    assert not invoke(state,5,WRITE,data).success

def test_v3_inspector_has_only_safe_capability(tmp_path):
    state=setup(tmp_path); inspector=state[4][0]
    assert not isinstance(inspector,wt._CapabilityTool)
    assert set(vars(inspector))=={'_catalogue','_read'}
    assert set(inspector.spec.parameters['properties'])=={'source_id','start_line'}
    for i in range(1,8):
        result=invoke(state,i,INSPECT,dict(source_id='bad',start_line=1))
        assert not result.success
    assert state[0]._read_count==6
    assert not list(tmp_path.iterdir())

def test_v3_enrolled_identity_and_nonraising_observer(tmp_path):
    state=setup(tmp_path); ledger=state[0]
    assert len(ledger._enrolled)==2
    assert wt._ACTIVE.get() is None
    assert not state[4][1].execute(path='research.md').success
    assert not list(tmp_path.iterdir())
    ledger.observe_navigation(object(),caller_id=threading.get_ident(),binding_key=state[3].binding_key)
    assert ledger.first_failure

@pytest.mark.parametrize('fault',['path','ref','source','unread'])
def test_v3_invalid_write_zero_file(tmp_path,fault):
    state=setup(tmp_path)
    data=read_three(state)
    if fault=='path': data['path']='other.md'
    elif fault=='ref': data['sections'][0]['facts'][0]['evidence_id']='N3.'+'0'*16
    elif fault=='source': data['sections'][0]['source_id']='S2'
    else: data['sections'][0]['facts'][0]['evidence_id']='N3.'+'1'*16
    assert not invoke(state,4,WRITE,data).success
    assert not list(tmp_path.iterdir())
