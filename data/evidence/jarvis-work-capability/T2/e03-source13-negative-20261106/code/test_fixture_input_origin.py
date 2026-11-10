import ctypes as C
import itertools
import json

import pytest

import fixture_adapter as adapter


@pytest.fixture
def factory():
    def make(**kwargs):
        assert hasattr(adapter, 'InputOriginRecorder'), 'fixture lacks input-origin observation'
        return adapter.InputOriginRecorder(**kwargs)
    return make


def recorder(factory, events, **changes):
    options = dict(
        read_source=lambda: {'ok': True, 'device_type': 1, 'origin_id': 2},
        read_send_flags=lambda: 0,
        emit=events.append,
        pid=123,
        thread_id=lambda: 456,
        clock_ns=itertools.count(100).__next__,
        clock_utc=lambda: '2026-11-05T00:00:00Z',
    )
    options.update(changes)
    return factory(**options)


def test_entry_source_precedes_dispatch_and_preserves_arguments_and_result(factory):
    events, order, seen = [], [], []
    def read_source():
        order.append('source')
        return {'ok': True, 'device_type': 1, 'origin_id': 2}
    def original(*args):
        order.append('dispatch')
        seen.append(args)
        return 90210
    audit = recorder(factory, events, read_source=read_source)
    wrapped = audit.wrap(original, enabled=lambda: True, observed=lambda m: True)
    assert wrapped(77, 0x100, 0xBAD, 0xDEAD) == 90210
    assert seen == [(77, 0x100, 0xBAD, 0xDEAD)]
    assert order == ['source', 'dispatch']
    assert events[0]['entered_ns'] < events[0]['exited_ns']
    assert events[0]['source']['origin'] == 'injected_non_uiaccess'
    assert events[0]['dispatch_returned'] is True
    assert events[0]['parent_entry_id'] is None


def test_nested_completion_order_does_not_reverse_causal_order(factory):
    events = []
    audit = recorder(factory, events)
    def original(hwnd, message, wparam, lparam):
        return wrapped(hwnd, 0xC2, 0, 0) + 1 if message == 0x100 else 41
    wrapped = audit.wrap(original, enabled=lambda: True, observed=lambda m: True)
    assert wrapped(77, 0x100, 0, 0) == 42
    child, parent = events
    assert child['message_id'] == 0xC2 and parent['message_id'] == 0x100
    assert child['parent_entry_id'] == parent['entry_id']
    assert child['parent_message_id'] == 0x100
    assert parent['entered_ns'] < child['entered_ns'] < child['exited_ns'] < parent['exited_ns']
    assert child['ancestors'][-1]['entry_id'] == parent['entry_id']
    assert audit.summary()['open_frames'] == 0


def test_unlogged_parent_is_preserved_in_child_ancestry(factory):
    events = []
    audit = recorder(factory, events)
    def original(hwnd, message, wparam, lparam):
        if message == 0x282:
            return wrapped(hwnd, 0xC2, 0, 0)
        return 8
    wrapped = audit.wrap(original, enabled=lambda: True, observed=lambda m: m == 0xC2)
    assert wrapped(77, 0x282, 0, 0) == 8
    assert len(events) == 1
    assert events[0]['parent_message_id'] == 0x282
    assert events[0]['ancestors'][-1]['message_id'] == 0x282


@pytest.mark.parametrize('origin_id,expected', [
    (0, 'unavailable'), (1, 'hardware_or_uiaccess'),
    (2, 'injected_non_uiaccess'), (4, 'system'), (16, 'unrecognized'),
])
def test_origin_labels_do_not_claim_a_human_or_sender_process(factory, origin_id, expected):
    events = []
    audit = recorder(factory, events, read_source=lambda: {'ok': True, 'device_type': 1, 'origin_id': origin_id})
    audit.wrap(lambda *args: 0, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0)
    assert events[0]['source']['origin'] == expected
    assert events[0]['source']['origin_id'] == origin_id
    assert 'sender_pid' not in events[0]


def test_observation_failure_is_explicit_and_does_not_prevent_original_dispatch(factory):
    events, calls = [], []
    def source_failure():
        raise OSError('PRIVATE EXCEPTION PAYLOAD')
    audit = recorder(factory, events, read_source=source_failure)
    result = audit.wrap(lambda *args: calls.append(args) or 42, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0)
    assert result == 42 and len(calls) == 1
    assert events[0]['source']['status'] == 'error'
    assert audit.summary()['complete'] is False
    assert 'PRIVATE' not in json.dumps(events)


def test_sink_failure_marks_incomplete_and_preserves_dispatch(factory):
    def broken_sink(event):
        raise OSError('disk full')
    audit = recorder(factory, [], emit=broken_sink)
    assert audit.wrap(lambda *args: 9, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0) == 9
    assert audit.summary()['complete'] is False
    assert audit.summary()['emitted_records'] == 0


def test_original_exception_propagates_and_unwinds_nesting(factory):
    events = []
    audit = recorder(factory, events)
    problem = RuntimeError('original problem')
    def original(*args):
        raise problem
    with pytest.raises(RuntimeError) as caught:
        audit.wrap(original, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0)
    assert caught.value is problem
    assert events[0]['dispatch_returned'] is False
    assert audit.summary()['open_frames'] == 0


def test_disabled_observation_is_transparent(factory):
    def forbidden():
        pytest.fail('disabled observation queried input source')
    events = []
    audit = recorder(factory, events, read_source=forbidden)
    assert audit.wrap(lambda *args: 7, enabled=lambda: False, observed=lambda m: True)(77, 0x100, 1, 2) == 7
    assert events == []


def test_sidecar_never_serializes_key_payloads_or_raw_values_from_api(factory):
    events = []
    audit = recorder(factory, events, read_source=lambda: {'ok': True, 'device_type': 1, 'origin_id': 2, 'text': 'PRIVATE'})
    audit.wrap(lambda *args: 0, enabled=lambda: True, observed=lambda m: True)(77, 0x102, 0x50, 0x12345678)
    payload = json.dumps(events)
    assert 'PRIVATE' not in payload and 'wparam' not in payload and 'lparam' not in payload
    assert '305419896' not in payload


def test_win32_reader_uses_typed_fields_and_retains_failure_code():
    assert hasattr(adapter, 'bind_input_source_reader'), 'fixture lacks Win32 input source reader'
    class Api:
        succeeds = True
        def __call__(self, pointer):
            fields = C.cast(pointer, C.POINTER(C.c_int * 2)).contents
            fields[0], fields[1] = 1, 2
            return self.succeeds
    class User32:
        GetCurrentInputMessageSource = Api()
    user32 = User32()
    read = adapter.bind_input_source_reader(user32, last_error=lambda: 87)
    assert read() == {'ok': True, 'device_type': 1, 'origin_id': 2}
    user32.GetCurrentInputMessageSource.succeeds = False
    assert read() == {'ok': False, 'error_code': 87}


def test_clock_failure_does_not_suppress_original_dispatch(factory):
    def broken_clock():
        raise OSError('clock observation failed')
    audit = recorder(factory, [], clock_ns=broken_clock)
    assert audit.wrap(lambda *args: 13, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0) == 13
    assert audit.summary()['complete'] is False
    assert audit.summary()['open_frames'] == 0


def test_lifecycle_records_bind_owned_controls_and_counts(factory):
    events = []
    audit = recorder(factory, events)
    assert hasattr(audit, 'start') and hasattr(audit, 'finish'), 'sidecar lifecycle is missing'
    assert audit.start([77, 88]) is True
    audit.wrap(lambda *args: 0, enabled=lambda: True, observed=lambda m: True)(77, 0x100, 0, 0)
    summary = audit.finish()
    assert events[0] == {'schema': 1, 'type': 'origin-start', 'pid': 123, 'controls': [77, 88]}
    assert events[-1]['type'] == 'origin-stop'
    assert events[-1]['emitted_records'] == events[-1]['observed_records'] == 1
    assert summary['complete'] is True


def test_failed_sidecar_stop_can_never_skip_fixture_cleanup(factory):
    def broken_sink(event):
        raise OSError('sidecar unavailable')
    audit = recorder(factory, [], emit=broken_sink)
    assert hasattr(audit, 'finish'), 'safe sidecar finish is missing'
    assert audit.finish()['complete'] is False


def test_installed_fixture_callback_observes_before_text_reads(factory, tmp_path):
    from ctypes import wintypes as W
    from types import SimpleNamespace
    class Api:
        def __init__(self, function):
            self.function = function
        def __call__(self, *args):
            return self.function(*args)
    events, order = [], []
    def pid_for_window(hwnd, pointer):
        C.cast(pointer, C.POINTER(W.DWORD))[0] = 123
        return 456
    def last_input(pointer):
        C.cast(pointer, C.POINTER(adapter.LASTINPUTINFO)).contents.dwTime = 99
        return True
    def read_text(hwnd, buffer, size):
        buffer.value = 'abc'
        return 3
    user32 = SimpleNamespace(
        GetWindowLongW=Api(lambda *args: 12), SetWindowLongW=Api(lambda *args: 12),
        CallWindowProcW=Api(lambda *args: order.append('dispatch') or 42),
        GetWindowTextLengthW=Api(lambda *args: order.append('text-read') or 3),
        GetWindowTextW=Api(read_text), GetForegroundWindow=Api(lambda: 77),
        GetFocus=Api(lambda: 77), InSendMessageEx=Api(lambda *args: 0),
        GetLastInputInfo=Api(last_input), GetWindowThreadProcessId=Api(pid_for_window),
    )
    kernel = SimpleNamespace(GetCurrentThreadId=Api(lambda: 456))
    audit = recorder(factory, events, read_source=lambda: order.append('source') or {'ok': True, 'device_type': 1, 'origin_id': 1})
    handle = adapter._install_audit(user32, kernel, 77, 123, tmp_path, 0, audit)
    handle['state']['enabled'] = True
    assert handle['callback'](77, 0x100, 0, 0) == 42
    assert order == ['source', 'text-read', 'dispatch', 'text-read']
    assert events[0]['source']['origin'] == 'hardware_or_uiaccess'
    legacy = json.loads((tmp_path / 'fixture-events.jsonl').read_text())
    assert legacy['message_id'] == 0x100 and legacy['before'] == legacy['after']


def complete_records(factory):
    events = []
    audit = recorder(factory, events)
    audit.start([77, 88])
    wrapped = audit.wrap(lambda *args: 0, enabled=lambda: True, observed=lambda m: True)
    wrapped(77, 0, 0, 0)
    wrapped(88, 0, 0, 0)
    audit.finish()
    return events


def validate(events, *, closed=True):
    assert hasattr(adapter, 'validate_origin_records'), 'sidecar completeness gate missing'
    return adapter.validate_origin_records(events, pid=123, controls=[77, 88], require_closed=closed)


def nested_records(factory, *, parent_observed=True, middle_observed=True):
    events = []
    audit = recorder(factory, events)
    audit.start([77, 88])
    def original(hwnd, message, wparam, lparam):
        if message == 0x100:
            wrapped(hwnd, 0x101, 0, 0)
        elif message == 0x101:
            wrapped(hwnd, 0x102, 0, 0)
            wrapped(hwnd, 0x103, 0, 0)
        return 0
    wrapped = audit.wrap(original, enabled=lambda: True,
                         observed=lambda message: (parent_observed or message != 0x100)
                         and (middle_observed or message != 0x101))
    wrapped(77, 0, 0, 0)
    wrapped(88, 0, 0, 0)
    wrapped(77, 0x100, 0, 0)
    audit.finish()
    return events


@pytest.mark.parametrize('parent_observed,middle_observed', [(True, True), (False, True), (False, False)])
def test_nested_recorded_and_unlogged_parent_lineages_pass(factory, parent_observed, middle_observed):
    assert validate(nested_records(factory, parent_observed=parent_observed,
                                   middle_observed=middle_observed))['status'] == 'PASS'


def test_rejects_missing_transitive_ancestor_even_when_counts_and_intervals_match(factory):
    events = nested_records(factory)
    grandchild = next(row for row in events if row.get('message_id') == 0x102)
    grandchild['ancestors'] = grandchild['ancestors'][1:]
    grandchild['depth'] = 1
    # Parent C and all counts/intervals remain unchanged; only P was hidden.
    with pytest.raises(ValueError, match='ancestor.*consistent'):
        validate(events)


def test_rejects_conflicting_identity_for_unlogged_ancestor(factory):
    events = nested_records(factory, parent_observed=False)
    grandchild = next(row for row in events if row.get('message_id') == 0x102)
    grandchild['ancestors'][0]['message_id'] = 0x104
    # P has no separate record, but C and G must describe the same P identity.
    with pytest.raises(ValueError, match='ancestor.*consistent'):
        validate(events)


def test_rejects_conflicting_prefix_for_unlogged_ancestor(factory):
    events = nested_records(factory, parent_observed=False, middle_observed=False)
    sibling = next(row for row in events if row.get('message_id') == 0x103)
    sibling['ancestors'] = sibling['ancestors'][1:]
    sibling['depth'] = 1
    # Neither P nor C has its own record; the two children must agree on C's chain.
    with pytest.raises(ValueError, match='ancestor.*consistent'):
        validate(events)


def test_sidecar_live_and_closed_validation_require_both_probes(factory):
    events = complete_records(factory)
    assert validate(events)['message_records'] == 2
    assert validate(events[:-1], closed=False)['status'] == 'PASS'
    with pytest.raises(ValueError):
        validate(events[:-1])
    without_second_probe = [events[0], events[1], dict(events[-1], observed_records=1, emitted_records=1)]
    with pytest.raises(ValueError):
        validate(without_second_probe)


@pytest.mark.parametrize('change', [
    lambda events: events[1].update(wparam=99),
    lambda events: events[1].update(pid=999),
    lambda events: events[1].update(hwnd=999),
    lambda events: events[1].update(send_flags_at_entry=None),
    lambda events: events[1]['source'].update(origin='human'),
    lambda events: events[1].update(entered_ns=10000),
    lambda events: events[2].update(entry_id=events[1]['entry_id']),
    lambda events: events[-1].update(emitted_records=99),
    lambda events: events[-1].update(complete=False),
    lambda events: events[1].update(ancestors_truncated=True),
])
def test_sidecar_rejects_unbound_incomplete_or_payload_bearing_records(factory, change):
    events = complete_records(factory)
    change(events)
    with pytest.raises(ValueError):
        validate(events)


def test_file_validator_rejects_duplicate_keys_and_unframed_records(factory, tmp_path):
    events = complete_records(factory)
    fixture = {'pid': 123, 'targets': [{'control_hwnd': 77}, {'control_hwnd': 88}]}
    path = tmp_path / 'fixture-input-origin.jsonl'
    text = ''.join(json.dumps(row) + '\n' for row in events)
    path.write_text(text, encoding='utf-8')
    assert adapter.validate_origin_audit(path, fixture)['status'] == 'PASS'
    path.write_text(text.replace('"schema": 1', '"schema": 1, "schema": 1', 1), encoding='utf-8')
    with pytest.raises(ValueError):
        adapter.validate_origin_audit(path, fixture)
    path.write_text(text.rstrip('\n'), encoding='utf-8')
    with pytest.raises(ValueError):
        adapter.validate_origin_audit(path, fixture)


def controller_audit():
    # Execute the prepared controller's real pure validation functions only.
    # Importing its module would inspect native processes/authority at import.
    import ast
    import datetime as dt
    import hashlib
    from pathlib import Path
    source = ast.parse((Path(__file__).parent / 'controller.py').read_text(encoding='utf-8'))
    names = {'require', 'timestamp', '_unique_pairs', 'validate_fixture_audit'}
    selected = ast.Module(body=[node for node in source.body if isinstance(node, ast.FunctionDef) and node.name in names], type_ignores=[])
    namespace = dict(Path=Path, dt=dt, hashlib=hashlib, json=json, fixture_audit=adapter)
    exec(compile(selected, 'prepared-controller-validation', 'exec'), namespace)
    return namespace['validate_fixture_audit']


@pytest.mark.parametrize('mode', ['absent', 'complete', 'missing_input'])
def test_controller_requires_correlated_sidecar_before_audit_pass(factory, tmp_path, mode):
    from pathlib import Path
    root = Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-source12-20261105-r31-preflight-log-isolation\actual\e03-round2')
    fixture = json.loads((root / 'fixture.json').read_text())
    legacy = (root / 'fixture-events.jsonl').read_bytes()
    path = tmp_path / 'fixture-events.jsonl'
    path.write_bytes(legacy)
    if mode != 'absent':
        events = []
        audit = recorder(factory, events, pid=fixture['pid'])
        audit.start([item['control_hwnd'] for item in fixture['targets']])
        wrapped = audit.wrap(lambda *args: 0, enabled=lambda: True, observed=lambda m: True)
        for line in legacy.splitlines():
            row = json.loads(line)
            if row['type'] == 'edit-message' and (mode == 'complete' or row['message_id'] == 0):
                wrapped(row['hwnd'], row['message_id'], 0, 0)
        audit.finish()
        (tmp_path / 'fixture-input-origin.jsonl').write_text(''.join(json.dumps(row) + '\n' for row in events), encoding='utf-8')
    if mode == 'complete':
        result = controller_audit()(path, fixture)
        assert result['input_origin']['message_records'] == 17
    else:
        with pytest.raises((ValueError, FileNotFoundError)):
            controller_audit()(path, fixture)
