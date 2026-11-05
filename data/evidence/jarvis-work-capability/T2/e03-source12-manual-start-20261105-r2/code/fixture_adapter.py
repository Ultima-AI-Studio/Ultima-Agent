"""Isolated E03 fixture adapter with privacy-bounded Win32 edit auditing."""
from __future__ import annotations
import argparse
import ctypes as C
from ctypes import wintypes as W
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import sys
import threading
import time
from fixture_input_origin import (InputOriginRecorder, bind_input_source_reader, EXTRA_MESSAGES,
                                  validate_origin_records, validate_origin_audit)
from fixture_manual_start import manual_start, activate_owned, NO_ACTIVATE, APP_WINDOW

AUDIT_MESSAGES={
    0x0000:('WM_NULL','probe'),
    0x000C:('WM_SETTEXT','programmatic'),
    0x0100:('WM_KEYDOWN','input'),
    0x0101:('WM_KEYUP','input'),
    0x0102:('WM_CHAR','input'),
    0x0104:('WM_SYSKEYDOWN','input'),
    0x0105:('WM_SYSKEYUP','input'),
    0x0106:('WM_SYSCHAR','input'),
    0x0109:('WM_UNICHAR','input'),
    0x010D:('WM_IME_STARTCOMPOSITION','input'),
    0x010E:('WM_IME_ENDCOMPOSITION','input'),
    0x010F:('WM_IME_COMPOSITION','input'),
    0x0286:('WM_IME_CHAR','input'),
    0x0300:('WM_CUT','programmatic'),
    0x0302:('WM_PASTE','programmatic'),
    0x0303:('WM_CLEAR','programmatic'),
    0x00C2:('EM_REPLACESEL','programmatic'),
}

def message_kind(message):
    return AUDIT_MESSAGES.get(message)

def text_digest(value):
    return hashlib.sha256(value.encode('utf-16le')).hexdigest()

def _text_summary(value):
    if value is None:
        return None
    return {'utf16_units':len(value.encode('utf-16le'))//2,'sha256_utf16le':text_digest(value)}

def make_audit_record(*,message,hwnd=0,pid=0,tid=0,received_at_utc=None,qpc_ns=None,
                      last_input_tick_before=None,last_input_tick_after=None,
                      foreground_before_hwnd=None,focus_before_hwnd=None,
                      foreground_after_hwnd=None,focus_after_hwnd=None,
                      in_send_message=None,before_text=None,after_text=None):
    kind=message_kind(message)
    if kind is None:
        return None
    name,category=kind
    return {
        'schema':1,
        'type':'edit-message',
        'message':name,
        'message_id':message,
        'category':category,
        'hwnd':hwnd,
        'pid':pid,
        'tid':tid,
        'received_at_utc':received_at_utc or dt.datetime.now(dt.timezone.utc).isoformat(),
        'qpc_ns':qpc_ns if qpc_ns is not None else time.perf_counter_ns(),
        'last_input_tick_before':last_input_tick_before,
        'last_input_tick_after':last_input_tick_after,
        'foreground_before_hwnd':foreground_before_hwnd,
        'focus_before_hwnd':focus_before_hwnd,
        'foreground_after_hwnd':foreground_after_hwnd,
        'focus_after_hwnd':focus_after_hwnd,
        'in_send_message':in_send_message,
        'before':_text_summary(before_text),
        'after':_text_summary(after_text),
    }

class LASTINPUTINFO(C.Structure):
    _fields_=[('cbSize',W.UINT),('dwTime',W.DWORD)]

def _last_input_tick(user32):
    info=LASTINPUTINFO()
    info.cbSize=C.sizeof(info)
    if not user32.GetLastInputInfo(C.byref(info)):
        return None
    return int(info.dwTime)

def _append_record(path,record,lock):
    with lock:
        with Path(path).open('a',encoding='utf-8',newline='\n') as stream:
            stream.write(json.dumps(record,ensure_ascii=False,separators=(',',':'))+'\n')
            stream.flush()

def _window_text(user32,hwnd):
    length=user32.GetWindowTextLengthW(hwnd)
    if length<0 or length>65535:
        raise ValueError('Edit text length unavailable')
    buffer=C.create_unicode_buffer(length+1)
    copied=user32.GetWindowTextW(hwnd,buffer,length+1)
    if copied<0 or copied>length:
        raise ValueError('Edit text readback unavailable')
    return buffer.value

def _install_audit(user32,kernel,control_hwnd,pid,folder,index,origin=None):
    get_long=getattr(user32,'GetWindowLongPtrW',user32.GetWindowLongW)
    set_long=getattr(user32,'SetWindowLongPtrW',user32.SetWindowLongW)
    get_long.argtypes=[W.HWND,C.c_int]; get_long.restype=C.c_void_p
    set_long.argtypes=[W.HWND,C.c_int,C.c_void_p]; set_long.restype=C.c_void_p
    call=user32.CallWindowProcW
    call.argtypes=[C.c_void_p,W.HWND,W.UINT,W.WPARAM,W.LPARAM]
    call.restype=C.c_ssize_t
    user32.GetWindowTextLengthW.argtypes=[W.HWND]; user32.GetWindowTextLengthW.restype=C.c_int
    user32.GetWindowTextW.argtypes=[W.HWND,W.LPWSTR,C.c_int]; user32.GetWindowTextW.restype=C.c_int
    user32.GetForegroundWindow.restype=W.HWND
    user32.GetFocus.restype=W.HWND
    user32.InSendMessageEx.argtypes=[C.c_void_p]; user32.InSendMessageEx.restype=W.DWORD
    user32.GetLastInputInfo.argtypes=[C.POINTER(LASTINPUTINFO)]; user32.GetLastInputInfo.restype=W.BOOL
    kernel.GetCurrentThreadId.argtypes=[]; kernel.GetCurrentThreadId.restype=W.DWORD

    old_proc=get_long(control_hwnd,-4)
    if not old_proc:
        raise OSError('Edit WndProc lookup failed')
    audit_path=folder/'fixture-events.jsonl'
    lock=threading.Lock()
    state={'enabled':False,'error':False}
    pid_out=W.DWORD()
    user32.GetWindowThreadProcessId.argtypes=[W.HWND,C.POINTER(W.DWORD)]
    user32.GetWindowThreadProcessId(control_hwnd,C.byref(pid_out))
    if pid_out.value!=pid:
        raise ValueError('Audited Edit process identity mismatch')

    def wndproc(hwnd,message,wparam,lparam):
        kind=message_kind(int(message))
        if not state['enabled'] or kind is None:
            return call(old_proc,hwnd,message,wparam,lparam)
        try:
            before=_window_text(user32,hwnd)
        except Exception:
            before=None
            state['error']=True
        foreground_before=int(user32.GetForegroundWindow() or 0)
        focus_before=int(user32.GetFocus() or 0)
        last_input_before=_last_input_tick(user32)
        send_flags=int(user32.InSendMessageEx(None))
        result=call(old_proc,hwnd,message,wparam,lparam)
        try:
            after=_window_text(user32,hwnd)
            record=make_audit_record(
                message=int(message),hwnd=int(hwnd),pid=int(pid),tid=int(kernel.GetCurrentThreadId()),
                last_input_tick_before=last_input_before,last_input_tick_after=_last_input_tick(user32),
                foreground_before_hwnd=foreground_before,focus_before_hwnd=focus_before,
                foreground_after_hwnd=int(user32.GetForegroundWindow() or 0),
                focus_after_hwnd=int(user32.GetFocus() or 0),in_send_message=bool(send_flags),
                before_text=before,after_text=after)
            record['window_index']=index
            _append_record(audit_path,record,lock)
        except Exception:
            state['error']=True
        return result

    if origin is not None:
        wndproc=origin.wrap(wndproc,enabled=lambda:state['enabled'],
                           observed=lambda message:message_kind(message) is not None or message in EXTRA_MESSAGES)
    callback=C.WINFUNCTYPE(C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)(wndproc)
    previous=set_long(control_hwnd,-4,C.cast(callback,C.c_void_p))
    if not previous:
        raise OSError('Edit WndProc subclass failed')
    if previous!=old_proc:
        set_long(control_hwnd,-4,C.c_void_p(previous))
        raise ValueError('Edit WndProc changed during audit installation')
    return {'hwnd':control_hwnd,'old_proc':previous,'callback':callback,'path':audit_path,
            'lock':lock,'state':state,'index':index}

def fixture(folder,candidate_root):
    sys.path.insert(0,str(candidate_root))
    from src.brain.tests import work_context_acceptance as harness
    from src.brain.work_context import Win32Edit

    folder=Path(folder)
    folder.mkdir(parents=True,exist_ok=True)
    native=Win32Edit(); user32=native.u; kernel=native.k
    user32.CreateWindowExW.restype=W.HWND
    user32.CreateWindowExW.argtypes=[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p]
    for name in ('SetForegroundWindow','SetFocus','ShowWindow','DestroyWindow'):
        getattr(user32,name).argtypes=[W.HWND]+([C.c_int] if name=='ShowWindow' else [])
    user32.SetFocus.restype=W.HWND
    user32.PeekMessageW.argtypes=[C.POINTER(W.MSG),W.HWND,W.UINT,W.UINT,W.UINT]
    user32.TranslateMessage.argtypes=[C.POINTER(W.MSG)]
    user32.DispatchMessageW.argtypes=[C.POINTER(W.MSG)]; user32.DispatchMessageW.restype=C.c_ssize_t
    kernel.GetCurrentThreadId.restype=W.DWORD; kernel.GetCurrentThreadId.argtypes=[]
    targets=[]; expected_texts=[]
    for index,title in enumerate((harness.CASES['e03']['window_title'],harness.CASES['e03']['window_title']+' Other')):
        window=user32.CreateWindowExW(NO_ACTIVATE|APP_WINDOW,'STATIC',title,0x10CF0000,150+index*80,150+index*80,700,280,None,None,None,None)
        text=harness.CASES['e03']['text'] if index==0 else 'UNRELATED OWNED FIXTURE — DO NOT CHANGE'
        control=user32.CreateWindowExW(0,'EDIT',text,0x508100C4,10,10,660,180,window,None,None,None)
        if not window or not control:
            raise OSError('Fixture window creation failed')
        targets.append(dict(hwnd=int(window),control_hwnd=int(control),pid=os.getpid(),
                            process_created_filetime=native.created(os.getpid()),title=title,
                            **{'class':'Edit'},allowed_operations=['capture','replace_selection'],
                            max_age_seconds=300))
        expected_texts.append(text)

    initial_readbacks=[]
    for index,(target,text) in enumerate(zip(targets,expected_texts)):
        def set_text(value,control_hwnd=target['control_hwnd']):
            buffer=C.create_unicode_buffer(value)
            return bool(native.send(control_hwnd,0x000C,0,C.addressof(buffer)))
        before=harness.initialize_fixture_text(
            set_text,lambda control_hwnd=target['control_hwnd']:harness.read_fixture_edit_text(native,control_hwnd),text)
        initial_readbacks.append({'index':index,'hwnd':target['hwnd'],'control_hwnd':target['control_hwnd'],'before_activation':before})

    origin_path=folder/'fixture-input-origin.jsonl'
    origin_lock=threading.Lock()
    origin=InputOriginRecorder(
        read_source=bind_input_source_reader(user32),
        read_send_flags=lambda:int(user32.InSendMessageEx(None)),
        emit=lambda record:_append_record(origin_path,record,origin_lock),
        pid=os.getpid(),thread_id=lambda:int(kernel.GetCurrentThreadId()))
    audit_handles=[]
    for index,target in enumerate(targets):
        audit_handles.append(_install_audit(user32,kernel,target['control_hwnd'],target['pid'],folder,index,origin))

    activated=False
    def activate(index=0,select=True):
        nonlocal activated
        target=targets[index]
        record={'target':target['hwnd'],'cross_thread_attached':False}
        try:
            record.update(activate_owned(native,target,targets,initial=not activated,select=select))
            activated=True
        except Exception as exc:
            record.update(status='FAIL',error=type(exc).__name__+': '+str(exc))
            raise
        finally:
            with (folder/'activation.jsonl').open('a',encoding='utf-8') as stream:
                stream.write(json.dumps(record)+'\n')

    msg=W.MSG()
    try:
        manual_start(user32,targets[0]['hwnd'],folder)
        if (folder/'stop').exists():
            raise ValueError('Fixture stopped before operator handoff activation')
        activate()
        for index,(target,text) in enumerate(zip(targets,expected_texts)):
            observed=native.observe(target,foreground=False)
            units=len(text.encode('utf-16le'))//2
            if observed['text']!=text or (index==0 and (observed['start_utf16']!=0 or observed['end_utf16']!=units)):
                raise ValueError('Fixture activation text/selection readback mismatch')
            initial_readbacks[index]['after_activation']={
                'verified':observed['text']==text,
                'utf16_units':len(observed['text'].encode('utf-16le'))//2,
                'sha256_utf16le':hashlib.sha256(observed['text'].encode('utf-16le')).hexdigest(),
                'start_utf16':observed['start_utf16'],'end_utf16':observed['end_utf16'],
            }
        if not origin.start([target['control_hwnd'] for target in targets]):
            raise ValueError('Fixture input-origin audit start failed')
        for item in audit_handles:
            _append_record(item['path'],{
                'schema':1,'type':'audit-start','recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'hwnd':item['hwnd'],'pid':os.getpid(),'window_index':item['index']},item['lock'])
            item['state']['enabled']=True
        for target in targets:
            native.send(target['control_hwnd'],0x0000,0,0)
        if not origin.summary()['complete']:
            raise ValueError('Fixture input-origin audit preflight incomplete')
        harness.save(folder/'fixture-initial-readback.json',{'status':'PASS','targets':initial_readbacks})
        harness.save(folder/'policy.json',{'version':1,'targets':[targets[0]]})
        harness.save(folder/'fixture.json',{'targets':targets,'pid':os.getpid()})
        while not (folder/'stop').exists():
            while user32.PeekMessageW(C.byref(msg),None,0,0,1):
                user32.TranslateMessage(C.byref(msg))
                user32.DispatchMessageW(C.byref(msg))
            command=folder/'command.json'
            if command.exists():
                data=json.loads(command.read_text(encoding='utf-8')); command.unlink()
                activate(data.get('index',0),data.get('select',True))
                harness.save(folder/'command-done.json',{'status':'done','index':data.get('index',0)})
            time.sleep(.01)
    finally:
        for item in audit_handles:
            item['state']['enabled']=False
        origin_summary=origin.finish()
        for item in audit_handles:
            _append_record(item['path'],{
                'schema':1,'type':'audit-stop','recorded_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),
                'hwnd':item['hwnd'],'pid':os.getpid(),'window_index':item['index'],
                'audit_read_error':item['state']['error'] or not origin_summary['complete']},item['lock'])
            set_long=getattr(user32,'SetWindowLongPtrW',user32.SetWindowLongW)
            set_long.argtypes=[W.HWND,C.c_int,C.c_void_p]; set_long.restype=C.c_void_p
            set_long(item['hwnd'],-4,C.c_void_p(item['old_proc']))
        for target in reversed(targets):
            user32.DestroyWindow(target['hwnd'])
    return 0

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture',required=True)
    parser.add_argument('--candidate-root',required=True)
    args=parser.parse_args()
    return fixture(Path(args.fixture),Path(args.candidate_root))

if __name__=='__main__':
    raise SystemExit(main())


