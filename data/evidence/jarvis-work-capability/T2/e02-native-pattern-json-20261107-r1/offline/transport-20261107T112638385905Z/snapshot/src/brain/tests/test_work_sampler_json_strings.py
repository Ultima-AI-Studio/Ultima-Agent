"""Native regex strings are wire-only; strict decoded claims stay authoritative."""
from copy import deepcopy
import hashlib
import itertools
import json
import re
from pathlib import Path

import httpx
import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_code_claim_schema import (
    card, code_sources, delivered, facts, pages, phase, report,
)
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_navigation_transport import navigation_reply
from src.brain.tests.test_work_research import RESTRICTED, mock_jar, sdk_io, submit
from src.brain.tests.test_work_source_reference_schema import section_options, writer_schema

WRITE = 'ultima_work_research_write'


def pattern(schema, ref=None):
    ref = ref or card(1)[0]
    return next(f['properties']['claim']['pattern']
                for s in section_options(schema) for f in facts(s)
                if ref in f['properties']['evidence_id']['enum'])


@pytest.mark.parametrize('body', [
    'client.run "unescaped"',
    'x",\nclient.run();',
    'client.run\nx',
    'client.run\r',
    'client.run\t',
    'client.run\x00',
    'client.run\x1f',
    'client.run\\',
    r'client.run\q',
    r'client.run\x41',
    r'client.run\u123',
])
def test_sampler_rejects_raw_bodies_that_break_json(body):
    strict = phase(pages())
    assert re.fullmatch(pattern(strict), body), 'reproducer must pass the old raw pattern'
    with pytest.raises(json.JSONDecodeError):
        json.loads('"' + body + '"')
    projected = pattern(server._research_sampler_schema(strict))
    assert not re.fullmatch(projected, body)


@pytest.mark.parametrize('op', ['Logger.info', 'Date.now', '$run', 'a_9.$x', 'a中.bé'])
def test_correct_json_serializations_keep_quotes_slashes_unicode_and_boundaries(op):
    strict = phase(pages(op))
    projected = pattern(server._research_sampler_schema(strict))
    edges = ['', ' ', '(', ')', '"', '\\', '中', 'é', '\t', '\n', '\r', '\x00',
             '\x1f', '\x7f', '.9', '..', r'\u0061', r'\q']
    accepted = 0
    for left, right in itertools.product(edges, repeat=2):
        claim = left + op + right
        if not re.fullmatch(pattern(strict), claim):
            continue
        body = json.dumps(claim, ensure_ascii=False)[1:-1]
        assert re.fullmatch(projected, body), repr(claim)
        assert json.loads('"' + body + '"') == claim
        accepted += 1
    assert accepted > 100
    # An escaped JSON slash is allowed as a delimiter, as is an escaped quote.
    for body in [r'\/' + op + r'\/', r'\"' + op + r'\"']:
        assert re.fullmatch(projected, body)
        assert re.fullmatch(pattern(strict), json.loads('"' + body + '"'))


@pytest.mark.parametrize('bad', ['^.*$', '^.*(client.run|other.operation).*$', None, 3, []])
def test_unknown_claim_pattern_fails_closed(bad):
    schema = dict(type='object', properties=dict(claim=dict(type='string', pattern=bad)))
    with pytest.raises(ValueError, match='code claim pattern'):
        server._research_sampler_schema(schema)


@pytest.mark.parametrize('op_fragment', ['client.run', r'client\.run()', r'client\.\.run',
                                         'x' * 201, r'9run', r'client\.run\q'])
def test_noncanonical_operation_encoding_fails_closed(op_fragment):
    value = r'^(.*[^A-Za-z0-9_$.])?' + op_fragment + r'([^A-Za-z0-9_$.].*|\.([^A-Za-z_$].*)?)?$'
    schema = dict(type='object', properties=dict(claim=dict(type='string', pattern=value)))
    with pytest.raises(ValueError, match='code claim pattern'):
        server._research_sampler_schema(schema)


def test_projection_preserves_strict_schema_ids_literals_and_nested_claim_context():
    strict = phase(pages())
    before = deepcopy(strict)
    projected = server._research_sampler_schema(strict)
    assert strict == before
    for a, b in zip(section_options(strict), section_options(projected)):
        assert a['properties']['source_id'] == dict(b['properties']['source_id'], maxLength=2)
        for old, new in zip(facts(a), facts(b)):
            assert old['properties']['evidence_id'] == dict(new['properties']['evidence_id'], maxLength=19)
            assert new['properties']['claim']['minLength'] == 1
            assert 'maxLength' not in new['properties']['claim']
            if 'pattern' in old['properties']['claim']:
                assert old['properties']['claim']['pattern'] != new['properties']['claim']['pattern']
    data = {'claim': {'pattern': '^.*$', 'maxLength': 9}}
    value = dict(type='object', properties=dict(
        claim=dict(anyOf=[dict(type='string', pattern=pattern(strict))]),
        source_id=dict(type='string', pattern=r'^S[1-5]$'),
        text=dict(type='object', default=data, enum=[data], const=data)),
        examples=[data])
    before = deepcopy(value)
    result = server._research_sampler_schema(value)
    assert value == before
    assert result['properties']['text'] == value['properties']['text']
    assert result['examples'] == [data]
    assert result['properties']['source_id'] == value['properties']['source_id']
    assert result['properties']['claim']['anyOf'][0]['pattern'] != pattern(strict)


def test_escaped_word_boundary_does_not_satisfy_decoded_strict_contract():
    strict = phase(pages())
    raw_body = r'\u0061client.run'
    assert re.fullmatch(pattern(server._research_sampler_schema(strict)), raw_body)
    decoded = json.loads('"' + raw_body + '"')
    assert decoded == 'aclient.run'
    assert not Draft7Validator(strict).is_valid(report(decoded))


def test_sdk_writes_quoted_chinese_and_backslash_claim_and_replays(
        tmp_path, sdk_io, mock_jar, code_sources, monkeypatch):
    original_get = httpx.request
    source_text = 'client.run("中文", "\\\\")\nclient.stop()\n'
    def get(method, url, **kwargs):
        if url == code_sources[1]:
            return httpx.Response(200, headers={'content-type': 'text/plain'}, text=source_text,
                                  request=httpx.Request(method, url))
        return original_get(method, url, **kwargs)
    monkeypatch.setattr(httpx, 'request', get)
    claim = '可见 client.run 调用，参数含 "中文" 和反斜杠 \\。'
    def reply(body):
        value = json.loads(navigation_reply(body))
        if value.get('action') == WRITE:
            fact = value['action_input']['sections'][1]['facts'][0]
            fact['claim'] = claim
            writer = writer_schema(body['format'])
            assert re.fullmatch(pattern(writer, fact['evidence_id']),
                                json.dumps(claim, ensure_ascii=False)[1:-1])
        return json.dumps(value, ensure_ascii=False)
    reply.no_auto_navigation = True
    mock_jar[3].extend([reply] * 5)
    result = submit(tmp_path, sdk_io[0], mock_jar[1], source_urls=code_sources)
    assert result['status'] == 'succeeded', result['error']
    ledger = RESTRICTED[result['task_id']]
    packet = json.loads(ledger._runtime_final)
    assert len(mock_jar[2]) == 5
    assert len(result['artifacts']) == len(result['research_effects']) == 1
    artifact = Path(result['artifacts'][0]['path']).read_bytes()
    assert hashlib.sha256(artifact).hexdigest() == result['artifacts'][0]['sha256']
    assert '中文' in artifact.decode('utf8') and b'client.run' in artifact
    assert 'maxLength' in json.dumps(packet['wires'][-2]['strict_schema'])
    assert len(packet['wires'][-2]['entity'].encode()) <= 49152
    from src.brain.work_research import verify_runtime_packet
    verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                          ledger._runtime_final, require_ack=True, runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('fault', ['escaped_word_boundary', 'missing_operation', 'control_character', 'raw_json'])
def test_sdk_strict_validation_and_writer_keep_bad_claims_unwritten(
        tmp_path, sdk_io, mock_jar, code_sources, fault):
    def reply(body):
        value = json.loads(navigation_reply(body))
        if value.get('action') == WRITE:
            fact = value['action_input']['sections'][1]['facts'][0]
            op = fact['claim'].removeprefix('Observed ')
            if fault == 'raw_json':
                return '{"action": "ultima_work_research_write", "action_input": {"claim":"x",\n' + op + '();"}}'
            fact['claim'] = {'escaped_word_boundary': 'a' + op,
                             'missing_operation': 'Observed behavior',
                             'control_character': op + '\n'}[fault]
        return json.dumps(value)
    reply.no_auto_navigation = True
    mock_jar[3].extend([reply] * 5)
    result = submit(tmp_path, sdk_io[0], mock_jar[1], source_urls=code_sources)
    assert result['status'] == 'failed'
    assert '未交付' in result['content']
    assert not result['artifacts'] and not list(tmp_path.rglob('research.md'))


def test_replay_rejects_coherently_rehashed_sampler_grammar_corruption(
        tmp_path, sdk_io, mock_jar, code_sources):
    _, ledger = delivered(tmp_path, sdk_io, mock_jar, code_sources)
    packet = json.loads(ledger._runtime_prewrite)
    wire = packet['wires'][-1]
    sampler = writer_schema(wire['sampler_schema'])
    target = next(f['properties']['claim'] for s in section_options(sampler)
                  for f in facts(s) if 'pattern' in f['properties']['claim'])
    target['pattern'] = '^.*$'
    request = json.loads(wire['entity'])
    request['format'] = wire['sampler_schema']
    entity = nav.canonical_v3(request)
    wire['entity'] = entity.decode('utf8')
    wire['hashes'] = {k: hashlib.sha256(v).hexdigest() for k, v in dict(
        messages=nav.canonical_v3(wire['secured_messages']),
        strict=nav.canonical_v3(wire['strict_schema']),
        sampler=nav.canonical_v3(wire['sampler_schema']), entity=entity).items()}
    packet['transport']['receipts'][(len(packet['wires'])-1)*3+2].update(
        entity_sha256=wire['hashes']['entity'], entity_bytes=len(entity))
    packet['transport']['post_bytes'] = sum(len(w['entity'].encode()) for w in packet['wires'])
    from src.brain.work_research import verify_runtime_packet
    with pytest.raises(ValueError, match='Runtime native policy drift'):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                              nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)
