"""Reference-first schema emission and source-read opportunities, not semantic truth."""
from copy import deepcopy
import hashlib
import json

import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.work_tools import WorkInspectTool
from src.brain.tests.test_work_code_claim_schema import (
    code_sources, delivered, facts, pages, phase,
)
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_research import sdk_io, mock_jar
from src.brain.tests.test_work_source_coverage_budget import page
from src.brain.tests.test_work_source_reference_schema import section_options, writer_schema


def fact_node(kind):
    if kind == 'code':
        return deepcopy(facts(section_options(phase(pages()))[0])[0])
    return dict(type='object', additionalProperties=False, required=['claim', 'evidence_id'],
                properties=dict(claim=dict(type='string', minLength=1, maxLength=2000),
                                evidence_id=dict(type='string', enum=['N3.0000000000000001'])))


@pytest.mark.parametrize('kind', ['code', 'documented', 'limitation'])
def test_fact_projection_preserves_closed_object_contract(kind):
    strict = fact_node(kind)
    before = deepcopy(strict)
    projected = server._research_sampler_schema(strict)
    assert 'allOf' in projected, 'native fact generation still emits claim before its evidence'
    assert [list(part['properties']) for part in projected['allOf']] == [['evidence_id'], ['claim']]
    assert projected['required'] == ['evidence_id', 'claim']
    assert projected['minProperties'] == projected['maxProperties'] == 2
    assert 'properties' not in projected and 'additionalProperties' not in projected
    Draft7Validator.check_schema(projected)
    validator = Draft7Validator(projected)
    ref = strict['properties']['evidence_id']['enum'][0]
    claim = 'client.run executes the visible call.' if kind == 'code' else 'The visible sentence.'
    good = dict(evidence_id=ref, claim=claim)
    assert validator.is_valid(good)
    for bad in ({}, {'claim': claim}, {'evidence_id': ref}, {**good, 'extra': 'x'},
                {**good, 'claim': 3}, {**good, 'claim': ''}, {**good, 'evidence_id': 'N3.ffffffffffffffff'},
                [ref, claim], None):
        assert not validator.is_valid(bad), bad
    assert strict == before
    assert projected['allOf'][0]['properties']['evidence_id']['enum'] == strict['properties']['evidence_id']['enum']
    assert strict['properties']['claim']['maxLength'] == 2000


def test_projection_does_not_rewrite_literals_or_other_object_contracts():
    literal = fact_node('documented')
    extra = deepcopy(literal)
    extra['properties']['note'] = dict(type='string')
    extra['required'].append('note')
    optional = deepcopy(literal)
    optional['required'] = ['claim']
    extended = deepcopy(literal)
    extended['description'] = 'Preserve an extended contract as given.'
    schema = dict(type='object', properties=dict(
        literal=dict(enum=[literal], const=literal, default=literal, examples=[literal]),
        extra=extra, optional=optional, extended=extended), examples=[literal])
    before = deepcopy(schema)
    projected = server._research_sampler_schema(schema)
    assert projected['properties']['literal'] == schema['properties']['literal']
    assert projected['examples'] == schema['examples']
    for key in ('extra', 'optional', 'extended'):
        assert 'allOf' not in projected['properties'][key]
        assert projected['properties'][key]['required'] == schema['properties'][key]['required']
    assert schema == before


def test_canonical_request_keeps_reference_before_claim():
    projected = server._research_sampler_schema(fact_node('documented'))
    request = json.loads(nav.canonical_v3(dict(format=projected)))
    assert 'allOf' in request['format'], 'canonical sorting still controls fact property emission order'
    assert [list(part['properties']) for part in request['format']['allOf']] == [['evidence_id'], ['claim']]
    assert nav.canonical_v3(request) == nav.canonical_v3(dict(format=projected))


@pytest.mark.parametrize('available,visible,used,expected', [
    (('S1', 'S2', 'S3', 'S4'), tuple(page('S1', i) for i in range(1, 4)), 3, ['S2', 'S3', 'S4']),
    (('S1', 'S2', 'S3', 'S4', 'S5'), (page('S1'), page('S1', 2)), 2, ['S2', 'S3', 'S4', 'S5']),
    (('S5', 'S3', 'S1', 'S2'), tuple(page('S5', i) for i in range(1, 4)), 3, ['S3', 'S1', 'S2']),
    (('S1', 'S2', 'S3', 'S4', 'S5'), tuple(page('S1', i) for i in range(1, 4)), 3, ['S2', 'S3', 'S4', 'S5']),
    (('S1', 'S2', 'S3', 'S4'), (page('S1'), page('S2', 2), page('S3', 3)), 5, ['S4']),
    (('S1', 'S2', 'S3', 'S4'), (page('S1'), page('S2', 2, empty=True)), 3, ['S2', 'S3', 'S4']),
])
def test_source_reserve_protects_remaining_unread_opportunities(available, visible, used, expected):
    original = deepcopy(WorkInspectTool.parameters)
    schema = nav.v3_phase_inspect_schema(original, available, visible, used)
    assert schema is not None
    assert schema['properties']['source_id']['enum'] == expected
    assert schema['properties']['start_line'] == original['properties']['start_line']
    assert original == WorkInspectTool.parameters


def test_three_source_minimum_is_not_replaced_by_all_source_writer_requirement():
    visible = pages()
    assert nav.v3_phase_writer_schema(visible)
    available = ('S1', 'S2', 'S3', 'S4', 'S5')
    schema = nav.v3_phase_inspect_schema(WorkInspectTool.parameters, available, visible, 3)
    assert schema['properties']['source_id']['enum'] == list(available)
    assert nav.v3_phase_inspect_schema(WorkInspectTool.parameters, available, visible, 6) is None
    assert Draft7Validator(nav.v3_research_final_schema()).is_valid(dict(final_answer='本次研究未交付。'))


def projected_facts(value):
    if isinstance(value, dict):
        if value.get('required') == ['evidence_id', 'claim'] and 'allOf' in value:
            yield value
        for child in value.values():
            yield from projected_facts(child)
    elif isinstance(value, list):
        for child in value:
            yield from projected_facts(child)


def test_http_request_uses_evidence_first_schema_with_original_writer_arguments(tmp_path, sdk_io, mock_jar, code_sources):
    result, ledger = delivered(tmp_path, sdk_io, mock_jar, code_sources)
    wire = json.loads(ledger._runtime_final)['wires'][-2]
    request = json.loads(wire['entity'])
    bound = list(projected_facts(writer_schema(request['format'])))
    assert bound, 'actual prepared HTTP entity has no reference-first fact contract'
    assert all([list(p['properties']) for p in fact['allOf']] == [['evidence_id'], ['claim']] for fact in bound)
    submitted = wire['secured_envelope']['action_input']
    assert all(set(fact) == {'claim', 'evidence_id'} for section in submitted['sections'] for fact in section['facts'])
    assert request['options']['num_predict'] == 2048 and len(wire['entity'].encode()) <= 49152
    assert result['status'] == 'succeeded' and len(result['artifacts']) == 1
    assert len(mock_jar[2]) == 5


def test_replay_refuses_coherently_reordered_fact_components(tmp_path, sdk_io, mock_jar, code_sources):
    _, ledger = delivered(tmp_path, sdk_io, mock_jar, code_sources)
    packet = json.loads(ledger._runtime_prewrite)
    wire = packet['wires'][-1]
    bound = list(projected_facts(wire['sampler_schema']))
    assert bound, 'cannot protect an ordering contract that is absent'
    bound[0]['allOf'].reverse()
    request = json.loads(wire['entity'])
    request['format'] = wire['sampler_schema']
    entity = nav.canonical_v3(request)
    wire['entity'] = entity.decode()
    wire['hashes'].update(sampler=hashlib.sha256(nav.canonical_v3(wire['sampler_schema'])).hexdigest(),
                          entity=hashlib.sha256(entity).hexdigest())
    packet['transport']['receipts'][-1].update(entity_sha256=wire['hashes']['entity'], entity_bytes=len(entity))
    packet['transport']['post_bytes'] = sum(len(w['entity'].encode()) for w in packet['wires'])
    from src.brain.work_research import verify_runtime_packet
    with pytest.raises(ValueError, match='Runtime native policy drift'):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                              nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)
