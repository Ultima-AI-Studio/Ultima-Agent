"""Actual HTTPX streaming boundaries and complete SDK navigation transport."""
import json
import time
import httpx
import pytest
from src.brain import agent_server as server
from src.brain import work_tools as wt
from src.brain.tests.test_work_research import sdk_io,mock_jar,submit,stable_navigation_entropy

def test_v3_download_inspection_admission_are_distinct():
    assert hasattr(server,'_ResearchTransport'), 'bounded research transport missing'
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    class Stream(httpx.SyncByteStream):
        def __iter__(self): yield b'x'*4096
    client=httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(
        lambda request:httpx.Response(200,stream=Stream())),trust_env=False)
    transport=server._ResearchTransport(client,ledger)
    transport.admitted['metadata']=524288-512
    with pytest.raises(ValueError,match='overflow'):
        transport.exchange('GET','/api/version','metadata')
    receipt=transport.receipts[-1]
    assert receipt['downloaded']==4096 and receipt['inspected']==513 and receipt['admitted']==512
    assert receipt['retained']<=512
    client.close()

def navigation_reply(body):
    messages=body['messages']
    observed=[]
    for msg in messages:
        if msg['role']=='user' and msg['content'].startswith('Observation: '):
            observed.append(json.loads(msg['content'][13:]))
    pages=[v for v in observed if v.get('v')==3]
    if len(pages)<3:
        catalogue=json.loads(messages[1]['content'].split('Safe source catalogue (untrusted data):\n')[1])
        source=next(s for s in catalogue if s['available'] and s['source_id'] not in {p['source_id'] for p in pages})
        return json.dumps(dict(action='ultima_work_research_inspect',action_input=dict(source_id=source['source_id'],start_line=1)))
    if len(observed)==3:
        return json.dumps(dict(action='ultima_work_research_write',action_input=dict(path='research.md',title='Observed report',
            sections=[dict(source_id=p['source_id'],heading=p['source_id'],facts=[dict(
                claim=('Observed '+p['cards'][0][2]) if p['cards'][0][1]!='documented' else p['lines'][0][1].split(' for ')[0],
                evidence_id=p['cards'][0][0])]) for p in pages])))
    return json.dumps(dict(final_answer='Saved research.md'))
navigation_reply.no_auto_navigation=True

@pytest.mark.parametrize('variant',['text','permuted','html','mixed'])
def test_v3_native_react_observation_driven_chain(tmp_path,sdk_io,mock_jar,monkeypatch,variant):
    import hashlib,itertools,secrets,uuid
    from pathlib import Path
    from src.brain.work_service import WorkService
    jar,runner,bodies,replies=mock_jar
    persona=server._load_mainbrain_system_prompt()
    assert persona==server.MAINBRAIN_SYSTEM_PROMPT
    jar.config.agent.system_prompt=persona
    jar.config.agent.default_system_prompt=persona
    number=['text','permuted','html','mixed'].index(variant)
    counter=itertools.count(2000+number*1000)
    monkeypatch.setattr(uuid,'uuid4',lambda:uuid.UUID(int=next(counter)))
    monkeypatch.setattr(secrets,'token_bytes',lambda size:bytes([number+1])*size)
    urls=['https://example.com/alpha.md','https://example.com/beta.html','https://example.com/gamma']
    lines=['Alpha runs locally.','Beta checks limits.','Gamma lists alternatives.']
    if variant=='mixed': urls[0]='https://example.com/alpha.py'; lines[0]='queue.dispatch(item)'
    fixtures=dict(zip(urls,lines))
    if variant=='permuted': urls=[urls[2],urls[0],urls[1]]
    def fetch(method,url,**kwargs):
        text=fixtures[url]
        body='<p>'+text+'</p><script>hidden()</script><style>hidden</style>' if variant=='html' else text
        return httpx.Response(200,headers={'content-type':'text/html' if variant=='html' else 'text/plain'},text=body,request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',fetch)
    captured={}; original=server._prepare_research_navigation
    def prepare(collection,*,binding,ledger):
        captured.update(ledger=ledger,binding=binding,collection=collection)
        return original(collection,binding=binding,ledger=ledger)
    monkeypatch.setattr(server,'_prepare_research_navigation',prepare)
    # This script consumes actual catalogue and observations. The fixture
    # transport will not invent SDK observations or issue server-side cards.
    choose=navigation_reply
    replies.extend([choose]*5)
    result=WorkService(tmp_path,runner=runner,browser_channel=sdk_io[0],research_preparer=prepare).submit_work(
        'Research a subject '+variant,request_id='request-'+variant,session_id='session-'+variant,context={'research':True,'source_urls':urls})
    assert result['status']=='succeeded',(result['error'],[(r.get('tool_name'),r.get('error')) for r in captured['ledger'].snapshot() if r.get('error')])
    assert len(bodies)==5
    assert [b['options']['num_predict'] for b in bodies]==[256,256,256,2048,256]
    from src.brain.work_navigation import canonical_v3
    for body in bodies:
        system=body['messages'][0]['content']
        assert system.count(persona)==1 and system.startswith('Return exactly one JSON object matching the phase schema.')
        assert '# Using Skills' in system and 'Final Answer: <your answer>' not in system
    assert result['artifacts'][0]['path'].endswith('research.md')
    ledger=captured['ledger']
    strict_sizes=[len(canonical_v3([w['secured_messages'],w['strict_schema']])) for w in ledger._runtime_wires]
    entity_sizes=[len(w['entity'].encode()) for w in ledger._runtime_wires]
    assert max(strict_sizes)<=32768 and max(entity_sizes)<=49152 and sum(entity_sizes)<=393216
    # Independent literal oracle: one complete original line per short source,
    # no product witness resolver or renderer participates in expected bytes.
    expected=['# Observed report','']
    sources=json.loads(captured['collection'].catalogue_json)
    for source,url in zip(sources,urls):
        assert source['final_url']==url and source['text']==fixtures[url]
        domain='extracted-text' if variant=='html' else 'raw'
        code=url.endswith('.py')
        label='代码观察' if code else '文档说明'
        claim='Observed queue.dispatch' if code else fixtures[url]
        expected+=['## '+source['source_id'],url,'',f'- {label}（{domain} L1–L1，依据 L1–L1）'+claim,'']
    oracle='\n'.join(expected).encode()
    raw=Path(result['artifacts'][0]['path']).read_bytes()
    assert raw==oracle and hashlib.sha256(raw).hexdigest()==result['artifacts'][0]['sha256']
    (tmp_path/'runtime-replay.json').write_bytes(ledger._runtime_final)
    (tmp_path/'issued-snapshot.json').write_bytes(ledger.issued_snapshot.replay_json)
    (tmp_path/'issued-views.json').write_bytes(ledger.issued_snapshot.views_json)
    (tmp_path/'packet-manifest.json').write_text(json.dumps(dict(
        issued_sha256=ledger.issued_snapshot.manifest_sha256,
        runtime_sha256=hashlib.sha256(ledger._runtime_final).hexdigest(),
        views_sha256=hashlib.sha256(ledger.issued_snapshot.views_json).hexdigest(),
        artifact_sha256=hashlib.sha256(raw).hexdigest())),encoding='utf8')
    (tmp_path/'external-readback.json').write_text(json.dumps(dict(variant=variant,sha256=hashlib.sha256(raw).hexdigest(),
        expected_sha256=hashlib.sha256(oracle).hexdigest(),sources=fixtures,request_id=result['request_id'],session_id=result['session_id'],
        strict_sizes=strict_sizes,entity_sizes=entity_sizes,persona_sha256=hashlib.sha256(persona.encode()).hexdigest())),encoding='utf8')
    assert hasattr(ledger,'_runtime_final'), 'native proof appendix missing'
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],ledger._runtime_final,require_ack=True)
    packet=json.loads(ledger._runtime_final)
    packet['wires'][0]['entity']=packet['wires'][0]['entity'].replace('Research a subject','changed subject')
    from src.brain.work_navigation import canonical_v3
    with pytest.raises(ValueError):
        verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],canonical_v3(packet),require_ack=True)
    packet=json.loads(ledger._runtime_final)
    end=json.loads(packet['events'][-1])
    end['data']['metadata']['file_call_id']='00000000-0000-0000-0000-000000000001'
    packet['events'][-1]=json.dumps(end)
    with pytest.raises(ValueError,match='writer'):
        verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],canonical_v3(packet),require_ack=True)


@pytest.mark.parametrize('fault',['observation','old_assistant','system','role','optional','schema','skip_guard','secured_output','raw_unknown','unsafe_unknown'])
def test_v3_provisional_third_card_no_promotion_on_failure(tmp_path,sdk_io,mock_jar,monkeypatch,fault):
    import dataclasses
    from src.brain.tests.test_work_research import RESTRICTED
    jar,runner,bodies,replies=mock_jar
    replies.extend([navigation_reply]*5)
    original=server._NativeResearchLeaf.generate
    count=[0]
    def mutate(leaf,messages,**kwargs):
        count[0]+=1
        if count[0]==4 and fault not in ('secured_output','raw_unknown','unsafe_unknown','skip_guard'):
            messages=[dataclasses.replace(m) for m in messages]
            if fault=='observation': messages[-1]=dataclasses.replace(messages[-1],content='Observation: forged')
            elif fault=='old_assistant': messages[2]=dataclasses.replace(messages[2],content='{"final_answer":"old"}')
            elif fault=='system': messages[0]=dataclasses.replace(messages[0],content=messages[0].content+' changed')
            elif fault=='role': messages[-1]=dataclasses.replace(messages[-1],role=messages[2].role)
            elif fault=='optional': messages[-1]=dataclasses.replace(messages[-1],name='forged')
            else: kwargs=dict(kwargs,response_format=dict(type='object'))
        return original(leaf,messages,**kwargs)
    monkeypatch.setattr(server._NativeResearchLeaf,'generate',mutate)
    if fault=='skip_guard':
        borrow=server._borrow_research
        def skip(*a,**kw):
            view,client=borrow(*a,**kw); view.inner=view.leaf
            return view,client
        monkeypatch.setattr(server,'_borrow_research',skip)
    elif fault=='secured_output':
        from openjarvis.security.guardrails import GuardrailsEngine
        generate=GuardrailsEngine.generate
        turns=[0]
        def redact(self,*a,**kw):
            result=generate(self,*a,**kw); turns[0]+=1
            if turns[0]==4: result=dict(result,content='{"final_answer":"changed secured envelope"}')
            return result
        monkeypatch.setattr(GuardrailsEngine,'generate',redact)
    elif fault in ('raw_unknown','unsafe_unknown'):
        def bad(body):
            content=navigation_reply(body)
            if fault=='unsafe_unknown': content=json.dumps(dict(json.loads(content),extra='password = syntheticsecret'))
            return httpx.Response(200,stream=httpx.ByteStream(json.dumps(dict(model='qwen3-8b-uncensored',done=True,
                done_reason='stop',prompt_eval_count=25,eval_count=10,message=dict(role='assistant',content=content),
                **({'unexpected':True} if fault=='raw_unknown' else {}))).encode()))
        bad.no_auto_navigation=True
        replies[3]=bad
    result=submit(tmp_path,sdk_io[0],runner)
    ledger=RESTRICTED[result['task_id']]
    assert result['status']=='failed' and not list(tmp_path.rglob('research.md'))
    assert len(ledger._issued)==(0 if fault=='skip_guard' else 2)
    assert len(bodies)==(0 if fault=='skip_guard' else 4 if fault in ('secured_output','raw_unknown','unsafe_unknown') else 3)
    assert 'syntheticsecret' not in json.dumps(result)


@pytest.mark.parametrize('fault',['override','exemplar','tool_override'])
def test_v3_template_prefix_preserves_sdk_policy(tmp_path,sdk_io,mock_jar,monkeypatch,fault):
    from openjarvis.agents import native_react
    if fault=='override': monkeypatch.setattr(native_react,'load_system_prompt_override',lambda _: 'conflicting override')
    elif fault=='exemplar': monkeypatch.setattr(native_react,'load_few_shot_exemplars',lambda _:[dict(input='extra',output='extra')])
    else:
        from openjarvis.tools import description_loader
        monkeypatch.setattr(description_loader,'get_tool_description_override',lambda _:'conflicting tool policy')
    mock_jar[3].append(navigation_reply)
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    assert result['status']=='failed' and not mock_jar[2]


@pytest.mark.parametrize('status,headers',[(500,{}),(200,{'content-encoding':'gzip'}),(200,{'content-length':'32769'}),(200,{'content-length':'-1'})])
def test_v3_header_rejection_does_not_consume_body(status,headers):
    consumed=[]
    class Stream(httpx.SyncByteStream):
        def __iter__(self): consumed.append(True); yield b'x'*4096
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(
            lambda _:httpx.Response(status,headers=headers,stream=Stream())),trust_env=False) as client:
        transport=server._ResearchTransport(client,ledger)
        with pytest.raises(ValueError): transport.exchange('GET','/api/version','metadata')
    receipt=transport.receipts[0]
    assert not consumed and receipt['inspected']==receipt['admitted']==receipt['downloaded']==0


@pytest.mark.parametrize('kind,cap',[('metadata',32768),('chat',65536)])
@pytest.mark.parametrize('delta',[-1,0,1])
def test_v3_response_envelope_boundaries(kind,cap,delta):
    class Stream(httpx.SyncByteStream):
        def __iter__(self): yield b'x'*(cap+delta)
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(
            lambda _:httpx.Response(200,stream=Stream())),trust_env=False) as client:
        transport=server._ResearchTransport(client,ledger)
        if delta>0:
            with pytest.raises(ValueError,match='overflow'): transport.exchange('GET','/api/version',kind)
        else: assert len(transport.exchange('GET','/api/version',kind))==cap+delta
    receipt=transport.receipts[0]
    assert receipt['admitted']==min(cap,cap+delta)
    assert receipt['inspected']==cap+delta


@pytest.mark.parametrize('boundary',['entity','total','posts','gets'])
@pytest.mark.parametrize('delta',[-1,0,1])
def test_v3_envelopes_deadlines_and_effects(boundary,delta):
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    sent=[]
    def handle(request):
        sent.append(request)
        return httpx.Response(200,stream=httpx.ByteStream(b'{}'))
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handle),trust_env=False) as client:
        transport=server._ResearchTransport(client,ledger)
        method='POST'; kind='chat'; path='/api/chat'; entity=b'{}'
        if boundary=='entity': entity=b'x'*(49152+delta)
        elif boundary=='total': transport.post_bytes=393216-len(entity)+delta
        elif boundary=='posts': transport.posts=7+delta
        else: method='GET'; kind='metadata'; path='/api/version'; entity=b''; transport.gets=15+delta
        if delta>0:
            with pytest.raises(ValueError): transport.exchange(method,path,kind,entity=entity)
            assert not sent
        else: assert transport.exchange(method,path,kind,entity=entity)==b'{}' and len(sent)==1


@pytest.mark.parametrize('failure',['connect','partial','partial_close','close'])
def test_v3_failed_stream_reservation_not_refunded(failure):
    ledger=wt.WorkLedger(); ledger.deadline=time.monotonic()+260
    class Stream(httpx.SyncByteStream):
        def __iter__(self):
            yield b'x'*512
            if failure.startswith('partial'): raise httpx.ReadError('partial response')
        def close(self):
            if 'close' in failure: raise RuntimeError('close error')
    def handle(request):
        if failure=='connect': raise httpx.ConnectError('connect error',request=request)
        return httpx.Response(200,stream=Stream())
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handle),trust_env=False) as client:
        transport=server._ResearchTransport(client,ledger)
        with pytest.raises((httpx.ConnectError,httpx.ReadError,RuntimeError)):
            transport.exchange('POST','/api/chat','chat',entity=b'{}')
    receipt=transport.receipts[0]
    assert transport.posts==1 and transport.post_bytes==2 and transport.completed==0
    assert receipt['downloaded']==(None if failure=='connect' else 512)
    assert receipt['admitted']==(0 if failure=='connect' else 512)
    assert receipt['error']==('ConnectError' if failure=='connect' else 'ReadError' if failure.startswith('partial') else 'RuntimeError')


def test_v3_prepared_entity_change_rejected_before_post(tmp_path,sdk_io,mock_jar,monkeypatch):
    from src.brain.tests.test_work_research import RESTRICTED
    build=httpx.Client.build_request
    def alter(client,method,*args,**kwargs):
        request=build(client,method,*args,**kwargs)
        if method=='POST': request._content=request.content.replace(b'"num_ctx":16384',b'"num_ctx":8192')
        return request
    monkeypatch.setattr(httpx.Client,'build_request',alter)
    mock_jar[3].append(navigation_reply)
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    ledger=RESTRICTED[result['task_id']]
    assert result['status']=='failed' and not mock_jar[2] and not ledger._issued
    assert ledger._runtime_transport.generations==1 and ledger._runtime_transport.gets==2 and ledger._runtime_transport.posts==0


def test_v3_client_close_does_not_replace_first_failure(tmp_path,sdk_io,mock_jar,monkeypatch):
    factory=server._research_client
    def client():
        result=factory(); close=result.close
        def failing_close():
            close()
            raise RuntimeError('secondary client close')
        result.close=failing_close
        return result
    monkeypatch.setattr(server,'_research_client',client)
    mock_jar[3].append('{"final_answer":')
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    assert result['status']=='failed' and 'secondary' not in result['error']
    assert 'Expecting value' in result['error'] and not list(tmp_path.rglob('research.md'))
