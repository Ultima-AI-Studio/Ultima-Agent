"""Fixed research target is a generation contract and a retained writer guard.

SDK/executor/file IO is real; HTTP/native responses are isolated offline
fixtures. Passing these tests is not real-model research acceptance.
"""
import hashlib
import json
from pathlib import Path

import pytest
from jsonschema import Draft7Validator

from src.brain import work_navigation as nav
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_research import (
    RESTRICTED, action, mock_jar, report_payload, sdk_io, submit,
)

WRITE = 'ultima_work_research_write'


def schema_payload(path):
    payload = report_payload()
    payload['path'] = path
    for i, section in enumerate(payload['sections'], 1):
        section['facts'][0]['evidence_id'] = f'N3.{i:016x}'
    return payload


@pytest.mark.parametrize('path', [
    'other.md', './research.md', '../research.md', 'nested/research.md',
    'C:/work/research.md', ' research.md', 'research.md ', 'RESEARCH.MD',
])
def test_schema_rejects_targets_the_writer_cannot_accept(path):
    assert not Draft7Validator(nav.v3_writer_schema()).is_valid(schema_payload(path))


@pytest.mark.parametrize('path', [None, False, 0, [], {}, ''])
def test_schema_retains_path_type_and_nonempty_rejections(path):
    assert not Draft7Validator(nav.v3_writer_schema()).is_valid(schema_payload(path))


def test_schema_accepts_exact_research_target():
    assert Draft7Validator(nav.v3_writer_schema()).is_valid(schema_payload('research.md'))


@pytest.mark.parametrize('path', ['other.md', '../research.md', 'C:/work/research.md'])
def test_native_wrong_target_rejected_before_writer_dispatch(tmp_path, sdk_io, mock_jar, path):
    _, runner, bodies, replies = mock_jar
    payload = report_payload()
    payload['path'] = path
    replies.append(action(payload))
    result = submit(tmp_path, sdk_io[0], runner)
    assert result['status'] == 'failed'
    assert result['error'] == 'Invalid native research envelope'
    ledger = RESTRICTED[result['task_id']]
    assert not any(r['tool_name'] in (WRITE, 'ultima_work_file_write') for r in ledger.snapshot())
    assert not result['artifacts'] and not result.get('research_effects')
    assert 'research_failure' not in result  # refusal precedes the writer
    assert not list(tmp_path.rglob('research.md')) and not list(tmp_path.rglob('other.md'))
    assert len(bodies) == 4  # three fixture pages and one rejected author reply


def test_native_format_and_strict_replay_keep_target_and_complete_delivery(tmp_path, sdk_io, mock_jar):
    _, runner, bodies, replies = mock_jar
    replies.extend([action(report_payload()), '{"final_answer":"saved"}'])
    result = submit(tmp_path, sdk_io[0], runner)
    assert result['status'] == 'succeeded', result['error']
    ledger = RESTRICTED[result['task_id']]
    packet = json.loads(ledger._runtime_final)
    author = packet['wires'][-2]
    schemas = [bodies[-2]['format'], author['strict_schema'], author['sampler_schema']]
    for schema in schemas:
        writer = next(item for item in schema['anyOf']
                      if item['properties'].get('action', {}).get('enum') == [WRITE])
        path = writer['properties']['action_input']['properties']['path']
        assert path['type'] == 'string' and path['enum'] == ['research.md']
    artifact, = result['artifacts']
    output = Path(artifact['path'])
    assert output.name == 'research.md'
    assert hashlib.sha256(output.read_bytes()).hexdigest() == artifact['sha256']
    assert output.read_text('utf8').startswith('# Model title')
    assert len(result['sources']) == 3 and len(result['research_effects']) == 1
    assert not ledger.first_failure and 'research_failure' not in result
    assert bodies[-1]['format']['required'] == ['final_answer']
