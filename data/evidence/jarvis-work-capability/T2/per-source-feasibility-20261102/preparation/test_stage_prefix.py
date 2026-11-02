"""Offline only. Every SDK request is handled by HTTPX MockTransport."""
from pathlib import Path
import copy
import json
import os
import socket
import sys
import time
from unittest.mock import patch
import pytest

import run_stage_prefix as h
sys.path.insert(0,str(h.CHECKOUT))


@pytest.fixture(autouse=True)
def deny_sockets(monkeypatch):
    def deny(*a,**kw): raise AssertionError('real socket prohibited during preparation')
    monkeypatch.setattr(socket.socket,'connect',deny)
    monkeypatch.setattr(socket.socket,'connect_ex',deny)
    monkeypatch.setattr(socket,'getaddrinfo',deny)


def fresh_ledger(clock=time.monotonic):
    _,sources=h.load_material()
    source=sources[1]; view,omitted=h.project(source)
    assert not omitted
    return h.StageLedger(dict(request_id='r',session_id='s',task_id='t'),source,view,h.cards(source,view),clock()+36,clock)


def payload_for(ledger):
    # Mechanical fixture derives an operation witness, never a model hint.
    ref,card=next((r,c) for r,c in ledger.table.items() if c['kind']=='code')
    return dict(stage_token=ledger.token,facts=[dict(claim=card['symbol'],ref=ref,
               ranges=[dict(lo=card['first_line'],hi=card['last_line'])])])


def test_general_projection_and_same_anchor_rules():
    from src.brain import work_research as wr
    _,sources=h.load_material()
    for source in sources:
        view,omitted=h.project(source)
        assert len(h.compact(view))<=24000
        table=h.cards(source,view)
        assert 1<=len(table)<=48
        assert list(table)==list(range(1,len(table)+1))
        if source['source_id']=='S2':
            assert not omitted
            previous={k:c for k,c in wr.reference_cards(h.compact(sources)).items() if c['source_id']=='S2'}
            assert [(c['kind'],c['symbol'],c['first_line'],c['last_line']) for c in table.values()]==[
                (c['kind'],c['symbol'],c['first_line'],c['last_line']) for c in previous.values()]
    oversized=copy.deepcopy(sources[0]); oversized['text']='\n'.join('line '*50 for _ in range(300))
    view,omitted=h.project(oversized)
    assert omitted and view['omitted']
    assert all(n not in dict(view['lines']) for lo,hi in omitted for n in range(lo,hi+1))


@pytest.mark.parametrize('mode',['foreign','invalid_ref','length','replay','late','changed','duplicate','binding_tamper'])
def test_stage_negative(mode):
    now=[10.]
    ledger=fresh_ledger(lambda:now[0]); payload=payload_for(ledger)
    if mode=='foreign': payload['stage_token']='foreign'
    if mode=='invalid_ref': payload['facts'][0]['ref']=49
    if mode=='length': payload['facts'][0]['claim']='x'*401
    if mode=='changed': ledger.visible.clear()
    if mode=='duplicate': payload['facts']*=2
    if mode=='binding_tamper': ledger.binding['request_id']='another-request'
    ledger.protected=h.sha(h.compact(payload).encode())
    if mode=='replay': ledger.consume(payload)
    if mode=='late': now[0]=47
    with pytest.raises(Exception): ledger.consume(payload)


@pytest.mark.parametrize('mode',['happy','wrong_model','wrong_version','length','late_trickle','late_END'])
def test_actual_sdk_prefix(tmp_path,monkeypatch,mode):
    import httpx
    from openjarvis import Jarvis
    from openjarvis.core.config import JarvisConfig
    from openjarvis.core.events import EventType
    from openjarvis.core.registry import ToolRegistry
    from openjarvis.engine.ollama import OllamaEngine
    from src.brain import agent_server
    now=[100.]; requests=[]; manifests=[]
    monkeypatch.setattr(h,'register_stage',h.register_stage)
    # Registry is process global in SDK. Each test removes its own registration;
    # actual CLI only registers once and never modifies an existing entry.
    assert not ToolRegistry.contains(h.TOOL)
    original_register=h.register_stage
    holder={}
    def register(ledger):
        holder['ledger']=ledger
        return original_register(ledger)
    monkeypatch.setattr(h,'register_stage',register)
    def transport(req):
        requests.append(dict(method=req.method,path=req.url.path,timeout=req.extensions['timeout']))
        if req.url.path=='/api/version':
            return httpx.Response(200,json={'version':'wrong' if mode=='wrong_version' else '0.32.15'})
        if req.url.path=='/api/tags': return httpx.Response(200,json={'models':[{'name':h.MODEL,'digest':h.DIGEST}]})
        assert req.method=='POST' and req.url.path=='/api/chat'
        body=json.loads(req.content)
        assert body['options']==dict(num_ctx=16384,temperature=0,num_predict=480)
        assert all(body[k] is False for k in ('stream','think','truncate','shift'))
        payload=payload_for(holder['ledger'])
        if mode=='length': payload['facts'][0]['claim']='x'*401
        if mode=='late_trickle': now[0]=137  # response arrives despite inactivity timeout: absolute gate wins
        return httpx.Response(200,json=dict(model='wrong' if mode=='wrong_model' else h.MODEL,
            message=dict(role='assistant',content=h.compact(dict(action=h.TOOL,action_input=payload))),
            done=True,done_reason='stop',prompt_eval_count=4000,eval_count=50))
    client=httpx.Client(base_url=h.ORIGIN,transport=httpx.MockTransport(transport))
    # Public HTTPX construction injection only: actual SDK engine-selection,
    # OllamaEngine.health and all security setup execute unchanged.
    init=httpx.Client.__init__
    def mock_init(self,*args,**kwargs):
        kwargs['transport']=httpx.MockTransport(transport)
        init(self,*args,**kwargs)
    monkeypatch.setattr(httpx.Client,'__init__',mock_init)
    owner=h.make_owner(tmp_path)
    owner._ensure_engine()
    raw=owner._engine._inner._engine
    assert type(raw) is OllamaEngine
    assert len(requests)==1 and requests[0]['path']=='/api/tags'
    requests.clear()
    original_owner=owner._engine
    if mode=='late_END':
        def delay(event):
            if event.data.get('tool')==h.TOOL: now[0]=137
        owner._bus.subscribe(EventType.TOOL_CALL_END,delay)
    def manifest(): manifests.append(1); return h.DIGEST
    try:
        out=h.run_prefix(owner,client,tmp_path,'S2',manifest,clock=lambda:now[0])
        assert owner._engine is original_owner and not raw._client.is_closed
        if mode=='happy':
            assert out['status']=='PENDING_INDEPENDENT_FACT_REVIEW',out.get('error')
            assert out['confirmed'] and out['consumed'] and out['sdk_result']['turns']==1
            assert out['metadata_gets']==2 and out['native_posts']==1 and manifests==[1]
            assert out['captured_capabilities']['writer_exposed'] is False
            assert len([e for e in out['events'] if e['type']=='tool_call_start'])==1
            assert len([e for e in out['events'] if e['type']=='tool_call_end'])==1
            assert any(e['type']=='agent_turn_end' and e['data'].get('max_turns_exceeded') for e in out['events'])
        else:
            assert out['status']=='FAILED',out
            assert not out.get('confirmed') or mode=='late_END'
        assert out.get('native_posts',0)<=1
        assert all(0<t<=36 for req in requests for t in req['timeout'].values())
        assert not out['effects']
        # A consumed POST cannot be retried even after an error or empty result.
        leaf=h.NativeLeaf(client,holder['ledger'],tmp_path,manifest)
        leaf.posts=1
        with pytest.raises((ValueError,TimeoutError)): leaf.io('POST','/api/chat',json={})
        h.save(tmp_path/'smoke-summary.json',out)
    finally:
        owner.close(); client.close()
        # Test-only cleanup keeps parametrized tests independent.
        ToolRegistry._entries().pop(h.TOOL,None)


def test_duplicate_raw_envelope():
    with pytest.raises(ValueError): h.strict('{"action":"a","action":"b"}')


def test_sampler_projection_preserves_server_schema():
    from src.brain.agent_server import _research_sampler_schema
    ledger=fresh_ledger()
    server=copy.deepcopy(ledger.schema)
    sampler=_research_sampler_schema(server)
    assert 'maxLength' not in h.compact(sampler) and 'maxLength' in h.compact(server)
    assert server==ledger.schema
