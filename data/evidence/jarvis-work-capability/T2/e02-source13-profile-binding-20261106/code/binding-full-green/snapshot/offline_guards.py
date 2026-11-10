"""Python audit guard for the offline binding tests, with no runtime allowance."""
import sys

denied = []
enabled = False


def audit(event, args):
    network = event in ('socket.__new__', 'socket.connect', 'socket.bind', 'socket.getaddrinfo',
                        'socket.gethostbyname', 'socket.gethostbyaddr', 'socket.sendto')
    if enabled and (network or event in ('subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.spawn')):
        denied.append(event)
        raise RuntimeError('Offline binding verification blocked ' + event)


def install():
    global enabled
    sys.addaudithook(audit)
    enabled = True


def receipt():
    return dict(denied=list(denied), observed_python_requests=len(denied),
                native_or_OS_wide_activity=None,
                limitation='Python audit events only; selected tests use synthetic transports and services.')
