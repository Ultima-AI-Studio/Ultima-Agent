"""Read input-desktop identity and native PID inventory without UI input."""
import ctypes
from ctypes import wintypes as W
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('native_post_reboot', ROOT / 'scripts/inspect-native-environment.py')
native = importlib.util.module_from_spec(spec)
spec.loader.exec_module(native)
roles = native.codex_processes()
kernel, user = native.K, native.U
snapshot = kernel.CreateToolhelp32Snapshot(2, 0)
if snapshot == W.HANDLE(-1).value:
    raise ctypes.WinError(ctypes.get_last_error())
found = []
try:
    entry = native.ProcessEntry()
    entry.size = ctypes.sizeof(entry)
    present = kernel.Process32FirstW(snapshot, ctypes.byref(entry))
    while present:
        if entry.pid == 59328 or entry.name.lower() == 'ultimaagent.hostshell.exe':
            found.append({'pid': entry.pid, 'name': entry.name, 'parent_pid': entry.parent})
        ctypes.set_last_error(0)
        present = kernel.Process32NextW(snapshot, ctypes.byref(entry))
        if not present and ctypes.get_last_error() != 18:
            raise ctypes.WinError(ctypes.get_last_error())
finally:
    kernel.CloseHandle(snapshot)
user.OpenInputDesktop.argtypes = [W.DWORD, W.BOOL, W.DWORD]
user.OpenInputDesktop.restype = W.HANDLE
user.GetUserObjectInformationW.argtypes = [W.HANDLE, ctypes.c_int, ctypes.c_void_p, W.DWORD, ctypes.POINTER(W.DWORD)]
user.CloseDesktop.argtypes = [W.HANDLE]
desktop = user.OpenInputDesktop(0, False, 1)
desktop_name = None
error = None
if desktop:
    try:
        name = ctypes.create_unicode_buffer(256)
        needed = W.DWORD()
        if not user.GetUserObjectInformationW(desktop, 2, name, ctypes.sizeof(name), ctypes.byref(needed)):
            raise ctypes.WinError(ctypes.get_last_error())
        desktop_name = name.value
    finally:
        user.CloseDesktop(desktop)
else:
    error = ctypes.get_last_error()
result = {'at_utc': datetime.now(timezone.utc).isoformat(), 'read_only': True, 'codex_roles': roles,
          'native_relevant_processes': found, 'old_pid_59328_present': any(row['pid'] == 59328 for row in found),
          'input_desktop': desktop_name, 'desktop_error': error,
          'default_input_desktop_accessible': desktop_name == 'Default'}
target = ROOT / 'logs/maintenance/w1-restart-20261021/post-reboot-desktop-processes.json'
with target.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, indent=2)
print(json.dumps(result))
