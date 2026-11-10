"""Retained native worker handle, using synthetic Windows calls only."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from native_observation import RetainedExit

KEY = {'pid': 417, 'created_filetime': 134384100000000123, 'exe': r'C:\Python\python.exe'}


class Native:
    def __init__(self):
        self.key = deepcopy(KEY)
        self.created = KEY['created_filetime']
        self.wait = 0
        self.code = 0
        self.clock = 105
        self.closed = []
        self.calls = []

    def identity(self, pid):
        self.calls.append(('identity', pid))
        return deepcopy(self.key)

    def open(self, pid):
        self.calls.append(('open', pid))
        return 29

    def times(self, handle):
        self.calls.append(('times', handle))
        return self.created, 134384100000000200

    def signaled(self, handle):
        self.calls.append(('signaled', handle))
        return self.wait == 0

    def exit_code(self, handle):
        self.calls.append(('exit_code', handle))
        return self.code

    def close(self, handle):
        self.closed.append(handle)

    def now(self):
        return self.clock


def owner():
    return SimpleNamespace(known={417: {'identity': deepcopy(KEY), 'role': 'worker'}}, forbidden={81})


def test_worker_exit_observed_on_retained_handle():
    api = Native()
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        result = observer.poll(100, 110)
    assert result == {'identity': KEY, 'role': 'worker', 'signaled': True,
                      'exit_code': 0, 'observed_at_ns': 105}
    assert api.closed == [29]


def test_native_exit_failure_is_not_launcher_success():
    api = Native(); api.code = 7
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        assert observer.poll(100, 110)['exit_code'] == 7


def test_no_exit_code_is_observed_until_handle_signals():
    api = Native(); api.wait = 258
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        assert observer.poll(100, 110) is None
    assert not any(call[0] == 'exit_code' for call in api.calls)


@pytest.mark.parametrize('mutate', [
    lambda o: o.known.clear(),
    lambda o: o.forbidden.add(417),
    lambda o: o.known[417].update(role='launcher'),
    lambda o: o.known[417]['identity'].update(created_filetime=KEY['created_filetime']+1),
])
def test_ambiguous_or_protected_member_never_opens_handle(mutate):
    api = Native(); owned = owner(); mutate(owned)
    with pytest.raises(ValueError):
        RetainedExit(owned, KEY, 'worker', api=api, clock=api.now)
    assert not any(call[0] == 'open' for call in api.calls)


def test_handle_creation_mismatch_closes_without_exit_credit():
    api = Native(); api.created += 1
    with pytest.raises(ValueError):
        RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    assert api.closed == [29]


def test_pid_reuse_after_open_closes_handle():
    api = Native()
    old_open = api.open
    def replaced(pid):
        handle = old_open(pid)
        api.key['created_filetime'] += 20
        return handle
    api.open = replaced
    with pytest.raises(ValueError):
        RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    assert api.closed == [29]


@pytest.mark.parametrize('at', [99, 111, True])
def test_missing_or_expired_original_clock_never_returns_success(at):
    api = Native(); api.clock = at
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        with pytest.raises(ValueError):
            observer.poll(100, 110)


def test_clock_is_checked_after_native_exit_read():
    api = Native()
    def slow_exit(handle):
        api.clock = 111
        return 0
    api.exit_code = slow_exit
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        with pytest.raises(ValueError):
            observer.poll(100, 110)


def test_exit_observation_is_stable_on_pid_reuse_after_original_exit():
    api = Native()
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        api.key['created_filetime'] += 999  # PID lookup now names a different process.
        assert observer.poll(100, 110)['identity'] == KEY  # retained handle still names original.


def test_closed_handle_cannot_be_reused():
    api = Native(); observer = RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    observer.close(); observer.close()
    with pytest.raises(ValueError):
        observer.poll(100, 110)
    assert api.closed == [29]
