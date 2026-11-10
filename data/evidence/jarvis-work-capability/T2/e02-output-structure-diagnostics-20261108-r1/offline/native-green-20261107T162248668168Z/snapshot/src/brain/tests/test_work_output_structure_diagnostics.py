"""Unaccepted native output is observable without becoming tool authority."""
import copy
import hashlib
import json
import pytest
from src.brain import work_research_diagnostics as d
from src.brain.work_navigation import canonical_v3
from src.brain.tests.test_work_research import sdk_io,mock_jar,stable_navigation_entropy
from src.brain.tests.test_work_native_response_diagnostics import native_refusal
from src.brain.tests.test_work_failure_diagnostics import private_packet


def captured(result,ledger):
    p=private_packet(result,ledger)
    assert p['kind']=='research_failure_diagnostic_v5','missing request-bound output structure evidence'
    assert d.validate_failure_diagnostic(ledger._failure_diagnostic,ledger._navigation.binding_key)==p
    assert p['complete'] is False and p['acceptance_credit']==0
    return p,p['output_structure']


@pytest.mark.parametrize('content,status',[
    ('{"final_answer":"本次研究未交付。"}','COMPLETE'),
    ('{"action":"ultima_work_research_write","action_input":{"title":"cut','INVALID'),
    ('{"action_input":{"sections":[','INVALID'),('{','INVALID'),
    ('{"x":1,"x":2}','INVALID'),('{"x":NaN}','INVALID'),
    ('[]','COMPLETE'),(123,'NON_STRING'),(None,'NON_STRING')])
def test_received_content_shape_never_grants_write(tmp_path,sdk_io,mock_jar,monkeypatch,content,status):
    result,ledger,sent,bodies=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,
        updates=[('done_reason','length'),('message.content',content)])
    p,s=captured(result,ledger)
    assert s['json']['status']==status
    assert result['status']=='failed' and result['error']=='Invalid native research response'
    assert not list(tmp_path.rglob('research.md')) and not p['write_confirmed'] and not p['ack_confirmed']
    assert s['native_binding']['response_sha256']==hashlib.sha256(bodies[-1]).hexdigest()
    assert s['native_binding']['response_sha256']!=hashlib.sha256(canonical_v3(json.loads(bodies[-1]))).hexdigest()
    assert s['request']['sha256']==hashlib.sha256(sent[-1]).hexdigest()
    if status!='COMPLETE':assert s['json']['shape'] is None and s['json']['branch'] is None
    if type(content) is str and status!='INVALID':
        assert s['evidence']['mode']=='FULL' and s['evidence']['fragments'][0]['text']==content
    assert 'output_structure' not in result


def test_parse_location_and_request_contract_are_real(tmp_path,sdk_io,mock_jar,monkeypatch):
    content='{"action_input":{"title":"未结束'
    result,ledger,sent,bodies=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,reads=6,
        updates=[('done_reason','length'),('eval_count',2048),('message.content',content)])
    p,s=captured(result,ledger);actual=json.loads(sent[-1]);request=s['request']
    try:json.loads(content)
    except json.JSONDecodeError as exc:position=(exc.pos,exc.lineno,exc.colno)
    assert tuple(s['json']['error'][k] for k in ('pos','line','column'))==position
    assert s['json']['error']['kind']=='UNTERMINATED_STRING'
    assert request['options']==actual['options'] and request['options']['num_predict']==2048
    assert request['flags']=={k:actual[k] for k in ('think','stream','truncate','shift')}
    assert request['sampler_sha256']==hashlib.sha256(canonical_v3(actual['format'])).hexdigest()
    assert request['sampler_bytes']==len(canonical_v3(actual['format']))
    assert request['ack'] is False and 'ultima_work_research_write' in request['allowed_actions']
    assert request['evidence_ids_count']>0
    for key,value in s['native_binding'].items():assert value==p['native_response'][key]


def test_complete_invalid_schema_is_measured_without_acceptance(tmp_path,sdk_io,mock_jar,monkeypatch):
    content=json.dumps(dict(action='ultima_work_research_write',action_input=dict(path='research.md',title='标题',
        sections=[dict(source_id='S1',heading='h',facts=[dict(claim='atomic claim',evidence_id='N3.'+'0'*16)])])),ensure_ascii=False)
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,
        updates=[('done_reason','length'),('message.content',content)])
    _,s=captured(result,ledger);j=s['json']
    assert j['status']=='COMPLETE' and j['schema_valid'] is False and j['branch']=='write'
    assert j['shape']['title_chars']==2 and j['shape']['sections_total']==1
    assert j['shape']['sections'][0]['claim_chars']==[12]
    assert j['schema_error']['keyword'] in ('anyOf','enum','required','minItems','additionalProperties')


@pytest.mark.parametrize('content',['x'*14000,'中"\\\n'*3500])
def test_safe_excerpts_use_final_encoded_packet_cap(tmp_path,sdk_io,mock_jar,monkeypatch,content):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,reads=6,
        updates=[('done_reason','length'),('message.content',content)])
    _,s=captured(result,ledger);e=s['evidence']
    assert len(ledger._failure_diagnostic)<=16384 and e['mode']=='EXCERPTS'
    assert 1<=len(e['fragments'])<=3
    retained=0;end=0
    for fragment in e['fragments']:
        assert end<=fragment['start']<fragment['end']<=len(content)
        assert fragment['text']==content[fragment['start']:fragment['end']]
        end=fragment['end'];retained+=len(fragment['text'])
    assert e['omitted_chars']==len(content)-retained>0
    assert content not in json.dumps(result,ensure_ascii=False)


def test_sensitive_content_and_thinking_are_not_exported(tmp_path,sdk_io,mock_jar,monkeypatch):
    content='{"password":"supersecret123456"}'
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch,
        updates=[('done_reason','length'),('message.content',content),('message.thinking','private-thought-marker')])
    _,s=captured(result,ledger)
    assert s['evidence']['mode']=='OMITTED_POLICY' and s['evidence']['fragments']==[]
    assert s['message']['thinking']['chars']==22
    assert 'supersecret123456' not in ledger._failure_diagnostic.decode()+json.dumps(result)
    assert 'private-thought-marker' not in ledger._failure_diagnostic.decode()+json.dumps(result)


@pytest.mark.parametrize('path,value',[
    (('native_binding','response_sha256'),'0'*64),(('native_binding','response_bytes'),1),
    (('request','sha256'),'0'*64),(('request','options','num_predict'),1),
    (('request','flags','think'),True),(('message','content','chars'),999),
    (('evidence','omitted_chars'),1),(('json','status'),'OTHER'),
    (('evidence','fragments',0,'start'),1),(('evidence','fragments',0,'text'),'altered'),
    (('request','private_field'),'do not persist')])
def test_structure_decoder_rejects_tampering(tmp_path,sdk_io,mock_jar,monkeypatch,path,value):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    p,_=captured(result,ledger);s=p['output_structure']
    for key in path[:-1]:s=s[key]
    s[path[-1]]=value
    with pytest.raises(ValueError):d.validate_failure_diagnostic(canonical_v3(p),ledger._navigation.binding_key)


def test_structure_capture_failure_preserves_v4_and_original_error(tmp_path,sdk_io,mock_jar,monkeypatch):
    build=getattr(d,'build_output_structure',None)
    assert callable(build),'missing bounded structure recorder'
    def explode(*a,**kw):raise RuntimeError('do not leak recorder detail')
    monkeypatch.setattr(d,'build_output_structure',explode)
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    p=private_packet(result,ledger)
    assert p['kind']=='research_failure_diagnostic_v4' and p['native_response'] is not None
    assert result['error']=='Invalid native research response'
    assert 'recorder detail' not in json.dumps(result)+ledger._failure_diagnostic.decode()


def test_v5_can_be_projected_to_closed_legacy_versions(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger,_,_=native_refusal(tmp_path,sdk_io,mock_jar,monkeypatch)
    p,_=captured(result,ledger)
    for version in (4,3):
        old=copy.deepcopy(p);old['kind']='research_failure_diagnostic_v'+str(version);old.pop('output_structure')
        if version==3:old.pop('native_response')
        assert d.validate_failure_diagnostic(canonical_v3(old),ledger._navigation.binding_key)==old
        old['output_structure']=p['output_structure']
        with pytest.raises(ValueError):d.validate_failure_diagnostic(canonical_v3(old),ledger._navigation.binding_key)
