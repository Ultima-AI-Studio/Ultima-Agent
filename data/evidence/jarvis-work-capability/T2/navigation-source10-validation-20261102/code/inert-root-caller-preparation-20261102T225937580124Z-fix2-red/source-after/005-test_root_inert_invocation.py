"""Pure caller contracts. Runtime/native/launch/socket boundaries are denied."""
from pathlib import Path
from contextlib import nullcontext
import ctypes
import datetime as dt
import hashlib
import importlib.util
import json
import os
import socket
import subprocess
import sys
from types import SimpleNamespace
import pytest

HERE = Path(__file__).resolve().parent
REAL_V = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    exec(compile(path.read_bytes(), str(path), 'exec'), result.__dict__)
    return result


@pytest.fixture(autouse=True)
def deny_runtime(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError('PREPARATION runtime/native/network/launch denied')
    monkeypatch.setattr(socket, 'socket', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)
    monkeypatch.setattr(subprocess, 'Popen', denied)
    monkeypatch.setattr(os, 'system', denied)
    monkeypatch.setattr(ctypes, 'WinDLL', denied)
    monkeypatch.setattr(ctypes, 'CDLL', denied)


@pytest.fixture
def env(tmp_path, monkeypatch):
    c = module('caller_contract', HERE/'root-inert-invocation.py')
    a_path = REAL_V/'harness/adapter.py'
    assert hashlib.sha256(a_path.read_bytes()).hexdigest() == '3a5526abfbfdfd419c133d6a7c214d1cd4d09b24951f03ae991649a4dad8558f'
    definitions = module('reviewed_deadline_definitions', a_path)
    v, w = tmp_path/'V', tmp_path/'W'
    v.mkdir(); w.mkdir(); (v/'harness').mkdir(); (v/'inert-root-caller-review-2').mkdir()
    monkeypatch.setattr(c, 'V', v); monkeypatch.setattr(c, 'W', w)
    clock = [1_000_000_000]
    monkeypatch.setattr(c.time, 'monotonic_ns', lambda: clock[0])
    monkeypatch.setattr(c, 'ENTRY_NS', clock[0])
    def write(path, obj):
        path.write_text(json.dumps(obj, sort_keys=True), encoding='utf8')
    events = []
    protected = [dict(pid=i, created_filetime=1000+i, exe='native.exe') for i in range(1, 6)]
    historical = v/'historical.json'; write(historical, dict(protected5=protected))
    monkeypatch.setattr(c, 'HISTORICAL', historical); monkeypatch.setattr(c, 'HISTORICAL_SHA', c.sha(historical))
    candidate = v/'source10-candidate-manifest.json'; write(candidate, {})
    monkeypatch.setattr(c, 'CANDIDATE_SHA', c.sha(candidate))
    monkeypatch.setattr(definitions, 'MANIFEST_SHA', c.CANDIDATE_SHA)
    harness = dict(files={n: '' for n in ('adapter.py', 'test_adapter.py', 'headless_proof.py', 'README.md', 'run_checks.py')})
    for n in harness['files']:
        (v/'harness'/n).write_text('# mock checked definition\n', encoding='utf8')
        harness['files'][n] = c.sha(v/'harness'/n)
    write(v/'harness/manifest.json', harness); monkeypatch.setattr(c, 'HARNESS_SHA', c.sha(v/'harness/manifest.json'))
    for n in c.FILES:
        (w/n).write_text('# mock reviewed package\n', encoding='utf8')
    dependency = v/'dependency.txt'; dependency.write_text('immutable source input', encoding='utf8')
    manifest = dict(candidate=c.CANDIDATE, files={n: c.sha(w/n) for n in c.FILES}, dependencies={str(dependency): c.sha(dependency)})
    write(w/'inert-root-caller-manifest.json', manifest)
    caller_sha = c.sha(w/'inert-root-caller-manifest.json')
    review = dict(spec='PASS', quality='APPROVED', spec_verdict='PASS', quality_verdict='APPROVED', caller_manifest_sha256=caller_sha)
    write(v/'inert-root-caller-review-2/verdict.json', review)
    (v/'inert-root-caller-review-2/review.md').write_text('Independent mock review', encoding='utf8')
    review_sha = c.sha(v/'inert-root-caller-review-2/verdict.json'); report_sha = c.sha(v/'inert-root-caller-review-2/review.md')
    approval = dict(reviewer='root-independent', overall='PASS', candidate=c.CANDIDATE,
                    manifest_sha256=c.HARNESS_SHA, candidate_manifest_sha256=c.CANDIDATE_SHA,
                    review_sha256=c.REVIEW_SHA, review_report_sha256=c.REVIEW_REPORT_SHA,
                    caller_manifest_sha256=caller_sha, caller_review_sha256=review_sha,
                    caller_review_report_sha256=report_sha, caller_spec='PASS', caller_quality='APPROVED', model_policy=c.MODEL)
    write(v/'harness-approval.json', approval)
    now = c.utc()
    release = dict(schema=1, kind='source10_inert_root_release', issuer='root', released=True,
                   candidate=c.CANDIDATE, candidate_manifest_sha256=c.CANDIDATE_SHA,
                   harness_manifest_sha256=c.HARNESS_SHA, harness_review_sha256=c.REVIEW_SHA,
                   harness_review_report_sha256=c.REVIEW_REPORT_SHA, schedule=c.SCHEDULE,
                   model_policy=c.MODEL, scope=c.SCOPE, port=c.PORT, run_scope='one-new-inert-root-invocation',
                   issued_at=now.isoformat(), expires_at=(now+dt.timedelta(seconds=100)).isoformat(),
                   caller_manifest_sha256=caller_sha, approval_sha256=c.sha(v/'harness-approval.json'),
                   caller_review_sha256=review_sha, caller_review_report_sha256=report_sha)
    release.update(protocol_ruling_sha256=c.PROTOCOL_SHA, entry=c.entry_binding(), release_id='00000000-0000-4000-8000-000000000001')
    dispatch = dict(schema=1, kind='source10_inert_root_dispatch', issuer='root', consumed=1, max_attempts=1,
                    retry=0, candidate=c.CANDIDATE, caller_manifest_sha256=caller_sha, entry=c.entry_binding(),
                    scope=c.SCOPE, model_policy=c.MODEL, port=c.PORT, run_scope='one-new-inert-root-invocation',
                    release_id=release['release_id'], protocol_ruling_sha256=c.PROTOCOL_SHA)
    write(v/'inert-root-dispatch.json', dispatch)
    release['dispatch_sha256'] = c.sha(v/'inert-root-dispatch.json')
    monkeypatch.setattr(c, '_GO', dict(action='go', dispatch_sha256=release['dispatch_sha256']))
    write(v/'inert-root-release.json', release)
    def native():
        events.append('native')
        assert (v/'inert-root-release.consumed.json').is_file()
        return protected
    p4 = SimpleNamespace(protected=native, listener_owner=lambda port: events.append(('port', port)) or None)
    class Invocation:
        instances = []
        eligible = True
        error = None
        def __init__(self):
            self.budget = definitions.Deadline(clock=lambda: clock[0])
            self.observer = definitions.TimingObservation(self.budget)
            self.called = False; self.instances.append(self)
        def parent_timing(self):
            events.append('parent-native')
            return dict(self.budget.timing(), parent_identity=dict(pid=999, created_filetime=2000, exe='root.exe'))
        def call(self, entry):
            assert not self.called; self.called = True
            events.append('inv.call')
            try:
                result = entry()
            except Exception as exc:
                self.budget.failure = self.budget.failure or str(exc)
                result = None  # Match reviewed RootInvocation's exception observation.
            if self.error:
                raise self.error
            proofs = dict.fromkeys(('cleanup', 'closed', 'pins', 'protected', 'readback'), self.eligible)
            return dict(result=result, witness=self.observer.finish('a'*64, proofs))
    def headless_entry():
        events.append('MOCK headless')
        assert (v/'inert-authority.json').is_file()
        authority = c.load(v/'inert-authority.json')
        fake_a.inert_admit(budget=Invocation.instances[-1].budget)
        assert not Path(authority['folder']).exists()
        return dict(folder=authority['folder'], overall='READY_FOR_ROOT_TIMING_WITNESS')
    fake_a = SimpleNamespace(RootInvocation=Invocation, CLOCK_DOMAIN=definitions.CLOCK_DOMAIN,
        load_p4=lambda: events.append('P4 definitions') or p4,
        package_check=lambda p4: None, check_inputs=lambda: None, check_import_origins=lambda: None,
        validate_protected_members=lambda ids, p4: c.exact_native(ids, protected),
        check_native_baseline=lambda proof, p4: definitions.check_native_baseline(proof, SimpleNamespace(protected=lambda: protected, identity=lambda pid: protected[pid-1])),
        PrivateIO=lambda p4, budget: nullcontext(), validate_inert_documents=definitions.validate_inert_documents)
    def fake_admit(*, budget=None):
        authority = c.load(v/'inert-authority.json'); baseline = c.load(v/'inert-native-baseline.json')
        budget.admitted = dict(mode='inert', folder=authority['folder'], port=authority['port'],
            authority=authority, baseline=baseline, timing=budget.timing(), pins={str(v/n):c.sha(v/n) for n in ('inert-authority.json','inert-native-baseline.json','harness-approval.json')})
        return authority, Path(authority['folder']), p4, baseline['protected']
    fake_a.inert_admit = fake_admit
    headless = SimpleNamespace(run_inert=headless_entry)
    monkeypatch.setattr(c, 'load_harness', lambda h: (fake_a, headless))
    return SimpleNamespace(c=c, v=v, w=w, release=release, approval=approval, write=write, events=events,
                           clock=clock, inv=Invocation, protected=protected, dependency=dependency, definitions=definitions, a=fake_a, p4=p4, headless=headless)


@pytest.mark.parametrize('change', ['missing', 'false', 'wrong', 'stale', 'extra', 'bool_port', 'changed_model', 'retry'])
def test_release_rejection_precedes_every_runtime_boundary(env, change):
    e = env; r = dict(e.release)
    if change == 'missing': (e.v/'inert-root-release.json').unlink()
    else:
        if change == 'false': r['released'] = False
        if change == 'wrong': r['candidate'] = 'wrong'
        if change == 'stale': r['expires_at'] = r['issued_at']
        if change == 'extra': r['script'] = 'arbitrary.py'
        if change == 'bool_port': r['port'] = True
        if change == 'changed_model': r['model_policy'] = dict(alias='other')
        if change == 'retry': r['scope'] = dict(r['scope'], retry=1)
        e.write(e.v/'inert-root-release.json', r)
    with pytest.raises(ValueError): e.c.run()
    assert e.events == []
    assert not (e.v/'inert-authority.json').exists()
    assert not (e.v/'inert-root-release.consumed.json').exists()


@pytest.mark.parametrize('changed', ['caller', 'dependency', 'harness', 'manifest', 'approval', 'review'])
def test_changed_reviewed_bytes_consume_without_native(env, changed):
    e = env
    paths = dict(caller=e.w/'root-inert-invocation.py', dependency=e.dependency,
                 harness=e.v/'harness/adapter.py', manifest=e.w/'inert-root-caller-manifest.json',
                 approval=e.v/'harness-approval.json', review=e.v/'inert-root-caller-review-2/review.md')
    paths[changed].write_text('drift', encoding='utf8')
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert e.events == []
    assert (e.v/'inert-root-release.consumed.json').is_file()
    assert not (e.v/'inert-authority.json').exists()


def test_approval_bound_to_caller_even_with_updated_raw_hash(env):
    e = env
    approval = dict(e.approval, caller_manifest_sha256='0'*64)
    e.write(e.v/'harness-approval.json', approval)
    e.release['approval_sha256'] = e.c.sha(e.v/'harness-approval.json')
    e.write(e.v/'inert-root-release.json', e.release)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL' and e.events == []


def test_success_uses_one_existing_invocation_and_outside_witness(env):
    e = env; e.clock[0] += 4_000_000_000
    record = e.c.run()
    assert record['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW'
    assert e.events.count('inv.call') == e.events.count('MOCK headless') == 1
    assert e.inv.instances[0].budget.origin_ns == e.c.ENTRY_NS
    assert record['outcome']['witness']['origin_ns'] == e.c.ENTRY_NS
    authority = e.c.load(e.v/'inert-authority.json')
    assert authority['parent_timing']['origin_ns'] == e.c.ENTRY_NS
    assert authority['run_id'] == e.inv.instances[0].budget.run_id
    assert authority['native_baseline_sha256'] == e.c.sha(e.v/'inert-native-baseline.json')
    assert authority['approval_sha256'] == e.c.sha(e.v/'harness-approval.json')
    assert authority['port'] == 18765 and authority['schedule'] == e.c.SCHEDULE
    assert not Path(authority['folder']).exists()
    assert record['T2'] == 'NOT_PASSED' and record['production'] == 'CLOSED'
    before = (e.v/'inert-root-result.json').read_bytes()
    with pytest.raises(ValueError): e.c.run()
    assert before == (e.v/'inert-root-result.json').read_bytes()
    assert e.events.count('inv.call') == 1


@pytest.mark.parametrize('name', ['inert-authority.json', 'inert-native-baseline.json', 'inert-root-result.json'])
def test_existing_canonical_refused_and_never_overwritten(env, name):
    e = env; path = e.v/name; path.write_bytes(b'OLD IMMUTABLE')
    if name == 'inert-root-result.json':
        with pytest.raises(FileExistsError): e.c.run()
    else:
        assert e.c.run()['overall'] == 'PERMANENT_FAIL'
    assert path.read_bytes() == b'OLD IMMUTABLE' and e.events == []


def test_claim_is_exclusive(env):
    e = env; claim = e.v/'inert-root-release.consumed.json'; claim.write_bytes(b'old allocation')
    with pytest.raises(ValueError): e.c.run()
    assert claim.read_bytes() == b'old allocation' and e.events == []


def test_preimport_expired_origin_does_not_renew(env):
    e = env; e.clock[0] += 275_000_000_000
    with pytest.raises(ValueError, match='Deadline admission'): e.c.run()
    assert not e.inv.instances and not e.events


def test_slow_import_cannot_renew_allowance(env, monkeypatch):
    e = env; original = e.c.load_harness
    def slow(h):
        value = original(h); e.clock[0] += 276_000_000_000; return value
    monkeypatch.setattr(e.c, 'load_harness', slow)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL' and e.events == []
    assert not (e.v/'inert-authority.json').exists()


def test_late_claim_is_recorded_as_permanent_failure(env, monkeypatch):
    e = env; original = e.c.write_json; calls = [0]
    def slow(stream, value):
        original(stream, value); calls[0] += 1
        if calls[0] == 1: e.clock[0] += 276_000_000_000
    monkeypatch.setattr(e.c, 'write_json', slow)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL' and e.events == []
    assert record['first_cause']['type'] == 'TimeoutError'


@pytest.mark.parametrize('bad', ['bool_pid', 'float_time', 'bool_time', 'missing', 'extra', 'duplicate', 'drift'])
def test_exact_native_identity_contract(env, bad):
    e = env; ids = [dict(x) for x in e.protected]
    if bad == 'bool_pid': ids[0]['pid'] = True
    if bad == 'float_time': ids[0]['created_filetime'] = float(ids[0]['created_filetime'])
    if bad == 'bool_time': ids[0]['created_filetime'] = True
    if bad == 'missing': ids.pop()
    if bad == 'extra': ids[0]['cim'] = 'approximate'
    if bad == 'duplicate': ids[1] = ids[0]
    if bad == 'drift': ids[0]['created_filetime'] += 1
    with pytest.raises(ValueError): e.c.exact_native(ids, e.protected)


def test_exact_native_membership_order_irrelevant(env):
    env.c.exact_native(list(reversed(env.protected)), env.protected)


@pytest.mark.parametrize('mode', ['failed', 'late', 'exception', 'missing'])
def test_failed_unknown_or_late_return_never_promotes(env, monkeypatch, mode):
    e = env
    if mode == 'failed': e.inv.eligible = False
    if mode == 'exception': e.inv.error = RuntimeError('first original cause')
    if mode == 'late':
        original = e.inv.call
        def late(self, entry):
            e.clock[0] = e.c.ENTRY_NS+315_000_000_001
            return original(self, entry)
        monkeypatch.setattr(e.inv, 'call', late)
    if mode == 'missing': monkeypatch.setattr(e.inv, 'call', lambda *args: None)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert e.events.count('MOCK headless') <= 1
    if mode == 'late':
        assert record['outcome']['witness']['observed_ns'] == e.c.ENTRY_NS+315_000_000_001
        assert record['outcome']['witness']['eligible'] is False
    if mode == 'exception': assert record['first_cause']['message'] == 'first original cause'


def test_timely_observation_persisted_later_without_backdating(env, monkeypatch):
    e = env
    # Advance before record timestamp sample, after observed witness has returned.
    original_controls = e.c.check_controls
    count = [0]
    def controls(*args):
        result = original_controls(*args); count[0] += 1
        if count[0] == 3: e.clock[0] += 400_000_000_000
        return result
    monkeypatch.setattr(e.c, 'check_controls', controls)
    record = e.c.run()
    assert record['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW'
    assert record['persistence_started_monotonic_ns'] > record['origin_ns']+315_000_000_000
    assert record['outcome']['witness']['observed_ns'] <= record['origin_ns']+315_000_000_000


def test_checked_import_rejects_cached_module_and_drift(env, monkeypatch):
    e = env; path = e.w/'safe.py'; path.write_text('value = 1', encoding='utf8')
    monkeypatch.setitem(sys.modules, 'unexpected', object())
    with pytest.raises(ValueError, match='cached'): e.c.checked_import('unexpected', path, e.c.sha(path))
    with pytest.raises(ValueError, match='drift'): e.c.checked_import('fresh', path, '0'*64)


def test_actual_pinned_harness_definition_import_restores_bindings(env, monkeypatch):
    e = env; monkeypatch.setattr(e.c, 'V', REAL_V)
    harness = e.c.load(REAL_V/'harness/manifest.json')
    before = list(sys.path)
    # Invoke the real function, not the fixture replacement.
    actual = module('caller_import_contract', HERE/'root-inert-invocation.py')
    a, headless = actual.load_harness(harness)
    assert headless.a is a and sys.path == before and 'adapter' not in sys.modules
    with pytest.raises(AssertionError, match='denied'): socket.socket()


@pytest.mark.parametrize('payload', [b'{"a":1,"a":2}', b'{"a":NaN}', b'{"a":Infinity}'])
def test_strict_json_refuses_ambiguous_controls(env, payload):
    with pytest.raises(ValueError): env.c.decode(payload)


def test_released_false_template_is_never_runtime_authority(env):
    template = json.loads((HERE/'inert-root-release-template.json').read_text('utf8'))
    assert template['released'] is False
    with pytest.raises(ValueError): env.c.release_check(template)


def test_expired_origin_cannot_be_renewed_by_invocation_constructor(env, monkeypatch):
    e = env; original = e.inv.__init__
    def delayed(self):
        e.clock[0] += 276_000_000_000
        original(self)
    monkeypatch.setattr(e.inv, '__init__', delayed)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL' and e.events == []
    assert e.inv.instances[0].budget.origin_ns == e.c.ENTRY_NS
    assert 'earlier parent admission' in record['first_cause']['message']


def test_failed_claim_write_stays_consumed_and_records_unknown(env, monkeypatch):
    e = env; original = e.c.write_json; calls = [0]
    def broken(stream, value):
        calls[0] += 1
        if calls[0] == 1:
            stream.write('{')
            raise OSError('claim write interrupted')
        original(stream, value)
    monkeypatch.setattr(e.c, 'write_json', broken)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL' and record['effects'] == 'unknown'
    assert record['first_cause']['message'] == 'claim write interrupted'
    assert (e.v/'inert-root-release.consumed.json').read_text('utf8') == '{'
    assert e.events == []


def test_historical_one_tick_drift_blocks_before_headless(env):
    e = env; e.protected[0]['created_filetime'] += 1
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert 'Historical exact native identity drift' in record['first_cause']['message']
    assert 'inv.call' not in e.events and not (e.v/'inert-native-baseline.json').exists()


def test_changed_extra_root_control_cannot_promote_timely_witness(env, monkeypatch):
    e = env; original = e.inv.call
    def tamper(self, entry):
        result = original(self, entry)
        (e.v/'inert-root-release.consumed.json').write_bytes(b'tampered')
        return result
    monkeypatch.setattr(e.inv, 'call', tamper)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert record['outcome']['witness']['eligible'] is True
    assert 'Consumption drift' in record['first_cause']['message']


def test_stale_native_baseline_uses_existing_validator_with_fake_native(env):
    e = env
    proof = dict(precision='FILETIME100ns', candidate=e.c.CANDIDATE,
                 recorded_at=(e.c.utc()-dt.timedelta(seconds=61)).isoformat(), protected=e.protected)
    with pytest.raises(ValueError, match='Stale native baseline'):
        e.a.check_native_baseline(proof, e.p4)


def test_slow_native_scan_does_not_refresh_first_observation_time(env, monkeypatch):
    e = env; real_datetime = dt.datetime; wall = [real_datetime.now(dt.timezone.utc)]
    class WallClock(real_datetime):
        @classmethod
        def now(cls, tz=None):
            return wall[0] if tz else wall[0].replace(tzinfo=None)
    monkeypatch.setattr(dt, 'datetime', WallClock)
    original = e.p4.protected
    def slow_scan():
        value = original(); wall[0] += dt.timedelta(seconds=61); e.clock[0] += 61_000_000_000
        return value
    monkeypatch.setattr(e.p4, 'protected', slow_scan)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert 'Stale native baseline' in record['first_cause']['message']
    assert 'inv.call' not in e.events and not (e.v/'inert-native-baseline.json').exists()


@pytest.mark.parametrize('offset,eligible', [(315_000_000_000, True), (315_000_000_001, False)])
def test_existing_observation_inclusive_closure_boundary(env, offset, eligible):
    e = env; budget = e.definitions.Deadline(clock=lambda:e.clock[0])
    budget.adopt_parent(dict(run_id=budget.run_id, clock_domain=e.definitions.CLOCK_DOMAIN, origin_ns=e.c.ENTRY_NS))
    e.clock[0] = e.c.ENTRY_NS+offset
    witness = e.definitions.TimingObservation(budget).finish('a'*64, dict.fromkeys(('cleanup','closed','pins','protected','readback'), True))
    assert witness['eligible'] is eligible


# Formal fix round 1: behavioral reproductions for RC-01 through RC-07.
@pytest.mark.parametrize('control', ['harness', 'review', 'historical'])
def test_rc01_interprets_only_digest_checked_control_bytes(env, monkeypatch, control):
    e = env; original = e.c.load; replacements = []
    targets = dict(harness=e.v/'harness/manifest.json', review=e.v/'inert-root-caller-review-2/verdict.json', historical=e.c.HISTORICAL)
    target = targets[control]
    def second_read(path):
        if path == target:
            replacements.append(str(path))
            return {}  # Simulates replacement between successful hash and reopen.
        return original(path)
    monkeypatch.setattr(e.c, 'load', second_read)
    record = e.c.run()
    assert replacements == [], 'A digest-checked control was reopened for interpretation'
    assert record['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW'


@pytest.mark.parametrize('stall', ['before_p4', 'before_native'])
def test_rc02_stalled_prerequisite_cannot_admit_after_release_expiry(env, monkeypatch, stall):
    e = env; wall = [e.c.utc()]; monkeypatch.setattr(e.c, 'utc', lambda:wall[0])
    if stall == 'before_p4':
        original = e.c.sha
        def slow(path):
            value = original(path)
            if path == e.v/'inert-root-release.json': wall[0] += dt.timedelta(seconds=101)
            return value
        monkeypatch.setattr(e.c, 'sha', slow)
    else:
        original = e.c.raw
        def slow(path):
            value = original(path)
            if path == e.c.HISTORICAL: wall[0] += dt.timedelta(seconds=101)
            return value
        monkeypatch.setattr(e.c, 'raw', slow)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    if stall == 'before_p4': assert 'P4 definitions' not in e.events
    assert 'native' not in e.events and 'parent-native' not in e.events and 'inv.call' not in e.events


def test_rc03_precreation_claim_failure_cannot_replay_entry_or_allocation(env, monkeypatch):
    e = env; original = Path.open; fail = [True]
    def fail_open(path, *args, **kwargs):
        if path == e.v/'inert-root-release.consumed.json' and fail[0]:
            fail[0] = False
            raise PermissionError('mock pre-creation failure')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'open', fail_open)
    with pytest.raises(ValueError): e.c.run()
    try: e.c.run()
    except ValueError: pass
    assert e.events == [], 'Same release was replayed after failure before claim creation'
    # A distinct process-entry nonce cannot reuse the ROOT grant either.
    monkeypatch.setattr(e.c, 'ENTRY_NONCE', '00000000-0000-4000-8000-000000000099', raising=False)
    monkeypatch.setattr(e.c, '_ENTRY_USED', False, raising=False)
    try: e.c.run()
    except (ValueError, FileExistsError): pass
    assert e.events == []


@pytest.mark.parametrize('namespace', ['orphan', 'empty', 'unreadable'])
def test_rc04_existing_or_unknown_inert_namespace_blocks_before_p4(env, monkeypatch, namespace):
    e = env; root = e.v/'inert'; original = e.c.exists
    if namespace == 'orphan':
        old = root/'00000000-0000-4000-8000-000000000123'; old.mkdir(parents=True); (old/'attempt.json').write_bytes(b'old attempt')
    if namespace == 'empty': root.mkdir()
    if namespace == 'unreadable':
        def unknown(path):
            if path == root: raise PermissionError('unknown inert namespace')
            return original(path)
        monkeypatch.setattr(e.c, 'exists', unknown)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert 'P4 definitions' not in e.events and 'native' not in e.events
    if namespace == 'orphan': assert (old/'attempt.json').read_bytes() == b'old attempt'


@pytest.mark.parametrize('replacement', ['authority_port', 'baseline_time', 'unchanged'])
def test_rc05_original_admission_rejects_replaced_issued_document_before_launch(env, monkeypatch, replacement):
    e = env; d = e.definitions; launches = []
    monkeypatch.setattr(d, 'V', e.v); monkeypatch.setattr(d, 'HERE', e.v/'harness')
    monkeypatch.setattr(d, 'P1', e.v/'legacy/preparation/acceptance_adapter.py')
    (e.v/'legacy').mkdir(); e.write(e.v/'legacy/runtime-before.json', {})
    monkeypatch.setattr(d, 'check_inputs', lambda:{})
    monkeypatch.setattr(d, 'check_import_origins', lambda:None)
    monkeypatch.setattr(d, 'package_check', lambda p:None)
    monkeypatch.setattr(d, 'PrivateIO', lambda p,b:nullcontext())
    e.p4.no_reparse = e.c.no_reparse; e.p4.uuid_text = lambda text:text
    e.p4.identity = lambda pid: (dict(pid=999, created_filetime=2000, exe='root.exe') if pid == 999 else e.protected[pid-1])
    monkeypatch.setattr(d, 'load_p4', lambda:e.p4)
    def original_admission(*args, **kwargs):
        return d.inert_admit(budget=e.inv.instances[-1].budget)
    e.a.inert_admit = original_admission
    def handoff():
        authority = e.c.load(e.v/'inert-authority.json')
        if replacement == 'authority_port': authority['port'] = 8756
        elif replacement == 'baseline_time':
            proof = e.c.load(e.v/'inert-native-baseline.json')
            proof['recorded_at'] = (e.c.utc()-dt.timedelta(seconds=1)).isoformat()
            e.write(e.v/'inert-native-baseline.json', proof)
            authority['native_baseline_sha256'] = e.c.sha(e.v/'inert-native-baseline.json')
        if replacement != 'unchanged': e.write(e.v/'inert-authority.json', authority)
        returned = e.a.inert_admit()
        launches.append(returned[0]['port'])  # Mock Owned boundary, no actual runtime.
        return dict(folder=str(returned[1]))
    e.headless.run_inert = handoff
    record = e.c.run()
    assert launches == ([18765] if replacement == 'unchanged' else []), 'Original admission returned an unissued effective allocation'
    assert record['overall'] == ('ELIGIBLE_FOR_ROOT_REVIEW' if replacement == 'unchanged' else 'PERMANENT_FAIL')
    assert e.a.inert_admit is original_admission


def test_rc06_original_failure_precedes_separate_later_control_veto(env, monkeypatch):
    e = env; original = e.inv.call; captured = []
    def failed(self, entry):
        self.budget.failure = 'ORIGINAL native failure'
        result = original(self, entry); captured.append(json.dumps(result, sort_keys=True))
        e.dependency.write_text('later drift', encoding='utf8')
        return result
    monkeypatch.setattr(e.inv, 'call', failed)
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert record['first_cause']['message'] == 'ORIGINAL native failure'
    assert record.get('later_veto') and 'drift' in record['later_veto']['message']
    assert json.dumps(record['outcome'], sort_keys=True) == captured[0]


def test_rc07_fsync_failure_after_visible_result_does_not_publish_canonical(env, monkeypatch):
    e = env; original = e.c.write_json; visible = []
    def fail_close(stream, value):
        if isinstance(value, dict) and value.get('kind') == 'source10_inert_root_adjudication':
            json.dump(value, stream); stream.flush()
            visible.append(Path(stream.name).read_bytes())
            raise OSError('fsync/close uncertain after bytes visible')
        return original(stream, value)
    monkeypatch.setattr(e.c, 'write_json', fail_close)
    with pytest.raises(OSError, match='uncertain'): e.c.run()
    assert visible and json.loads(visible[0])['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW'
    assert not (e.v/'inert-root-result.json').exists(), 'Canonical eligible result exists without durable close'


@pytest.mark.parametrize('bad', ['no_go', 'abort', 'wrong_go', 'pid_bool', 'nonce', 'origin_bool', 'dispatch_not_consumed'])
def test_rc03_typed_live_entry_and_go_are_required_before_p4(env, monkeypatch, bad):
    e = env
    if bad == 'no_go': monkeypatch.setattr(e.c, '_GO', None)
    if bad == 'abort': monkeypatch.setattr(e.c, '_GO', dict(action='abort', dispatch_sha256=e.release['dispatch_sha256']))
    if bad == 'wrong_go': monkeypatch.setattr(e.c, '_GO', dict(action='go', dispatch_sha256='0'*64))
    if bad in ('pid_bool', 'nonce', 'origin_bool'):
        entry = dict(e.release['entry'])
        if bad == 'pid_bool': entry['pid'] = True
        if bad == 'origin_bool': entry['origin_ns'] = True
        if bad == 'nonce': entry['entry_nonce'] = '00000000-0000-4000-8000-000000000099'
        e.release['entry'] = entry
        e.write(e.v/'inert-root-release.json', e.release)
    if bad == 'dispatch_not_consumed':
        dispatch = e.c.load(e.v/'inert-root-dispatch.json'); dispatch['consumed'] = False
        e.write(e.v/'inert-root-dispatch.json', dispatch)
        e.release['dispatch_sha256'] = e.c.sha(e.v/'inert-root-dispatch.json')
        e.write(e.v/'inert-root-release.json', e.release)
        monkeypatch.setattr(e.c, '_GO', dict(action='go', dispatch_sha256=e.release['dispatch_sha256']))
    with pytest.raises(ValueError): e.c.run()
    assert e.events == [] and not (e.v/'inert-authority.json').exists()


def test_rc03_cli_hello_and_abort_use_mock_streams_with_original_origin(env, monkeypatch, capsys):
    import io
    e = env
    monkeypatch.setattr(sys, 'argv', ['root-inert-invocation.py'])
    monkeypatch.setattr(sys, 'executable', str(e.c.PY))
    monkeypatch.setattr(sys, 'stdin', io.StringIO('{"action":"abort","dispatch_sha256":"none"}\n'))
    with pytest.raises(ValueError): e.c.main()
    hello = json.loads(capsys.readouterr().out)
    assert hello['action'] == 'hello' and hello['protocol'] == 'T4C-ALLOC-01'
    assert hello['entry'] == e.c.entry_binding() and hello['entry']['origin_ns'] == e.c.ENTRY_NS
    assert e.events == []


def test_rc05_existing_child_full_argv_guard_blocks_replaced_port_before_listener(env, monkeypatch):
    e = env; d = e.definitions; listener = []
    monkeypatch.setattr(d, 'corpus', lambda:dict(query='original fixture query'))
    budget = d.Deadline(clock=lambda:e.clock[0]); folder = e.v/'inert/future'
    fixed_argv = d.inert_argv(folder, 18765)
    def constructor(address, handler):
        listener.append(address)
        raise AssertionError('Mock listener must never be reached')
    with pytest.raises(ValueError, match='Exact full authorized child argv'):
        d.inert_child_entry(dict(mode='inert', folder=folder, port=8756, budget=budget), e.p4, fixed_argv, 'a'*64, constructor=constructor)
    assert listener == [] and e.events == []


def test_rc07_close_failure_after_fsync_keeps_only_orphan_pending(env, monkeypatch):
    e = env; original = Path.open
    class CloseFailure:
        def __init__(self, stream): self.stream = stream
        def __enter__(self): return self.stream.__enter__()
        def __exit__(self, *args):
            self.stream.__exit__(*args)
            raise OSError('mock close failure after fsync')
    def pending_open(path, *args, **kwargs):
        stream = original(path, *args, **kwargs)
        if path == e.v/'inert-root-result.pending.json' and args and args[0] == 'x': return CloseFailure(stream)
        return stream
    monkeypatch.setattr(Path, 'open', pending_open)
    with pytest.raises(OSError, match='close failure'): e.c.run()
    assert (e.v/'inert-root-result.pending.json').exists()
    assert not (e.v/'inert-root-result.json').exists()


def test_rc07_publication_never_replaces_concurrently_existing_result(env, monkeypatch):
    e = env; original = e.c.os.link
    def collision(source, target):
        Path(target).write_bytes(b'first canonical result')
        return original(source, target)
    monkeypatch.setattr(e.c.os, 'link', collision)
    with pytest.raises(FileExistsError): e.c.run()
    assert (e.v/'inert-root-result.json').read_bytes() == b'first canonical result'
    assert (e.v/'inert-root-result.pending.json').exists()


def test_rc02_expiry_after_legitimate_admission_does_not_revoke_mock_cleanup(env, monkeypatch):
    e = env; wall = [e.c.utc()]; original = e.headless.run_inert
    monkeypatch.setattr(e.c, 'utc', lambda:wall[0])
    def cleanup_after_ttl():
        result = original()
        wall[0] += dt.timedelta(seconds=121); e.clock[0] += 121_000_000_000
        e.events.append('MOCK original cleanup after TTL')
        return result
    e.headless.run_inert = cleanup_after_ttl
    record = e.c.run()
    assert record['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW'
    assert 'MOCK original cleanup after TTL' in e.events


def test_rc05_private_admission_wrapper_refuses_second_parent_admission_and_restores(env):
    e = env; original = e.a.inert_admit
    def duplicate_entry():
        budget = e.inv.instances[-1].budget
        e.a.inert_admit(budget=budget)
        e.a.inert_admit(budget=budget)
        raise AssertionError('Second parent admission must not return')
    e.headless.run_inert = duplicate_entry
    record = e.c.run()
    assert record['overall'] == 'PERMANENT_FAIL'
    assert 'One original inert admission' in record['first_cause']['message']
    assert e.a.inert_admit is original


# Formal fix round 2: actual-read native scope and closed-source publication.
@pytest.mark.parametrize('replacement', ['port8756', 'parent_pid', 'unchanged'])
def test_rc08_later_original_read_cannot_query_unissued_native_target(env, monkeypatch, replacement):
    e = env; d = e.definitions; lookups = []; swaps = []; launches = []
    original_load = d.load
    monkeypatch.setattr(d, 'V', e.v); monkeypatch.setattr(d, 'HERE', e.v/'harness')
    monkeypatch.setattr(d, 'P1', e.v/'legacy/preparation/acceptance_adapter.py')
    (e.v/'legacy').mkdir(); e.write(e.v/'legacy/runtime-before.json', {})
    monkeypatch.setattr(d, 'RootInvocation', e.inv)
    monkeypatch.setattr(d, 'check_inputs', lambda:{})
    monkeypatch.setattr(d, 'check_import_origins', lambda:None)
    monkeypatch.setattr(d, 'package_check', lambda p:None)
    monkeypatch.setattr(d, 'PrivateIO', lambda p,b:nullcontext())
    e.p4.uuid_text = lambda text:text
    def identity(pid):
        lookups.append(('pid', pid))
        if pid in (999, 424242): return dict(pid=pid, created_filetime=2000, exe='root.exe')
        return e.protected[pid-1]
    def listener_owner(port):
        lookups.append(('port', port))
        return None
    e.p4.identity = identity; e.p4.listener_owner = listener_owner
    def at_original_read(path):
        # Occurs in ORIGINAL inert_admit after all earlier caller checks/hashes,
        # immediately before its load(path); no stand-in admission algorithm.
        if Path(path) == e.v/'inert-authority.json' and not swaps:
            assert 'inv.call' in e.events
            swaps.append(replacement)
            if replacement != 'unchanged':
                authority = e.c.load(path)
                if replacement == 'port8756': authority['port'] = 8756
                if replacement == 'parent_pid': authority['parent_timing']['parent_identity']['pid'] = 424242
                e.write(path, authority)
        return e.c.no_reparse(path)
    e.p4.no_reparse = at_original_read
    monkeypatch.setattr(d, 'load_p4', lambda:e.p4)
    def headless_boundary():
        returned = d.inert_admit(budget=e.inv.instances[-1].budget)
        launches.append(returned[0]['port'])
        return dict(folder=str(returned[1]))
    monkeypatch.setattr(e.c, 'load_harness', lambda h:(d, SimpleNamespace(run_inert=headless_boundary)))
    original_admit = d.inert_admit
    record = e.c.run()
    assert swaps == [replacement]
    assert ('pid', 424242) not in lookups, 'Unissued parent PID was queried before the post-admit guard'
    assert ('port', 8756) not in lookups, 'Off-scope port was queried before the post-admit guard'
    assert all(kind in ('pid', 'port') and (value in (1,2,3,4,5,999) if kind == 'pid' else value == 18765) for kind,value in lookups)
    assert launches == ([18765] if replacement == 'unchanged' else [])
    assert record['overall'] == ('ELIGIBLE_FOR_ROOT_REVIEW' if replacement == 'unchanged' else 'PERMANENT_FAIL')
    assert d.inert_admit is original_admit and d.load is original_load


def test_rc09_replaced_closed_pending_cannot_return_eligible_process_outcome(env, monkeypatch):
    e = env; original_link = e.c.os.link; expected = []; replacement = b'{"overall":"ELIGIBLE_FOR_ROOT_REVIEW","replacement":true}\n'
    def swap_closed_regular_source(source, target):
        source = Path(source)
        expected.append(source.read_bytes())
        # Preserve the original closed object as test evidence while replacing
        # only its pathname with another ordinary file before real os.link.
        source.rename(source.with_name('closed-original-result.raw'))
        source.write_bytes(replacement)
        assert source.is_file() and not source.is_symlink()
        return original_link(source, target)
    monkeypatch.setattr(e.c.os, 'link', swap_closed_regular_source)
    with pytest.raises(ValueError, match='publication'):
        e.c.run()
    assert expected and expected[0] != replacement
    assert (e.v/'inert-root-result.json').read_bytes() == replacement
    assert (e.v/'inert-root-result.pending.json').read_bytes() == replacement
    assert (e.v/'closed-original-result.raw').read_bytes() == expected[0]
    with pytest.raises(ValueError, match='consumed'): e.c.run()
