"""On-demand standard Edit context. Startup policy, never text, grants authority."""
from __future__ import annotations
import copy
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import threading
import time
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


def digest(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


IDENTITY = ('hwnd','control_hwnd','pid','process_created_filetime','title','class')


class Win32Edit:
    """Only standard system Edit messages; all sends bounded, no input injection."""
    def __init__(self):
        self.u = C.WinDLL('user32', use_last_error=True)
        self.k = C.WinDLL('kernel32', use_last_error=True)
        signatures = {
            'GetForegroundWindow': (W.HWND, []),
            'GetWindowThreadProcessId': (W.DWORD,[W.HWND,C.POINTER(W.DWORD)]),
            'GetGUIThreadInfo': (W.BOOL,[W.DWORD,C.c_void_p]),
            'GetAncestor': (W.HWND,[W.HWND,W.UINT]),
            'GetWindowTextW': (C.c_int,[W.HWND,W.LPWSTR,C.c_int]),
            'GetClassNameW': (C.c_int,[W.HWND,W.LPWSTR,C.c_int]),
            'GetWindowLongW': (C.c_long,[W.HWND,C.c_int]),
            'IsWindowEnabled': (W.BOOL,[W.HWND]),
            'SendMessageTimeoutW': (C.c_ssize_t,[W.HWND,W.UINT,C.c_size_t,C.c_ssize_t,W.UINT,W.UINT,C.POINTER(C.c_size_t)]),
        }
        for name,(ret,args) in signatures.items():
            fn=getattr(self.u,name); fn.restype=ret; fn.argtypes=args
        self.k.OpenProcess.restype=W.HANDLE
        self.k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]
        self.k.GetProcessTimes.restype=W.BOOL
        self.k.GetProcessTimes.argtypes=[W.HANDLE,C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME),C.POINTER(W.FILETIME)]
        self.k.CloseHandle.argtypes=[W.HANDLE]; self.k.CloseHandle.restype=W.BOOL

    def created(self,pid):
        h=self.k.OpenProcess(0x1000,False,pid)
        if not h: raise ValueError('Cannot query process identity')
        values=[W.FILETIME() for _ in range(4)]
        try:
            if not self.k.GetProcessTimes(h,*[C.byref(x) for x in values]):
                raise ValueError('Cannot read process creation identity')
            return values[0].dwLowDateTime | values[0].dwHighDateTime << 32
        finally: self.k.CloseHandle(h)

    def focused(self):
        class GUI(C.Structure):
            _fields_=[('cbSize',W.DWORD),('flags',W.DWORD)]+[(n,W.HWND) for n in ('active','focus','capture','menu','move','caret')]+[('rect',W.RECT)]
        hwnd=self.u.GetForegroundWindow()
        tid=self.u.GetWindowThreadProcessId(hwnd,None)
        info=GUI(); info.cbSize=C.sizeof(info)
        if not self.u.GetGUIThreadInfo(tid,C.byref(info)): raise ValueError('Focus unavailable')
        return int(hwnd or 0),int(info.focus or 0)

    def send(self,hwnd,msg,w=0,l=0):
        out=C.c_size_t()
        if not self.u.SendMessageTimeoutW(hwnd,msg,w,l,3,1000,C.byref(out)):
            raise TimeoutError('Native Edit message failed or timed out')
        return out.value

    def identity(self,target,foreground=True):
        h,ch=target['hwnd'],target['control_hwnd']
        if foreground and self.focused()!=(h,ch): raise ValueError('Foreground/focus changed')
        if self.u.GetAncestor(ch,2)!=h: raise ValueError('Control root changed')
        pid=W.DWORD(); self.u.GetWindowThreadProcessId(ch,C.byref(pid))
        parent_pid=W.DWORD(); self.u.GetWindowThreadProcessId(h,C.byref(parent_pid))
        if pid.value!=parent_pid.value: raise ValueError('Control ownership mismatch')
        title=C.create_unicode_buffer(1024); cls=C.create_unicode_buffer(128)
        self.u.GetWindowTextW(h,title,1024); self.u.GetClassNameW(ch,cls,128)
        current=dict(hwnd=h,control_hwnd=ch,pid=pid.value,process_created_filetime=self.created(pid.value),title=title.value,**{'class':cls.value})
        if any(current[k]!=target[k] for k in IDENTITY): raise ValueError('Approved target identity changed')
        return current

    def observe(self,target,*,foreground=True):
        current=self.identity(target,foreground=foreground)  # authorize identity before reading text
        style=self.u.GetWindowLongW(target['control_hwnd'],-16)
        if style & 0x20: raise ValueError('Password controls unsupported')
        n=self.send(target['control_hwnd'],0x000E)
        if n>65535: raise ValueError('Edit text too large')
        text=C.create_unicode_buffer(n+1)
        self.send(target['control_hwnd'],0x000D,n+1,C.addressof(text))
        start=W.DWORD(); end=W.DWORD()
        self.send(target['control_hwnd'],0x00B0,C.addressof(start),C.addressof(end))
        self.identity(target,foreground=foreground)
        return dict(current,text=text.value,start_utf16=start.value,end_utf16=end.value,
                    editable=not bool(style & 0x800) and bool(self.u.IsWindowEnabled(target['control_hwnd'])),password=False)

    def replace(self,target,content):
        text=C.create_unicode_buffer(content)
        self.send(target['control_hwnd'],0x00C2,1,C.addressof(text))


class WorkContextProvider:
    def __init__(self,policy,*,native=None,clock=None):
        if not isinstance(policy,dict) or set(policy)!={'version','targets'} or policy['version']!=1:
            raise ValueError('Invalid target policy')
        self._native=native or Win32Edit()
        self._clock=clock or time.monotonic
        self._lock=threading.RLock()
        self._captures={}
        self._targets=[]
        for raw in policy['targets']:
            t=copy.deepcopy(raw)
            if set(t)!=set(IDENTITY)|{'allowed_operations','max_age_seconds'} or t['class']!='Edit':
                raise ValueError('Only exact standard Edit targets supported')
            if any(type(t[k]) is not int or t[k]<=0 for k in ('hwnd','control_hwnd','pid','process_created_filetime')):
                raise ValueError('Invalid target identity')
            if type(t['max_age_seconds']) not in (int,float) or not 0<t['max_age_seconds']<=300:
                raise ValueError('Capture age must be within 300 seconds')
            if set(t['allowed_operations'])-{'capture','replace_selection'} or 'capture' not in t['allowed_operations']:
                raise ValueError('Invalid operations')
            if hasattr(self._native,'identity'): self._native.identity(t,foreground=False)
            self._targets.append(json.dumps(t,sort_keys=True))

    def _observe(self,target):
        o=self._native.observe(target)
        if any(o[k]!=target[k] for k in IDENTITY): raise ValueError('Target changed')
        if o.get('password') or not o.get('editable'): raise ValueError('Protected or unsupported Edit')
        raw=o['text'].encode('utf-16-le')
        start,end=o['start_utf16'],o['end_utf16']
        if not 0<=start<end<=len(raw)//2 or len(raw)>131070: raise ValueError('Missing or invalid selection')
        selected=raw[start*2:end*2].decode('utf-16-le')
        return o,selected

    def capture_work_context(self):
        reasons=[]
        for encoded in self._targets:
            t=json.loads(encoded)
            try:
                o,selected=self._observe(t)
                c=dict(schema_version=1,capture_id=str(uuid.uuid4()),available=True,missing=[],source='win32.standard_edit',captured_at=now(),window={k:o[k] for k in IDENTITY},selection=dict(start_utf16=o['start_utf16'],end_utf16=o['end_utf16'],text=selected),text_sha256=digest(o['text']),page=None)
                with self._lock: self._captures[c['capture_id']]=(json.dumps(c,sort_keys=True),encoded,json.dumps(o,sort_keys=True),self._clock())
                return c
            except (ValueError,OSError,TimeoutError,UnicodeError) as exc: reasons.append(str(exc))
        return dict(available=False,missing=reasons or ['No approved current target'],selection=None,source='win32.standard_edit',captured_at=now(),page=None)

    def _get(self,context):
        with self._lock: item=self._captures.get(context.get('capture_id'))
        if not item or json.dumps(context,sort_keys=True)!=item[0]: raise ValueError('Unbound capture')
        t=json.loads(item[1]); original=json.loads(item[2])
        if not 0<=self._clock()-item[3]<=t['max_age_seconds']: raise ValueError('Capture expired')
        return t,original

    def validate_work_target(self,context):
        try:
            t,o=self._get(context)
            current,_=self._observe(t)
            return current==o
        except (ValueError,OSError,TimeoutError,UnicodeError): return False

    def replace_selection(self,context,content,*,before_send):
        t,o=self._get(context)
        if 'replace_selection' not in t['allowed_operations'] or not self.validate_work_target(context):
            raise ValueError('Selection target stale or unauthorized')
        if not isinstance(content,str) or not content or '\0' in content or len(content.encode('utf-16-le'))>131070:
            raise ValueError('Invalid replacement text')
        raw=o['text'].encode('utf-16-le')
        expected=(raw[:2*o['start_utf16']]+content.encode('utf-16-le')+raw[2*o['end_utf16']:]).decode('utf-16-le')
        before_send()  # durable within request ledger BEFORE potentially committed send
        self._native.replace(t,content)
        after=self.verify_replacement(context,expected)
        return dict(verified=True,before=o,after=after,expected_text=expected,sha256=digest(expected),source=context['source'])

    def verify_replacement(self,context,expected):
        t,original=self._get(context)
        # A completed edit may leave an empty caret selection; don't require a range here.
        o=self._native.observe(t)
        caret=original['start_utf16']+(len(expected.encode('utf-16-le'))-len(original['text'].encode('utf-16-le')))//2+original['end_utf16']-original['start_utf16']
        if any(o[k]!=t[k] for k in IDENTITY) or o['text']!=expected or (o['start_utf16'],o['end_utf16'])!=(caret,caret):
            raise ValueError('Independent target readback mismatch')
        return o

    def release(self,context):
        if context:
            with self._lock: self._captures.pop(context.get('capture_id'),None)


def capture_work_context(*,provider):
    return provider.capture_work_context()


def validate_work_target(context,*,provider):
    return provider.validate_work_target(context)
