"""Generation must not admit source sections that the unchanged writer rejects."""
from copy import deepcopy
from itertools import combinations
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import navigation_reply
from src.brain.tests.test_work_research import RESTRICTED, action, mock_jar, report_payload, sdk_io, submit

WRITE='ultima_work_research_write'


def visible(count=3):
    return tuple((f'S{i}',nav.canonical_v3([[f'N3.{i:016x}','documented','',1,1,1,1]])) for i in range(1,count+1))


def report(ids=(1,2,3)):
    return dict(path='research.md',title='Observed sources',sections=[dict(source_id=f'S{i}',heading=f'Source {i}',
        facts=[dict(claim=f'Documented item {i}',evidence_id=f'N3.{i:016x}')]) for i in ids])


@pytest.mark.parametrize('change',['same','heading','fact'])
def test_distinct_values_same_source_are_not_distinct_sections(change):
    value=report();value['sections'][1]=deepcopy(value['sections'][0])
    if change=='heading':value['sections'][1]['heading']='Another heading for the same source'
    if change=='fact':value['sections'][1]['facts'][0]['claim']='Another supported fact from the same source'
    # The general writer input shape stays compatible; the phase must reject
    # the cross-section mismatch before a write is dispatched.
    assert Draft7Validator(nav.v3_writer_schema()).is_valid(value)
    assert not Draft7Validator(nav.v3_phase_writer_schema(visible())).is_valid(value)


@pytest.mark.parametrize('count',[3,4,5])
def test_all_valid_source_subsets_remain_available(count):
    schema=nav.v3_phase_writer_schema(visible(count));Draft7Validator.check_schema(schema)
    validator=Draft7Validator(schema)
    for size in range(3,count+1):
        for ids in combinations(range(1,count+1),size):assert validator.is_valid(report(ids)),ids
    assert schema==nav.v3_phase_writer_schema(tuple(reversed(visible(count))))


@pytest.mark.parametrize('ids',[(1,1,3),(3,2,1),(1,2),(1,2,3,3),(1,2,4)])
def test_noncanonical_or_repeated_sections_rejected(ids):
    assert not Draft7Validator(nav.v3_phase_writer_schema(visible())).is_valid(report(ids))


def test_same_source_pages_share_one_section():
    extra=('S1',nav.canonical_v3([['N3.0000000000000010','documented','',30,30,30,30]]))
    schema=nav.v3_phase_writer_schema((*visible(),extra))
    value=report();value['sections'][0]['facts'].append(dict(claim='Another page',evidence_id='N3.0000000000000010'))
    assert Draft7Validator(schema).is_valid(value)
    value['sections'][1]['facts'].append(value['sections'][0]['facts'][-1])
    assert not Draft7Validator(schema).is_valid(value)


@pytest.mark.parametrize('count',[3,4,5])
def test_envelope_definitions_resolve_without_network(count):
    wrap=getattr(nav,'v3_research_envelope',None);assert callable(wrap),'Whole-envelope local definition binding missing'
    writer=nav.v3_phase_writer_schema(visible(count));before=deepcopy(writer)
    option=dict(type='object',additionalProperties=False,required=['action','action_input'],
        properties=dict(action=dict(enum=[WRITE]),action_input=writer))
    final=dict(type='object',additionalProperties=False,required=['final_answer'],properties=dict(final_answer=dict(type='string')))
    whole=wrap([option,final]);assert writer==before
    Draft7Validator.check_schema(whole)
    for schema in (whole,server._research_sampler_schema(whole)):
        validator=Draft7Validator(schema)
        for ids in combinations(range(1,count+1),3):assert validator.is_valid(dict(action=WRITE,action_input=report(ids)))
        assert not validator.is_valid(dict(action=WRITE,action_input=report((1,1,3))))
        assert validator.is_valid(dict(final_answer='Insufficient evidence'))
    def walk(value):
        if isinstance(value,dict):
            if '$ref' in value:
                ref=value['$ref'];assert ref.startswith('#/definitions/')
                target=whole
                for part in ref[2:].split('/'):target=target[part]
                assert isinstance(target,dict)
            for child in value.values():walk(child)
        elif isinstance(value,list):
            for child in value:walk(child)
    walk(whole)


def test_duplicate_source_stops_before_sdk_writer(tmp_path,sdk_io,mock_jar):
    def reply(body):
        observed=[json.loads(m['content'][13:]) for m in body['messages'] if m['role']=='user' and m['content'].startswith('Observation: ')]
        value=report_payload()
        for section,page in zip(value['sections'],observed):section['facts'][0]['evidence_id']=page['cards'][0][0]
        value['sections'][1]=deepcopy(value['sections'][0]);value['sections'][1]['heading']='Same source, different heading'
        return action(value)
    mock_jar[3].append(reply)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
    assert result['status']=='failed' and result['error']=='Invalid native research envelope'
    assert not any(r['tool_name']==WRITE for r in ledger.snapshot())
    assert not list(tmp_path.rglob('research.md')) and not result['artifacts']
    assert 'research_failure' not in result


def test_success_still_delivers_and_replays(tmp_path,sdk_io,mock_jar):
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);assert result['status']=='succeeded',result['error']
    ledger=RESTRICTED[result['task_id']]
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,
        require_ack=True,runtime_inputs=ledger._runtime_inputs)
    assert Path(result['artifacts'][0]['path']).is_file() and len(result['sources'])==3
    assert len(mock_jar[2])==5 and 'research_diagnostic' not in result


@pytest.mark.parametrize('ids',[(1,2,3),(1,3,5),(2,4,5)])
def test_any_three_of_five_confirmed_sources_can_deliver(tmp_path,sdk_io,mock_jar,ids):
    def reply(body):
        observed=[json.loads(m['content'][13:]) for m in body['messages'] if m['role']=='user' and m['content'].startswith('Observation: ')]
        pages=[x for x in observed if x.get('v')==3]
        if len(pages)<5:return json.dumps(dict(action='ultima_work_research_inspect',action_input=dict(source_id=f'S{len(pages)+1}',start_line=1)))
        if len(observed)==5:
            chosen=[pages[i-1] for i in ids]
            return action(dict(path='research.md',title='Selected evidence',sections=[dict(source_id=p['source_id'],heading=p['source_id'],
                facts=[dict(claim=p['lines'][0][1].split(' for ')[0],evidence_id=p['cards'][0][0])]) for p in chosen]))
        return json.dumps(dict(final_answer='Saved research.md'))
    reply.no_auto_navigation=True;mock_jar[3].extend([reply]*7)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);assert result['status']=='succeeded',result['error']
    assert {s['source_id'] for s in result['sources']}=={f'S{i}' for i in ids}
    assert len(mock_jar[2])==7 and len(result['artifacts'])==1


def test_replay_compares_trusted_schema_before_consulting_forged_refs(tmp_path,sdk_io,mock_jar,monkeypatch):
    mock_jar[3].extend([navigation_reply]*5)
    result=submit(tmp_path,sdk_io[0],mock_jar[1]);assert result['status']=='succeeded',result['error']
    ledger=RESTRICTED[result['task_id']];packet=json.loads(ledger._runtime_prewrite);wire=packet['wires'][-1]
    wire['strict_schema']={'$ref':'https://example.invalid/untrusted-schema'}
    wire['sampler_schema']=server._research_sampler_schema(wire['strict_schema'])
    request=json.loads(wire['entity']);request.update(messages=wire['secured_messages'],format=wire['sampler_schema'])
    entity=nav.canonical_v3(request);wire['entity']=entity.decode()
    wire['hashes']={k:hashlib.sha256(v).hexdigest() for k,v in dict(messages=nav.canonical_v3(wire['secured_messages']),
        strict=nav.canonical_v3(wire['strict_schema']),sampler=nav.canonical_v3(wire['sampler_schema']),entity=entity).items()}
    receipt=packet['transport']['receipts'][(len(packet['wires'])-1)*3+2]
    receipt.update(entity_sha256=wire['hashes']['entity'],entity_bytes=len(entity))
    packet['transport']['post_bytes']=sum(len(w['entity'].encode()) for w in packet['wires'])
    consulted=[];validate=Draft7Validator.validate
    def guarded(self,instance,*args,**kwargs):
        if self.schema==wire['strict_schema']:
            consulted.append(True);raise AssertionError('Untrusted reference schema consulted before comparison')
        return validate(self,instance,*args,**kwargs)
    monkeypatch.setattr(Draft7Validator,'validate',guarded)
    from src.brain.work_research import verify_runtime_packet
    with pytest.raises(ValueError,match='Runtime phase schema or output budget drift'):
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,nav.canonical_v3(packet),
            require_ack=False,runtime_inputs=ledger._runtime_inputs)
    assert not consulted
