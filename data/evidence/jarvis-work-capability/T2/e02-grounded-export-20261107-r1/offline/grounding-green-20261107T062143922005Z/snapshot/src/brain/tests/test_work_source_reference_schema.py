"""Source ownership is constrained before dispatch, then independently replayed."""
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator, ValidationError

from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_research import RESTRICTED, action, mock_jar, report_payload, sdk_io, submit
from src.brain.tests.test_work_navigation_transport import navigation_reply

WRITE = 'ultima_work_research_write'


def card(number):
    return [f'N3.{number:016x}', 'documented', '', 1, 1, 1, 1]


def visible():
    return tuple((f'S{i}', nav.canonical_v3([card(i)])) for i in range(1, 4))


def refs(pages):
    assert hasattr(nav, 'v3_source_reference_map'), 'visible source/reference constructor missing'
    return nav.v3_source_reference_map(pages)


def payload():
    value = report_payload()
    for i, section in enumerate(value['sections'], 1):
        section['facts'][0]['evidence_id'] = card(i)[0]
    return value


def writer_schema(schema):
    return next(a['properties']['action_input'] for a in schema['anyOf']
                if a['properties'].get('action', {}).get('enum') == [WRITE])


def test_correlated_schema_rejects_cross_source_and_unknown_refs():
    schema = nav.v3_writer_schema(refs(visible()))
    assert Draft7Validator(schema).is_valid(payload())
    for bad_ref in (card(2)[0], card(99)[0]):
        bad = payload(); bad['sections'][0]['facts'][0]['evidence_id'] = bad_ref
        assert not Draft7Validator(schema).is_valid(bad)
    assert nav.v3_writer_schema()['properties']['path']['enum'] == ['research.md']


def test_visible_map_is_sorted_merges_pages_and_omits_empty_sources():
    pages = (('S2', nav.canonical_v3([card(9), card(8)])),
             ('S1', nav.canonical_v3([card(3)])), ('S4', b'[]'),
             ('S1', nav.canonical_v3([card(2)])))
    expected = {'S1': (card(2)[0], card(3)[0]), 'S2': (card(8)[0], card(9)[0])}
    assert refs(pages) == refs(tuple(reversed(pages))) == expected
    assert refs(()) == {}


@pytest.mark.parametrize('pages', [
    [], (('S0', b'[]'),), (('S6', b'[]'),), (('S1', '[]'),),
    (('S1', b'{}'),), (('S1', b'[[]]'),),
    (('S1', nav.canonical_v3([['bad', 'documented', '', 1, 1, 1, 1]])),),
    (('S1', nav.canonical_v3([[card(1)[0], 'bad', '', 1, 1, 1, 1]])),),
    (('S1', nav.canonical_v3([[card(1)[0], 'documented', '', True, 1, 1, 1]])),),
    (('S1', nav.canonical_v3([[card(1)[0], 'documented', '', 2, 1, 1, 1]])),),
    (('S1', nav.canonical_v3([card(i) for i in range(9)])),),
    tuple(('S1', b'[]') for _ in range(7)),
    (('S1', nav.canonical_v3([card(1)])), ('S2', nav.canonical_v3([card(1)]))),
])
def test_invalid_or_foreign_visible_cards_fail_closed(pages):
    with pytest.raises(ValueError): refs(pages)


@pytest.mark.parametrize('mapping', [{}, {'S1': ()}, {'S1': (card(1)[0],)},
    {1: (card(1)[0],), 'S2': (card(2)[0],), 'S3': (card(3)[0],)},
    {'S1': (card(1)[0],), 'S2': (card(1)[0],), 'S3': (card(3)[0],)}])
def test_writer_mapping_never_falls_back_when_empty_partial_or_colliding(mapping):
    with pytest.raises(ValueError): nav.v3_writer_schema(mapping)


@pytest.mark.parametrize('fault', ['foreign', 'unissued', 'other_request'])
def test_native_bad_reference_rejected_before_writer_dispatch(tmp_path, sdk_io, mock_jar, fault):
    def reply(body):
        pages = [json.loads(m['content'][13:]) for m in body['messages']
                 if m['role'] == 'user' and m['content'].startswith('Observation: ')]
        value = report_payload()
        for section, page in zip(value['sections'], pages):
            section['facts'][0]['evidence_id'] = page['cards'][0][0]
        value['sections'][0]['facts'][0]['evidence_id'] = (
            pages[1]['cards'][0][0] if fault == 'foreign' else card(99 if fault == 'unissued' else 100)[0])
        return action(value)
    mock_jar[3].append(reply)
    result = submit(tmp_path, sdk_io[0], mock_jar[1])
    assert result['status'] == 'failed' and result['error'] == 'Invalid native research envelope'
    ledger = RESTRICTED[result['task_id']]
    assert not any(r['tool_name'] in (WRITE, 'ultima_work_file_write') for r in ledger.snapshot())
    assert not result['artifacts'] and not result.get('research_effects')
    assert 'research_failure' not in result and not list(tmp_path.rglob('research.md'))


def delivered(tmp_path, sdk_io, mock_jar):
    mock_jar[3].extend([navigation_reply] * 5)
    result = submit(tmp_path, sdk_io[0], mock_jar[1])
    assert result['status'] == 'succeeded', result['error']
    ledger = RESTRICTED[result['task_id']]
    return result, ledger, json.loads(ledger._runtime_final)


def test_native_author_schema_uses_confirmed_third_view_and_complete_delivery(tmp_path, sdk_io, mock_jar):
    result, ledger, packet = delivered(tmp_path, sdk_io, mock_jar)
    wire = packet['wires'][-2]
    observations = [json.loads(m['content'][13:]) for m in wire['secured_messages']
                    if m['role'] == 'user' and m['content'].startswith('Observation: ')]
    expected = refs(tuple((p['source_id'], nav.canonical_v3(p['cards'])) for p in observations))
    assert len(expected) == 3
    for outer in (mock_jar[2][-2]['format'], wire['strict_schema'], wire['sampler_schema']):
        branches = writer_schema(outer)['properties']['sections']['items']['anyOf']
        actual = {b['properties']['source_id']['enum'][0]:
                  tuple(b['properties']['facts']['items']['properties']['evidence_id']['enum']) for b in branches}
        assert actual == expected
    for outer in (b['format'] for b in mock_jar[2][:3]):
        assert not any(a['properties'].get('action', {}).get('enum') == [WRITE] for a in outer['anyOf'])
    output = Path(result['artifacts'][0]['path'])
    assert hashlib.sha256(output.read_bytes()).hexdigest() == result['artifacts'][0]['sha256']
    assert len(result['sources']) == 3 and len(result['research_effects']) == 1
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                          ledger._runtime_final, require_ack=True, runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('fault', ['foreign', 'remove_branch', 'other_request', 'phase'])
def test_independent_replay_rejects_correlated_schema_or_phase_forgery(tmp_path, sdk_io, mock_jar, fault):
    _, ledger, _ = delivered(tmp_path, sdk_io, mock_jar)
    packet = json.loads(ledger._runtime_prewrite)
    wire = packet['wires'][-1]
    branches = writer_schema(wire['strict_schema'])['properties']['sections']['items']['anyOf']
    if fault == 'phase': wire['secured_messages'][0]['content'] += ' altered'
    elif fault == 'remove_branch': branches.pop()
    else:
        ref = (branches[1]['properties']['facts']['items']['properties']['evidence_id']['enum'][0]
               if fault == 'foreign' else card(99)[0])
        branches[0]['properties']['facts']['items']['properties']['evidence_id']['enum'].append(ref)
    # Coherently repair all self-reported hashes and the actual native entity.
    # The replay must still reconstruct the contract from trusted visible reads.
    wire['sampler_schema'] = server._research_sampler_schema(wire['strict_schema'])
    request = json.loads(wire['entity'])
    request.update(messages=wire['secured_messages'], format=wire['sampler_schema'])
    entity = nav.canonical_v3(request); wire['entity'] = entity.decode('utf8')
    wire['hashes'] = {k: hashlib.sha256(v).hexdigest() for k, v in dict(
        messages=nav.canonical_v3(wire['secured_messages']), strict=nav.canonical_v3(wire['strict_schema']),
        sampler=nav.canonical_v3(wire['sampler_schema']), entity=entity).items()}
    receipt = packet['transport']['receipts'][(len(packet['wires'])-1)*3+2]
    receipt.update(entity_sha256=wire['hashes']['entity'], entity_bytes=len(entity))
    packet['transport']['post_bytes'] = sum(len(w['entity'].encode('utf8')) for w in packet['wires'])
    from src.brain.work_research import verify_runtime_packet
    expected = ('Runtime exact phase system drift' if fault == 'phase' else
                None if fault == 'remove_branch' else 'Runtime phase schema or output budget drift')
    with pytest.raises((ValueError, ValidationError), match=expected):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                              nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)


def test_six_pages_max_cards_schema_keeps_original_budget_and_limits():
    pages = tuple((f'S{min(page + 1, 5)}', nav.canonical_v3([card(page * 8 + i) for i in range(8)])) for page in range(6))
    mapping = refs(pages)
    assert len(mapping) == 5 and sum(map(len, mapping.values())) == 48
    schema = nav.v3_writer_schema(mapping)
    assert len(nav.canonical_v3(schema)) < 32768
    assert schema['properties']['sections']['maxItems'] == 5
    from openjarvis.core.types import Message, Role
    server._research_budget([Message(role=Role.USER, content='x')], schema, 2048)
    with pytest.raises(ValueError):
        server._research_budget([Message(role=Role.USER, content='x' * 100000)], schema, 2048)
