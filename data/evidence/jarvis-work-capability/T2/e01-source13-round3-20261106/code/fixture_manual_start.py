"""Owned fixture start button; no input injection or foreign queue attachment."""
from __future__ import annotations

import ctypes as C
from ctypes import wintypes as W
import datetime as dt
import json
import os
from pathlib import Path
import time

START_BUTTON_ID = 1001
WAIT_SECONDS = 15
NO_ACTIVATE = 0x08000000
APP_WINDOW = 0x00040000


def require(ok, message):
    if not ok:
        raise ValueError(message)


def is_start_command(parent, button, hwnd, message, wparam, lparam):
    return (hwnd == parent and message == 0x111 and lparam == button
            and wparam == START_BUTTON_ID)


def wait_for_start(pump_once, keyboard_clear, cancelled, *, timeout_seconds=WAIT_SECONDS,
                   clock=time.monotonic, sleep=time.sleep):
    require(0 < timeout_seconds <= WAIT_SECONDS, 'Invalid handoff wait')
    start = clock()
    while True:
        require(not cancelled(), 'Manual start cancelled')
        if clock() - start >= timeout_seconds:
            raise TimeoutError('Manual start button wait expired')
        clicked = pump_once()
        require(not cancelled(), 'Manual start cancelled')
        if clock() - start >= timeout_seconds:
            raise TimeoutError('Manual start button wait expired')
        if clicked:
            require(keyboard_clear() is True, 'Manual start requires released keyboard keys')
            require(not cancelled(), 'Manual start cancelled')
            elapsed = clock() - start
            if elapsed >= timeout_seconds:
                raise TimeoutError('Manual start expired during keyboard check')
            return {'keyboard_clear': True, 'elapsed_seconds': elapsed}
        sleep(min(.01, max(0, timeout_seconds - (clock() - start))))


def activate_owned(native, target, owned_targets, *, initial=False, select=True):
    native.identity(target, foreground=False)
    if not initial:
        require(native.focused() in [(t['hwnd'],t['control_hwnd']) for t in owned_targets],
                'Fixture lost owned foreground; do not reclaim another application')
    require(bool(native.u.SetForegroundWindow(target['hwnd'])), 'Owned foreground activation refused')
    native.u.SetFocus(target['control_hwnd'])
    require(native.focused() == (target['hwnd'],target['control_hwnd']), 'Owned focus activation refused')
    native.send(target['control_hwnd'], 0xB1, 0, -1 if select else 1)
    return {'status':'PASS', 'target':target['hwnd'], 'cross_thread_attached':False,
            'mode':'operator-handoff' if initial else 'already-owned-focus'}


def validate_handoff(value, fixture):
    fields = {'schema','status','pid','window_hwnd','button_hwnd','keyboard_clear',
              'cross_thread_attached','requested_by','ready_at','accepted_at',
              'timeout_seconds','elapsed_seconds'}
    require(isinstance(value,dict) and set(value)==fields, 'Manual handoff receipt fields invalid')
    require(value['schema']==1 and value['status']=='ACCEPTED' and value['pid']==fixture['pid']
            and value['window_hwnd']==fixture['targets'][0]['hwnd']
            and type(value['button_hwnd']) is int and value['button_hwnd']>0, 'Manual handoff identity mismatch')
    require(value['keyboard_clear'] is True and value['cross_thread_attached'] is False
            and value['requested_by']=='owned_start_button', 'Manual handoff not accepted')
    require(type(value['timeout_seconds']) in (int,float) and value['timeout_seconds']==WAIT_SECONDS
            and type(value['elapsed_seconds']) in (int,float)
            and 0<=value['elapsed_seconds']<WAIT_SECONDS, 'Manual handoff wait expanded or expired')
    ready, accepted = (dt.datetime.fromisoformat(value[key]) for key in ('ready_at','accepted_at'))
    require(ready.tzinfo is not None and accepted.tzinfo is not None and ready<=accepted, 'Manual handoff timestamp invalid')
    return True


def manual_start(user32, window, folder):
    folder = Path(folder)
    for name in ('manual-start-ready.json','manual-start.json'):
        if (folder/name).exists():
            raise FileExistsError('Manual start receipt already exists')
    user32.GetWindowLongW.argtypes=[W.HWND,C.c_int]; user32.GetWindowLongW.restype=C.c_long
    require(user32.GetWindowLongW(window,-20)&NO_ACTIVATE, 'Waiting fixture must not auto-activate')
    user32.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
    def owned(hwnd):
        pid=W.DWORD(); user32.GetWindowThreadProcessId(hwnd,C.byref(pid))
        require(pid.value==os.getpid(), 'Manual start control is not owned')
    owned(window)
    button=user32.CreateWindowExW(0,'BUTTON','开始测试（结束前请勿点击、输入或切换窗口）',0x50010000,
                                  10,200,660,28,window,START_BUTTON_ID,None,None)
    require(bool(button), 'Manual start button creation failed')
    get_long=getattr(user32,'GetWindowLongPtrW',None) or user32.GetWindowLongW
    set_long=getattr(user32,'SetWindowLongPtrW',None) or user32.SetWindowLongW
    get_long.argtypes=[W.HWND,C.c_int]; get_long.restype=C.c_void_p
    set_long.argtypes=[W.HWND,C.c_int,C.c_void_p]; set_long.restype=C.c_void_p
    user32.CallWindowProcW.argtypes=[C.c_void_p,W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    user32.CallWindowProcW.restype=C.c_ssize_t
    user32.GetAsyncKeyState.argtypes=[C.c_int]; user32.GetAsyncKeyState.restype=C.c_short
    old_proc=None; previous=None; callback=None
    try:
        owned(button)
        old_proc=get_long(window,-4)
        require(bool(old_proc), 'Manual start parent procedure unavailable')
        requested=False
        def dispatch(hwnd,message,wparam,lparam):
            nonlocal requested
            if is_start_command(window,button,hwnd,message,wparam,lparam):
                requested=True
                return 0
            return user32.CallWindowProcW(old_proc,hwnd,message,wparam,lparam)
        callback=C.WINFUNCTYPE(C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)(dispatch)
        callback_address=C.cast(callback,C.c_void_p)
        previous=set_long(window,-4,callback_address)
        require(bool(previous) and previous==old_proc, 'Manual start parent procedure changed')
        user32.SetWindowPos.argtypes=[W.HWND,W.HWND,C.c_int,C.c_int,C.c_int,C.c_int,W.UINT]
        user32.SetWindowPos.restype=W.BOOL
        # HWND_TOP with NOACTIVATE: show Start above its sibling without taking
        # keyboard input from the application in which the operator is typing.
        require(bool(user32.SetWindowPos(window,0,0,0,0,0,0x53)), 'Manual start window display failed')
        ready_at=dt.datetime.now(dt.timezone.utc).isoformat()
        with (folder/'manual-start-ready.json').open('x',encoding='utf-8',newline='\n') as stream:
            json.dump({'status':'READY','pid':os.getpid(),'window_hwnd':int(window),
                       'button_hwnd':int(button),'ready_at':ready_at,'timeout_seconds':WAIT_SECONDS,
                       'automatic_activation':False,'cross_thread_attached':False},stream)
        msg=W.MSG()
        def pump_once():
            for _ in range(32):
                if not user32.PeekMessageW(C.byref(msg),None,0,0,1):
                    break
                user32.TranslateMessage(C.byref(msg))
                user32.DispatchMessageW(C.byref(msg))
                if requested:
                    break
            return requested
        result=wait_for_start(pump_once,
            lambda:not any(user32.GetAsyncKeyState(key)&0x8000 for key in range(8,256)),
            lambda:(folder/'stop').exists())
        receipt=dict(schema=1,status='ACCEPTED',pid=os.getpid(),window_hwnd=int(window),
                     button_hwnd=int(button),cross_thread_attached=False,requested_by='owned_start_button',
                     ready_at=ready_at,accepted_at=dt.datetime.now(dt.timezone.utc).isoformat(),
                     timeout_seconds=WAIT_SECONDS,**result)
        with (folder/'manual-start.json').open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(receipt,stream,ensure_ascii=False,indent=2);stream.write('\n')
        return receipt
    finally:
        try:
            if previous:
                restored=set_long(window,-4,C.c_void_p(previous))
                require(restored==C.cast(callback,C.c_void_p).value, 'Manual start callback restoration failed')
        finally:
            require(bool(user32.DestroyWindow(button)), 'Manual start button cleanup failed')
