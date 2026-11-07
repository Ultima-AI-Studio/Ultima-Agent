"""Code generation discharges its operation obligation before free prose."""
import json
import re

import pytest
from jsonschema import Draft7Validator

from src.brain import agent_server as server, work_navigation as nav
from src.brain.tests.test_work_code_claim_schema import pages, phase, report
from src.brain.tests.test_work_sampler_json_strings import pattern
from src.brain.tests.test_work_navigation_transport import genuine_navigation, rewrite_wire
from src.brain.tests.test_work_research import sdk_io, mock_jar, stable_navigation_entropy
from src.brain.work_research import verify_runtime_packet


@pytest.mark.parametrize('operation', ['Logger.info', 'Date.now', '$run', 'a中.bé'])
@pytest.mark.parametrize('prefix', ['概述。', 'Visible ', '"引用" '])
def test_prefix_cannot_precede_bound_operation(operation, prefix):
    strict = phase(pages(operation))
    old_form = prefix + operation + ' 记录选定语句中的调用。'
    # The original decoded acceptance language still permits this expression.
    assert Draft7Validator(strict).is_valid(report(old_form))
    raw = json.dumps(old_form, ensure_ascii=False)[1:-1]
    assert not re.fullmatch(pattern(server._research_sampler_schema(strict)), raw)


def test_long_synthetic_prose_cannot_defer_the_required_operation():
    # Text shaped like the saved failure; this is not a repaired actual response.
    prefix = ('支持多种LLM模型和工具的集成，实现灵活的交互方式。'
              '支持本地和云服务的混合使用，以平衡速度与隐私。') * 50
    raw = json.dumps(prefix + ' Logger.info', ensure_ascii=False)[1:-1]
    projected = pattern(server._research_sampler_schema(phase(pages('Logger.info'))))
    assert not re.fullmatch(projected, raw)


@pytest.mark.parametrize('operation', ['Logger.info', 'Date.now', '$run', 'a中.bé'])
def test_operation_first_can_close_or_describe_a_serialized_statement(operation):
    strict = phase(pages(operation))
    projected = pattern(server._research_sampler_schema(strict))
    for claim in (operation, operation + ' 记录 "中文" 和反斜杠 \\。', operation + '(value)'):
        raw = json.dumps(claim, ensure_ascii=False)[1:-1]
        assert re.fullmatch(projected, raw)
        assert json.loads('"' + raw + '"') == claim
        assert Draft7Validator(strict).is_valid(report(claim))
    for claim in ('x' + operation, 'parent.' + operation, operation + '.child'):
        assert not re.fullmatch(projected, json.dumps(claim)[1:-1])


def test_decoded_boundary_remains_stricter_than_sampler_escape_boundary():
    strict = phase(pages('Logger.info'))
    raw = r'Logger.info\u0061'
    assert re.fullmatch(pattern(server._research_sampler_schema(strict)), raw)
    assert not Draft7Validator(strict).is_valid(report(json.loads('"' + raw + '"')))


def test_replay_rejects_old_operation_anywhere_directive_with_coherent_hashes(
        tmp_path, sdk_io, mock_jar):
    _, ledger = genuine_navigation(tmp_path, sdk_io, mock_jar)
    packet = json.loads(ledger._runtime_prewrite)
    index = len(packet['wires']) - 1
    wire = packet['wires'][index]
    system = wire['secured_messages'][0]['content']
    before, current = system.split('For code, ', 1)
    _, after = current.split('A TODO is a comment, ', 1)
    old_directive = 'For code, name the exact operation and describe only what the cited statement shows. '
    wire['secured_messages'][0]['content'] = before + old_directive + 'A TODO is a comment, ' + after
    rewrite_wire(packet, index)
    with pytest.raises(ValueError, match='Runtime exact phase system drift'):
        verify_runtime_packet(ledger._binding, ledger.issued_snapshot, ledger._collection,
                              nav.canonical_v3(packet), runtime_inputs=ledger._runtime_inputs)
