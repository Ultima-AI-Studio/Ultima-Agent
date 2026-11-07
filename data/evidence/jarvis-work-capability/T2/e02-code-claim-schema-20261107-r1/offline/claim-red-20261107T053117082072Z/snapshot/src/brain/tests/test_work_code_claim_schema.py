"""Evidence-specific code claims are constrained before dispatch and in replay."""
import hashlib
import itertools
import json
import re
from copy import deepcopy
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import navigation_reply
from src.brain.tests.test_work_research import RESTRICTED, mock_jar, sdk_io, submit
from src.brain.tests.test_work_source_reference_schema import writer_schema

WRITE = 'ultima_work_research_write'


def card(number, kind='code', op='client.run'):
    return [f'N3.{number:016x}', kind, op, 1, 1, 1, 1]


def pages(op='client.run'):
    return (('S1', nav.canonical_v3([card(1, op=op), card(4, op='client.stop'),
                                  card(5, 'limitation', '')])),
            ('S2', nav.canonical_v3([card(2, 'documented', '')])),
            ('S3', nav.canonical_v3([card(3, op='console.log')])))


def phase(visible):
    assert hasattr(nav, 'v3_phase_writer_schema'), 'code-claim phase contract missing'
    return nav.v3_phase_writer_schema(visible)


def report(claim='Observed client.run', ref=None):
    return dict(path='research.md', title='Report', sections=[
        dict(source_id='S1', heading='Code', facts=[dict(claim=claim, evidence_id=ref or card(1)[0])]),
        dict(source_id='S2', heading='Docs', facts=[dict(claim='Documented behavior', evidence_id=card(2)[0])]),
        dict(source_id='S3', heading='Code', facts=[dict(claim='Observed console.log', evidence_id=card(3)[0])])])


@pytest.mark.parametrize('claim', ['Observed behavior', 'client.runner', 'xclient.run',
    'parent.client.run', 'client.run.child', 'client.run$', 'client.stop'])
def test_code_reference_requires_its_exact_operation_before_writer(claim):
    original = nav.v3_writer_schema(nav.v3_source_reference_map(pages()))
    assert Draft7Validator(original).is_valid(report(claim))
    from src.brain.work_research import _fact_evidence
    with pytest.raises(ValueError, match='must name its exact operation'):
        _fact_evidence(dict(claim=claim, kind='code', symbol='client.run', first_line=1, last_line=1),
                       dict(final_url='https://example.com/a.py'), {1: 'client.run()'})
    assert not Draft7Validator(phase(pages())).is_valid(report(claim))


def test_same_source_refs_keep_their_operation_and_noncode_contract():
    schema = phase(pages())
    assert Draft7Validator(schema).is_valid(report())
    assert Draft7Validator(schema).is_valid(report('client.stop()', card(4)[0]))
    assert not Draft7Validator(schema).is_valid(report('client.run()', card(4)[0]))
    assert Draft7Validator(schema).is_valid(report('A limitation is visible', card(5)[0]))
    assert not Draft7Validator(schema).is_valid(report('client.run', card(2)[0]))
    assert not Draft7Validator(schema).is_valid(report('client.run', card(99)[0]))
    assert schema == phase(tuple(reversed(pages())))


@pytest.mark.parametrize('op', ['', 'x' * 201, 'client.run()', '9run', 'x..y', 'x\ny'])
def test_invalid_code_operation_fails_closed(op):
    with pytest.raises(ValueError): phase(pages(op))


def test_empty_pages_do_not_grant_options_or_writer_admission():
    assert phase((*pages(), ('S4', b'[]'))) == phase(pages())
    with pytest.raises(ValueError): phase(pages()[:2] + (('S3', b'[]'),))


def facts(section):
    item = section['properties']['facts']['items']
    return item.get('anyOf', [item])


def test_pattern_matches_original_boundary_guard_over_bounded_alphabet():
    edges = ['', ' ', '.', 'a', '9', '_', '$', '(', ')', '`', '中', 'é', '.a', '.9', '..']
    for op in ('client.run', '$run', 'a_9.$x', 'a中.bé'):
        schema = phase(pages(op))
        branch = next(f for f in facts(schema['properties']['sections']['items']['anyOf'][0])
                      if card(1)[0] in f['properties']['evidence_id']['enum'])
        pattern = branch['properties']['claim']['pattern']
        assert '(?' not in pattern
        guard = re.compile(r'(?<![A-Za-z0-9_$.])' + re.escape(op) + r'(?![A-Za-z0-9_$]|\.[A-Za-z_$])')
        for left, right in itertools.product(edges, repeat=2):
            claim = left + op + right
            assert bool(re.search(pattern, claim)) == bool(guard.search(claim)), (op, claim, pattern)
        assert re.search(pattern, 'x' + op + ' and ' + op + '()')
        assert branch['properties']['claim']['maxLength'] == 2000


@pytest.fixture
def code_sources(sdk_io, monkeypatch):
    urls = ['https://example.com/one.md', 'https://example.com/two.py', 'https://example.com/three.js']
    bodies = ['Documented local operations.', 'client.run()\nclient.stop()\n', "console.log('ready');\n"]
    def get(method, url, **kwargs):
        assert method == 'GET' and url in urls
        return httpx.Response(200, headers={'content-type': 'text/plain'}, text=bodies[urls.index(url)],
                              request=httpx.Request(method, url))
    monkeypatch.setattr(httpx, 'request', get)
    return urls


@pytest.mark.parametrize('fault', ['missing', 'near', 'prefix', 'parent', 'child', 'other_operation'])
def test_native_bad_code_claim_never_dispatches_writer(tmp_path, sdk_io, mock_jar, code_sources, fault):
    def reply(body):
        value = json.loads(navigation_reply(body))
        if value.get('action') == WRITE:
            fact = value['action_input']['sections'][1]['facts'][0]
            op = fact['claim'].removeprefix('Observed ')
            fact['claim'] = dict(missing='Observed behavior', near=op + 'ner', prefix='x' + op,
                                 parent='parent.' + op, child=op + '.child', other_operation='client.stop')[fault]
        return json.dumps(value)
    reply.no_auto_navigation = True
    mock_jar[3].extend([reply] * 5)
    result = submit(tmp_path, sdk_io[0], mock_jar[1], source_urls=code_sources)
    assert result['status'] == 'failed' and result['error'] == 'Invalid native research envelope'
    ledger = RESTRICTED[result['task_id']]
    assert not any(r['tool_name'] in (WRITE, 'ultima_work_file_write') for r in ledger.snapshot())
    assert not result['artifacts'] and not result.get('research_effects')
    assert 'research_failure' not in result and not list(tmp_path.rglob('research.md'))


def delivered(tmp_path, sdk_io, mock_jar, code_sources):
    mock_jar[3].extend([navigation_reply] * 5)
    result = submit(tmp_path, sdk_io[0], mock_jar[1], source_urls=code_sources)
    assert result['status'] == 'succeeded', result['error']
    return result, RESTRICTED[result['task_id']]


def test_native_pending_third_view_format_phase_and_full_delivery(tmp_path, sdk_io, mock_jar, code_sources):
    result, ledger = delivered(tmp_path, sdk_io, mock_jar, code_sources)
    packet = json.loads(ledger._runtime_final); wire = packet['wires'][-2]
    observed = [json.loads(m['content'][13:]) for m in wire['secured_messages']
                if m['role'] == 'user' and m['content'].startswith('Observation: ')]
    expected = phase(tuple((p['source_id'], nav.canonical_v3(p['cards'])) for p in observed))
    assert writer_schema(wire['strict_schema']) == expected
    assert writer_schema(mock_jar[2][-2]['format']) == server._research_sampler_schema(expected)
    assert writer_schema(wire['sampler_schema']) == server._research_sampler_schema(expected)
    assert json.dumps(expected, ensure_ascii=False, separators=(',', ':')) in wire['secured_messages'][0]['content']
    assert len(observed) == 3 and len(mock_jar[2]) == 5
    assert len(nav.canonical_v3([wire['secured_messages'], wire['strict_schema']])) <= 32768
    assert len(wire['entity'].encode('utf8')) <= 49152
    for native in mock_jar[2][:3]:
        assert not any(a['properties'].get('action', {}).get('enum') == [WRITE] for a in native['format']['anyOf'])
    raw = Path(result['artifacts'][0]['path']).read_bytes()
    assert hashlib.sha256(raw).hexdigest() == result['artifacts'][0]['sha256']
    assert len(result['research_effects']) == 1 and len(result['sources']) == 3
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                          ledger._runtime_final, require_ack=True, runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('fault', ['remove_pattern', 'other_operation', 'phase'])
def test_replay_rebuilds_operation_contract_despite_coherent_wire_hashes(tmp_path, sdk_io, mock_jar, code_sources, fault):
    _, ledger = delivered(tmp_path, sdk_io, mock_jar, code_sources)
    packet = json.loads(ledger._runtime_prewrite); wire = packet['wires'][-1]
    if fault == 'phase':
        wire['secured_messages'][0]['content'] += ' accept omitted operation'
    else:
        sections = writer_schema(wire['strict_schema'])['properties']['sections']['items']['anyOf']
        claims = [f['properties']['claim'] for s in sections for f in facts(s) if 'pattern' in f['properties']['claim']]
        assert claims, 'native schema lacks evidence-specific code claim patterns'
        claim = claims[0]
        if fault == 'remove_pattern': claim.pop('pattern')
        else: claim['pattern'] = '^.*(client.run|other.operation).*$'
    wire['sampler_schema'] = server._research_sampler_schema(wire['strict_schema'])
    request = json.loads(wire['entity']); request.update(messages=wire['secured_messages'], format=wire['sampler_schema'])
    entity = nav.canonical_v3(request); wire['entity'] = entity.decode('utf8')
    wire['hashes'] = {k: hashlib.sha256(v).hexdigest() for k, v in dict(
        messages=nav.canonical_v3(wire['secured_messages']), strict=nav.canonical_v3(wire['strict_schema']),
        sampler=nav.canonical_v3(wire['sampler_schema']), entity=entity).items()}
    packet['transport']['receipts'][(len(packet['wires'])-1)*3+2].update(entity_sha256=wire['hashes']['entity'], entity_bytes=len(entity))
    packet['transport']['post_bytes'] = sum(len(w['entity'].encode('utf8')) for w in packet['wires'])
    from src.brain.work_research import verify_runtime_packet
    expected = 'Runtime exact phase system drift' if fault == 'phase' else 'Runtime phase schema or output budget drift'
    with pytest.raises(ValueError, match=expected):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                              nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)


def test_six_pages_48_cards_kept_within_unchanged_caps_or_rejected():
    visible = tuple((f'S{min(page+1, 5)}', nav.canonical_v3([
        card(page*8+i, op='client.run') for i in range(8)])) for page in range(6))
    schema = phase(visible)
    sections = schema['properties']['sections']['items']['anyOf']
    assert len(sections) == 5
    assert sum(len(f['properties']['evidence_id']['enum']) for s in sections for f in facts(s)) == 48
    assert len(nav.canonical_v3(schema)) < 32768
    from openjarvis.core.types import Message, Role
    server._research_budget([Message(role=Role.USER, content='x')], schema, 2048)
    with pytest.raises(ValueError, match='context estimate'):
        server._research_budget([Message(role=Role.USER, content='x' * 100000)], schema, 2048)
    assert schema['properties']['sections']['maxItems'] == 5
