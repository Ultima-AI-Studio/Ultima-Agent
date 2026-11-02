"""U2 SDK boundary tests. Confirmed fixture projections are not native wire proof."""
import dataclasses
import hashlib
import json
import socket
import threading
import time
import uuid
import pytest
from src.brain.tests.test_work_navigation import fixture, policy, j,stable_navigation_entropy
from src.brain import work_tools as wt
from src.brain import work_navigation as nav
from src.brain.tests.test_work_research import sdk_io, mock_jar

INSPECT = 'ultima_work_research_inspect'
WRITE = 'ultima_work_research_write'

@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*a, **kw): raise AssertionError('live network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)

def setup(tmp_path, texts=None):
    c,b,r = fixture(texts)
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
    executor = ToolExecutor(tools,bus=bus,agent_id='native_react')
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

def test_v3_writer_real_io_and_external_bytes(tmp_path,monkeypatch):
    seen=[]; caller=threading.get_ident(); original=wt.FileWriteTool.execute
    def observe(tool,**args):
        seen.append((threading.get_ident(),wt._ACTIVE.get(),tuple(tool._allowed_dirs)))
        return original(tool,**args)
    monkeypatch.setattr(wt.FileWriteTool,'execute',observe)
    state=setup(tmp_path); data=read_three(state)
    result=invoke(state,4,WRITE,data)
    assert result.success,result.content
    ledger,b,c,*_=state
    resolved,bindings=nav.resolve_v3(data,ledger.issued_snapshot,c)
    oracle=nav.render_v3(resolved,c.catalogue_json,bindings=bindings).content.encode()
    raw=(tmp_path/'research.md').read_bytes()
    assert raw==oracle and hashlib.sha256(raw).hexdigest()==json.loads(result.content)['sha256']
    assert len(result.content.encode())<=3072
    assert len(seen)==1 and seen[0][0]!=caller and seen[0][1] is None
    assert len([r for r in ledger.snapshot() if r['tool_name']=='ultima_work_file_write'])==1
    assert not invoke(state,5,WRITE,data).success

def test_v3_inspector_has_only_safe_capability(tmp_path):
    state=setup(tmp_path,['\n'.join(f'Source {i} line {line} documents usage.' for line in range(30)) for i in range(3)])
    inspector=state[4][0]
    assert not isinstance(inspector,wt._CapabilityTool)
    assert set(vars(inspector))=={'_catalogue','_read'}
    assert set(inspector.spec.parameters['properties'])=={'source_id','start_line'}
    for i in range(1,7):
        result=invoke(state,i,INSPECT,dict(source_id=f'S{(i-1)//2+1}',start_line=1 if i%2 else 25))
        assert result.success,result.content
    assert not invoke(state,7,INSPECT,dict(source_id='S1',start_line=2)).success
    assert state[0]._read_count==6
    assert not list(tmp_path.iterdir())

def test_v3_invalid_attempt_not_refunded(tmp_path):
    state=setup(tmp_path)
    assert not invoke(state,1,INSPECT,dict(source_id='invalid',start_line=1)).success
    assert state[0]._read_count==1 and state[0].first_failure

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

def test_v3_service_preparer_uses_checked_configured_scanners(tmp_path,sdk_io,mock_jar):
    from src.brain.work_service import WorkService
    from src.brain import agent_server
    owner,*_=mock_jar
    browser,calls,_=sdk_io
    captured={}
    def prepare(collection,*,binding,ledger):
        captured.update(collection=collection,records=ledger.snapshot())
        cat=agent_server._prepare_research_navigation(collection,binding=binding,ledger=ledger)
        assert ledger._collection is collection
        assert ledger._policy.scanners==tuple(owner._engine._inner._scanners)
        return cat
    def runner(prompt,**kw):
        caps=wt._ACTIVE.get()[2]
        assert caps.browser is caps.provider is None and caps.replace is False
        assert caps.cards_json is None
        assert 'Fetched distinct body' not in prompt and 'Issued references' not in prompt
        assert kw['tools']==[INSPECT,WRITE]
        return {}
    result=WorkService(tmp_path,runner=runner,browser_channel=browser,research_preparer=prepare).submit_work(
        'Question',request_id='r',session_id='s',context={'research':True})
    assert result['status']=='failed' and not result['artifacts']
    assert [k for k,_ in calls]==['search']+['get']*5
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    c,b,r=fixture(); cat=nav.prepare_navigation(c,b,agent_server._checked_research_security(owner),get_records_json=r,deadline=ledger.deadline)
    ledger._prepare_navigation(b,cat,c,r,agent_server._checked_research_security(owner))
    owner.config.security.mode='block'
    with pytest.raises(ValueError): ledger._check_policy(agent_server._checked_research_security(owner))

def test_v3_missing_preparer_never_collects_or_composes(tmp_path,sdk_io):
    from src.brain.work_service import WorkService
    browser,calls,_=sdk_io
    result=WorkService(tmp_path,runner=lambda *a,**kw:pytest.fail('compose'),browser_channel=browser).submit_work(
        'Question',request_id='r',session_id='s',context={'research':True})
    assert result['status']=='failed' and calls==[]

@pytest.mark.parametrize('stage',['before_intent','after_intent'])
def test_v3_intent_race_and_ack_failure_preserve_effect(tmp_path,monkeypatch,stage):
    state=setup(tmp_path); data=read_three(state); ledger=state[0]
    entered=threading.Barrier(2); released=threading.Barrier(2)
    if stage=='before_intent':
        original=ledger.write_intent
        def delayed(*a,**kw):
            entered.wait(timeout=5); released.wait(timeout=5)
            return original(*a,**kw)
        monkeypatch.setattr(ledger,'write_intent',delayed)
    else:
        original=wt.FileWriteTool.execute
        def delayed(*a,**kw):
            entered.wait(timeout=5); released.wait(timeout=5)
            return original(*a,**kw)
        monkeypatch.setattr(wt.FileWriteTool,'execute',delayed)
    def seal():
        entered.wait(timeout=5)
        ledger.seal('first controlled failure')
        released.wait(timeout=5)
    thread=threading.Thread(target=seal); thread.start()
    result=invoke(state,4,WRITE,data)
    thread.join(timeout=5)
    assert not thread.is_alive()
    assert ledger.first_failure=='first controlled failure'
    records,effects=ledger.outcome_snapshot()
    if stage=='before_intent': assert not effects and not (tmp_path/'research.md').exists()
    else:
        assert (tmp_path/'research.md').read_bytes()
        assert len(effects)==1 and effects[0]['state']=='write_attempted'
        assert any(r['tool_name']=='ultima_work_file_write' and r['success'] for r in records)

@pytest.mark.parametrize('fault',['wrong_agent','wrong_args','duplicate_start','missing_start','wrong_metadata','missing_end','late_end'])
def test_v3_observer_fails_closed(tmp_path,fault):
    from openjarvis.core.events import Event,EventType
    state=setup(tmp_path); ledger=state[0]; inspector=state[4][0]
    args=dict(source_id='S1',start_line=1)
    ledger.expect(1,INSPECT,hashlib.sha256(j(args)).hexdigest())
    data=dict(tool=INSPECT,arguments=args,agent='native_react')
    if fault=='wrong_agent': data['agent']='other'
    if fault=='wrong_args': data['arguments']=dict(args,start_line=2)
    def observe(kind,data):
        ledger.observe_navigation(Event(kind,time.time(),data),caller_id=threading.get_ident(),binding_key=state[3].binding_key)
    if fault!='missing_start': observe(EventType.TOOL_CALL_START,data)
    if fault=='duplicate_start': observe(EventType.TOOL_CALL_START,data)
    result=inspector.execute(**args)
    if fault in ('wrong_agent','wrong_args','duplicate_start','missing_start'):
        assert not result.success
    elif fault=='missing_end':
        with pytest.raises(ValueError): ledger.promote_visible(1,hashlib.sha256(result.content.encode()).hexdigest())
    else:
        metadata=dict(result.metadata)
        if fault=='wrong_metadata': metadata['adapter_uuid']=str(uuid.uuid4())
        else: ledger.seal('expired before END')
        observe(EventType.TOOL_CALL_END,dict(tool=INSPECT,agent='native_react',success=True,result=result.content,metadata=metadata))
    assert ledger._issued==[]
    assert not list(tmp_path.iterdir())

@pytest.mark.parametrize('fault',['duplicate_enroll','second_object','skip_callback','throwing_subscriber'])
def test_v3_exact_enrollment_permit(tmp_path,fault):
    from openjarvis.core.events import Event,EventType
    state=setup(tmp_path); ledger=state[0]
    if fault=='duplicate_enroll':
        with pytest.raises(ValueError): ledger.enroll(INSPECT,object())
    elif fault=='skip_callback':
        ledger.expect(1,INSPECT,hashlib.sha256(j(dict(source_id='S1',start_line=1))).hexdigest())
        assert not state[4][0].execute(source_id='S1',start_line=1).success
    elif fault=='second_object':
        args=dict(source_id='S1',start_line=1); digest=hashlib.sha256(j(args)).hexdigest()
        ledger.expect(1,INSPECT,digest)
        ledger.observe_navigation(Event(EventType.TOOL_CALL_START,time.time(),dict(tool=INSPECT,agent='native_react',arguments=args)),
            caller_id=threading.get_ident(),binding_key=state[3].binding_key)
        with pytest.raises(ValueError): ledger.claim(1,INSPECT,digest,str(uuid.uuid4()),instance=object())
    else:
        def broken(event): raise RuntimeError('subscriber failure')
        state[6].subscribe(EventType.TOOL_CALL_START,broken)
        result=invoke(state,1,INSPECT,dict(source_id='S1',start_line=1))
        assert result.success and len(ledger._issued)==1
    assert not list(tmp_path.iterdir())

@pytest.mark.parametrize('fault',['false_success','wrong_bytes'])
def test_v3_file_success_does_not_substitute_bytes(tmp_path,monkeypatch,fault):
    from openjarvis.core.types import ToolResult
    state=setup(tmp_path); data=read_three(state)
    original=wt.FileWriteTool.execute
    def bad(tool,**args):
        if fault=='wrong_bytes': original(tool,**dict(args,content='wrong bytes'))
        return ToolResult(tool_name='file_write',success=True,content='claimed')
    monkeypatch.setattr(wt.FileWriteTool,'execute',bad)
    result=invoke(state,4,WRITE,data)
    assert not result.success and state[0].first_failure
    assert state[0].outcome_snapshot()[1][0]['state']=='write_attempted'
