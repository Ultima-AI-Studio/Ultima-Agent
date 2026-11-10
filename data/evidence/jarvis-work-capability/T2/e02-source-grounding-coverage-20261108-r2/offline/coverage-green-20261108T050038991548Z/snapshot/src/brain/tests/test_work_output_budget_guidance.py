"""The trusted phase describes the exact request allowance without relaxing evidence."""
import copy
import json
from pathlib import Path

import pytest

from src.brain import work_navigation as nav
from src.brain.tests.test_work_research import (
    sdk_io, mock_jar, stable_navigation_entropy, source9_clock,
    WorkService, fixture_prepare, report_payload, action, RESTRICTED,
)
from src.brain.tests.test_work_navigation_transport import genuine_navigation, rewrite_wire
from src.brain.work_research import verify_runtime_packet


@pytest.mark.parametrize('limit', [1, 32, 256, 2048])
def test_phase_states_actual_budget_and_preserves_full_schema(limit):
    schema = nav.v3_writer_schema()
    before = copy.deepcopy(schema)
    phase = nav.v3_research_phase(schema, output_tokens=limit)
    assert f'Response budget: {limit} tokens for the entire JSON object.' in phase
    assert schema == before
    encoded = json.dumps(schema, ensure_ascii=False, separators=(',', ':'))
    assert phase.endswith(encoded + '\nEnd argument schema.')
    for required in ('anchor_start', 'context_start', 'original question', 'three sources',
                     'atomic claims', 'compact JSON', 'complete object', 'citations'):
        assert required in phase


@pytest.mark.parametrize('limit', [True, False, None, '256', 256.0, 0, -1, 2049])
def test_phase_rejects_invalid_output_allowance(limit):
    with pytest.raises(ValueError, match='output budget'):
        nav.v3_research_phase(nav.v3_writer_schema(), output_tokens=limit)


def test_phase_budget_is_required_keyword_only():
    with pytest.raises(TypeError):
        nav.v3_research_phase(nav.v3_writer_schema())
    with pytest.raises(TypeError):
        nav.v3_research_phase(nav.v3_writer_schema(), 256)


@pytest.mark.parametrize('allowance,expected', [
    (None, [256, 256, 256, 2048, 256]),
    (32, [32] * 5),
    (8192, [256, 256, 256, 2048, 256]),
])
def test_sdk_phase_matches_actual_request_and_replay_accepts_write_ack(
        tmp_path, sdk_io, mock_jar, allowance, expected):
    _, runner, bodies, replies = mock_jar
    replies.extend([action(report_payload()), '{"final_answer":"saved"}'])
    result = WorkService(tmp_path, runner=runner, browser_channel=sdk_io[0],
        research_preparer=fixture_prepare).submit_work(
            'Research a subject', request_id='r', session_id='s',
            context={'research': True}, max_tokens=allowance)
    assert result['status'] == 'succeeded', result['error']
    assert [body['options']['num_predict'] for body in bodies] == expected
    for body in bodies[:-1]:
        limit = body['options']['num_predict']
        assert f'Response budget: {limit} tokens for the entire JSON object.' in body['messages'][0]['content']
    assert bodies[-1]['messages'][0]['content'].endswith(
        'Acknowledge the verified research.md file. No further action is authorized.')
    assert 'Response budget:' not in bodies[-1]['messages'][0]['content']
    assert Path(result['artifacts'][0]['path']).is_file()
    ledger = RESTRICTED[result['task_id']]
    verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
        ledger._runtime_final, require_ack=True, runtime_inputs=ledger._runtime_inputs)


@pytest.mark.parametrize('mutation', ['wrong_budget', 'missing_budget'])
def test_replay_rejects_budget_prompt_tamper_with_coherent_hashes(
        tmp_path, sdk_io, mock_jar, mutation):
    _, ledger = genuine_navigation(tmp_path, sdk_io, mock_jar)
    packet = json.loads(ledger._runtime_prewrite)
    index = len(packet['wires']) - 1
    wire = packet['wires'][index]
    expected = 'Response budget: 2048 tokens for the entire JSON object.'
    original = wire['secured_messages'][0]['content']
    assert expected in original
    replacement = ('Response budget: 256 tokens for the entire JSON object.'
        if mutation == 'wrong_budget' else '')
    wire['secured_messages'][0]['content'] = original.replace(expected, replacement, 1)
    rewrite_wire(packet, index)
    with pytest.raises(ValueError, match='Runtime exact phase system drift'):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
            nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)
