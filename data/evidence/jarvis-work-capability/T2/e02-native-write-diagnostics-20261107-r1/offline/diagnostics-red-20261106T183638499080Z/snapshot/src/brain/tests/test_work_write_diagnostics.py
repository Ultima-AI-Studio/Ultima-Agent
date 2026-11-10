"""Public failure diagnostics use trusted ledger records, never model summaries.

The SDK/executor/writer/END path is real; native transport and source GETs are
offline fixtures. These tests do not establish live research acceptance.
"""
import hashlib
import json

import pytest

from src.brain import work_tools as wt
from src.brain.tests.test_work_navigation import stable_navigation_entropy
from src.brain.tests.test_work_research import (
    CURRENT_NATIVE, RESTRICTED, action, fixture_dispatch, mock_jar,
    report_payload, sdk_io, submit,
)

WRITE = 'ultima_work_research_write'


def failed_write(tmp_path, sdk_io, payload=None, after=None):
    def runner(*args, **kwargs):
        response = fixture_dispatch(payload or report_payload())
        if after:
            after(response, wt._ACTIVE.get()[1])
        return response
    return submit(tmp_path, sdk_io[0], runner)


@pytest.mark.parametrize('fault,reason', [
    ('unissued', 'UNISSUED_REFERENCE'),
    ('foreign', 'FOREIGN_REFERENCE'),
    ('duplicate_source', 'INVALID_SOURCE_SECTION'),
    ('multiline_claim', 'INVALID_REPORT_TEXT'),
])
def test_real_writer_reason_survives_failed_end(tmp_path, sdk_io, fault, reason):
    payload = report_payload()
    if fault == 'unissued':
        payload['sections'][0]['facts'][0]['evidence_id'] = 'N3.' + '0' * 16
    elif fault == 'foreign':
        payload['sections'][0]['facts'][0]['evidence_id'] = 'issued:S2'
    elif fault == 'duplicate_source':
        payload['sections'][1]['source_id'] = 'S1'
    else:
        payload['sections'][0]['facts'][0]['claim'] = 'first line\nsecond line'
    result = failed_write(tmp_path, sdk_io, payload)
    assert result['status'] == 'failed' and not result['artifacts']
    assert result['error'] == 'Unlinked or failed END'
    writer = next(r for r in RESTRICTED[result['task_id']].snapshot()
                  if r['tool_name'] == WRITE and r['success'] is False)
    diagnostic = result['research_failure']
    assert diagnostic == dict(
        stage='research.write', reason_code=reason, error_type='ValueError',
        error_text_length=len(writer['error']),
        error_text_sha256=hashlib.sha256(writer['error'].encode('utf8')).hexdigest(),
    )
    assert not list(tmp_path.rglob('research.md'))
    assert all('error' not in r and 'result' not in r for r in result['tool_results'])


def test_earliest_writer_reason_wins_over_later_ledger_and_sdk_errors(tmp_path, sdk_io):
    payload = report_payload()
    payload['sections'][0]['facts'][0]['evidence_id'] = 'N3.' + '0' * 16
    def after(response, ledger):
        ledger.record(dict(tool_name=WRITE, success=False, error_type='ValueError',
                           error='Foreign reference'))
        response.setdefault('tool_results', []).insert(0, dict(
            tool_name=WRITE, success=False, error_type='ValueError',
            error='Foreign reference', research_failure={'reason_code': 'FORGED'}))
    result = failed_write(tmp_path, sdk_io, payload, after)
    assert result['error'] == 'Unlinked or failed END'
    assert result['research_failure']['reason_code'] == 'UNISSUED_REFERENCE'
    assert 'FORGED' not in json.dumps(result)


@pytest.mark.parametrize('message', [
    'secret-token-123 source body and prompt',
    'Unknown or unissued reference: secret-token-123',
    'Unknown or unissued reference\n',
    'secret-token-123' * 400,
    'secret-token-123\ud800',
])
def test_unknown_exception_text_never_enters_public_diagnostic(tmp_path, sdk_io, monkeypatch, message):
    def reject(*args, **kwargs):
        raise ValueError(message)
    monkeypatch.setattr(wt.WorkResearchWriteTool, 'run', reject)
    result = failed_write(tmp_path, sdk_io)
    assert result['status'] == 'failed' and result['error'] == 'Unlinked or failed END'
    diagnostic = result['research_failure']
    assert diagnostic['reason_code'] == 'UNKNOWN'
    assert diagnostic['error_type'] == 'ValueError'
    assert diagnostic['error_text_length'] == len(message)
    expected_hash = (hashlib.sha256(message.encode('utf8', errors='surrogatepass')).hexdigest()
                     if len(message) <= 4096 else None)
    assert diagnostic['error_text_sha256'] == expected_hash
    public = json.dumps(result, ensure_ascii=True)
    assert 'secret-token-123' not in public
    assert len(json.dumps(diagnostic)) < 300


@pytest.mark.parametrize('exception_type', [RuntimeError, TypeError, KeyError])
def test_reason_mapping_requires_value_error(tmp_path, sdk_io, monkeypatch, exception_type):
    def reject(*args, **kwargs):
        raise exception_type('Unknown or unissued reference')
    monkeypatch.setattr(wt.WorkResearchWriteTool, 'run', reject)
    result = failed_write(tmp_path, sdk_io)
    assert result['research_failure']['reason_code'] == 'UNKNOWN'
    assert result['research_failure']['error_type'] == exception_type.__name__
    assert result['status'] == 'failed' and not result['artifacts']


def test_arbitrary_exception_type_is_bounded(tmp_path, sdk_io, monkeypatch):
    error = type('UntrustedExceptionType' * 100, (Exception,), {})
    def reject(*args, **kwargs):
        raise error('private error text')
    monkeypatch.setattr(wt.WorkResearchWriteTool, 'run', reject)
    result = failed_write(tmp_path, sdk_io)
    assert result['research_failure']['error_type'] == 'UNKNOWN'
    assert len(json.dumps(result['research_failure'])) < 300


def test_sdk_failure_cannot_create_trusted_writer_diagnostic(tmp_path, sdk_io):
    def runner(*args, **kwargs):
        return dict(compose_error='Unlinked or failed END', tool_results=[dict(
            tool_name=WRITE, success=False, error_type='ValueError',
            error='Unknown or unissued reference', research_failure={'reason_code': 'FORGED'})])
    result = submit(tmp_path, sdk_io[0], runner)
    assert result['status'] == 'failed'
    assert 'research_failure' not in result
    assert 'FORGED' not in json.dumps(result)


def test_legal_research_keeps_success_and_has_no_failure_diagnostic(tmp_path, sdk_io):
    result = failed_write(tmp_path, sdk_io)
    assert result['status'] == 'succeeded', result['error']
    assert len(result['artifacts']) == 1 and len(result['sources']) == 3
    assert 'research_failure' not in result
    assert RESTRICTED[result['task_id']]._runtime_final


def test_early_failure_and_nonresearch_do_not_gain_writer_diagnostic(tmp_path):
    from src.brain.work_service import WorkService
    service = WorkService(tmp_path, runner=lambda *a, **kw: {})
    research = service.submit_work('question', request_id='r', session_id='s', context={'research': True})
    assert research['status'] == 'failed' and 'research_failure' not in research
    ordinary = service.submit_work('question', request_id='r', session_id='s')
    assert 'research_failure' not in ordinary
