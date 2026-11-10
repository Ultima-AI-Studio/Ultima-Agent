"""Test-process I/O guard: only owned loopback HTTP and owned junction creation."""
from pathlib import Path
import json
import os
import socket
import subprocess
import weakref

_original = {}
_listeners = []
_ports = set()
_denied = []
_allowed = []


def _reject(kind, target):
    _denied.append({'kind': kind, 'target': str(target)[:250]})
    raise AssertionError(f'Offline verification blocked {kind}: {target}')


def pytest_sessionstart(session):
    base = Path(session.config.option.basetemp).resolve()
    evidence = Path(__file__).resolve().parent
    assert base.is_relative_to(evidence)
    _original.update(bind=socket.socket.bind, connect=socket.socket.connect,
                     connect_ex=socket.socket.connect_ex, getaddrinfo=socket.getaddrinfo,
                     popen=subprocess.Popen)

    def bind(sock, address):
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1') or address[1] != 0:
            _reject('bind', address)
        result = _original['bind'](sock, address)
        _ports.add(sock.getsockname()[1])
        _listeners.append(weakref.ref(sock))
        return result

    def connect(sock, address):
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1') or address[1] not in _ports:
            _reject('connect', address)
        _allowed.append({'kind': 'owned-loopback', 'port': address[1]})
        return _original['connect'](sock, address)

    def connect_ex(sock, address):
        if not isinstance(address, tuple) or address[0] not in ('127.0.0.1', '::1') or address[1] not in _ports:
            _reject('connect_ex', address)
        _allowed.append({'kind': 'owned-loopback', 'port': address[1]})
        return _original['connect_ex'](sock, address)

    def getaddrinfo(host, *args, **kwargs):
        if host not in ('127.0.0.1', '::1', 'localhost'):
            _reject('DNS', host)
        return _original['getaddrinfo'](host, *args, **kwargs)

    class GuardedPopen(_original['popen']):
        def __init__(self, argv, *args, **kwargs):
            approved = (isinstance(argv, (list, tuple)) and len(argv) == 6
                        and [str(x).lower() for x in argv[:4]] == ['cmd', '/c', 'mklink', '/j']
                        and not kwargs.get('shell')
                        and all(Path(x).is_absolute() and Path(x).resolve().is_relative_to(base) for x in argv[4:]))
            if not approved:
                _reject('process', argv)
            _allowed.append({'kind': 'owned-test-junction'})
            kwargs['creationflags'] = kwargs.get('creationflags', 0) | subprocess.CREATE_NO_WINDOW
            super().__init__(argv, *args, **kwargs)

    socket.socket.bind = bind
    socket.socket.connect = connect
    socket.socket.connect_ex = connect_ex
    socket.getaddrinfo = getaddrinfo
    subprocess.Popen = GuardedPopen


def pytest_sessionfinish(session, exitstatus):
    open_listeners = [sock.getsockname() for ref in _listeners if (sock := ref()) is not None and sock.fileno() != -1]
    socket.socket.bind = _original['bind']
    socket.socket.connect = _original['connect']
    socket.socket.connect_ex = _original['connect_ex']
    socket.getaddrinfo = _original['getaddrinfo']
    subprocess.Popen = _original['popen']
    if _denied or open_listeners:
        session.exitstatus = 1
    receipt = dict(denied=_denied, allowed=_allowed, open_owned_listeners=open_listeners,
                   pytest_exit_before_guard=int(exitstatus), final_exit=int(session.exitstatus),
                   limitation='Python socket/subprocess interception only; inference uses explicit fake engines or SDK MockTransport in the selected tests. No actual E03 allocation.')
    Path(os.environ['ULTIMA_OFFLINE_GUARD_RECEIPT']).write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
