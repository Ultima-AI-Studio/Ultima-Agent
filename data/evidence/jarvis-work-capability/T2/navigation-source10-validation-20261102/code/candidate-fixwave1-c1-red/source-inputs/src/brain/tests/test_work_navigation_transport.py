"""Actual HTTPX streaming boundaries and complete SDK navigation transport."""
import json
import time
import httpx
import pytest
from src.brain import agent_server as server
from src.brain import work_tools as wt
from src.brain.tests.test_work_research import sdk_io,mock_jar,submit,stable_navigation_entropy,source9_clock

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


def genuine_navigation(tmp_path,sdk_io,mock_jar):
    from src.brain.tests.test_work_research import RESTRICTED
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    assert result['status']=='succeeded',result['error']
    ledger=RESTRICTED[result['task_id']]
    return result,ledger


def fractional_navigation(tmp_path,sdk_io,mock_jar,state,monkeypatch,edge=False):
    import hashlib,math
    from dataclasses import asdict
    from pathlib import Path
    from src.brain import work_service
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    monkeypatch.setattr(work_service,'monotonic',lambda:800.2)
    author=math.nextafter(1005.2,-math.inf) if edge else 1000.1
    ack=math.nextafter(1060.2,-math.inf) if edge else 1040.1
    state['now']=author
    build=httpx.Client.build_request;send=httpx.Client.send;prepared={};observed=[]
    def capture(client,verb,*args,**kwargs):
        request=build(client,verb,*args,**kwargs)
        ledger=wt._ACTIVE.get()[1]
        if ledger._runtime_transport.generations==5: state['now']=ack
        prepared[id(request)]=hashlib.sha256(request.content).hexdigest()
        return request
    def inspect(client,request,*args,**kwargs):
        digest=hashlib.sha256(request.content).hexdigest()
        assert prepared.pop(id(request))==digest
        observed.append(dict(method=request.method,path=request.url.path,at=repr(state['now']),
            timeout=dict(request.extensions['timeout']),entity_sha256=digest))
        return send(client,request,*args,**kwargs)
    monkeypatch.setattr(httpx.Client,'build_request',capture)
    monkeypatch.setattr(httpx.Client,'send',inspect)
    from src.brain.tests.test_work_research import RESTRICTED
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    if result['status']!='succeeded' and hasattr(ledger,'_runtime_prewrite'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_prewrite,
            runtime_inputs=ledger._runtime_inputs)
    assert result['status']=='succeeded',result['error']
    assert ledger.deadline==1060.2 and not prepared and len(observed)==15
    for index,item in enumerate(observed):
        cap=(1060.2-ack) if index>=12 else (1060.2-author)-55
        assert item['timeout']==dict(connect=cap,read=cap,write=cap,pool=cap)
    if not edge: assert observed[0]['timeout']['read']==5.100000000000023
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,
        require_ack=True,runtime_inputs=ledger._runtime_inputs)
    artifact=Path(result['artifacts'][0]['path']);artifact_hash=hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert artifact_hash==result['artifacts'][0]['sha256']
    for name,raw in [('runtime',ledger._runtime_final),('prewrite',ledger._runtime_prewrite),
            ('issued',ledger.issued_snapshot.replay_json),('views',ledger.issued_snapshot.views_json),
            ('inputs',canonical_v3(dict(asdict(ledger._runtime_inputs),binding_key=list(ledger._runtime_inputs.binding_key))))]:
        (tmp_path/('fractional-'+name+'.json')).write_bytes(raw)
    (tmp_path/'fractional-proof.json').write_text(json.dumps(dict(edge=edge,deadline=repr(ledger.deadline),
        author_at=repr(author),ack_at=repr(ack),prepared_requests=observed,artifact=str(artifact),
        artifact_sha256=artifact_hash,replay_accepted=True)),encoding='utf8')
    return ledger


@pytest.mark.parametrize('edge',[False,True])
def test_fix2_n1_fractional_prepared_sdk_replay(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch,edge):
    fractional_navigation(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch,edge)


@pytest.mark.parametrize('ack',[False,True])
@pytest.mark.parametrize('method',['GET','POST'])
def test_fix2_n1_next_float_above_cap_rejected(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch,ack,method):
    import math
    from src.brain.work_research import verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    ledger=fractional_navigation(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch)
    packet=json.loads(ledger._runtime_final if ack else ledger._runtime_prewrite)
    index=(12 if ack else 0)+(2 if method=='POST' else 0)
    receipt=packet['transport']['receipts'][index];timeout=json.loads(receipt['timeout_json'])
    timeout['read']=math.nextafter(timeout['read'],math.inf)
    receipt['timeout_json']=json.dumps(timeout,sort_keys=True,separators=(',',':'))
    with pytest.raises(ValueError,match='Runtime final timeout admission drift'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,canonical_v3(packet),
            require_ack=ack,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('ack',[False,True])
@pytest.mark.parametrize('method',['GET','POST'])
@pytest.mark.parametrize('side',[-1,0,1])
def test_fix2_n1_fractional_send_boundary(monkeypatch,ack,method,side):
    import math
    threshold=1060.2 if ack else 1005.2
    now=math.nextafter(threshold,-math.inf) if side<0 else math.nextafter(threshold,math.inf) if side>0 else threshold
    monkeypatch.setattr(wt,'monotonic',lambda:now)
    ledger=wt.WorkLedger();ledger.deadline=1060.2;observed=[];prepared=[]
    def receive(request):
        assert request is prepared[0]
        observed.append(dict(request.extensions['timeout']))
        return httpx.Response(200,stream=httpx.ByteStream(b'{}'))
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(receive),trust_env=False) as client:
        build=client.build_request
        def capture(*args,**kwargs):
            request=build(*args,**kwargs);prepared.append(request);return request
        monkeypatch.setattr(client,'build_request',capture)
        transport=server._ResearchTransport(client,ledger)
        if side<0:
            assert transport.exchange(method,'/api/chat' if method=='POST' else '/api/version',
                'chat' if method=='POST' else 'metadata',ack=ack)==b'{}'
            cap=(1060.2-now)-(0 if ack else 55)
            assert observed==[dict(connect=cap,read=cap,write=cap,pool=cap)] and cap>0
        else:
            with pytest.raises(ValueError,match='admission deadline|acknowledgement deadline'):
                transport.exchange(method,'/api/chat' if method=='POST' else '/api/version',
                    'chat' if method=='POST' else 'metadata',ack=ack)
            assert not observed and not transport.receipts[-1]['send_reserved']


@pytest.mark.parametrize('kind',['START','END'])
def test_fix2_f3_writer_transcript_identity(tmp_path,sdk_io,mock_jar,kind):
    from src.brain.work_research import verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    _,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,
        require_ack=True,runtime_inputs=ledger._runtime_inputs)
    packet=json.loads(ledger._runtime_final if kind=='END' else ledger._runtime_prewrite)
    original_prewrite=packet['prewrite_packet']
    event=json.loads(packet['events'][-1]); event['data']['agent']='foreign'
    packet['events'][-1]=json.dumps(event,sort_keys=True,separators=(',',':'))
    assert packet['prewrite_packet']==original_prewrite
    with pytest.raises(ValueError,match='writer '+kind+' identity'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,canonical_v3(packet),
            require_ack=kind=='END',runtime_inputs=ledger._runtime_inputs)


def escaped_scanner_fixture():
    """Reuse the reviewed synthetic fixture without duplicating decoded evidence."""
    import ast,inspect,textwrap
    from src.brain.tests.test_work_navigation import test_v3_placeholder_renderability_does_not_expose_or_certify_wire
    tree=ast.parse(textwrap.dedent(inspect.getsource(test_v3_placeholder_renderability_does_not_expose_or_certify_wire)))
    reference=next(n.value for n in ast.walk(tree) if isinstance(n,ast.Constant) and isinstance(n.value,str)
        and n.value.startswith('N3.') and len(n.value)==19 and n.value[3:].isdecimal())
    return reference[3:]


def escaped_envelope(value):
    from src.brain.work_navigation import canonical_v3
    raw=canonical_v3(value).decode()
    digits=set(escaped_scanner_fixture())
    encoded=''.join('\\u'+format(ord(c),'04x') if c in digits else c for c in raw)
    if json.loads(encoded)!=value: raise AssertionError('Synthetic escape fixture mismatch')
    return encoded


def rewrite_response(packet,index,value,content):
    import hashlib
    from src.brain.work_navigation import canonical_v3
    wire=packet['wires'][index];wire['raw']['message']['content']=content
    wire['raw_envelope']=value;wire['secured_envelope']=value
    wire['raw_response']=canonical_v3(wire['raw']).decode()
    receipt=packet['transport']['receipts'][index*3+2];size=len(wire['raw_response'].encode())
    receipt.update(response_sha256=hashlib.sha256(wire['raw_response'].encode()).hexdigest(),
        downloaded=size,inspected=size,admitted=size,retained=size)
    packet['transport']['admitted']['chat']=sum(r['admitted'] for r in packet['transport']['receipts'] if r['kind']=='chat')


@pytest.mark.parametrize('fault',['empty','whitespace','escaped_final','escaped_action'])
def test_fix2_f4_decoded_envelope_replay(tmp_path,sdk_io,mock_jar,fault):
    import hashlib
    from src.brain.work_research import verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    _,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    action=fault=='escaped_action'
    raw=ledger._runtime_prewrite if action else ledger._runtime_final
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=not action,runtime_inputs=ledger._runtime_inputs)
    packet=json.loads(raw);original_prefix=packet['prewrite_packet'];index=len(packet['wires'])-1
    if action:
        value=packet['wires'][index]['raw_envelope'];value['action_input']['title']=escaped_scanner_fixture()
        start=json.loads(packet['events'][-1]);start['data']['arguments']=value['action_input'];packet['events'][-1]=json.dumps(start)
        next(n for n in reversed(packet['timeline']) if n['kind']=='expect')['args_hash']=hashlib.sha256(canonical_v3(value['action_input'])).hexdigest()
    else: value=dict(final_answer='' if fault=='empty' else ' \t ' if fault=='whitespace' else escaped_scanner_fixture())
    content=escaped_envelope(value) if fault.startswith('escaped') else canonical_v3(value).decode()
    if fault.startswith('escaped'):
        assert all(s.scan(content).clean for s in ledger._policy.scanners)
        assert any(not s.scan(escaped_scanner_fixture()).clean for s in ledger._policy.scanners)
    rewrite_response(packet,index,value,content)
    assert packet['prewrite_packet']==original_prefix
    with pytest.raises(ValueError,match='Unsafe native evidence string' if fault.startswith('escaped') else 'Empty research final answer'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,canonical_v3(packet),
            require_ack=not action,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('action',[False,True])
def test_fix2_f4_encoded_answer_live_decode_gate(tmp_path,sdk_io,mock_jar,action):
    from src.brain.tests.test_work_research import RESTRICTED
    def unsafe(body):
        value=json.loads(navigation_reply(body))
        if action: value['action_input']['title']=escaped_scanner_fixture()
        else: value['final_answer']=escaped_scanner_fixture()
        content=escaped_envelope(value)
        assert all(s.scan(content).clean for s in wt._ACTIVE.get()[1]._policy.scanners)
        return content
    unsafe.no_auto_navigation=True
    mock_jar[3].extend([navigation_reply]*3+([unsafe] if action else [navigation_reply,unsafe]))
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['status']==('failed' if action else 'needs_attention') and 'Unsafe research output' in result['error']
    assert len(ledger._runtime_wires)==(3 if action else 4)
    assert len(list((tmp_path/result['task_id']).glob('research.md')))==int(not action)


def test_fix1_f2_coherent_title_substitution_rejected(tmp_path,sdk_io,mock_jar):
    import copy,hashlib
    from pathlib import Path
    from src.brain.work_research import verify_research_artifacts
    result,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    artifact=copy.deepcopy(result['artifacts'][0])
    record=copy.deepcopy(next(r for r in ledger.snapshot() if r['tool_name']=='ultima_work_research_write'))
    for key in ('submitted_json','payload_json'):
        value=json.loads(record['result'][key]); value['title']='Coherent substitute title'; record['result'][key]=json.dumps(value)
    path=Path(artifact['path']); path.write_bytes(b'# Coherent substitute title\n'+path.read_bytes().split(b'\n',1)[1])
    artifact['sha256']=record['result']['sha256']=hashlib.sha256(path.read_bytes()).hexdigest()
    with pytest.raises(ValueError,match='authored|receipt|intent'):
        verify_research_artifacts(ledger._binding,[artifact],[record],ledger._collection.catalogue_json,required_version=3,
            issued_snapshot=ledger.issued_snapshot,runtime_packet=ledger._runtime_final,require_ack=True,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('fault',['report_generation','report_binding','file_binding','effect_binding'])
def test_fix1_f2_all_original_receipt_and_adapter_fields_bound(tmp_path,sdk_io,mock_jar,fault):
    import copy
    from src.brain.work_research import verify_research_artifacts,verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    result,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    record=copy.deepcopy(next(r for r in ledger.snapshot() if r['tool_name']=='ultima_work_research_write'))
    packet=json.loads(ledger._runtime_final)
    if fault=='report_generation': record['result']['generation']+=1
    elif fault=='report_binding': record['result']['binding'][0]='other-request'
    elif fault=='file_binding': packet['execution']['files'][0]['request_id']='other-request'
    else: packet['execution']['effects'][0]['request_id']='other-request'
    with pytest.raises(ValueError):
        verify_research_artifacts(ledger._binding,result['artifacts'],[record],ledger._collection.catalogue_json,
            required_version=3,issued_snapshot=ledger.issued_snapshot,runtime_packet=canonical_v3(packet),require_ack=True,runtime_inputs=ledger._runtime_inputs)


def rewrite_wire(packet,index):
    import hashlib
    from src.brain.work_navigation import canonical_v3
    wire=packet['wires'][index]; request=json.loads(wire['entity']); request['messages']=wire['secured_messages']
    entity=canonical_v3(request); wire['entity']=entity.decode(); wire['hashes']['messages']=hashlib.sha256(canonical_v3(request['messages'])).hexdigest()
    wire['hashes']['entity']=hashlib.sha256(entity).hexdigest()
    receipt=packet['transport']['receipts'][index*3+2]; receipt['entity_sha256']=wire['hashes']['entity']; receipt['entity_bytes']=len(entity)
    packet['transport']['post_bytes']=sum(len(w['entity'].encode()) for w in packet['wires'])


@pytest.mark.parametrize('fault',['chronology','phase_suffix','prompt','prewrite_hash'])
def test_fix1_f3_replay_rejects_coherent_history_mutations(tmp_path,sdk_io,mock_jar,fault):
    from src.brain.work_research import verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    _,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    packet=json.loads(ledger._runtime_final)
    if fault=='chronology': packet['events'][0],packet['events'][1]=packet['events'][1],packet['events'][0]
    elif fault=='phase_suffix':
        packet['wires'][0]['secured_messages'][0]['content']+=' Arbitrary altered phase rule.'
        rewrite_wire(packet,0)
    elif fault=='prompt':
        packet['prompt']=packet['prompt'].replace('Research a subject','Unrelated subject')
        for i,wire in enumerate(packet['wires']):
            wire['secured_messages'][1]['content']=packet['prompt']; rewrite_wire(packet,i)
    else:
        packet['prewrite_sha256']='f'*64
        end=json.loads(packet['events'][-1]); receipt=json.loads(end['data']['result']); receipt['runtime_sha256']='f'*64
        end['data']['result']=canonical_v3(receipt).decode(); end['data']['metadata']['runtime_sha256']='f'*64
        packet['events'][-1]=json.dumps(end)
        packet['wires'][-1]['secured_messages'][-1]['content']='Observation: '+end['data']['result']; rewrite_wire(packet,len(packet['wires'])-1)
    kwargs=dict(require_ack=True)
    if hasattr(ledger,'_runtime_inputs'): kwargs['runtime_inputs']=ledger._runtime_inputs
    with pytest.raises(ValueError):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,canonical_v3(packet),**kwargs)


@pytest.mark.parametrize('fault',['metadata_hash','metadata_digest','outer_model','outer_role','outer_extra','negative_prompt','context_total','options_extra'])
def test_fix1_f4_native_identity_and_outer_policy_replayed(tmp_path,sdk_io,mock_jar,fault):
    import hashlib
    from src.brain.work_research import verify_runtime_packet
    from src.brain.work_navigation import canonical_v3
    _,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar); packet=json.loads(ledger._runtime_final)
    index=len(packet['wires'])-1; wire=packet['wires'][index]
    if fault=='metadata_hash': packet['transport']['receipts'][index*3]['response_sha256']='0'*64
    elif fault=='metadata_digest':
        assert 'identity' in wire,'replayable metadata identity missing'
        tags=json.loads(wire['identity']['tags_response']); tags['models'][0]['digest']='0'*64
        wire['identity']['tags_response']=json.dumps(tags)
        receipt=packet['transport']['receipts'][index*3+1]
        receipt.update(response_sha256=hashlib.sha256(wire['identity']['tags_response'].encode()).hexdigest(),
            admitted=len(wire['identity']['tags_response'].encode()),retained=len(wire['identity']['tags_response'].encode()),
            inspected=len(wire['identity']['tags_response'].encode()),downloaded=len(wire['identity']['tags_response'].encode()))
        packet['transport']['admitted']['metadata']=sum(r['admitted'] for r in packet['transport']['receipts'] if r['kind']=='metadata')
    elif fault=='options_extra':
        request=json.loads(wire['entity']); request['options']['num_gpu']=1; wire['entity']=canonical_v3(request).decode(); rewrite_wire(packet,index)
    else:
        raw=wire['raw']
        if fault=='outer_model': raw['model']='wrong-model'
        elif fault=='outer_role': raw['message']['role']='user'
        elif fault=='outer_extra': raw['unexpected']=True
        elif fault=='negative_prompt': raw['prompt_eval_count']=-1
        else: raw['prompt_eval_count']=16384
        wire['raw_response']=json.dumps(raw); receipt=packet['transport']['receipts'][index*3+2]
        receipt.update(response_sha256=hashlib.sha256(wire['raw_response'].encode()).hexdigest(),admitted=len(wire['raw_response'].encode()),
            retained=len(wire['raw_response'].encode()),inspected=len(wire['raw_response'].encode()),downloaded=len(wire['raw_response'].encode()))
        packet['transport']['admitted']['chat']=sum(r['admitted'] for r in packet['transport']['receipts'] if r['kind']=='chat')
    with pytest.raises(ValueError):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,canonical_v3(packet),require_ack=True,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('method',['GET','POST'])
@pytest.mark.parametrize('expired',[False,True])
def test_fix1_f5_final_send_timeout_and_refusal_receipt(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch,method,expired):
    from src.brain.tests.test_work_research import RESTRICTED
    state=source9_clock;state['now']=200
    build=httpx.Client.build_request; changed=[False]
    def advance(client,verb,*args,**kwargs):
        request=build(client,verb,*args,**kwargs)
        if verb==method and not changed[0]: state['now']=206 if expired else 204;changed[0]=True
        return request
    monkeypatch.setattr(httpx.Client,'build_request',advance)
    mock_jar[3].append('{"final_answer":"refused"}')
    result=submit(tmp_path,sdk_io[0],mock_jar[1]); ledger=RESTRICTED[result['task_id']]; transport=ledger._runtime_transport
    assert result['status']=='failed' and changed[0]
    if expired:
        assert transport.posts==0 and transport.gets==(2 if method=='POST' else 0)
        receipt=transport.receipts[-1]
        assert receipt['method']==method and receipt['send_reserved'] is False and receipt['admission_error']
    else:
        phase='author' if method=='POST' else 'metadata'
        assert next(timeout for label,timeout in state['requests'] if label==phase)==dict(connect=1,write=1,pool=1,read=1)


@pytest.mark.parametrize('proof',['null','empty','mutable'])
def test_fix1_f7_fresh_verifier_requires_immutable_runtime(tmp_path,sdk_io,mock_jar,proof):
    from src.brain.work_research import verify_research_artifacts
    result,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    record=next(r for r in ledger.snapshot() if r['tool_name']=='ultima_work_research_write')
    raw=None if proof=='null' else b'' if proof=='empty' else bytearray(ledger._runtime_final)
    with pytest.raises(ValueError,match='runtime|Runtime'):
        verify_research_artifacts(ledger._binding,result['artifacts'],[record],ledger._collection.catalogue_json,required_version=3,
            issued_snapshot=ledger.issued_snapshot,runtime_packet=raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('proof',['absent','null','empty','mutable'])
def test_fix1_f7_service_missing_final_proof_needs_attention(tmp_path,sdk_io,mock_jar,proof):
    from src.brain.tests.test_work_research import RESTRICTED
    runner=mock_jar[1];mock_jar[3].extend([navigation_reply]*5)
    def drop(*a,**kw):
        response=runner(*a,**kw)
        ledger=wt._ACTIVE.get()[1]
        assert type(ledger._runtime_final) is bytes
        if proof=='absent': del ledger._runtime_final
        else: ledger._runtime_final=None if proof=='null' else b'' if proof=='empty' else bytearray(ledger._runtime_final)
        return response
    result=submit(tmp_path,sdk_io[0],drop)
    assert result['status']=='needs_attention' and not result['artifacts']
    assert len(list(tmp_path.rglob('research.md')))==1
    assert RESTRICTED[result['task_id']].outcome_snapshot()[1][0]['state']=='completed'

@pytest.mark.parametrize('boundary',['before','at','after'])
def test_service_deadline_after_final_readback(tmp_path,sdk_io,mock_jar,source9_clock,monkeypatch,boundary):
    import hashlib, math
    from pathlib import Path
    from src.brain import work_research, work_service
    from src.brain.tests.test_work_research import RESTRICTED

    clock=source9_clock
    monkeypatch.setattr(work_service,'monotonic',lambda:clock['now'])
    verify=work_research.verify_research_artifacts
    sample={}
    def readback(binding,artifacts,reports,*args,**kwargs):
        sources=verify(binding,artifacts,reports,*args,**kwargs)
        if kwargs.get('require_ack'):
            ledger=RESTRICTED[binding.task_id]
            artifact,=artifacts
            report,=reports
            effect,=ledger.outcome_snapshot()[1]
            intent=ledger._intent_record
            assert effect['state']=='completed'
            assert artifact['call_id']==effect['file_call_id']==intent['file_call_id']
            assert report['call_id']==effect['report_call_id']==intent['report_call_id']
            assert report['result']['adapter_uuid']==intent['adapter_uuid']
            assert report['result']['dispatch_uuid']==intent['dispatch_uuid']==effect['dispatch_id']
            assert effect['path']==artifact['path']==str(binding.root/'research.md')
            assert ledger.deadline==260 and clock['now']==0
            sample.update(before=clock['now'],deadline=ledger.deadline,artifact=artifact.copy(),
                effect=effect,intent=intent.copy(),sends=len(clock['requests']))
            clock['now']={'before':math.nextafter(260,-math.inf),'at':260,'after':math.nextafter(260,math.inf)}[boundary]
        return sources
    monkeypatch.setattr(work_research,'verify_research_artifacts',readback)
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    assert len(clock['requests'])==sample['sends']==15 and len(mock_jar[2])==5
    assert result['research_effects']==[sample['effect']] and result['artifacts']==[sample['artifact']]
    path,=tmp_path.rglob('research.md')
    assert path==Path(sample['artifact']['path'])
    assert hashlib.sha256(path.read_bytes()).hexdigest()==sample['artifact']['sha256']==sample['intent']['sha256']
    (tmp_path/'service-deadline.json').write_text(json.dumps(dict(sample,after=clock['now'],
        boundary=boundary,status=result['status'],error=result['error'])),encoding='utf8')
    assert result['status']==('succeeded' if boundary=='before' else 'needs_attention')
    if boundary!='before':
        assert result['error']=='Research acknowledgement deadline'

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
    from dataclasses import asdict
    inputs_bytes=canonical_v3(dict(asdict(ledger._runtime_inputs),binding_key=list(ledger._runtime_inputs.binding_key)))
    (tmp_path/'runtime-inputs.json').write_bytes(inputs_bytes)
    (tmp_path/'prewrite-packet.json').write_bytes(ledger._runtime_prewrite)
    (tmp_path/'issued-snapshot.json').write_bytes(ledger.issued_snapshot.replay_json)
    (tmp_path/'issued-views.json').write_bytes(ledger.issued_snapshot.views_json)
    (tmp_path/'packet-manifest.json').write_text(json.dumps(dict(
        issued_sha256=ledger.issued_snapshot.manifest_sha256,
        runtime_sha256=hashlib.sha256(ledger._runtime_final).hexdigest(),
        views_sha256=hashlib.sha256(ledger.issued_snapshot.views_json).hexdigest(),
        inputs_sha256=hashlib.sha256(inputs_bytes).hexdigest(),
        prewrite_sha256=hashlib.sha256(ledger._runtime_prewrite).hexdigest(),
        artifact_sha256=hashlib.sha256(raw).hexdigest())),encoding='utf8')
    (tmp_path/'external-readback.json').write_text(json.dumps(dict(variant=variant,sha256=hashlib.sha256(raw).hexdigest(),
        expected_sha256=hashlib.sha256(oracle).hexdigest(),sources=fixtures,request_id=result['request_id'],session_id=result['session_id'],
        strict_sizes=strict_sizes,entity_sizes=entity_sizes,persona_sha256=hashlib.sha256(persona.encode()).hexdigest())),encoding='utf8')
    assert hasattr(ledger,'_runtime_final'), 'native proof appendix missing'
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],ledger._runtime_final,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    packet=json.loads(ledger._runtime_final)
    packet['wires'][0]['entity']=packet['wires'][0]['entity'].replace('Research a subject','changed subject')
    from src.brain.work_navigation import canonical_v3
    with pytest.raises(ValueError):
        verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],canonical_v3(packet),require_ack=True,runtime_inputs=ledger._runtime_inputs)
    packet=json.loads(ledger._runtime_final)
    end=json.loads(packet['events'][-1])
    end['data']['metadata']['file_call_id']='00000000-0000-0000-0000-000000000001'
    packet['events'][-1]=json.dumps(end)
    with pytest.raises(ValueError,match='writer'):
        verify_runtime_packet(captured['binding'],ledger.issued_snapshot,captured['collection'],canonical_v3(packet),require_ack=True,runtime_inputs=ledger._runtime_inputs)


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
