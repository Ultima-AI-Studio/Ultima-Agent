"""Read native monitor topology and Codex process roles, without screen capture."""
import ctypes
from ctypes import wintypes as W
import json
from pathlib import Path

K = ctypes.WinDLL('kernel32', use_last_error=True)
U = ctypes.WinDLL('user32', use_last_error=True)


class ProcessEntry(ctypes.Structure):
    _fields_ = [('size', W.DWORD), ('usage', W.DWORD), ('pid', W.DWORD),
                ('heap', ctypes.c_size_t), ('module', W.DWORD), ('threads', W.DWORD),
                ('parent', W.DWORD), ('priority', W.LONG), ('flags', W.DWORD),
                ('name', W.WCHAR * 260)]


def codex_processes():
    K.CreateToolhelp32Snapshot.restype = W.HANDLE
    K.Process32FirstW.argtypes = [W.HANDLE, ctypes.POINTER(ProcessEntry)]
    K.Process32NextW.argtypes = K.Process32FirstW.argtypes
    K.CloseHandle.argtypes = [W.HANDLE]
    K.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
    K.OpenProcess.restype = W.HANDLE
    snapshot = K.CreateToolhelp32Snapshot(2, 0)
    if snapshot == W.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    rows = []
    try:
        entry = ProcessEntry()
        entry.size = ctypes.sizeof(entry)
        ctypes.set_last_error(0)
        present = K.Process32FirstW(snapshot, ctypes.byref(entry))
        if not present and ctypes.get_last_error() != 18:
            raise ctypes.WinError(ctypes.get_last_error())
        while present:
            if entry.name.lower() == 'codex.exe':
                rows.append({'pid': entry.pid, 'parent_pid': entry.parent, **role(entry.pid)})
            ctypes.set_last_error(0)
            present = K.Process32NextW(snapshot, ctypes.byref(entry))
            if not present and ctypes.get_last_error() != 18:
                raise ctypes.WinError(ctypes.get_last_error())
    finally:
        K.CloseHandle(snapshot)
    by_pid = {item['pid']: item for item in rows}
    for item in rows:
        if item['role'] == 'mxc-helper':
            if by_pid.get(item['parent_pid'], {}).get('role') != 'app-server':
                item['role'] = 'unknown'
    return rows


def role(pid):
    handle = K.OpenProcess(0x1000, False, pid)
    if not handle:
        return {'role': 'unknown', 'reason': 'process inaccessible'}
    try:
        ntdll = ctypes.WinDLL('ntdll')
        query = ntdll.NtQueryInformationProcess
        query.argtypes = [W.HANDLE, W.ULONG, ctypes.c_void_p, W.ULONG, ctypes.POINTER(W.ULONG)]
        query.restype = W.LONG
        length = W.ULONG()
        query(handle, 60, None, 0, ctypes.byref(length))
        if not length.value or length.value > 1024 * 1024:
            return {'role': 'unknown', 'reason': 'command metadata unavailable'}
        buffer = ctypes.create_string_buffer(length.value)
        if query(handle, 60, buffer, len(buffer), ctypes.byref(length)) < 0:
            return {'role': 'unknown', 'reason': 'command metadata query failed'}
        class UnicodeString(ctypes.Structure):
            _fields_ = [('length', W.USHORT), ('maximum', W.USHORT), ('buffer', ctypes.c_void_p)]
        value = UnicodeString.from_buffer(buffer)
        command = ctypes.wstring_at(value.buffer, value.length // 2)
        shell = ctypes.WinDLL('shell32')
        shell.CommandLineToArgvW.argtypes = [W.LPCWSTR, ctypes.POINTER(ctypes.c_int)]
        shell.CommandLineToArgvW.restype = ctypes.POINTER(W.LPWSTR)
        count = ctypes.c_int()
        argv = shell.CommandLineToArgvW(command, ctypes.byref(count))
        try:
            args = [argv[i] for i in range(count.value)]
        finally:
            K.LocalFree.argtypes = [ctypes.c_void_p]
            K.LocalFree(argv)
        result = parse_role(args)
        if result['role'] == 'unknown':
            result['argument_shape'] = [arg.split('=')[0] if arg.startswith('-') else arg
                                        if arg in {'app-server', 'exec-server', 'exec'} else '<value>' for arg in args[1:]]
        return result
    finally:
        K.CloseHandle(handle)


def parse_role(args):
    if args[1:] == ['--__codex-windows-mxc']:
        return {'role': 'mxc-helper', 'project': None}
    valued = {'-a', '--ask-for-approval', '-c', '--config', '-m', '--model', '-C', '--cd',
              '-s', '--sandbox', '-p', '--profile', '--output-last-message', '-o',
              '--output-schema', '--image', '-i'}
    flags = {'--json', '--skip-git-repo-check', '--full-auto', '--dangerously-bypass-approvals-and-sandbox',
             '--analytics-default-enabled', '--no-alt-screen'}
    command, project, index = None, None, 1
    while index < len(args):
        value = args[index]
        if value == '--' or value == '-':
            break
        if value in valued:
            if index + 1 >= len(args):
                return {'role': 'unknown', 'project': None}
            if value in {'-C', '--cd'}:
                project = args[index + 1]
            index += 2
            continue
        if value in flags or value.startswith('--color='):
            index += 1
            continue
        if value == '--color':
            index += 2
            continue
        if command is None:
            if value not in {'app-server', 'exec-server', 'exec'}:
                return {'role': 'unknown', 'project': None}
            command = value
            index += 1
            continue
        if command in {'app-server', 'exec-server'}:
            break
        if value.startswith('-'):
            return {'role': 'unknown', 'project': None}
        # First positional value after exec is the prompt, never parse its text as options.
        break
    return {'role': command or 'unknown', 'project': project}


def monitors():
    class Info(ctypes.Structure):
        _fields_ = [('size', W.DWORD), ('monitor', W.RECT), ('work', W.RECT),
                    ('flags', W.DWORD), ('device', W.WCHAR * 32)]
    callback_type = ctypes.WINFUNCTYPE(W.BOOL, W.HANDLE, W.HDC, ctypes.POINTER(W.RECT), W.LPARAM)
    U.GetMonitorInfoW.argtypes = [W.HANDLE, ctypes.POINTER(Info)]
    shcore = ctypes.WinDLL('shcore')
    shcore.GetDpiForMonitor.argtypes = [W.HANDLE, ctypes.c_int, ctypes.POINTER(W.UINT), ctypes.POINTER(W.UINT)]
    result = []
    def receive(handle, dc, rect, data):
        info = Info()
        info.size = ctypes.sizeof(info)
        if not U.GetMonitorInfoW(handle, ctypes.byref(info)):
            return False
        x, y = W.UINT(), W.UINT()
        status = shcore.GetDpiForMonitor(handle, 0, ctypes.byref(x), ctypes.byref(y))
        result.append({'device': info.device, 'dpi': [x.value, y.value] if status == 0 else None,
                       'rect': [info.monitor.left, info.monitor.top, info.monitor.right, info.monitor.bottom]})
        return True
    callback = callback_type(receive)
    if not U.EnumDisplayMonitors(None, None, callback, 0):
        raise ctypes.WinError(ctypes.get_last_error())
    return result


if __name__ == '__main__':
    U.SetProcessDpiAwarenessContext.argtypes = [ctypes.c_void_p]
    U.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))
    print(json.dumps({'codex': codex_processes(), 'monitors': monitors()}, ensure_ascii=False, indent=2))
