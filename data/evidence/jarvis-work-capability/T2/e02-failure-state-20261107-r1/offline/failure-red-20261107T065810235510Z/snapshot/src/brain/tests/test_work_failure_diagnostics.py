"""Failure diagnostics must explain the real SDK path without granting delivery."""
import hashlib
import json
from dataclasses import replace
from pathlib import Path
import httpx
import pytest
from src.brain import work_tools as wt
from src.brain.tests.test_work_research import sdk_io,mock_jar,submit,RESTRICTED,stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import genuine_navigation,navigation_reply

FINAL='现有证据不足以回答原题的任务架构；未写入研究文件。'


def early_case(tmp_path,sdk_io,mock_jar,monkeypatch,*,final=FINAL,reads=6,after=None):
    def get(method,url,**kwargs):
        assert method=='GET'
        body='\n\n'.join('Visible fact %d for %s.' % (i,url) for i in range(75))
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
    assert 'Visible fact' not in json.dumps(packet) and FINAL not in json.dumps(result,ensure_ascii=False)
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
    def remove_cards(response,ledger):
        item=next(iter(ledger._staged.values()));item['view']=replace(item['view'],cards_json=b'[]')
    result,ledger=early_case(tmp_path,sdk_io,mock_jar,monkeypatch,reads=1,after=remove_cards)
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


def test_failure_before_navigation_has_no_fabricated_diagnostic(tmp_path,sdk_io,mock_jar):
    result=submit(tmp_path,sdk_io[0],mock_jar[1],research=False)
    assert 'research_diagnostic' not in result
