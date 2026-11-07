"""Trusted last-exchange evidence must survive failures without reading bodies."""
import copy
import hashlib
import json
import httpx
import pytest
from src.brain import agent_server as server, work_tools as wt
from src.brain.work_navigation import canonical_v3
from src.brain.work_research_diagnostics import capture_failure, validate_failure_diagnostic
from src.brain.tests.test_work_research import sdk_io, mock_jar, stable_navigation_entropy
from src.brain.tests.test_work_failure_diagnostics import early_case, private_packet


def _response(content):
    raw=dict(model='qwen3-8b-uncensored',done=True,done_reason='stop',created_at='2026-11-03T00:00:00Z',
        total_duration=9876543210,load_duration=1234567890,prompt_eval_duration=2345678901,eval_duration=3456789012,
        prompt_eval_count=25,eval_count=10,message=dict(role='assistant',content=content))
    return httpx.Response(200,stream=httpx.ByteStream(json.dumps(raw).encode()))


def failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch,*,fault='http500',route='/api/chat'):
    factory=server._research_client;seen=[];consumed=[];closed=[];hits=[]
    class PrivateBody(httpx.SyncByteStream):
        def __iter__(self):
            consumed.append(True)
            yield b'password = "syntheticsecret"'*50000
        def close(self):closed.append(True)
    def client():
        instance=factory();handle=instance._transport.handle_request
        def receive(request):
            seen.append((request.url.path,bytes(request.content)))
            if request.url.path==route:
                hits.append(request)
                if len(hits)==2:
                    if fault=='http500':return httpx.Response(500,stream=PrivateBody())
                    if fault=='bad_json':return httpx.Response(200,stream=httpx.ByteStream(b'{'))
                    if fault=='overflow':return httpx.Response(200,stream=httpx.ByteStream(b'x'*65537))
                    if fault=='scan':return _response(json.dumps(dict(final_answer='password = "syntheticsecret"')))
                    if fault=='schema':return _response('{"final_answer":7}')
                    if fault=='connect':raise httpx.ConnectError('synthetic connection failure',request=request)
                    raise AssertionError(fault)
            return handle(request)
        monkeypatch.setattr(instance._transport,'handle_request',receive)
        return instance
    monkeypatch.setattr(server,'_research_client',client)
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1)
    return result,ledger,seen,consumed,closed


def test_http500_has_request_bound_status_without_reading_private_body(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger,seen,consumed,closed=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch)
    assert result['status']=='failed' and result['error']=='Research HTTP status'
    packet=private_packet(result,ledger);last=packet['last_http']
    assert last==dict(generation=2,receipt_index=5,route='chat',status=500,send_reserved=True,
        request_sha256=hashlib.sha256(seen[-1][1]).hexdigest(),request_bytes=len(seen[-1][1]),
        downloaded=0,inspected=0,admitted=0,retained=0,transport_failed=True,validated_response=False)
    assert not consumed and closed and len([p for p,_ in seen if p=='/api/chat'])==2
    assert packet['branch']=='unvalidated_response' and len(packet['pages'])==1
    assert packet['pages'][0]['confirmed'] and not packet['pages'][0]['visible']
    assert packet['budget']['native_posts']==2 and packet['budget']['completed_posts']==1
    assert packet['complete'] is False and packet['acceptance_credit']==0
    assert not packet['write_confirmed'] and not packet['ack_confirmed'] and not list(tmp_path.rglob('research.md'))
    assert 'syntheticsecret' not in json.dumps(packet)+json.dumps(result)
    # The same original secured request still goes to native chat, without tools or retry.
    sent=json.loads(seen[-1][1])
    assert sent['think'] is False and sent['stream'] is False and sent['truncate'] is False and sent['shift'] is False
    assert sent.get('tools',[])==[] and type(sent['format']) is dict
    assert sent['options']==dict(num_ctx=16384,num_predict=256,temperature=0.0)
    assert len(seen[-1][1])<=49152


@pytest.mark.parametrize('fault',['bad_json','overflow','scan','schema','connect'])
def test_non_http_failures_keep_http_status_distinct_from_validation(tmp_path,sdk_io,mock_jar,monkeypatch,fault):
    result,ledger,seen,_,_=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch,fault=fault)
    assert result['status']=='failed'
    packet=private_packet(result,ledger);last=packet['last_http']
    assert last['status']==(None if fault=='connect' else 200)
    assert last['send_reserved'] and not last['validated_response'] and last['generation']==2
    assert last['transport_failed']==(fault in ('connect','overflow'))
    assert last['request_sha256']==hashlib.sha256(seen[-1][1]).hexdigest()
    assert packet['branch']=='unvalidated_response' and packet['acceptance_credit']==0
    assert 'syntheticsecret' not in json.dumps(packet)+json.dumps(result)
    if fault=='overflow':
        assert last['inspected']==65537 and last['admitted']==last['retained']==65536
    if fault=='connect':
        assert last['downloaded'] is None and last['inspected']==0
    assert not list(tmp_path.rglob('research.md'))


@pytest.mark.parametrize('route,label,index',[('/api/version','version',3),('/api/tags','tags',4)])
def test_metadata_http_failure_does_not_inherit_previous_chat_validation(tmp_path,sdk_io,mock_jar,monkeypatch,route,label,index):
    result,ledger,_,consumed,_=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch,route=route)
    packet=private_packet(result,ledger);last=packet['last_http']
    assert last['route']==label and last['generation']==2 and last['receipt_index']==index and last['status']==500
    assert last['request_bytes']==0 and last['request_sha256']==hashlib.sha256(b'').hexdigest()
    assert not last['validated_response'] and not consumed and packet['budget']['native_posts']==1


def test_admission_refusal_is_not_an_http_response_or_a_sent_request(tmp_path,sdk_io,mock_jar,monkeypatch):
    factory=server._research_client;posts=[]
    def client():
        instance=factory();build=instance.build_request
        def request(method,path,**kwargs):
            prepared=build(method,path,**kwargs)
            if method=='POST':
                posts.append(path)
                if len(posts)==2:wt._ACTIVE.get()[1].deadline=wt.monotonic()+54
            return prepared
        monkeypatch.setattr(instance,'build_request',request)
        return instance
    monkeypatch.setattr(server,'_research_client',client)
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1)
    packet=private_packet(result,ledger);last=packet['last_http']
    assert result['status']=='failed' and 'admission deadline' in result['error']
    assert last['generation']==2 and last['route']=='chat' and not last['send_reserved']
    assert last['status'] is None and last['downloaded'] is None and last['transport_failed']
    assert last['inspected']==last['admitted']==last['retained']==0 and not last['validated_response']
    assert packet['budget']['native_posts']==1 and len(mock_jar[2])==1


def test_validated_http200_still_does_not_grant_delivery_credit(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1)
    packet=private_packet(result,ledger);last=packet['last_http']
    assert last['status']==200 and last['validated_response'] and not last['transport_failed']
    assert packet['branch']=='final_before_write' and result['status']=='failed'
    assert packet['acceptance_credit']==0 and not packet['write_confirmed'] and not packet['ack_confirmed']


def test_last_http_diagnostic_freezes_before_late_receipt_mutation(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger,*_=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch)
    raw=ledger._failure_diagnostic;packet=private_packet(result,ledger)
    assert packet['last_http']['status']==500
    ledger._runtime_transport.receipts[-1].update(status=200,entity_sha256='0'*64,error=None)
    ledger._timeline.clear()
    assert capture_failure(ledger)==result['research_diagnostic'] and ledger._failure_diagnostic==raw


@pytest.mark.parametrize('poison',['missing_event','duplicate_event','event_kind','wire_digest','route','count','status'])
def test_untrusted_or_incoherent_local_receipt_projection_fails_closed(tmp_path,sdk_io,mock_jar,monkeypatch,poison):
    def corrupt(response,ledger):
        r=ledger._runtime_transport.receipts[-1]
        index=len(ledger._runtime_transport.receipts)-1
        event=next(e for e in ledger._timeline if e['kind']=='send' and e['receipt_index']==index)
        if poison=='missing_event':ledger._timeline.remove(event)
        elif poison=='duplicate_event':ledger._timeline.append(copy.deepcopy(event))
        elif poison=='event_kind':event['kind']='admission_refused'
        elif poison=='wire_digest':ledger._runtime_wires[-1]['hashes']['entity']='0'*64
        elif poison=='route':r['path']='https://private.invalid/secret'
        elif poison=='count':r['admitted']=True
        elif poison=='status':r['status']=True
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=corrupt)
    assert result['error']=='Missing nonempty immutable runtime proof'
    assert result['research_diagnostic']['status']=='UNAVAILABLE'
    assert not hasattr(ledger,'_failure_diagnostic')


@pytest.mark.parametrize('change',['field','route','status_bool','status_low','status_high','generation_zero','generation_high',
    'index_bool','index_high','bytes_bool','bytes_high','digest','downloaded_bool','downloaded_high','inspected',
    'retained','unsent','validated','transport_failed','version'])
def test_closed_http_decoder_rejects_forged_shape_and_contradictions(tmp_path,sdk_io,mock_jar,monkeypatch,change):
    result,ledger,*_=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch)
    packet=private_packet(result,ledger);last=packet['last_http']
    changes=dict(route='arbitrary',status_bool=True,status_low=99,status_high=600,generation_zero=0,generation_high=9,
        index_bool=True,index_high=24,bytes_bool=True,bytes_high=2**63,digest='x',downloaded_bool=True,downloaded_high=2**63,
        inspected=65538,retained=1,unsent=False,validated=True,transport_failed=False)
    fields=dict(status_bool='status',status_low='status',status_high='status',generation_zero='generation',generation_high='generation',
        index_bool='receipt_index',index_high='receipt_index',bytes_bool='request_bytes',bytes_high='request_bytes',digest='request_sha256',
        downloaded_bool='downloaded',downloaded_high='downloaded',unsent='send_reserved',validated='validated_response')
    if change=='field':last['body']='private body'
    elif change=='version':packet['kind']='research_failure_diagnostic_v2'
    else:last[fields.get(change,change)]=changes[change]
    with pytest.raises(ValueError):validate_failure_diagnostic(canonical_v3(packet),ledger._navigation.binding_key)
