"""Real root records and original profile consumers; process boundary is synthetic."""
import importlib.util
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import pytest
import controls as c
import entry as e
from test_controls import fixture,put,get,digest,RUN,NONCE,ORIGIN,ROOT_KEY,WORKER,LAUNCHER

READER=dict(WORKER,pid=WORKER['pid']+1,created_filetime=WORKER['created_filetime']+1)
spec=importlib.util.spec_from_file_location('original_counter_fixtures',c.BASE_MANIFEST.parent/'test_profile.py')
fixtures=importlib.util.module_from_spec(spec);spec.loader.exec_module(fixtures)


def worker_files(f):
    put(f.case/'service-first-result.json',dict(status='succeeded',task_id=RUN))
    put(f.case/'profile-observations.json',dict(synthetic=True))
    put(f.case/'runtime-inputs.json',dict(synthetic=True))
    members={role:dict(name='trusted-'+role+'.raw',bytes=2,sha256=c.digest(b'{}')) for role in ('runtime','views','replay','collection')}
    for member in members.values():(f.case/member['name']).write_bytes(b'{}')
    put(f.case/'trusted-export.json',dict(format=2,complete=True,END=True,ack_admitted=True,members=members))
    put(f.case/'closed-index.json',dict(format=1,files=c.PROFILE.case_files(f.case)))
    first=dict(format=1,status='candidate',run_id=RUN,entry_nonce=NONCE,worker_pid=WORKER['pid'],
        worker_creation_filetime=WORKER['created_filetime'],product_status='succeeded',
        first_product_sha256=digest(f.case/'service-first-result.json'),closed_index_sha256=digest(f.case/'closed-index.json'),
        observations_sha256=digest(f.case/'profile-observations.json'),runtime_inputs_sha256=digest(f.case/'runtime-inputs.json'),
        work_returned_ns=ORIGIN+2,cleanup_closed_ns=ORIGIN+2,sealed_ns=ORIGIN+2,counters=fixtures.good_counter_fixture(),
        error_type=None,secondary_errors=[],released_members=[])
    put(f.case/'profile-first-result.json',first)
    return first


class NativeDouble:
    """Only OS process work is replaced. All gates, grants and readbacks remain real."""
    def __init__(self,f,fail=None):self.f=f;self.fail=fail;self.started=[];self.cleanups=0;self.closed=False;self.polled=set()
    def root_identity(self):return ROOT_KEY
    def require_cleanup_room(self,additional=0):pass
    def protected(self):
        if self.fail=='protected' and self.started:return self.f.expected[:5]
        return self.f.expected
    def normal_backend(self):return 'python'
    def start(self,role):
        self.started.append(role)
        if self.fail=='launch':raise OSError('Synthetic launch failure')
        pid=WORKER['pid'] if role=='worker' else READER['pid']
        put(self.f.control/(role+'-hello.json'),dict(schema=1,role=role,run_id=RUN,entry_nonce=NONCE,
            pid=pid,executable=str(c.PY),root_manifest_sha256=self.f.context.manifest_sha))
    def qualify(self,role,hello):
        if self.fail=='identity':raise ValueError('Synthetic native/HELLO mismatch')
        return dict(identity=WORKER if role=='worker' else READER,launcher=LAUNCHER,parent_pid=LAUNCHER['pid'],argv_sha256='a'*64)
    def poll(self,role):
        f=self.f
        if role not in self.polled:
            if role=='worker':
                c.WorkerControls(f.context).admit(f.case,f.context.pins())
                f.clock[0]=max(f.clock[0],ORIGIN+3)
                worker_files(f)
                if self.fail=='work_late':f.clock[0]=ORIGIN+275*10**9
                elif self.fail=='cleanup_late':f.clock[0]=ORIGIN+310*10**9+1
            else:
                first=get(f.case/'profile-first-result.json');controls=c.ReaderControls(f.context)
                one=controls.readback(f.case,first);two=controls.readback(f.case,first)
                c.PROFILE.observation_gate(first,two,f.context.closed_hashes(),one,expected_backend='python')
                result=dict(status='candidate_mechanical_verified',outer_root_gate='NOT_ISSUED',ack_attempted=True,
                    ack_admitted=True,ack_verified=True,ssrf=fixtures.ssrf_receipt_fixture('reader'),observed_at_ns=two['observed_at_ns'],
                    released_members=list(get(f.case/'trusted-export.json')['members'].values()))
                if self.fail=='readback_drift':two['first_result_sha256']='f'*64
                if self.fail=='reader_failed':result['status']='failed'
                put(f.control/'reader-result.json',dict(schema=1,run_id=RUN,entry_nonce=NONCE,result=result,observations=[one,two]))
                if self.fail=='reader_late':f.clock[0]=ORIGIN+315*10**9+1
            self.polled.add(role)
        return dict(identity=WORKER if role=='worker' else READER,role=role,signaled=True,
            exit_code=7 if self.fail==role+'_exit' else 0,observed_at_ns=f.clock[0])
    def pause(self):self.f.clock[0]+=1
    def cleanup(self):
        self.cleanups+=1
        return dict(status='FAIL' if self.fail=='cleanup' else 'PASS',logs_closed=True,unregistered_launch_possible=False)
    def close(self):self.closed=True


def run(tmp_path,fail=None):
    f=fixture(tmp_path,folders=False);native=NativeDouble(f,fail)
    return f,native,e.execute(f.context,ORIGIN,lambda context,origin:native)


def test_real_root_closes_only_after_both_actual_exits_and_two_readbacks(tmp_path):
    f,native,result=run(tmp_path)
    assert result['status']=='PENDING_RESULT_REVIEW' and result['mechanical']=='PASS'
    assert result['e02']=='NOT_PASSED' and result['acceptance_credit'] is False
    assert native.started==['worker','reader'] and native.cleanups==1 and native.closed
    assert get(f.root/'release/consumed.json')['consumed']==1
    assert get(f.control/'worker-progress.json')['work']['observed_at_ns']>=ORIGIN
    assert get(f.control/'reader-result.json')['observations'][1]['python_exit_code']==0


@pytest.mark.parametrize('failure',['launch','identity','protected','work_late','cleanup_late','worker_exit',
    'reader_exit','reader_late','reader_failed','readback_drift','cleanup'])
def test_entry_failure_never_promotes_candidate_or_retries(tmp_path,failure):
    f,native,result=run(tmp_path,failure)
    assert result['status']=='FAIL' and result['acceptance_credit'] is False
    assert get(f.root/'release/consumed.json')['consumed']==1
    assert native.started.count('worker')==1 and native.started.count('reader')<=1
    assert native.cleanups==1 and native.closed
    if failure in ('launch','identity','protected','work_late','cleanup_late','worker_exit'):assert 'reader' not in native.started


def test_no_approval_never_initializes_native_backend(tmp_path):
    f=fixture(tmp_path,folders=False)
    (f.root/'release/user-approval.json').unlink()
    called=[]
    with pytest.raises((ValueError,FileNotFoundError)):e.execute(f.context,ORIGIN,lambda *args:called.append(args))
    assert not called and not (f.root/'release/consumed.json').exists()


def test_consumed_run_never_launches_again(tmp_path):
    f,native,result=run(tmp_path)
    other=NativeDouble(f)
    with pytest.raises((ValueError,FileExistsError)):e.execute(f.context,ORIGIN,lambda *args:other)
    assert not other.started


def test_child_environment_removes_all_profile_injection_and_preserves_system():
    clean=e.clean_environment(dict(SystemRoot=r'C:\Windows',PATH='system',TMP='tmp',TEMP='tmp',PYTHONPATH='bad',
        OLLAMA_HOST='bad',OPENJARVIS_HOME='bad',HTTP_PROXY='bad',OPENJARVIS_SSRF_FAIL_OPEN='1'))
    assert clean==dict(SystemRoot=r'C:\Windows',PATH='system')


def test_bootstrap_uses_exact_derived_pins_and_restores_parent(tmp_path,monkeypatch):
    f=fixture(tmp_path);old_cwd=Path.cwd();old_path=list(sys.path)
    for name in list(os.environ):
        if name.upper() in {'TMP','TEMP','TMPDIR','PYTHONPATH','OLLAMA_HOST','OPENJARVIS_HOME'} or name.upper().endswith('_PROXY'):
            monkeypatch.delenv(name)
    def callback(pins):
        c.PROFILE.validate_bootstrap(f.case,pins)
        assert Path.cwd()==c.BASE_MANIFEST.parent
        raise RuntimeError('after validation')
    with pytest.raises(RuntimeError,match='after validation'):e.bootstrap(f.context,callback)
    assert Path.cwd()==old_cwd and sys.path==old_path


def test_concrete_reader_controls_through_original_read_profile(tmp_path,monkeypatch):
    """Reuse the original synthetic pure-replay fixture; no native profile/client.

    Its existing scanner/typed-runtime doubles remain explicit. Root consumption,
    worker observation, file hashes and BOTH actual RootControls calls are real.
    """
    from test_controls import admitted
    f=fixture(tmp_path);admitted(f)
    f.case.rmdir()  # empty synthetic pytest folder; original fixture creates it
    monkeypatch.setitem(sys.modules,'original_counter_fixtures',fixtures)
    r=fixtures.pure_reconstruction.__wrapped__(monkeypatch,tmp_path/'reconstruction',SimpleNamespace())
    original=r.p.read_profile;captured=[]
    def capture(folder,first,p4,**kw):
        captured.append((folder,first,p4,kw['pins']))
        return original(folder,first,p4,**kw)
    monkeypatch.setattr(r.p,'read_profile',capture)
    fixtures.test_replay_tamper_read_profile_gate(None,r,f.case.parent,monkeypatch)
    folder,first,p4,pins=captured[0]
    first.update(run_id=RUN,entry_nonce=NONCE,worker_pid=WORKER['pid'],worker_creation_filetime=WORKER['created_filetime'],
        work_returned_ns=ORIGIN+1,cleanup_closed_ns=ORIGIN+1,sealed_ns=ORIGIN+1)
    (folder/'profile-first-result.json').write_bytes(r.p.canonical(first))
    f.clock[0]=ORIGIN+3
    f.context.record_progress('work');f.context.record_progress('cleanup')
    put(f.control/'protected-after.json',dict(schema=1,observed_at_ns=ORIGIN+2,identities=f.expected))
    f.context.seal_worker(dict(identity=WORKER,role='worker',signaled=True,exit_code=0,observed_at_ns=ORIGIN+2))
    monkeypatch.setattr(r.p,'RootControls',c.PROFILE.RootControls)
    controls=c.ReaderControls(f.context)
    result=original(folder,first,p4,controls=controls,pins=pins)
    assert result['status']=='candidate_mechanical_verified',result
    assert controls.calls==2 and len(controls.observations)==2 and len(result['released_members'])==4


@pytest.mark.parametrize('stalled_role',['worker','reader'])
def test_stall_reserves_real_privateio_termination_and_owned_cleanup(tmp_path,stalled_role):
    """Unchanged Owned.cleanup + Deadline/PrivateIO; only OS calls are simulated."""
    import ast
    import io as streams
    from types import MethodType
    import native_observation as native
    f=fixture(tmp_path,folders=False);entered=[];alive=set()
    Deadline,PrivateIO=native.deadline_io()
    budget=Deadline(clock=lambda:f.clock[0]);budget.origin_ns=ORIGIN;budget.phase='seal'
    script='Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CreationFileTime=[Int64]$_.CreationDate.ToFileTimeUtc();CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
    def advance(seconds):f.clock[0]+=int(seconds*10**9)
    def raw_query(argv,**kw):advance(15);return b'[]'
    def raw_terminate(key):
        entered.append((key['pid'],budget.remaining_ns()));advance(10);alive.discard(key['pid'])
    helper=SimpleNamespace(subprocess=SimpleNamespace(check_output=raw_query,TimeoutExpired=TimeoutError),
        time=SimpleNamespace(monotonic=lambda:f.clock[0]/10**9,sleep=advance),socket=SimpleNamespace(),
        terminate_owned=raw_terminate,save=lambda *args:None)
    private=PrivateIO(helper,budget);private.__enter__()
    def snapshot():
        helper.subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],timeout=15)
        return {pid:{} for pid in alive}
    tree=ast.parse((native.HELPER/'code/controller.py').read_bytes())
    cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Owned')
    method=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='cleanup')
    namespace=dict(process_snapshot=snapshot,terminate_owned=lambda key:helper.terminate_owned(key),
        require=c.require,subprocess=helper.subprocess,time=helper.time,save=lambda *args:helper.save(*args))
    exec(compile(ast.Module(body=[method],type_ignores=[]),'unchanged-Owned.cleanup','exec'),namespace)
    owned=SimpleNamespace(folder=f.context.process,known={},launchers=[],logs=[streams.StringIO(),streams.StringIO()],
        errors=[],auxiliary={},discover=snapshot)
    owned.cleanup=MethodType(namespace['cleanup'],owned)
    class StalledNative(NativeDouble):
        def require_cleanup_room(self,additional=0):
            reserve=native.cleanup_reservation(owned,additional)
            if budget.remaining_ns('seal')<=reserve*10**9:raise TimeoutError('Existing cleanup allowance reserved')
        def start(self,role):
            super().start(role)
            keys=[WORKER,LAUNCHER] if role=='worker' else [READER,dict(LAUNCHER,pid=919)]
            for key in keys:owned.known[key['pid']]=dict(identity=key,role=role);alive.add(key['pid'])
            proc=SimpleNamespace(pid=keys[1]['pid'],wait=lambda timeout:advance(2))
            owned.launchers.append(dict(proc=proc,role=role))
        def poll(self,role):
            if role!=stalled_role:
                result=super().poll(role)
                for key,item in owned.known.items():
                    if item['role']==role:alive.discard(key)
                return result
            if role=='worker' and not (f.case/'service-first-result.json').exists():
                put(f.case/'service-first-result.json',dict(status='succeeded'))
            return None
        def pause(self):advance(1)
        def cleanup(self):
            self.cleanups+=1
            return native.cleanup_no_listener(private,owned)
        def protected(self):
            if self.cleanups:advance(15)  # current exact7 final CIM observation
            return super().protected()
        def close(self):private.__exit__(None,None,None);super().close()
    backend=StalledNative(f)
    result=e.execute(f.context,ORIGIN,lambda *args:backend)
    assert result['status']=='FAIL' and result['acceptance_credit'] is False
    assert not alive and all(log.closed for log in owned.logs)
    assert len(entered)==2 and all(left>=10*10**9 for _,left in entered)
    assert result['cleanup']['status']=='PASS' and f.clock[0]<=ORIGIN+315*10**9


@pytest.mark.parametrize('role',['worker','reader'])
@pytest.mark.parametrize('arrival',['safe','late','read_slip'])
def test_delayed_hello_keeps_queries_and_unregistered_interpreter_reserve(tmp_path,monkeypatch,role,arrival):
    """Production start/qualification; original cleanup and deadline I/O; OS only is synthetic."""
    import ast
    import io as streams
    from types import MethodType
    import native_observation as native
    f=fixture(tmp_path);alive=set();entered=[];queries=[];discoveries=[]
    Deadline,PrivateIO=native.deadline_io()
    budget=Deadline(clock=lambda:f.clock[0]);budget.origin_ns=ORIGIN;budget.phase='seal'
    safe_at=134 if role=='worker' else 52
    hello_at=(182 if role=='worker' else 100) if arrival=='late' else safe_at
    script='Get-CimInstance Win32_Process | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CreationFileTime=[Int64]$_.CreationDate.ToFileTimeUtc();CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
    def advance(seconds):f.clock[0]+=int(seconds*10**9)
    def raw_query(argv,**kw):
        assert kw['timeout']>=15  # Original calls must retain their entire bounded allowance.
        queries.append(f.clock[0]);advance(15);return b'[]'
    def terminate(key):
        entered.append((key['pid'],budget.remaining_ns()));advance(10);alive.discard(key['pid'])
    helper=SimpleNamespace(ROOT=f.root,subprocess=SimpleNamespace(check_output=raw_query,TimeoutExpired=TimeoutError),
        time=SimpleNamespace(monotonic=lambda:f.clock[0]/10**9,sleep=advance),socket=SimpleNamespace(),
        terminate_owned=terminate,save=lambda *args:None)
    private=PrivateIO(helper,budget);private.__enter__()
    key=WORKER if role=='worker' else READER
    launcher=LAUNCHER if role=='worker' else dict(LAUNCHER,pid=919)
    owned=SimpleNamespace(folder=f.context.process,known={},launchers=[],logs=[],errors=[],auxiliary={},forbidden={81})
    backend=native.NativeBackend.__new__(native.NativeBackend)
    backend.context=f.context;backend.origin=ORIGIN;backend.owned=None;backend.pending=None
    backend.observers={};backend.arguments={};backend.environment={};backend.budget=budget;backend.controller=helper;backend.io=private
    command=['python']
    def snapshot(**kwargs):
        helper.subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],timeout=15)
        return {pid:dict(ProcessId=pid,CreationFileTime=(key if pid==key['pid'] else launcher)['created_filetime'],
            ParentProcessId=launcher['pid'] if pid==key['pid'] else os.getpid(),CommandLine=' '.join(command)) for pid in alive}
    def discover():
        rows=snapshot();discoveries.append(f.clock[0])
        if len(discoveries)>1:  # Interpreter becomes visible after the launch snapshot.
            owned.known[key['pid']]=dict(identity=key,role=role,parent=launcher['pid'])
            owned.auxiliary[777]=dict(identity=dict(key,pid=777),authority='observe-only')
        return rows
    def proc(pid):return SimpleNamespace(pid=pid,wait=lambda timeout:advance(2))
    if role=='reader':
        for oldkey in (WORKER,LAUNCHER):owned.known[oldkey['pid']]=dict(identity=oldkey,role='worker')
        owned.launchers.append(dict(identity=LAUNCHER,role='worker',proc=proc(LAUNCHER['pid'])))
        owned.logs.extend([streams.StringIO(),streams.StringIO()])
        backend.owned=owned  # Completed worker remains registered, though already absent.
    def launch(argv,launched_role):
        assert launched_role==role;command[1:]=argv
        owned.known[launcher['pid']]=dict(identity=launcher,role=role,parent=os.getpid())
        owned.launchers.append(dict(identity=launcher,role=role,argv=argv,proc=proc(launcher['pid'])))
        owned.logs.extend([streams.StringIO(),streams.StringIO()]);alive.update((key['pid'],launcher['pid']))
        discover()
    owned.launch=launch;owned.discover=discover
    helper.Owned=lambda *args:owned;helper.process_snapshot=snapshot
    helper.argv_parse=lambda value:command
    helper.snapshot_identity_matches=lambda k,row:k['pid']==row['ProcessId'] and k['created_filetime']==row['CreationFileTime']
    closed_handles=[]
    backend.api=SimpleNamespace(identity=lambda pid:dict(key),open=lambda pid:pid+1000,
        times=lambda handle:(key['created_filetime'],0),close=closed_handles.append)
    def pause():
        advance(1)
        if f.clock[0]>=ORIGIN+hello_at*10**9 and not (f.control/(role+'-hello.json')).exists():
            put(f.control/(role+'-hello.json'),dict(schema=1,role=role,run_id=RUN,entry_nonce=NONCE,
                pid=key['pid'],executable=str(c.PY),root_manifest_sha256=f.context.manifest_sha))
    backend.pause=pause
    if arrival=='read_slip':
        original=e.check_hello
        def slow_read(*args):original(*args);advance(2)
        monkeypatch.setattr(e,'check_hello',slow_read)
    tree=ast.parse((native.HELPER/'code/controller.py').read_bytes())
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Owned')
    cleanup=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='cleanup')
    ns=dict(process_snapshot=snapshot,terminate_owned=lambda k:helper.terminate_owned(k),require=c.require,
        subprocess=helper.subprocess,time=helper.time,save=lambda *args:helper.save(*args))
    exec(compile(ast.Module(body=[cleanup],type_ignores=[]),'unchanged-Owned.cleanup','exec'),ns)
    owned.cleanup=MethodType(ns['cleanup'],owned)
    qualified=None;failure=None;cleanup_result=None;cleanup_error=None
    try:
        try:qualified=e.start(f.context,backend,role,ORIGIN)
        except (ValueError,TimeoutError) as exc:failure=exc
        queries_before_cleanup=len(queries)
        try:
            cleanup_result=backend.cleanup()
            snapshot()  # Same full15s final protected identity observation budget.
            budget.post('final protected readback and proof')
        except (ValueError,TimeoutError,AssertionError) as exc:cleanup_error=exc
    finally:backend.close()
    assert cleanup_error is None,repr(cleanup_error)
    assert cleanup_result['status']=='PASS',cleanup_result
    assert not alive and all(log.closed for log in owned.logs)
    assert len(entered)==2 and all(left>=10*10**9 for _,left in entered)
    assert budget.origin_ns==ORIGIN and f.clock[0]<=ORIGIN+315*10**9
    if arrival=='safe':
        assert failure is None and qualified['identity']==key
        assert queries_before_cleanup==3 and len(closed_handles)==1  # Launch + both real qualification calls.
    else:
        assert qualified is None and failure is not None
        assert queries_before_cleanup==1 and not closed_handles  # Refuse before spending either qualification call.
