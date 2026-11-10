"""Retained native worker handle, using synthetic Windows calls only."""
from copy import deepcopy
from types import SimpleNamespace
import pytest
from native_observation import RetainedExit
import native_observation as n

KEY = {'pid': 417, 'created_filetime': 134384100000000123, 'exe': r'C:\Python\python.exe'}


class Native:
    def __init__(self):
        self.key = deepcopy(KEY)
        self.created = KEY['created_filetime']
        self.wait = 0
        self.code = 0
        self.clock = 105
        self.closed = []
        self.calls = []

    def identity(self, pid):
        self.calls.append(('identity', pid))
        return deepcopy(self.key)

    def open(self, pid):
        self.calls.append(('open', pid))
        return 29

    def times(self, handle):
        self.calls.append(('times', handle))
        return self.created, 134384100000000200

    def signaled(self, handle):
        self.calls.append(('signaled', handle))
        return self.wait == 0

    def exit_code(self, handle):
        self.calls.append(('exit_code', handle))
        return self.code

    def close(self, handle):
        self.closed.append(handle)

    def now(self):
        return self.clock


def owner():
    return SimpleNamespace(known={417: {'identity': deepcopy(KEY), 'role': 'worker'}}, forbidden={81})


def private_io_fixture():
    Deadline,PrivateIO=n.deadline_io();now=[100];b=Deadline(clock=lambda:now[0]);b.run_id='test'
    b.adopt_parent(dict(clock_domain=b.timing()['clock_domain'],run_id='test',origin_ns=90))
    calls=[]
    process=SimpleNamespace(check_output=lambda argv,**kw:calls.append((argv,kw)) or b'[]')
    c=SimpleNamespace(subprocess=process,time=SimpleNamespace(sleep=lambda _:None),socket=SimpleNamespace(),
        terminate_owned=lambda key:None,save=lambda path,value:None)
    return b,PrivateIO(c,b),c,calls,now


def test_existing_private_io_accepts_only_explicit_current_cim_extension():
    b,io,c,calls,now=private_io_fixture()
    script='Get-CimInstance Win32_Process -Filter "ProcessId=417" | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CreationFileTime=[Int64]$_.CreationDate.ToFileTimeUtc();CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
    original=c.subprocess
    with io:
        assert c.subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],timeout=15)==b'[]'
        with pytest.raises(ValueError):c.subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script+'; bad'],timeout=15)
    assert c.subprocess is original and len(calls)==1 and calls[0][1]['timeout']==15
    assert b.origin_ns==90


def test_no_listener_cleanup_keeps_original_clock_and_requires_closed_logs():
    b,io,c,calls,now=private_io_fixture();b.phase='work'
    owned=SimpleNamespace(launchers=[],logs=[SimpleNamespace(closed=True)],cleanup=lambda port:{'status':'PASS','processes':[{'absent':True}]})
    with io:result=n.cleanup_no_listener(io,owned)
    assert result['status']=='PASS' and result['logs_closed'] is True and result['port_probe']=='NOT_APPLICABLE_NO_LISTENER'
    assert b.phase=='seal' and b.origin_ns==90 and not calls


@pytest.mark.parametrize('issue',['late','logs','unregistered'])
def test_cleanup_cannot_invent_grace_or_registration(issue):
    b,io,c,calls,now=private_io_fixture()
    owned=SimpleNamespace(launchers=[],logs=[SimpleNamespace(closed=issue!='logs')],cleanup=lambda port:{'status':'PASS'})
    if issue=='late':now[0]=90+315*10**9+1
    if issue=='unregistered':io.launch_attempts=[dict(registered=False)]
    with io:
        try:result=n.cleanup_no_listener(io,owned)
        except TimeoutError:assert issue=='late'
        else:assert result['status']=='FAIL'


def qualification_fixture(tmp_path):
    obj=n.NativeBackend.__new__(n.NativeBackend);api=Native()
    launcher=dict(KEY,pid=418,created_filetime=KEY['created_filetime']-1)
    row=dict(ProcessId=417,CreationFileTime=KEY['created_filetime'],ParentProcessId=418,CommandLine='python fixed')
    owned=owner();owned.known[417].update(parent=418,argv='python fixed')
    owned.launchers=[dict(identity=launcher,role='worker',argv=['fixed'],proc=SimpleNamespace(pid=418))]
    owned.discover=lambda:{417:row}
    obj.controller=SimpleNamespace(process_snapshot=lambda **kw:{417:row},argv_parse=lambda value:value.split(),
        snapshot_identity_matches=lambda key,value:key['pid']==value['ProcessId'] and key['created_filetime']==value['CreationFileTime'])
    obj.owned=owned;obj.api=api;obj.observers={};obj.arguments={'worker':['fixed']}
    obj.context=SimpleNamespace(clock=api.now,process=tmp_path,_time=lambda *a,**k:api.now())
    obj.origin=100
    return obj,api,row


def test_native_role_requires_registered_argv_parent_and_retained_actual_handle(tmp_path):
    obj,api,row=qualification_fixture(tmp_path)
    result=obj.qualify('worker',{'pid':417})
    assert result['identity']==KEY and result['parent_pid']==418 and 'worker' in obj.observers
    assert api.calls[-1]==('identity',417)
    obj.observers['worker'].close()


@pytest.mark.parametrize('issue',['argv','parent','creation','protected','role','unknown'])
def test_native_role_cannot_be_established_by_hello_only(tmp_path,issue):
    obj,api,row=qualification_fixture(tmp_path)
    if issue=='argv':row['CommandLine']='python other'
    if issue=='parent':row['ParentProcessId']=81
    if issue=='creation':row['CreationFileTime']+=100
    if issue=='protected':obj.owned.forbidden.add(417)
    if issue=='role':obj.owned.known[417]['role']='reader'
    if issue=='unknown':obj.owned.known.clear()
    with pytest.raises(ValueError):obj.qualify('worker',{'pid':417})
    assert not obj.observers and not any(call[0]=='open' for call in api.calls)


def test_worker_exit_observed_on_retained_handle():
    api = Native()
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        result = observer.poll(100, 110)
    assert result == {'identity': KEY, 'role': 'worker', 'signaled': True,
                      'exit_code': 0, 'observed_at_ns': 105}
    assert api.closed == [29]


def test_native_exit_failure_is_not_launcher_success():
    api = Native(); api.code = 7
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        assert observer.poll(100, 110)['exit_code'] == 7


def test_no_exit_code_is_observed_until_handle_signals():
    api = Native(); api.wait = 258
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        assert observer.poll(100, 110) is None
    assert not any(call[0] == 'exit_code' for call in api.calls)


@pytest.mark.parametrize('mutate', [
    lambda o: o.known.clear(),
    lambda o: o.forbidden.add(417),
    lambda o: o.known[417].update(role='launcher'),
    lambda o: o.known[417]['identity'].update(created_filetime=KEY['created_filetime']+1),
])
def test_ambiguous_or_protected_member_never_opens_handle(mutate):
    api = Native(); owned = owner(); mutate(owned)
    with pytest.raises(ValueError):
        RetainedExit(owned, KEY, 'worker', api=api, clock=api.now)
    assert not any(call[0] == 'open' for call in api.calls)


def test_handle_creation_mismatch_closes_without_exit_credit():
    api = Native(); api.created += 1
    with pytest.raises(ValueError):
        RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    assert api.closed == [29]


def test_pid_reuse_after_open_closes_handle():
    api = Native()
    old_open = api.open
    def replaced(pid):
        handle = old_open(pid)
        api.key['created_filetime'] += 20
        return handle
    api.open = replaced
    with pytest.raises(ValueError):
        RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    assert api.closed == [29]


@pytest.mark.parametrize('at', [99, 111, True])
def test_missing_or_expired_original_clock_never_returns_success(at):
    api = Native(); api.clock = at
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        with pytest.raises(ValueError):
            observer.poll(100, 110)


def test_clock_is_checked_after_native_exit_read():
    api = Native()
    def slow_exit(handle):
        api.clock = 111
        return 0
    api.exit_code = slow_exit
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        with pytest.raises(ValueError):
            observer.poll(100, 110)


def test_exit_observation_is_stable_on_pid_reuse_after_original_exit():
    api = Native()
    with RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now) as observer:
        api.key['created_filetime'] += 999  # PID lookup now names a different process.
        assert observer.poll(100, 110)['identity'] == KEY  # retained handle still names original.


def test_closed_handle_cannot_be_reused():
    api = Native(); observer = RetainedExit(owner(), KEY, 'worker', api=api, clock=api.now)
    observer.close(); observer.close()
    with pytest.raises(ValueError):
        observer.poll(100, 110)
    assert api.closed == [29]
