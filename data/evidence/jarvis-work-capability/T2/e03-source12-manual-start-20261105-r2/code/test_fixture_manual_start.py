import ctypes as C
from ctypes import wintypes as W
import importlib
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest


def module():
    return importlib.import_module('fixture_manual_start')


@pytest.mark.parametrize('change', ['window','button','id','notification','message'])
def test_only_owned_start_button_notification_is_accepted(change):
    m=module();args=dict(parent=11,button=22,hwnd=11,message=0x111,wparam=m.START_BUTTON_ID,lparam=22)
    assert m.is_start_command(**args)
    args[{'window':'hwnd','button':'lparam','id':'wparam','notification':'wparam','message':'message'}[change]]=({
        'window':12,'button':23,'id':m.START_BUTTON_ID+1,'notification':m.START_BUTTON_ID+(1<<16),'message':0x100}[change])
    assert not m.is_start_command(**args)


class Clock:
    value=0.0
    def now(self):return self.value
    def sleep(self,seconds):self.value+=seconds


def test_no_click_waits_to_timeout_without_reading_keyboard_or_activating():
    m=module();clock=Clock();reads=[]
    with pytest.raises(TimeoutError):
        m.wait_for_start(lambda:False,lambda:reads.append('keyboard'),lambda:False,
                         timeout_seconds=.03,clock=clock.now,sleep=clock.sleep)
    assert not reads


@pytest.mark.parametrize('fault',['held-key','stop','expired-in-pump'])
def test_invalid_handoff_stops_before_activation(fault):
    m=module();clock=Clock();reads=[]
    def pump():
        if fault=='expired-in-pump':clock.value=16
        return True
    def keyboard():reads.append(True);return fault!='held-key'
    with pytest.raises((ValueError,TimeoutError)):
        m.wait_for_start(pump,keyboard,lambda:fault=='stop',clock=clock.now,sleep=clock.sleep)
    assert len(reads)==(1 if fault=='held-key' else 0)


def test_click_and_released_keys_complete_handoff_once():
    m=module();clock=Clock();calls=[]
    result=m.wait_for_start(lambda:calls.append('click') or True,lambda:calls.append('keyboard') or True,
                           lambda:False,clock=clock.now,sleep=clock.sleep)
    assert result['keyboard_clear'] is True and calls==['click','keyboard']


def native(*,foreground=True,focus=True):
    calls=[];target=dict(hwnd=11,control_hwnd=22,pid=33)
    u=SimpleNamespace(SetForegroundWindow=lambda hwnd:calls.append(('foreground',hwnd)) or foreground,
                      SetFocus=lambda hwnd:calls.append(('focus',hwnd)))
    n=SimpleNamespace(u=u,identity=lambda t,foreground:calls.append(('identity',foreground)),
                      focused=lambda:(11,22) if focus else (99,98),
                      send=lambda *args:calls.append(('send',*args)))
    return n,target,calls


def test_start_uses_owned_foreground_and_focus_then_selects_without_attachment():
    m=module();n,target,calls=native()
    result=m.activate_owned(n,target,[target],initial=True)
    assert result['status']=='PASS' and result['cross_thread_attached'] is False
    assert calls==[('identity',False),('foreground',11),('focus',22),('send',22,0xB1,0,-1)]


@pytest.mark.parametrize('failure',['foreground','focus','foreign-foreground'])
def test_failed_or_lost_focus_never_selects_or_reclaims_foreign_window(failure):
    m=module();n,target,calls=native(foreground=failure!='foreground',focus=failure not in ('focus','foreign-foreground'))
    with pytest.raises(ValueError):m.activate_owned(n,target,[target],initial=failure!='foreign-foreground')
    assert not any(x[0]=='send' for x in calls)
    if failure=='foreign-foreground':assert not any(x[0]=='foreground' for x in calls)


def test_handoff_receipt_is_bound_to_fixture_and_no_automatic_attachment():
    m=module();fixture={'pid':33,'targets':[{'hwnd':11}]}
    valid=dict(schema=1,status='ACCEPTED',pid=33,window_hwnd=11,button_hwnd=22,
               keyboard_clear=True,cross_thread_attached=False,requested_by='owned_start_button',
               ready_at='2026-11-05T12:00:00+00:00',accepted_at='2026-11-05T12:00:01+00:00',
               timeout_seconds=15,elapsed_seconds=1)
    assert m.validate_handoff(valid,fixture) is True
    for key,value in [('pid',34),('window_hwnd',12),('keyboard_clear',False),('cross_thread_attached',True),
                      ('status','READY'),('requested_by','automatic'),('elapsed_seconds',15),('extra_key_payload',123)]:
        changed=dict(valid);changed[key]=value
        with pytest.raises(ValueError):m.validate_handoff(changed,fixture)


class Fn:
    def __init__(self,call):self.call=call
    def __call__(self,*args):return self.call(*args)


def fake_user32(*,held=False):
    m=module();calls=[];state={'proc':123,'queued':True}
    prototype=C.WINFUNCTYPE(C.c_ssize_t,W.HWND,W.UINT,W.WPARAM,W.LPARAM)
    def set_long(hwnd,index,value):
        previous=state['proc'];state['proc']=value.value if hasattr(value,'value') else value
        calls.append(('subclass',state['proc']));return previous
    def peek(pointer,*args):
        if not state['queued']:return False
        state['queued']=False;msg=C.cast(pointer,C.POINTER(W.MSG)).contents
        msg.hWnd=11;msg.message=0x111;msg.wParam=m.START_BUTTON_ID;msg.lParam=22
        return True
    def dispatch(pointer):
        msg=C.cast(pointer,C.POINTER(W.MSG)).contents
        return prototype(state['proc'])(msg.hWnd,msg.message,msg.wParam,msg.lParam)
    def owner(hwnd,pid):C.cast(pid,C.POINTER(W.DWORD)).contents.value=os.getpid();return 44
    u=SimpleNamespace(
        CreateWindowExW=Fn(lambda *args:calls.append(('create-button',args)) or 22),
        GetWindowLongW=Fn(lambda *args:m.NO_ACTIVATE),
        GetWindowLongPtrW=Fn(lambda *args:state['proc']),SetWindowLongPtrW=Fn(set_long),
        CallWindowProcW=Fn(lambda *args:0),GetWindowThreadProcessId=Fn(owner),
        PeekMessageW=Fn(peek),TranslateMessage=Fn(lambda *args:True),DispatchMessageW=Fn(dispatch),
        GetAsyncKeyState=Fn(lambda code:0x8000 if held and code==8 else 0),
        SetWindowPos=Fn(lambda *args:calls.append(('show-noactivate',args)) or True),
        DestroyWindow=Fn(lambda hwnd:calls.append(('destroy-button',hwnd)) or True))
    return u,calls,state


@pytest.mark.parametrize('held',[False,True])
def test_actual_native_button_adapter_restores_callback_and_destroys_button(tmp_path,held):
    m=module();u,calls,state=fake_user32(held=held)
    if held:
        with pytest.raises(ValueError,match='keyboard'):m.manual_start(u,11,tmp_path)
        assert not (tmp_path/'manual-start.json').exists()
    else:
        m.manual_start(u,11,tmp_path)
        receipt=json.loads((tmp_path/'manual-start.json').read_text(encoding='utf-8'))
        assert receipt['keyboard_clear'] is True and receipt['window_hwnd']==11
        assert m.validate_handoff(receipt,{'pid':os.getpid(),'targets':[{'hwnd':11}]}) is True
    assert state['proc']==123 and calls[-1]==('destroy-button',22)
    assert not any(x[0] in ('foreground','focus','attach') for x in calls)


def test_completed_manual_start_cannot_be_reused(tmp_path):
    m=module();u,calls,state=fake_user32();m.manual_start(u,11,tmp_path)
    before=list(calls)
    with pytest.raises(FileExistsError):m.manual_start(u,11,tmp_path)
    assert calls==before


def test_primary_start_button_is_shown_above_sibling_without_activation(tmp_path):
    m=module();u,calls,state=fake_user32();m.manual_start(u,11,tmp_path)
    shows=[row[1] for row in calls if row[0]=='show-noactivate']
    assert shows==[(11,0,0,0,0,0,0x53)]


def test_real_fixture_definition_waits_before_focus_and_creates_nonactivating_windows(tmp_path,monkeypatch):
    import sys
    f=importlib.import_module('fixture_adapter');m=module()
    calls=[];state={'next':100,'armed':False,'foreground':900,'focus':901};texts={};selections={};windows=[]
    def create(exstyle,cls,title,style,*args):
        state['next']+=1;hwnd=state['next']
        if cls=='STATIC':windows.append((hwnd,exstyle))
        else:texts[hwnd]=title;selections[hwnd]=(0,0)
        return hwnd
    def foreground(hwnd):
        assert state['armed'],'Fixture stole foreground before operator Start'
        calls.append('foreground');state['foreground']=hwnd;return True
    def focus(hwnd):calls.append('focus');state['focus']=hwnd;return 0
    def send(hwnd,message,w=0,l=0):
        if message==0xC:texts[hwnd]=C.wstring_at(l)
        if message==0xB1:
            assert state['armed'];calls.append('select')
            selections[hwnd]=(w,len(texts[hwnd]) if l==-1 else l)
        return 1
    u=SimpleNamespace(**{name:Fn(lambda *args:1) for name in (
        'ShowWindow','DestroyWindow','PeekMessageW','TranslateMessage','DispatchMessageW',
        'SetWindowLongPtrW','SetWindowLongW','InSendMessageEx')})
    u.CreateWindowExW=Fn(create);u.SetForegroundWindow=Fn(foreground);u.SetFocus=Fn(focus)
    u.GetForegroundWindow=Fn(lambda:state['foreground']);u.GetWindowThreadProcessId=Fn(lambda *args:88)
    u.AttachThreadInput=Fn(lambda *args:calls.append('attach') or True)
    k=SimpleNamespace(GetCurrentThreadId=Fn(lambda:77))
    n=SimpleNamespace(u=u,k=k,created=lambda pid:99,send=send,identity=lambda *args,**kw:None,
        focused=lambda:(state['foreground'],state['focus']))
    n.observe=lambda target,**kw:dict(text=texts[target['control_hwnd']],
        start_utf16=selections[target['control_hwnd']][0],end_utf16=selections[target['control_hwnd']][1])
    def save(path,value):
        path.write_text(json.dumps(value),encoding='utf-8')
        if path.name=='fixture.json':(tmp_path/'stop').touch()
    def initialize(set_text,read_text,expected):
        set_text(expected);assert read_text()==expected
        return {'verified':True}
    harness=SimpleNamespace(CASES={'e03':{'text':'fixed source','window_title':'fixture'}},save=save,
                            initialize_fixture_text=initialize,read_fixture_edit_text=lambda native,hwnd:texts[hwnd])
    monkeypatch.setitem(sys.modules,'src.brain.tests',SimpleNamespace(work_context_acceptance=harness))
    monkeypatch.setitem(sys.modules,'src.brain.work_context',SimpleNamespace(Win32Edit=lambda:n))
    origin=SimpleNamespace(start=lambda controls:True,summary=lambda:{'complete':True},finish=lambda:{'complete':True})
    monkeypatch.setattr(f,'InputOriginRecorder',lambda **kw:origin)
    monkeypatch.setattr(f,'bind_input_source_reader',lambda user:lambda:None)
    monkeypatch.setattr(f,'_append_record',lambda *args:None)
    monkeypatch.setattr(f,'_install_audit',lambda user,kernel,hwnd,pid,folder,index,origin:dict(
        hwnd=hwnd,old_proc=1,path=folder/'events',lock=None,index=index,state={'enabled':False,'error':False}))
    def start_button(user,window,folder):
        assert not calls;calls.append('manual-start');state['armed']=True
    monkeypatch.setattr(f,'manual_start',start_button,raising=False)
    monkeypatch.setattr(f,'activate_owned',m.activate_owned,raising=False)
    monkeypatch.setattr(f,'NO_ACTIVATE',m.NO_ACTIVATE,raising=False)
    monkeypatch.setattr(f,'APP_WINDOW',m.APP_WINDOW,raising=False)
    assert f.fixture(tmp_path,tmp_path/'candidate')==0
    assert calls==['manual-start','foreground','focus','select']
    assert len(windows)==2 and all(style&(m.NO_ACTIVATE|m.APP_WINDOW)==m.NO_ACTIVATE|m.APP_WINDOW for _,style in windows)
