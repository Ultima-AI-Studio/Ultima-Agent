"""Native rejection evidence must preserve validation, request identity and effects."""
import copy
import hashlib
import json
import httpx
import pytest
from src.brain import agent_server as server, work_research_diagnostics as diagnostics
from src.brain.work_research import checked_native_response, verify_runtime_packet
from src.brain.work_navigation import canonical_v3
from src.brain.tests.test_work_research import sdk_io, mock_jar, submit, RESTRICTED, stable_navigation_entropy
from src.brain.tests.test_work_failure_diagnostics import early_case, private_packet
from src.brain.tests.test_work_navigation_transport import genuine_navigation, navigation_reply
from src.brain.tests.test_work_http_failure_diagnostics import failing_exchange


def valid_raw():
    return dict(model='qwen3-8b-uncensored',done=True,done_reason='stop',prompt_eval_count=25,eval_count=10,
                message=dict(role='assistant',content='private response text'))


def change(raw,path,value):
    keys=path.split('.');parent=raw
    for k in keys[:-1]:parent=parent[k]
    parent[keys[-1]]=value


REFUSALS=[('unknown_private_field','do not persist','extra_fields'),('model','private-model','model'),
    ('done',1,'done'),('done',False,'done'),('done_reason','length','done_reason'),('done_reason',None,'done_reason'),
    ('message',None,'message_type'),('message',[],'message_type'),('message',{},'message_fields'),
    ('message.thinking','private thoughts','message_fields'),('message.role','private-role','message_role'),
    ('message.content',7,'content_type'),('message.content',' \n\t','content_empty'),
    ('prompt_eval_count',True,'prompt_eval_count'),('prompt_eval_count',0,'prompt_eval_count'),
    ('prompt_eval_count',-1,'prompt_eval_count'),('prompt_eval_count','private-count','prompt_eval_count'),
    ('eval_count',True,'eval_count'),('eval_count',0,'eval_count'),('eval_count',-1,'eval_count'),
    ('eval_count',1.5,'eval_count'),('eval_count',257,'completion_limit'),('prompt_eval_count',16375,'context_limit'),
    *[(name,value,name) for name in ('total_duration','load_duration','prompt_eval_duration','eval_duration')
      for value in (True,-1,2**63,1.5)],('created_at',7,'created_at')]


@pytest.mark.parametrize('path,value,reason',REFUSALS)
def test_each_original_guard_has_a_fixed_reason(path,value,reason):
    raw=valid_raw();change(raw,path,value)
    with pytest.raises(ValueError,match='^Invalid native research response$') as exc:checked_native_response(raw,256)
    assert getattr(exc.value,'native_response_reason',None)==reason


@pytest.mark.parametrize('index',range(len(REFUSALS)))
def test_earlier_guard_wins_over_later_created_at(index):
    path,value,reason=REFUSALS[index];raw=valid_raw();raw['created_at']=7;change(raw,path,value)
    with pytest.raises(ValueError) as exc:checked_native_response(raw,256)
    assert getattr(exc.value,'native_response_reason',None)==reason


@pytest.mark.parametrize('alias',['qwen3-8b-uncensored','qwen3-8b-uncensored:latest'])
@pytest.mark.parametrize('limit',[256,2048])
@pytest.mark.parametrize('optional',[False,True])
def test_original_valid_boundaries_and_optional_fields_stay_valid(alias,limit,optional):
    raw=valid_raw();raw.update(model=alias,eval_count=limit,prompt_eval_count=16384-limit)
    if optional:raw.update(created_at='',total_duration=0,load_duration=2**63-1,prompt_eval_duration=0,eval_duration=1)
    assert checked_native_response(raw,limit) is None


def native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,*,updates=None,reads=1,ack=False,hook=None):
    factory=server._research_client;seen=[];hits=[];response_bytes=[]
    def client():
        instance=factory();original=instance._transport.handle_request
        def handle(request):
            response=original(request)
            if request.url.path=='/api/chat':
                seen.append(bytes(request.content));hits.append(True)
                if len(hits)==(5 if ack else reads+1):
                    raw=json.loads(response.read());response.close()
                    for path,value in (updates or [('done_reason','length')]):change(raw,path,value)
                    body=json.dumps(raw,ensure_ascii=False).encode();response_bytes.append(body)
                    return httpx.Response(200,stream=httpx.ByteStream(body))
            return response
        monkeypatch.setattr(instance._transport,'handle_request',handle)
        return instance
    monkeypatch.setattr(server,'_research_client',client)
    if hook:
        original=getattr(diagnostics,'record_native_response_rejection',None)
        assert callable(original),'missing native rejection recorder'
        def capture(*args,**kwargs):
            original(*args,**kwargs);hook(args[0])
        monkeypatch.setattr(diagnostics,'record_native_response_rejection',capture)
    if ack:
        mock_jar[3].extend([navigation_reply]*5)
        result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    else:result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=reads)
    return result,ledger,seen,response_bytes


@pytest.mark.parametrize('updates,reason',[
    ([('done_reason','length')],'done_reason'),([('private_field','password = "syntheticsecret"')],'extra_fields'),
    ([('eval_count',True)],'eval_count'),([('message.thinking','private thoughts')],'message_fields')])
@pytest.mark.parametrize('reads',[1,6])
def test_sdk_native_rejection_is_bound_and_bounded(tmp_path,sdk_io,mock_jar,monkeypatch,updates,reason,reads):
    result,ledger,sent,bodies=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,updates=updates,reads=reads)
    assert result['status']=='failed' and result['error']=='Invalid native research response'
    assert result['content']=='本次研究未交付。' and not list(tmp_path.rglob('research.md'))
    packet=private_packet(result,ledger);native=packet['native_response'];last=packet['last_http']
    assert packet['kind']=='research_failure_diagnostic_v5' and native['reason']==reason
    assert native['request_sha256']==hashlib.sha256(sent[-1]).hexdigest()==last['request_sha256']
    assert native['response_sha256']==hashlib.sha256(bodies[-1]).hexdigest()
    assert native['response_bytes']==len(bodies[-1])==last['admitted']
    assert native['generation']==reads+1==last['generation'] and native['receipt_index']==last['receipt_index']
    assert native['max_tokens']==(2048 if reads==6 else 256)
    assert packet['budget']['reads_used']==reads and packet['budget']['native_posts']==reads+1
    assert packet['branch']=='unvalidated_response' and not packet['write_confirmed'] and not packet['ack_confirmed']
    assert packet['complete'] is False and packet['acceptance_credit']==0
    assert 'syntheticsecret' not in json.dumps(packet)+json.dumps(result) and 'private thoughts' not in json.dumps(packet)
    assert diagnostics.validate_failure_diagnostic(ledger._failure_diagnostic,ledger._navigation.binding_key)==packet


def test_ack_native_rejection_preserves_committed_write(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,ack=True)
    packet=private_packet(result,ledger)
    assert result['error']=='Invalid native research response' and result['status']=='needs_attention'
    assert packet['branch']=='write_without_ack' and packet['write_confirmed'] and not packet['ack_confirmed']
    assert packet['native_response']['generation']==5 and packet['native_response']['max_tokens']==256
    assert len(list(tmp_path.rglob('research.md')))==1 and packet['acceptance_credit']==0


@pytest.mark.parametrize('fault',['http500','bad_json','overflow','scan','schema','connect'])
def test_other_failure_boundaries_never_claim_native_rejection(tmp_path,sdk_io,mock_jar,monkeypatch,fault):
    result,ledger,_,consumed,_=failing_exchange(tmp_path,sdk_io,mock_jar,monkeypatch,fault=fault)
    assert private_packet(result,ledger)['native_response'] is None
    if fault=='http500':assert not consumed


def test_successful_sdk_write_ack_and_replay_unchanged(tmp_path,sdk_io,mock_jar):
    result,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    assert result['status']=='succeeded' and not hasattr(ledger,'_failure_diagnostic')
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,
        require_ack=True,runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('field,value,expected',[('prompt_eval_count',True,None),('eval_count',2**63,None),
    ('eval_count',-1,-1),('done_reason','secret-value','other'),('done_reason',None,'type'),('done',7,None),
    ('message.content',7,None)])
def test_untrusted_scalars_use_bounded_projection(tmp_path,sdk_io,mock_jar,monkeypatch,field,value,expected):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,updates=[(field,value)])
    packet=private_packet(result,ledger);name='content_chars' if field=='message.content' else field
    assert packet['native_response'][name]==expected and 'secret-value' not in json.dumps(packet)


@pytest.mark.parametrize('field,value',[('reason','private'),('prompt_eval_count',True),('eval_count',2**63),
    ('response_sha256','x'),('generation',1),('receipt_index',0),('request_sha256','0'*64),
    ('response_bytes',1),('max_tokens',512),('done',1),('done_reason','private'),('content_chars',65537),('body','private')])
def test_native_decoder_rejects_closed_shape_and_correlations(tmp_path,sdk_io,mock_jar,monkeypatch,field,value):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    packet=private_packet(result,ledger);packet['native_response'][field]=value
    with pytest.raises(ValueError):diagnostics.validate_failure_diagnostic(canonical_v3(packet),ledger._navigation.binding_key)


@pytest.mark.parametrize('field,value',[('response_sha256','0'*64),('generation',1),('receipt_index',0),
    ('request_sha256','0'*64),('response_bytes',1)])
def test_snapshot_cannot_be_projected_for_another_exchange(tmp_path,sdk_io,mock_jar,monkeypatch,field,value):
    def poison(ledger):ledger._native_response_rejection[field]=value
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,hook=poison)
    assert result['error']=='Invalid native research response'
    assert result['research_diagnostic']['status']=='UNAVAILABLE' and not hasattr(ledger,'_failure_diagnostic')


def test_recorder_error_does_not_replace_main_failure(tmp_path,sdk_io,mock_jar,monkeypatch):
    def explode(*args,**kwargs):raise RuntimeError('private recorder error')
    monkeypatch.setattr(diagnostics,'record_native_response_rejection',explode,raising=False)
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    assert result['error']=='Invalid native research response' and 'private recorder' not in json.dumps(result)
    assert private_packet(result,ledger)['native_response'] is None


def test_freeze_once_and_legacy_decoder_do_not_accept_extension(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    packet=private_packet(result,ledger);frozen=ledger._failure_diagnostic
    legacy=copy.deepcopy(packet);legacy.pop('output_structure');legacy.pop('native_response');legacy['kind']='research_failure_diagnostic_v3'
    assert diagnostics.validate_failure_diagnostic(canonical_v3(legacy),ledger._navigation.binding_key)==legacy
    legacy['native_response']=None
    with pytest.raises(ValueError):diagnostics.validate_failure_diagnostic(canonical_v3(legacy),ledger._navigation.binding_key)
    ledger._native_response_rejection['reason']='model';ledger._runtime_transport.receipts.clear()
    assert diagnostics.capture_failure(ledger)==result['research_diagnostic'] and ledger._failure_diagnostic==frozen
