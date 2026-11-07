"""Failure diagnostics must explain the real SDK path without granting delivery."""
import hashlib
import json
import math
from pathlib import Path
import httpx
import pytest
from src.brain import work_tools as wt
from src.brain.tests.test_work_research import sdk_io,mock_jar,submit,RESTRICTED,stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import genuine_navigation,navigation_reply

FINAL='本次研究未交付。'


def test_trusted_numeric_deadline_is_not_interpreted_as_text_pii(tmp_path,sdk_io,mock_jar,monkeypatch):
    # This internal seconds value has the same digit shape as a phone number.
    # It is a counter, not user/source text, and must not discard the snapshot.
    remaining=259.1234567
    def clock(response,ledger):
        ledger.deadline=remaining;monkeypatch.setattr(wt,'monotonic',lambda:0.0)
        pii=next(s for s in ledger._policy.scanners if type(s).__name__=='PIIScanner')
        assert not pii.scan(repr(remaining)).clean
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=clock)
    assert result['status']=='failed' and result['error']=='Missing nonempty immutable runtime proof'
    packet=private_packet(result,ledger)
    numerator,denominator=remaining.as_integer_ratio()
    assert packet['budget']['deadline_remaining_microseconds']==numerator*1000000//denominator
    assert packet['budget']['write_admission_open'] is True


@pytest.mark.parametrize('remaining',[math.nextafter(55.0,-math.inf),55.0,0.0,-1.0])
def test_integer_clock_projection_preserves_original_admission_boundary(tmp_path,sdk_io,mock_jar,monkeypatch,remaining):
    def clock(response,ledger):
        ledger.deadline=remaining;monkeypatch.setattr(wt,'monotonic',lambda:0.0)
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=clock)
    packet=private_packet(result,ledger);budget=packet['budget']
    assert packet['kind']=='research_failure_diagnostic_v3'
    numerator,denominator=remaining.as_integer_ratio()
    assert budget['deadline_remaining_microseconds']==numerator*1000000//denominator
    assert budget['write_admission_open']==(remaining>=55)
    assert ledger.deadline==remaining


def early_case(tmp_path,sdk_io,mock_jar,monkeypatch,*,final=FINAL,reads=6,after=None,empty_first_page=False):
    def get(method,url,**kwargs):
        assert method=='GET'
        body='\n\n'.join('Visible fact %d for %s.' % (i,url) for i in range(75))
        if empty_first_page:body='\n'*30+body
        return httpx.Response(200,headers={'content-type':'text/plain'},text=body,request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',get)
    def reply(body):
        pages=[json.loads(m['content'][13:]) for m in body['messages'] if m['role']=='user' and m['content'].startswith('Observation: ')]
        if len(pages)<reads:
            return json.dumps(dict(action='ultima_work_research_inspect',action_input=dict(source_id='S'+str(len(pages)%3+1),start_line=1 if len(pages)<3 else 35)))
        return json.dumps(dict(final_answer=final),ensure_ascii=False)
    reply.no_auto_navigation=True
    mock_jar[3].extend([reply]*(reads+1))
    def runner(prompt,**kwargs):
        result=mock_jar[1](prompt,**kwargs)
        if after:after(result,wt._ACTIVE.get()[1])
        return result
    result=submit(tmp_path,sdk_io[0],runner)
    return result,RESTRICTED[result['task_id']]


def private_packet(result,ledger):
    assert isinstance(result.get('research_diagnostic'),dict), 'failed SDK result loses final branch and selected pages'
    raw=getattr(ledger,'_failure_diagnostic',None)
    assert type(raw) is bytes and len(raw)<=16384, 'missing bounded immutable private diagnostic'
    assert result['research_diagnostic']['sha256']==hashlib.sha256(raw).hexdigest()
    return json.loads(raw)


def test_six_reads_then_final_preserves_branch_pages_and_budget_without_delivery(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch)
    assert result['status']=='failed' and result['error']=='Missing nonempty immutable runtime proof'
    packet=private_packet(result,ledger)
    assert packet['branch']=='final_before_write' and packet['final_answer']['text']==FINAL
    assert packet['complete'] is False and packet['acceptance_credit']==0
    assert packet['budget']['reads_used']==6 and packet['budget']['reads_limit']==6
    assert packet['budget']['native_posts']==7 and packet['budget']['native_posts_limit']==8
    assert packet['eligible_source_ids']==['S1','S2','S3'] and not packet['write_confirmed'] and not packet['ack_confirmed']
    assert len(packet['pages'])==6
    for page,staged in zip(packet['pages'],ledger._staged.values()):
        view=staged['view'];cards=json.loads(view.cards_json)
        assert page['source_id']==view.source_id and page['requested_start']==staged['metadata']['arguments']['start_line']
        assert page['range']==[view.start,view.end] and page['view_sha256']==view.wire_sha256
        assert page['confirmed'] and page['visible']
        assert [c['id'] for c in page['cards']]==[c[0] for c in cards]
    assert 'Visible fact' not in json.dumps(packet)
    assert 'final_answer' not in json.dumps(result) and result['content']==FINAL
    assert not getattr(ledger,'_runtime_final',None) and not list(tmp_path.rglob('research.md'))


def test_failure_diagnostic_does_not_trust_sdk_supplied_fields(tmp_path,sdk_io,mock_jar,monkeypatch):
    def forge(response,ledger):response['research_diagnostic']=dict(branch='ack',text='FORGED')
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=forge)
    packet=private_packet(result,ledger)
    assert packet['branch']=='final_before_write' and packet['eligible_source_ids']==['S1']
    assert 'FORGED' not in json.dumps(result)+json.dumps(packet)


def test_successful_write_and_ack_have_no_failure_diagnostic(tmp_path,sdk_io,mock_jar):
    result,ledger=genuine_navigation(tmp_path,sdk_io,mock_jar)
    assert result['status']=='succeeded' and ledger._runtime_final
    assert 'research_diagnostic' not in result and not getattr(ledger,'_failure_diagnostic',None)


@pytest.mark.parametrize('final',['password = "syntheticsecret"','x'*1001])
def test_unverified_or_unsafe_final_never_enters_diagnostic(tmp_path,sdk_io,mock_jar,monkeypatch,final):
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,final=final,reads=1)
    assert result['status']=='failed'
    packet=private_packet(result,ledger)
    assert packet['branch']=='unvalidated_response' and packet['final_answer'] is None
    assert final not in json.dumps(result)+json.dumps(packet)


def test_frozen_diagnostic_does_not_follow_late_mutation(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1)
    original=private_packet(result,ledger);raw=ledger._failure_diagnostic
    ledger._runtime_wires[-1]['secured_envelope']['final_answer']='LATE CHANGE'
    ledger._staged.clear();ledger._read_count=999
    from src.brain.work_research_diagnostics import capture_failure
    again=capture_failure(ledger)
    assert ledger._failure_diagnostic==raw and again==result['research_diagnostic']
    assert json.loads(raw)==original


def test_no_cards_never_count_as_eligible_source(tmp_path,sdk_io,mock_jar,monkeypatch):
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,empty_first_page=True)
    packet=private_packet(result,ledger)
    assert packet['eligible_source_ids']==[] and packet['pages'][0]['cards']==[]


def test_unconfirmed_page_is_distinguished_from_confirmed_visible_page(tmp_path,sdk_io,mock_jar,monkeypatch):
    def unconfirm(response,ledger):
        item=next(iter(ledger._staged.values()));item.update(confirmed=False,promoted=False)
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=unconfirm)
    packet=private_packet(result,ledger)
    assert packet['eligible_source_ids']==[]
    assert not packet['pages'][0]['confirmed'] and not packet['pages'][0]['visible']


def test_capture_failure_cannot_replace_original_product_failure(tmp_path,sdk_io,mock_jar,monkeypatch):
    def poison(response,ledger):ledger._runtime_wires=None
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=poison)
    assert result['error']=='Missing nonempty immutable runtime proof' and result['status']=='failed'
    assert result.get('research_diagnostic')==dict(status='UNAVAILABLE',reason='DIAGNOSTIC_CAPTURE_FAILED',complete=False,acceptance_credit=0)
    assert not getattr(ledger,'_failure_diagnostic',None)


def test_nonresearch_request_has_no_research_diagnostic(tmp_path,sdk_io,mock_jar):
    result=submit(tmp_path,sdk_io[0],mock_jar[1],research=False)
    assert 'research_diagnostic' not in result


def test_failure_before_navigation_has_no_fabricated_diagnostic(tmp_path):
    from src.brain.work_service import WorkService
    result=WorkService(tmp_path,runner=lambda *a,**k:pytest.fail('runner must not start')).submit_work(
        'research',request_id='r',session_id='s',context={'research':True})
    assert result['status']=='failed' and 'trusted startup' in result['error']
    assert 'research_diagnostic' not in result


def test_write_without_ack_is_preserved_as_unconfirmed_delivery(tmp_path,sdk_io,mock_jar):
    def bad_ack(body):return json.dumps(dict(final_answer='x'*1001))
    bad_ack.no_auto_navigation=True
    mock_jar[3].extend([navigation_reply]*4+[bad_ack])
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['status']=='needs_attention' and list(tmp_path.rglob('research.md'))
    packet=private_packet(result,ledger)
    assert packet['branch']=='write_without_ack' and packet['write_confirmed'] and not packet['ack_confirmed']
    assert packet['final_answer'] is None and not getattr(ledger,'_runtime_final',None)


def test_scanner_failure_blocks_private_diagnostic_without_changing_failure(tmp_path,sdk_io,mock_jar,monkeypatch):
    def poison(response,ledger):
        def reject(value):raise RuntimeError('private scanner failure')
        ledger._scan_output=reject
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=poison)
    assert result['error']=='Missing nonempty immutable runtime proof'
    assert result.get('research_diagnostic',{}).get('status')=='UNAVAILABLE'
    assert not getattr(ledger,'_failure_diagnostic',None)
    assert 'private scanner failure' not in json.dumps(result)


def test_maximum_allowed_final_is_bounded_and_private(tmp_path,sdk_io,mock_jar,monkeypatch):
    from src.brain import work_service
    final='测'*1000
    def fail(*args,**kwargs):raise ValueError('synthetic independent artifact failure')
    monkeypatch.setattr(work_service,'verify_artifacts',fail)
    def ack(body):return json.dumps(dict(final_answer=final))
    ack.no_auto_navigation=True
    mock_jar[3].extend([navigation_reply]*4+[ack])
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    packet=private_packet(result,ledger)
    assert result['status']=='needs_attention' and packet['branch']=='ack'
    assert packet['write_confirmed'] and packet['ack_confirmed'] and packet['acceptance_credit']==0
    assert packet['final_answer']['text']==final and len(ledger._failure_diagnostic)<=16384
    assert final not in json.dumps(result,ensure_ascii=False)


def test_excess_pages_fail_closed_without_dropping_or_truncating_evidence(tmp_path,sdk_io,mock_jar,monkeypatch):
    def poison(response,ledger):
        item=next(iter(ledger._staged.values()))
        ledger._staged={i:item for i in range(7)}
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=poison)
    assert result['error']=='Missing nonempty immutable runtime proof'
    assert result.get('research_diagnostic',{}).get('status')=='UNAVAILABLE'
    assert not getattr(ledger,'_failure_diagnostic',None)


@pytest.mark.parametrize('change',['complete','credit','binding','extra','limit','branch','card','version','clock_type','clock_overflow'])
def test_closed_decoder_rejects_coherent_diagnostic_forgery(tmp_path,sdk_io,mock_jar,monkeypatch,change):
    from src.brain.work_research_diagnostics import validate_failure_diagnostic
    from src.brain.work_navigation import canonical_v3
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1)
    packet=private_packet(result,ledger)
    if change=='complete':packet['complete']=True
    elif change=='credit':packet['acceptance_credit']=1
    elif change=='binding':packet['binding_sha256']='0'*64
    elif change=='extra':packet['source_body']='untrusted source text'
    elif change=='limit':packet['budget']['native_posts_limit']=9
    elif change=='branch':packet['branch']='ack'
    elif change=='card':packet['pages'][0]['cards'][0]['operation']='unexpected free text'
    elif change=='version':packet['kind']='research_failure_diagnostic_v1'
    elif change=='clock_type':packet['budget']['deadline_remaining_microseconds']=True
    elif change=='clock_overflow':packet['budget']['deadline_remaining_microseconds']=2**63
    with pytest.raises(ValueError):validate_failure_diagnostic(canonical_v3(packet),ledger._navigation.binding_key)


def test_post_ack_artifact_failure_stays_failed_and_keeps_ack_distinct(tmp_path,sdk_io,mock_jar,monkeypatch):
    from src.brain import work_service
    def fail(*args,**kwargs):raise ValueError('synthetic independent artifact failure')
    monkeypatch.setattr(work_service,'verify_artifacts',fail)
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['status']=='needs_attention' and ledger._runtime_final
    packet=private_packet(result,ledger)
    assert packet['branch']=='ack' and packet['ack_confirmed'] and packet['write_confirmed']
    assert packet['complete'] is False and packet['acceptance_credit']==0
