"""Observe a verified Owned member through one retained, readonly Windows handle."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace

LEGACY=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261103-inert2\harness\adapter.py')
LEGACY_SHA='27100afd246c9fb58579ed0389412731b4f029f1c5073ecce9e0cdd8b89d09ed'


def deadline_io():
    raise ValueError('Unconfigured explicit compatibility')


def cleanup_no_listener(io,owned):
    raise ValueError('Unconfigured zero listener cleanup')


class NativeBackend:
    def qualify(self,role,hello):
        raise ValueError('Unconfigured native role qualification')


def require(value, message):
    if not value: raise ValueError(message)


class WindowsReadAPI:
    """Existing native identity/times helpers and CPython's handle observation calls."""
    def __init__(self, controller):
        import _winapi
        self.api = _winapi
        self.controller = controller

    def identity(self, pid): return self.controller.identity(pid)
    def open(self, pid): return self.api.OpenProcess(0x00100000 | 0x1000, False, pid)
    def times(self, handle): return self.controller.process_times(SimpleNamespace(_handle=handle))
    def signaled(self, handle):
        result = self.api.WaitForSingleObject(handle, 0)
        require(result in (self.api.WAIT_OBJECT_0, self.api.WAIT_TIMEOUT), 'Native wait observation failed')
        return result == self.api.WAIT_OBJECT_0
    def exit_code(self, handle): return self.api.GetExitCodeProcess(handle)
    def close(self, handle): self.api.CloseHandle(handle)


class RetainedExit:
    def __init__(self, owned, key, role, *, api, clock):
        require(type(key) is dict and set(key)=={'pid','created_filetime','exe'}, 'Closed native identity required')
        require(all(type(key[name]) is int and key[name]>0 for name in ('pid','created_filetime'))
                and type(key['exe']) is str and Path(key['exe']).is_absolute(), 'Native identity types')
        require(role in ('worker','reader') and key['pid'] not in owned.forbidden, 'Protected or wrong role')
        member = owned.known.get(key['pid'])
        require(type(member) is dict and member.get('identity')==key and member.get('role')==role,
                'Exact Owned member required before handle acquisition')
        self.key, self.role, self.api, self.clock = deepcopy(key), role, api, clock
        self.handle = None
        require(api.identity(key['pid'])==self.key, 'Native identity changed before open')
        handle = api.open(key['pid'])
        require(type(handle) is int and handle>0, 'Readonly native handle unavailable')
        self.handle = handle
        try:
            created, _ = api.times(handle)
            require(type(created) is int and created==self.key['created_filetime'], 'Retained handle creation mismatch')
            require(api.identity(key['pid'])==self.key, 'PID reused during handle acquisition')
        except BaseException:
            self.close()
            raise

    def _time(self, origin, cutoff):
        require(type(origin) is int and type(cutoff) is int and 0<origin<=cutoff, 'Original bounded clock required')
        now = self.clock()
        require(type(now) is int and origin<=now<=cutoff, 'Native observation outside original deadline')
        return now

    def poll(self, origin, cutoff):
        require(self.handle is not None, 'Retained handle closed')
        self._time(origin, cutoff)
        signaled = self.api.signaled(self.handle)
        require(type(signaled) is bool, 'Unknown native signal observation')
        if not signaled:
            self._time(origin, cutoff)
            return None
        code = self.api.exit_code(self.handle)
        require(type(code) is int and 0<=code<=0xffffffff, 'Unknown native exit code')
        observed = self._time(origin, cutoff)
        return dict(identity=deepcopy(self.key),role=self.role,signaled=True,exit_code=code,observed_at_ns=observed)

    def close(self):
        handle, self.handle = self.handle, None
        if handle is not None: self.api.close(handle)

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
