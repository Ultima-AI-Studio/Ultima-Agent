import datetime as dt
import hashlib
import importlib
import json
from pathlib import Path

import pytest


@pytest.fixture
def api():
    return importlib.import_module('fixture_diagnostic')


NOW = dt.datetime(2026, 11, 5, 9, 0, tzinfo=dt.timezone.utc)
HEAD = '7975e477665c02820fa235b73d203718bd33b2c9'
MANIFEST = 'a' * 64


def authority():
    return dict(schema=1, issuer='root', scope='fixture-only-diagnostic', case='fixture-origin-01',
                candidate=HEAD, manifest_sha256=MANIFEST, review_sha256='b' * 64,
                case_cap=1, retry_authorized=False, acceptance_credit=False,
                model_requests=0, product_cli_requests=0, audio_actions=0,
                issued_at='2026-11-05T08:59:00+00:00', expires_at='2026-11-05T09:09:00+00:00',
                user_authorization='Explicitly approved one fixture-only diagnostic after independent review')


def review():
    return dict(reviewer='root-independent', verdict='PASS', scope='fixture-only-diagnostic-package',
                manifest_sha256=MANIFEST)


def test_valid_release_is_only_one_fixture_diagnostic(api):
    assert api.validate_authority(authority(), MANIFEST, review(), NOW) == 'fixture-origin-01'


@pytest.mark.parametrize('change', [
    {'scope': 'recovery-diagnostic'}, {'case': 'e03-round2'}, {'candidate': '0' * 40},
    {'case_cap': 2}, {'case_cap': True}, {'retry_authorized': True}, {'acceptance_credit': True},
    {'model_requests': 1}, {'product_cli_requests': 1}, {'audio_actions': 1},
    {'manifest_sha256': 'c' * 64}, {'user_authorization': ''},
    {'allow_other_models': True}, {'model_requests': False},
    {'expires_at': '2026-11-05T08:59:00+00:00'},
    {'expires_at': '2026-11-06T09:09:00+00:00'},
])
def test_rejects_expired_reused_or_broader_scope(api, change):
    value = authority(); value.update(change)
    with pytest.raises(ValueError):
        api.validate_authority(value, MANIFEST, review(), NOW)


def test_rejects_mismatched_or_failed_review(api):
    for change in ({'manifest_sha256': '0' * 64}, {'verdict': 'NEEDS_FIXES'},
                   {'scope': 'input-origin-patch-only'}, {'reviewer': 'root'}):
        value = review(); value.update(change)
        with pytest.raises(ValueError):
            api.validate_authority(authority(), MANIFEST, value, NOW)


class FakeBackend:
    def __init__(self, failure=None, changed=False, late=False):
        self.calls = []; self.failure = failure; self.changed = changed; self.late = late
        self.deadline_triggered = False
    def action(self, name):
        self.calls.append(name)
        if self.failure == name: raise RuntimeError(name + ' failed')
    def preflight(self):
        self.action('preflight'); return {'seven': 'same'}
    def start(self, folder):
        assert (folder / 'admission.json').exists()
        self.action('start')
    def capture(self):
        self.action('capture')
        return {'phenomenon': 'TEXT_CHANGED' if self.changed else 'UNCHANGED',
                'baseline_summaries': [{'utf16_units': 0 if self.changed else 41, 'sha256_utf16le': 'd' * 64}]}
    def close(self):
        self.action('close'); return {'status': 'PASS'}
    def postflight(self, before):
        assert before == {'seven': 'same'}
        self.action('postflight'); return {'status': 'PASS'}
    def audit(self):
        self.action('audit'); return {'status': 'PASS'}


def claimed_run(api, tmp_path, backend, *, elapsed=1):
    now = iter([0.0, elapsed])
    return api.execute_claimed(tmp_path, authority(), backend, clock=lambda: next(now))


@pytest.mark.parametrize('changed', [True, False])
def test_single_claim_preserves_operation_order_without_product_acceptance(api, tmp_path, changed):
    backend = FakeBackend(changed=changed)
    result = claimed_run(api, tmp_path, backend)
    assert backend.calls == ['preflight', 'start', 'capture', 'close', 'postflight', 'audit']
    assert result['diagnostic_status'] == 'COMPLETE'
    assert result['phenomenon'] == ('TEXT_CHANGED' if changed else 'UNCHANGED')
    assert result['product_acceptance'] == 'NOT_EVALUATED'
    assert result['model_requests'] == result['product_cli_requests'] == 0
    second = FakeBackend()
    with pytest.raises(FileExistsError):
        claimed_run(api, tmp_path, second)
    assert second.calls == []


@pytest.mark.parametrize('failure', ['start', 'capture', 'close', 'postflight', 'audit'])
def test_admitted_failures_never_skip_cleanup_or_consume_twice(api, tmp_path, failure):
    backend = FakeBackend(failure=failure)
    result = claimed_run(api, tmp_path, backend)
    assert 'close' in backend.calls and 'postflight' in backend.calls and 'audit' in backend.calls
    assert result['diagnostic_status'] == 'INCOMPLETE'
    assert result['phenomenon'] == 'UNKNOWN'
    assert (tmp_path / 'actual/fixture-origin-01/admission.json').exists()
    assert (tmp_path / 'actual/fixture-origin-01/terminal.json').exists()


def test_preflight_failure_starts_no_window_and_does_not_claim(api, tmp_path):
    backend = FakeBackend(failure='preflight')
    with pytest.raises(RuntimeError): claimed_run(api, tmp_path, backend)
    assert backend.calls == ['preflight']
    assert not (tmp_path / 'actual/fixture-origin-01').exists()


def test_late_completion_is_incomplete_but_cleanup_finishes(api, tmp_path):
    backend = FakeBackend()
    result = claimed_run(api, tmp_path, backend, elapsed=61)
    assert backend.calls[-3:] == ['close', 'postflight', 'audit']
    assert result['diagnostic_status'] == 'INCOMPLETE'
    assert result['deadline_exceeded'] is True


def test_watchdog_stop_is_not_a_success(api, tmp_path):
    backend = FakeBackend(); backend.deadline_triggered = True
    assert claimed_run(api, tmp_path, backend)['diagnostic_status'] == 'INCOMPLETE'


def test_result_summary_excludes_plaintext(api):
    rows = [{'text': 'private unexpected typing', 'hwnd': 11, 'control_hwnd': 12, 'pid': 13,
             'start_utf16': 0, 'end_utf16': 25}]
    value = api.summarize_observations(rows)
    assert 'private' not in json.dumps(value) and 'text' not in value[0]
    assert value[0]['utf16_units'] == 25 and len(value[0]['sha256_utf16le']) == 64


def sealed_package(api, tmp_path):
    records = []
    for relative in sorted(api.RUNTIME_FILES):
        path = tmp_path / relative
        path.parent.mkdir(exist_ok=True, parents=True)
        path.write_bytes(b'opaque offline test dependency')
        records.append(dict(path=relative, bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
    manifest = dict(schema=1, scope='fixture-only-diagnostic', candidate=HEAD,
                    package_root=str(tmp_path), acceptance_credit=False, files=records,
                    python_executable=r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
    path = tmp_path / 'manifest.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def release(api, tmp_path):
    digest = sealed_package(api, tmp_path)
    folder = tmp_path / 'release'; folder.mkdir()
    reviewed = review(); reviewed['manifest_sha256'] = digest
    path = folder / 'independent-review.json'; path.write_text(json.dumps(reviewed), encoding='utf-8')
    grant = authority(); grant['manifest_sha256'] = digest
    grant['review_sha256'] = hashlib.sha256(path.read_bytes()).hexdigest()
    (folder / 'authority.json').write_text(json.dumps(grant), encoding='utf-8')


@pytest.mark.parametrize('problem', ['missing_authority', 'changed_review', 'changed_code', 'extra_code', 'path_escape'])
def test_release_gate_fails_before_constructing_native_backend(api, tmp_path, problem):
    release(api, tmp_path)
    if problem == 'missing_authority': (tmp_path / 'release/authority.json').unlink()
    elif problem == 'changed_review': (tmp_path / 'release/independent-review.json').write_text('{}')
    elif problem == 'changed_code': (tmp_path / 'code/controller.py').write_text('changed')
    elif problem == 'extra_code': (tmp_path / 'code/extra.py').write_text('unexpected')
    else:
        path = tmp_path / 'manifest.json'; value = json.loads(path.read_text())
        value['files'][0]['path'] = '../outside'; path.write_text(json.dumps(value))
    constructed = []
    def factory(root):
        constructed.append(root)
        return FakeBackend()
    with pytest.raises((ValueError, FileNotFoundError)):
        api.run_once(tmp_path, now=NOW, backend_factory=factory)
    assert constructed == [] and not (tmp_path / 'actual').exists()


def test_complete_release_reaches_only_injected_fixture_backend(api, tmp_path):
    release(api, tmp_path)
    backend = FakeBackend()
    result = api.run_once(tmp_path, now=NOW, backend_factory=lambda root: backend)
    assert result['product_acceptance'] == 'NOT_EVALUATED'
    assert backend.calls == ['preflight', 'start', 'capture', 'close', 'postflight', 'audit']


def test_consumed_case_is_rejected_before_constructing_backend(api, tmp_path):
    release(api, tmp_path)
    (tmp_path/'actual/fixture-origin-01').mkdir(parents=True)
    constructed=[]
    def factory(root):
        constructed.append(root)
        return FakeBackend()
    with pytest.raises(FileExistsError):
        api.run_once(tmp_path,now=NOW,backend_factory=factory)
    assert constructed==[]


def test_dangling_link_is_rejected_before_any_write(api, tmp_path, monkeypatch):
    target = tmp_path / 'dangling'
    original = Path.is_symlink
    monkeypatch.setattr(Path, 'is_symlink', lambda path: path == target or original(path))
    with pytest.raises(ValueError, match='Reparse'):
        api.safe_path(target)


def test_dangling_junction_attributes_are_rejected(api, tmp_path, monkeypatch):
    from types import SimpleNamespace
    target = tmp_path / 'dangling-junction'
    original = Path.lstat
    monkeypatch.setattr(Path, 'lstat', lambda path: SimpleNamespace(st_mode=0o40755, st_file_attributes=0x400)
                        if path == target else original(path))
    with pytest.raises(ValueError, match='Reparse'):
        api.safe_path(target)


def test_wrong_interpreter_stops_before_loading_native_bridge(api, tmp_path, monkeypatch):
    release(api, tmp_path)
    monkeypatch.setattr(api.sys, 'executable', r'C:\other\python.exe')
    with pytest.raises(ValueError, match='interpreter'):
        api.run_once(tmp_path, now=NOW)
    assert not (tmp_path/'actual').exists()
