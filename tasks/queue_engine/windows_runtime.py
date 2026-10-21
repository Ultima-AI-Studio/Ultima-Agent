"""Observe the complete run process tree without capturing desktop pixels."""
import ctypes
from ctypes import wintypes as W
import os
import threading
import time


def descendants(root):
    class Entry(ctypes.Structure):
        _fields_ = [('size', W.DWORD), ('usage', W.DWORD), ('pid', W.DWORD),
                    ('heap', ctypes.c_size_t), ('module', W.DWORD), ('threads', W.DWORD),
                    ('parent', W.DWORD), ('priority', W.LONG), ('flags', W.DWORD), ('name', W.WCHAR * 260)]
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateToolhelp32Snapshot.restype = W.HANDLE
    kernel.Process32FirstW.argtypes = [W.HANDLE, ctypes.POINTER(Entry)]
    kernel.Process32NextW.argtypes = kernel.Process32FirstW.argtypes
    kernel.CloseHandle.argtypes = [W.HANDLE]
    handle = kernel.CreateToolhelp32Snapshot(2, 0)
    if handle == W.HANDLE(-1).value:
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        entry = Entry()
        entry.size = ctypes.sizeof(entry)
        parents = {}
        present = kernel.Process32FirstW(handle, ctypes.byref(entry))
        while present:
            parents[entry.pid] = entry.parent
            present = kernel.Process32NextW(handle, ctypes.byref(entry))
    finally:
        kernel.CloseHandle(handle)
    found = {root}
    while True:
        new = {pid for pid, parent in parents.items() if parent in found} - found
        if not new:
            return found
        found.update(new)


class WindowMonitor:
    def __init__(self, root):
        self.root = root
        self.pids = {root}
        self.observations = []
        self.samples = 0
        self.ready = threading.Event()
        self.stopping = threading.Event()
        self.error = None

    def start(self):
        if os.name == 'nt':
            self.thread = threading.Thread(target=self.observe, daemon=True)
            self.thread.start()
            if not self.ready.wait(5) or self.error:
                raise RuntimeError('Windows process-tree observation unavailable')
        return self

    def stop(self):
        self.stopping.set()
        if os.name == 'nt':
            self.thread.join(5)
            if self.thread.is_alive():
                raise RuntimeError('Windows observer did not stop')
        if self.error:
            raise RuntimeError(self.error)
        return {'method': 'WinEvent CREATE..SHOW plus process-tree window enumeration',
                'observed_pids': sorted(self.pids), 'samples': self.samples,
                'visible_windows': self.observations}

    def observe(self):
        user = ctypes.WinDLL('user32', use_last_error=True)
        user.IsWindowVisible.argtypes = [W.HWND]
        user.GetAncestor.argtypes = [W.HWND, W.UINT]
        user.GetAncestor.restype = W.HWND
        user.GetWindowThreadProcessId.argtypes = [W.HWND, ctypes.POINTER(W.DWORD)]
        event_type = ctypes.WINFUNCTYPE(None, W.HANDLE, W.DWORD, W.HWND, W.LONG, W.LONG, W.DWORD, W.DWORD)
        enum_type = ctypes.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)
        user.SetWinEventHook.argtypes = [W.DWORD, W.DWORD, W.HMODULE, event_type, W.DWORD, W.DWORD, W.DWORD]
        user.SetWinEventHook.restype = W.HANDLE
        user.UnhookWinEvent.argtypes = [W.HANDLE]
        hook = None
        try:
            def observe(hwnd, source):
                if not hwnd or not user.IsWindowVisible(hwnd) or user.GetAncestor(hwnd, 2) != hwnd:
                    return
                pid = W.DWORD()
                user.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                self.pids.update(descendants(self.root))
                if pid.value in self.pids:
                    self.observations.append({'pid': pid.value, 'hwnd': int(hwnd),
                                               'source': source, 'at_monotonic': time.monotonic()})
            def on_event(hook, event, hwnd, object_id, child_id, thread, at):
                try:
                    if object_id == 0 and child_id == 0:
                        observe(hwnd, 'WinEvent')
                except Exception as exc:
                    self.error = type(exc).__name__
            def on_enum(hwnd, data):
                try:
                    observe(hwnd, 'enumeration')
                except Exception as exc:
                    self.error = type(exc).__name__
                return True
            event_callback, enum_callback = event_type(on_event), enum_type(on_enum)
            hook = user.SetWinEventHook(0x8000, 0x8002, None, event_callback, 0, 0, 0)
            if not hook:
                raise ctypes.WinError(ctypes.get_last_error())
            self.ready.set()
            message = W.MSG()
            while not self.stopping.is_set():
                self.pids.update(descendants(self.root))
                while user.PeekMessageW(ctypes.byref(message), None, 0, 0, 1):
                    user.DispatchMessageW(ctypes.byref(message))
                user.EnumWindows(enum_callback, 0)
                self.samples += 1
                self.stopping.wait(.01)
        except Exception as exc:
            self.error = type(exc).__name__
        finally:
            self.ready.set()
            if hook:
                user.UnhookWinEvent(hook)
