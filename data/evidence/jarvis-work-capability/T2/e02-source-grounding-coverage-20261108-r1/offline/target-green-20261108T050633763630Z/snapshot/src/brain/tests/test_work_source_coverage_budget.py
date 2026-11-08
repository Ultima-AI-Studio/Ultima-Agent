"""Preserve coverage opportunities within six reads and report non-delivery honestly."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.work_tools import WorkInspectTool
from src.brain.tests.test_work_research import sdk_io, mock_jar, submit, RESTRICTED, stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import navigation_reply

NOT_DELIVERED='本次研究未交付。'
SOURCES=('S1','S2','S3','S4','S5')


def page(sid, number=1, *, empty=False):
    cards=[] if empty else [[f'N3.{number:016x}','documented','text',1,1,1,1]]
    return sid,nav.canonical_v3(cards)


def phase(available=SOURCES, visible=(), used=0, base=None):
    helper=getattr(nav,'v3_phase_inspect_schema',None)
    assert callable(helper), 'missing shared read-budget/source-coverage contract'
    return helper(WorkInspectTool.parameters if base is None else base,available,visible,used)


@pytest.mark.parametrize('available,visible,used,expected',[
    (SOURCES,(),0,list(SOURCES)),
    (SOURCES,tuple(page('S1',i) for i in range(1,4)),3,['S2','S3','S4','S5']),
    (SOURCES,tuple(page('S1',i) for i in range(1,5)),4,['S2','S3','S4','S5']),
    (SOURCES,tuple(page('S1',i) for i in range(1,5))+(page('S2',5),),5,['S3','S4','S5']),
    (SOURCES,(page('S1'),page('S2',2),page('S3',3)),5,['S4','S5']),
    (SOURCES,(page('S1'),page('S2',2),page('S3',3)),6,None),
    (SOURCES,(page('S1',empty=True),),4,None),
    (SOURCES,(page('S1'),page('S2',2,empty=True)),4,['S2','S3','S4','S5']),
    (SOURCES,tuple(page('S1',i) for i in range(1,6)),5,None),
    (('S1','S2'),(page('S1'),),1,None),
    ((),(),0,None),
    (('S5','S3','S1'),tuple(page('S5',i) for i in range(1,5)),4,['S3','S1']),
])
def test_budget_reserves_remaining_opportunities_for_missing_sources(available,visible,used,expected):
    before=deepcopy(WorkInspectTool.parameters)
    schema=phase(available,visible,used)
    assert WorkInspectTool.parameters==before
    if expected is None:
        assert schema is None
    else:
        wanted=deepcopy(before);wanted['properties']['source_id']['enum']=expected
        assert schema==wanted and schema is not WorkInspectTool.parameters
        assert Draft7Validator(before).is_valid(dict(source_id=expected[0],start_line=17))
        assert Draft7Validator(schema).is_valid(dict(source_id=expected[0],start_line=17))


@pytest.mark.parametrize('used',[True,False,-1,7,1.5,'4',None])
def test_read_count_is_a_strict_bounded_integer(used):
    with pytest.raises(ValueError):phase(used=used)


@pytest.mark.parametrize('available',[['S1','S2','S3'],('S1','S1','S2'),('S6',),('S1',True)])
def test_availability_cannot_be_malformed_or_model_invented(available):
    with pytest.raises(ValueError):phase(available)


@pytest.mark.parametrize('empty',[False,True])
def test_even_empty_visible_pages_must_belong_to_trusted_availability(empty):
    with pytest.raises(ValueError):phase(('S1','S2','S3'),(page('S5',empty=empty),),1)


def test_phase_never_expands_original_tool_capability():
    base=deepcopy(WorkInspectTool.parameters);base['properties']['source_id']['enum']=['S1','S2','S3']
    with pytest.raises(ValueError):phase(SOURCES,base=base)


@pytest.mark.parametrize('visible,used',[
    ((page('S1'),),0),
    ((page('S1'),page('S2')),2),
    ((('S1',b'[[]]'),),1),
    ([page('S1')],1),
])
def test_invalid_or_duplicate_visible_evidence_does_not_buy_coverage(visible,used):
    with pytest.raises(ValueError):phase(visible=visible,used=used)


def inspect_params(schema):
    for option in schema.get('anyOf',[]):
        properties=option.get('properties',{})
        if properties.get('action',{}).get('enum')==['ultima_work_research_inspect']:
            return properties['action_input']
    return None


def repeated_case(tmp_path,sdk_io,mock_jar,monkeypatch,*,adaptive):
    def get(method,url,**kwargs):
        assert method=='GET'
        # One card per page: exercise six real reads without changing request caps.
        body='\n'.join('Visible fact %d for %s.' % (i,url) if i%24==0 else '' for i in range(145))
        return httpx.Response(200,headers={'content-type':'text/plain'},text=body,request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',get)
    def reply(body):
        observed=[json.loads(m['content'][13:]) for m in body['messages']
                  if m['role']=='user' and m['content'].startswith('Observation: ')]
        pages=[p for p in observed if p.get('v')==3]
        if len(pages)<6:
            allowed=inspect_params(body['format'])['properties']['source_id']['enum']
            sid='S1' if not adaptive or 'S1' in allowed else allowed[0]
            start=1+24*sum(p['source_id']==sid for p in pages)
            return json.dumps(dict(action='ultima_work_research_inspect',action_input=dict(source_id=sid,start_line=start)))
        if not adaptive:return json.dumps(dict(final_answer=NOT_DELIVERED))
        if len(observed)==6:
            chosen={}
            for p in pages:chosen.setdefault(p['source_id'],p)
            return json.dumps(dict(action='ultima_work_research_write',action_input=dict(path='research.md',title='Coverage report',
                sections=[dict(source_id=sid,heading=sid,facts=[dict(claim=p['lines'][0][1].split(' for ')[0],
                    evidence_id=p['cards'][0][0])]) for sid,p in sorted(chosen.items())])))
        return json.dumps(dict(final_answer='Saved research.md'))
    reply.no_auto_navigation=True
    mock_jar[3].extend([reply]*8)
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    return result,RESTRICTED[result['task_id']]


def test_sdk_rejects_third_same_source_read_before_spending_reserved_budget(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=repeated_case(tmp_path,sdk_io,mock_jar,monkeypatch,adaptive=False)
    assert ledger._read_count==2, 'third same-source read consumed the coverage reserve'
    assert len(mock_jar[2])==3 and result['status']=='failed'
    assert 'Invalid native research envelope' in result['error']
    assert result['content']==NOT_DELIVERED
    assert not list(tmp_path.rglob('research.md')) and not getattr(ledger,'_runtime_final',None)


def test_sdk_uses_six_reads_then_write_ack_and_independent_replay(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=repeated_case(tmp_path,sdk_io,mock_jar,monkeypatch,adaptive=True)
    assert result['status']=='succeeded',result['error']
    assert ledger._read_count==6 and len(mock_jar[2])==8
    assert [v.source_id for _,v in ledger._issued]==['S1']*2+['S2','S3','S4','S5']
    assert inspect_params(mock_jar[2][2]['format'])['properties']['source_id']['enum']==['S2','S3','S4','S5']
    assert inspect_params(mock_jar[2][4]['format'])['properties']['source_id']['enum']==['S4','S5']
    assert inspect_params(mock_jar[2][5]['format'])['properties']['source_id']['enum']==['S5']
    assert inspect_params(mock_jar[2][6]['format']) is None
    # The unchanged writer-eligible phase starts as soon as three sources were read.
    assert [b['options']['num_predict'] for b in mock_jar[2]]==[256]*4+[2048]*3+[256]
    assert len(result['artifacts'])==1 and Path(result['artifacts'][0]['path']).is_file()
    assert {s['source_id'] for s in result['sources']}==set(SOURCES)
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,
        require_ack=True,runtime_inputs=ledger._runtime_inputs)


def test_replay_rejects_coherently_widened_fifth_read_schema(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=repeated_case(tmp_path,sdk_io,mock_jar,monkeypatch,adaptive=True)
    assert result['status']=='succeeded',result['error']
    packet=json.loads(ledger._runtime_prewrite);wire=packet['wires'][4]
    inspect_params(wire['strict_schema'])['properties']['source_id']['enum']=list(SOURCES)
    wire['sampler_schema']=server._research_sampler_schema(wire['strict_schema'])
    request=json.loads(wire['entity']);request['format']=wire['sampler_schema']
    entity=nav.canonical_v3(request);wire['entity']=entity.decode()
    wire['hashes'].update({k:hashlib.sha256(v).hexdigest() for k,v in dict(
        strict=nav.canonical_v3(wire['strict_schema']),sampler=nav.canonical_v3(wire['sampler_schema']),entity=entity).items()})
    packet['transport']['receipts'][14].update(entity_sha256=wire['hashes']['entity'],entity_bytes=len(entity))
    packet['transport']['post_bytes']=sum(len(w['entity'].encode()) for w in packet['wires'])
    from src.brain.work_research import verify_runtime_packet
    with pytest.raises(ValueError,match='Runtime phase schema or output budget drift'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,nav.canonical_v3(packet),
            runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('text',['已保存research.md','已交付完整报告','测'*1000])
def test_false_or_arbitrary_prewrite_final_is_rejected(tmp_path,sdk_io,mock_jar,text):
    mock_jar[3].append(json.dumps(dict(final_answer=text)))
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['error']=='Invalid native research envelope'
    assert result['status']=='failed' and result['content']==NOT_DELIVERED
    assert not list(tmp_path.rglob('research.md')) and not getattr(ledger,'_runtime_final',None)
    assert json.loads(ledger._failure_diagnostic)['final_answer'] is None


def test_valid_non_delivery_final_remains_available_without_delivery_credit(tmp_path,sdk_io,mock_jar):
    mock_jar[3].append(json.dumps(dict(final_answer=NOT_DELIVERED)))
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['error']=='Missing nonempty immutable runtime proof' and result['status']=='failed'
    assert result['content']==NOT_DELIVERED and not result['artifacts']
    diagnostic=json.loads(ledger._failure_diagnostic)
    assert diagnostic['branch']=='final_before_write' and diagnostic['final_answer']['text']==NOT_DELIVERED
    assert diagnostic['acceptance_credit']==0 and not diagnostic['write_confirmed'] and not diagnostic['ack_confirmed']


def test_unconfirmed_delivery_keeps_partial_effect_warning(tmp_path,sdk_io,mock_jar):
    def bad_ack(body):return json.dumps(dict(final_answer='x'*1001))
    bad_ack.no_auto_navigation=True
    mock_jar[3].extend([navigation_reply]*4+[bad_ack])
    result=submit(tmp_path,sdk_io[0],mock_jar[1])
    assert result['status']=='needs_attention' and list(tmp_path.rglob('research.md'))
    assert result['content']=='本次研究未交付，部分操作可能已生效，请核对结果。'


def test_nonresearch_failure_keeps_existing_message(tmp_path):
    from src.brain.work_service import WorkService
    def fail(*args,**kwargs):raise ValueError('synthetic nonresearch failure')
    result=WorkService(tmp_path,runner=fail).submit_work('task',request_id='r',session_id='s')
    assert result['status']=='failed' and result['content']=='本次任务未完成。'


def test_final_schema_distinguishes_refusal_from_verified_ack():
    helper=getattr(nav,'v3_research_final_schema',None)
    assert callable(helper), 'missing shared delivery-state contract'
    assert Draft7Validator(helper()).is_valid(dict(final_answer=NOT_DELIVERED))
    assert not Draft7Validator(helper()).is_valid(dict(final_answer='Saved research.md'))
    assert Draft7Validator(helper(ack=True)).is_valid(dict(final_answer='Saved research.md'))
    assert Draft7Validator(helper(ack=True)).is_valid(dict(final_answer='测'*1000))
    assert not Draft7Validator(helper(ack=True)).is_valid(dict(final_answer='测'*1001))
    for bad in (0,1,None,'yes'):
        with pytest.raises(ValueError):helper(ack=bad)
