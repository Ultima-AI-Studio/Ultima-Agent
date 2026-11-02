"""No real launch, kill, HTTP, product submission, model or qualification."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import types
import pytest

spec=importlib.util.spec_from_file_location('source10_adapter',Path(__file__).with_name('adapter.py'))
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
with a.candidate_import_path():
    from src.brain.tests.test_work_research import sdk_io,mock_jar
    from src.brain.tests.test_work_navigation_transport import genuine_navigation

def synthetic_bundle(folder,sdk_io,mock_jar,monkeypatch,*,write=True):
    from dataclasses import asdict
    from src.brain.tests import test_work_research as fixtures
    monkeypatch.setattr(fixtures,'URLS',fixtures.URLS[:4])
    result,ledger=genuine_navigation(folder/'outputs',sdk_io,mock_jar)
    sources=json.loads(ledger._collection.catalogue_json)
    monkeypatch.setattr(a,'corpus',lambda:dict(query='Research a subject',sources=sources))
    result['marker']='first'
    if write:
        a.save_new(folder/'service-first-result.json',result)
        a.save_new(folder/'runtime-inputs.json',asdict(ledger._runtime_inputs))
        a.export_completed(folder,ledger,result)
    return result,ledger

def documents():
    now=dt.datetime.now(dt.timezone.utc)
    authority=dict(schema=11,kind='source10_execution',issuer='root',case='E02-controlled-1',candidate='118ba152b007c30d358c8bc44c51aabe8ae820f0',candidate_manifest_sha256='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50',issued_at=now.isoformat(),expires_at=(now+dt.timedelta(seconds=90)).isoformat(),budgets=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,outer_seconds=315,retry=0),native_precision='FILETIME100ns',actual=True,schedule=dict(work_seconds=275,cleanup_seconds=310,outer_seconds=315,ruling_sha256='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'),parent_timing=dict(origin_ns=100,clock_domain=a.CLOCK_DOMAIN,run_id='test',parent_identity={}))
    ledger=dict(schema=11,released_case='E02-controlled-1',consumed=['E02-controlled-1'],attempts=1,retry=0)
    return authority,ledger,now

@pytest.mark.parametrize('mutation',['candidate','budget','baseline','expired','kind','schema','model','source','defaults','hash','retry'])
def test_adapter_rejects_wrong_candidate_budget_and_baseline(mutation):
    authority,ledger,now=documents()
    a.validate_documents(authority,ledger,now)
    if mutation=='candidate': authority['candidate']='source9'
    elif mutation=='budget': authority['budgets']['native_POST']=9
    elif mutation=='baseline': authority['native_precision']='legacy-CIM-ticks'
    elif mutation=='expired': authority['expires_at']=(now-dt.timedelta(seconds=1)).isoformat()
    elif mutation=='kind': authority['kind']='source10_harness_preparation_only'
    elif mutation=='schema': ledger['schema']=2
    elif mutation=='model': authority['model']='other'
    elif mutation=='source': authority['candidate_manifest_sha256']='0'*64
    elif mutation=='defaults': authority['overrides']=['max_turns=20']
    elif mutation=='hash': authority['candidate']='0'*40
    elif mutation=='retry': ledger['consumed'].append('E02-controlled-2')
    with pytest.raises(ValueError): a.validate_documents(authority,ledger,now)

def test_pinned_import_rejects_cached_acceptance_adapter(monkeypatch):
    sentinel=types.ModuleType('acceptance_adapter'); sentinel.__file__=__file__
    monkeypatch.setitem(sys.modules,'acceptance_adapter',sentinel)
    with pytest.raises(ValueError,match='cached'): a.load_p4()
    assert sys.modules['acceptance_adapter'] is sentinel

@pytest.mark.parametrize('failure',['timeout','nonzero','invalidJSON','partialpacket','missingEND','cleanup','finalboundary'])
def test_adapter_first_failure_retained_and_no_next_case(tmp_path,monkeypatch,failure,sdk_io,mock_jar):
    first,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch)
    p4=a.load_p4()
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable))
    monkeypatch.setattr(p4,'process_times',lambda proc:(100,0))
    monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:{})
    monkeypatch.setattr(p4,'terminate_owned',lambda key:None)
    monkeypatch.setattr(p4,'assert_listener',lambda *args:None)
    monkeypatch.setattr(p4,'listener_owner',lambda port:[7890])
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    if failure in ('partialpacket','missingEND'):
        export=a.load(tmp_path/'trusted-export.json')
        if failure=='partialpacket': export['members']['runtime']['sha256']='0'*64
        else: export['END']=False
        (tmp_path/'trusted-export.json').write_text(json.dumps(export),encoding='utf8')
    pin_reads=[]
    def pins():
        pin_reads.append(1)
        return {'drift':'changed'} if failure=='finalboundary' and len(pin_reads)>=3 else {}
    monkeypatch.setattr(a,'check_inputs',pins)
    monkeypatch.setattr(a,'check_native_baseline',lambda *args: [])
    launches=[]
    class Proc:
        pid=7890; returncode=2 if failure=='nonzero' else 0
        def wait(self,timeout=None):
            if failure=='timeout' and timeout and timeout>3: raise TimeoutError('CLI timeout')
            return self.returncode
    def launch(argv,env,out,err):
        launches.append(argv)
        if '--research' in argv: out.write('{broken' if failure=='invalidJSON' else json.dumps(first)); out.flush()
        return Proc()
    # Patch only the actual launcher boundary; real P4 Owned.launch/discover/cleanup execute.
    root=a.C
    monkeypatch.syspath_prepend(str(root))
    from src.brain.tests import work_context_acceptance as helper
    monkeypatch.setattr(helper,'launch',launch)
    if failure=='cleanup': monkeypatch.setattr(p4,'terminate_owned',lambda key: (_ for _ in ()).throw(OSError('cleanup blocked'))); monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:{7890:{'ParentProcessId':0}})
    context=dict(folder=tmp_path,port=18799,request_id='r',session_id='s',baseline={},authority={},ledger={})
    result=a.execute_case(context,p4)
    assert len(launches)<=2
    assert result['work_cli_attempts']==1
    assert result['actual_native_start_count'] is None
    assert result['overall']=='FAIL'
    assert result['next_case'] is False
    expected={'timeout':'CLI timeout','nonzero':'CLI nonzero','invalidJSON':'Expecting property name','partialpacket':'Export member digest','missingEND':'Missing complete packet or END','cleanup':'cleanup terminate_owned: cleanup blocked','finalboundary':'final-boundary: Input drift'}
    assert expected[failure] in result['first_failure']
    if failure=='cleanup': assert result['cleanup']['status']=='FAIL' and any(e.get('effects_unknown') for e in result['errors'])
    else: assert result['cleanup']['status']=='PASS'
    if failure not in ('timeout','invalidJSON'):
        assert json.loads((tmp_path/'product-result.json').read_text('utf8'))['marker']=='first'
    with pytest.raises(FileExistsError): a.execute_case(context,p4)
    assert len(launches)<=2

def test_adapter_reuses_owned_cleanup_and_retains_unknown_effect(tmp_path,monkeypatch):
    p4=a.load_p4()
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100+pid,exe=sys.executable))
    monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:{5:dict(ParentProcessId=4,CommandLine='unknown')})
    owned=p4.Owned(tmp_path,{})
    owned.known[4]=dict(identity=dict(pid=4,created_filetime=104,exe=sys.executable),role='server',argv=[],parent=0)
    killed=[]; monkeypatch.setattr(p4,'terminate_owned',lambda key:killed.append(key))
    result=owned.cleanup()
    assert result['status']=='FAIL'
    assert not killed
    assert any(e.get('discovery')=='unknown-nested-descendant' for e in result['errors'])

@pytest.mark.parametrize('section',['source_files','sdk22','policy','model'])
def test_real_manifest_detects_input_hash_drift(monkeypatch,section):
    m=a.load(a.V/'source10-candidate-manifest.json')
    path=next(iter(m[section])) if section in ('source_files','sdk22') else m['model']['policy_path' if section=='policy' else 'local_manifest_path']
    original=a.sha
    monkeypatch.setattr(a,'sha',lambda candidate:'0'*64 if Path(candidate)==Path(path) else original(candidate))
    with pytest.raises(ValueError,match='drift'): a.check_inputs()

def test_missing_or_preparation_authority_never_constructs_owned(monkeypatch):
    p4=a.load_p4(); constructed=[]
    monkeypatch.setattr(p4,'Owned',lambda *args:constructed.append(args))
    monkeypatch.setattr(a,'load_p4',lambda:p4)
    with pytest.raises(FileNotFoundError): a.run_case(a.V/'controller-authority'/f'{a.CASE}.json',a.V/'controller-ledger.json')
    with pytest.raises(ValueError): a.run_case(a.V/'harness-preparation-authority.json',a.V/'controller-ledger.json')
    assert not constructed

@pytest.mark.parametrize('precision,drift',[('legacy-CIM',0),('FILETIME100ns',1),('FILETIME100ns',0)])
def test_native_baseline_requires_exact_integer_filetime(monkeypatch,precision,drift):
    protected=[dict(pid=p,created_filetime=100000001+p,exe='python') for p in range(1,6)]
    proof=dict(precision=precision,candidate=a.CANDIDATE,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=protected)
    p4=a.load_p4()
    monkeypatch.setattr(p4,'protected',lambda:protected)
    monkeypatch.setattr(p4,'identity',lambda pid:dict(protected[pid-1],created_filetime=protected[pid-1]['created_filetime']+drift))
    if precision=='FILETIME100ns' and drift==0: assert a.check_native_baseline(proof,p4)==protected
    else:
        with pytest.raises(ValueError): a.check_native_baseline(proof,p4)

@pytest.mark.parametrize('complete,end',[(False,False),(True,False)])
def test_real_export_reader_rejects_partial_or_missing_end(tmp_path,monkeypatch,complete,end):
    monkeypatch.syspath_prepend(str(a.C))
    a.save_new(tmp_path/'trusted-export.json',dict(complete=complete,END=end))
    a.save_new(tmp_path/'runtime-inputs.json',{})
    with pytest.raises(ValueError,match='END'): a.verify_exports(tmp_path,{},a.load_p4())

def test_original_browser_fixture_preserves_bodies_without_native_send_observer(monkeypatch):
    import ddgs,httpx,socket
    original_send=httpx.Client.send
    with monkeypatch.context() as scope:
        scope.setattr(ddgs,'DDGS',ddgs.DDGS); scope.setattr(httpx,'request',httpx.request); scope.setattr(socket,'getaddrinfo',socket.getaddrinfo)
        a.install_browser_fixture()
        assert httpx.Client.send is original_send
        sources=a.corpus()['sources']; hits=ddgs.DDGS().text(a.corpus()['query'])
        assert [h['href'] for h in hits]==[s['final_url'] for s in sources]
        for source in sources:
            response=httpx.request('GET',source['final_url'],follow_redirects=False,timeout=5)
            assert response.content==source['body'].encode('utf8')
        with pytest.raises(OSError): socket.getaddrinfo('other.example',443)

def test_runtime_inputs_captured_at_real_freeze_before_packet_exists(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.work_tools import WorkLedger,WorkBinding
    from src.brain.work_service import WorkService
    # Restore definitions after observing them in this isolated unit process.
    monkeypatch.setattr(WorkLedger,'__init__',WorkLedger.__init__)
    monkeypatch.setattr(WorkLedger,'_freeze_runtime_inputs',WorkLedger._freeze_runtime_inputs)
    monkeypatch.setattr(WorkService,'submit_work',WorkService.submit_work)
    a.install_trusted_exports(tmp_path)
    ledger=WorkLedger(); ledger._binding=WorkBinding(tmp_path,'r','s','t'); ledger._navigation=types.SimpleNamespace(binding_key=('r','s','t')); ledger.deadline=260.25
    ledger._freeze_runtime_inputs('trusted original prompt',None)
    saved=a.load(tmp_path/'runtime-inputs.json')
    assert saved==dict(prompt='trusted original prompt',binding_key=['r','s','t'],root=str(tmp_path),allowance=2048,deadline='260.25')
    assert not hasattr(ledger,'_runtime_final')
    with pytest.raises(ValueError): ledger._freeze_runtime_inputs('packet-derived forgery',None)
    assert a.load(tmp_path/'runtime-inputs.json')==saved

def test_inert_requires_separate_concrete_authority():
    prep=a.load(a.V/'harness-preparation-authority.json')
    with pytest.raises(ValueError,match='Separate'): a.validate_inert_documents(prep,dt.datetime.now(dt.timezone.utc))

@pytest.mark.parametrize('failure',['hash','bytes','extra','escape','none'])
def test_real_external_readback_validates_hash_bytes_inventory_and_root(tmp_path,failure):
    p4=a.load_p4(); task='12345678-1234-4234-8234-123456789abc'
    folder=tmp_path; output=folder/'outputs'/task; output.mkdir(parents=True)
    path=output/'research.md'; path.write_bytes(b'original report')
    result=dict(task_id=task,artifacts=[dict(path=str(path),sha256=a.sha(path))])
    if failure=='hash': result['artifacts'][0]['sha256']='0'*64
    elif failure=='bytes': path.write_bytes(b'tampered report')
    elif failure=='extra': (output/'extra.txt').write_bytes(b'extra effect')
    elif failure=='escape': result['artifacts'][0]['path']=str(folder/'outside.md')
    if failure=='none': assert a.verify_readback(folder,result,p4,'original report')[0]['text']=='original report'
    else:
        with pytest.raises(ValueError): a.verify_readback(folder,result,p4,'original report')

# Deadline correction: real P4 algorithms, caller-local clocks and I/O only.
class Clock:
    def __init__(self): self.value=1000000000000
    def __call__(self): return self.value
    def advance(self,seconds): self.value+=int(seconds*1000000000)

def test_deadline_preclaim_charged_parent_no_rebase():
    clock=Clock(); budget=a.Deadline(clock=clock); origin=budget.origin_ns
    clock.advance(12)
    assert budget.remaining_ns()==263000000000
    budget.adopt_parent(dict(origin_ns=origin-1000000000,clock_domain=a.CLOCK_DOMAIN,run_id=budget.run_id))
    assert budget.origin_ns==origin-1000000000
    with pytest.raises(ValueError): budget.adopt_parent(dict(origin_ns=clock(),clock_domain=a.CLOCK_DOMAIN,run_id=budget.run_id))

@pytest.mark.parametrize('offset,admitted',[(274999999999,True),(275000000000,False),(275000000001,False)])
def test_deadline_strict_admission_inclusive_return(offset,admitted):
    clock=Clock(); budget=a.Deadline(clock=clock); clock.value=budget.origin_ns+offset
    if admitted: budget.pre('work')
    else:
        with pytest.raises(TimeoutError): budget.pre('work')
    clock.value=budget.origin_ns+275000000000; budget.post('work')

def test_private_snapshot_timeouts_decrease_late_return_and_restore(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); original=p4.subprocess; calls=[]
    def checkout(argv,**kwargs):
        calls.append((argv,kwargs['timeout'])); clock.advance(8); return b'[]'
    monkeypatch.setattr(original,'check_output',checkout)
    clock.advance(255)
    with a.PrivateIO(p4,budget) as io:
        p4.process_snapshot(); p4.process_snapshot()
        with pytest.raises(TimeoutError): p4.process_snapshot()
    assert [round(x[1]) for x in calls]==[15,12,4]
    assert p4.subprocess is original

def test_real_popen_identity_wait_clipping_and_restoration():
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    import subprocess
    proc=object.__new__(subprocess.Popen); proc._handle=object(); handle=proc._handle
    calls=[]
    def wait(timeout=None): calls.append(timeout); return 0
    proc.wait=wait
    owned=types.SimpleNamespace(launchers=[dict(proc=proc)])
    with a.PrivateIO(p4,budget) as io:
        io.wrap_waits(owned); assert proc._handle is handle
        clock.advance(274); proc.wait(timeout=300)
    assert proc.wait is wait and calls==[1.0]

@pytest.mark.parametrize('seconds,entered',[(9.999999999,False),(10,True),(11,True)])
def test_termination_full_ten_second_admission(monkeypatch,seconds,entered):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); calls=[]
    # Admission boundary test; separate native test below exercises original P1.
    monkeypatch.setattr(p4,'terminate_owned',lambda key:calls.append(key))
    clock.value=budget.origin_ns+310000000000-int(seconds*1000000000)
    with a.PrivateIO(p4,budget) as io:
        if entered: p4.terminate_owned(dict(pid=7))
        else:
            with pytest.raises(TimeoutError): p4.terminate_owned(dict(pid=7))
    assert bool(calls)==entered

@pytest.mark.parametrize('code,closed',[(10061,True),(111,111 in {a.errno.ECONNREFUSED,10061}),(10060,False),(0,False)])
def test_private_port_probe_requires_definitive_refusal(monkeypatch,code,closed):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); probes=[]
    class Probe:
        def __init__(self): self.closed=False; probes.append(self)
        def settimeout(self,value): pass
        def connect_ex(self,address): return code
        def close(self): self.closed=True
    monkeypatch.setattr(p4.socket,'socket',Probe)
    with a.PrivateIO(p4,budget) as io:
        probe=p4.socket.socket(); probe.settimeout(1)
        try: probe.connect_ex(('127.0.0.1',18799))
        finally: probe.close()
        assert io.port_closed is closed
    assert probes[0].closed

@pytest.mark.parametrize('offset,expected',[(314999999999,True),(315000000000,True),(315000000001,False)])
def test_enclosing_witness_timely_exact315_late_and_permanent(offset,expected):
    clock=Clock(); budget=a.Deadline(clock=clock)
    observer=a.TimingObservation(budget)
    clock.value=budget.origin_ns+offset
    witness=observer.finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))
    assert witness['eligible'] is expected
    with pytest.raises(ValueError): observer.finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))

class NativeFunction:
    def __init__(self,function): self.function=function
    def __call__(self,*args): return self.function(*args)

def native_kernel(monkeypatch,p4,active,clock,wait_seconds=0):
    calls=[]
    def opened(access,inherit,pid): calls.append(('open',access,pid)); return pid+1000
    def times(handle,*values):
        for item in values: item._obj.dwLowDateTime=0; item._obj.dwHighDateTime=0
        values[0]._obj.dwLowDateTime=1000000+int(handle)-1000
        return 1
    def image(handle,flags,buffer,size): buffer.value=sys.executable; return 1
    def terminate(handle,code): calls.append(('terminate',int(handle)-1000)); active.discard(int(handle)-1000); return 1
    def wait(handle,milliseconds): calls.append(('wait',milliseconds)); clock.advance(wait_seconds); return 0
    kernel=types.SimpleNamespace(**{name:NativeFunction(func) for name,func in dict(OpenProcess=opened,CloseHandle=lambda h:calls.append(('close',h)),GetProcessTimes=times,QueryFullProcessImageNameW=image,TerminateProcess=terminate,WaitForSingleObject=wait).items()})
    monkeypatch.setattr(p4.old.C,'WinDLL',lambda *args,**kwargs:kernel)
    return kernel,calls

def test_original_p1_primitive_overrun_closes_handle_and_never_later_succeeds(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={77}
    kernel,calls=native_kernel(monkeypatch,p4,active,clock,wait_seconds=11)
    key=p4.identity(77); original=p4.old.terminate_owned
    clock.value=budget.origin_ns+299500000000
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(TimeoutError,match='Late'): p4.terminate_owned(key)
        assert io.events[-1]['entered'] and io.events[-1]['returned'] and io.events[-1]['late']
    assert ('wait',10000) in calls and calls[-1][0]=='close'
    assert p4.old.terminate_owned is original
    assert not a.TimingObservation(budget).finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))['eligible']

def test_original_p1_identity_mismatch_never_terminates(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={77}
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    key=dict(p4.identity(77),created_filetime=1)
    with a.PrivateIO(p4,budget):
        with pytest.raises(ValueError,match='identity mismatch'): p4.terminate_owned(key)
    assert not any(call[0]=='terminate' for call in calls)

@pytest.mark.parametrize('count',[2,4,7])
def test_real_p4_cleanup_native_snapshot_and_original_termination(tmp_path,monkeypatch,count):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active=set(range(10,10+count))
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    observed=[]
    def checkout(argv,**kwargs):
        observed.append((argv,kwargs['timeout'])); clock.advance(.1)
        return json.dumps([dict(ProcessId=pid,ParentProcessId=0,CommandLineBase64='') for pid in sorted(active)]).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    for pid in active: owned.known[pid]=dict(identity=p4.identity(pid),role='server',argv=[],parent=0)
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='PASS' and result['port_definitively_closed']
    assert len([c for c in calls if c[0]=='terminate'])==count
    assert not active and observed
    assert all(x[1]<=15 for x in observed)

def test_launch_registration_failure_retains_possible_effect_and_wraps_wait(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    import subprocess
    proc=object.__new__(subprocess.Popen); proc.pid=999; proc._handle=object(); handle=proc._handle; proc.wait=lambda timeout=None:0
    original_wait=proc.wait
    monkeypatch.setattr(helper,'launch',lambda *args:proc)
    # Real discover fails at the OS snapshot boundary after original registration.
    monkeypatch.setattr(p4.subprocess,'check_output',lambda *args,**kwargs: (_ for _ in ()).throw(OSError('snapshot unavailable')))
    owned=p4.Owned(tmp_path,{})
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(OSError): io.launch(owned,['-B','script'],'server')
        assert proc.wait is not original_wait and proc._handle is handle
        assert io.launch_attempts[0]['possible_live_effect'] and len(owned.launchers)==1
    assert proc.wait is original_wait
    for stream in owned.logs: stream.close()

def test_launch_failure_before_registration_retains_unknown_live_effect(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    monkeypatch.setattr(helper,'launch',lambda *args: (_ for _ in ()).throw(OSError('creation outcome unknown')))
    owned=p4.Owned(tmp_path,{})
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(OSError): io.launch(owned,['-B','script'],'server')
        assert not owned.known and io.launch_attempts[0]['possible_live_effect']
    for stream in owned.logs: stream.close()

def test_readiness_late_listener_cannot_dispatch(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); proofs=[]
    def listener(port): clock.advance(31); return [1]
    monkeypatch.setattr(p4,'listener_owner',listener); monkeypatch.setattr(p4,'assert_listener',lambda *args:proofs.append(args))
    with pytest.raises(TimeoutError,match='Late listener'): a.ready_listener(p4,None,18799,[],budget)
    assert not proofs

@pytest.mark.parametrize('failure',['missing_snapshot','log_close','socket_timeout'])
def test_cleanup_uncertainty_is_never_pass(tmp_path,monkeypatch,failure):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    count=[]
    def checkout(*args,**kwargs):
        count.append(1)
        if failure=='missing_snapshot' and len(count)>1: raise OSError('snapshot missing')
        return b'[]'
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return 10060 if failure=='socket_timeout' else a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    if failure=='log_close':
        class BadLog:
            closed=False
            def close(self): raise OSError('close failed')
        owned.logs=[BadLog()]
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='FAIL'

def test_private_bindings_shared_identity_survives_two_exception_scopes():
    import subprocess,time,socket
    p4=a.load_p4(); original=(subprocess.check_output,time.monotonic,time.sleep,socket.socket,p4.old.terminate_owned)
    for _ in range(2):
        fresh=a.load_p4(); saved=(fresh.subprocess,fresh.time,fresh.socket,fresh.terminate_owned,fresh.save)
        with pytest.raises(RuntimeError):
            with a.PrivateIO(fresh,a.Deadline()): raise RuntimeError('scope failure')
        assert saved==(fresh.subprocess,fresh.time,fresh.socket,fresh.terminate_owned,fresh.save)
        assert original==(subprocess.check_output,time.monotonic,time.sleep,socket.socket,p4.old.terminate_owned)

@pytest.mark.parametrize('missing,late',[('none',False),('seal-index.json',False),('data',False),('none',True)])
def test_root_observes_closed_package_after_return_no_missing_or_late_promotion(tmp_path,missing,late):
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget; p4=a.load_p4()
    required={'attempt.json','argv-roundtrip.json','native-argv.json','native-argv.raw','listener.json','owned-tree.json','cleanup.json','protected-before.json','protected-after.json','server.stdout','server.stderr'}
    def entry():
        b.phase='seal'
        for name in required: a.save_new(tmp_path/name,{})
        terminal=dict(kind='inert',folder=str(tmp_path),run_id=b.run_id,overall='READY_FOR_ROOT_TIMING_WITNESS',cleanup=dict(status='PASS',port_definitively_closed=True,logs_closed=True),errors=[])
        a.save_new(tmp_path/'terminal.json',terminal); a.seal_index(tmp_path,b,p4)
        if missing=='seal-index.json': (tmp_path/'seal-index.json').unlink()
        if missing=='data': (tmp_path/'native-argv.raw').unlink()
        clock.value=b.origin_ns+(315000000001 if late else 314999999999)
        return terminal
    observed=invocation.call(entry)
    assert observed['witness']['eligible'] is False  # Empty member objects are never substantive proof.
    assert observed['witness']['observed_ns']==clock()
    with pytest.raises(ValueError): invocation.call(lambda:observed['result'])

def test_missing_witness_or_uncertain_proof_never_eligible():
    for key in ('cleanup','closed','pins','protected','readback'):
        proof=dict(cleanup=True,closed=True,pins=True,protected=True,readback=True); proof.pop(key)
        assert not a.TimingObservation(a.Deadline()).finish('digest',proof)['eligible']
    assert not a.TimingObservation(a.Deadline()).finish(None,dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))['eligible']

def test_client_at_work_cutoff_retains_first_result_but_cannot_validate_or_pass(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); processes=[]
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable))
    monkeypatch.setattr(p4,'process_times',lambda proc:(100,0))
    def checkout(argv,**kwargs): return '7891' if 'Get-NetTCPConnection' in argv[-1] else b'[]'
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    monkeypatch.setattr(a,'check_inputs',lambda:{})
    monkeypatch.setattr(a,'check_native_baseline',lambda *args:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    class Proc:
        returncode=0
        def __init__(self,pid): self.pid=pid; self._handle=object()
        def wait(self,timeout=None):
            if self.pid==7892 and timeout>3: clock.value=budget.cutoff_ns('work')
            return 0
    def launch(argv,env,out,err):
        proc=Proc(7892 if '--research' in argv else 7891); processes.append(proc)
        if '--research' in argv: out.write(json.dumps(dict(status='succeeded',marker='first',request_id='r',session_id='s'))); out.flush()
        return proc
    monkeypatch.setattr(helper,'launch',launch)
    context=dict(folder=tmp_path,port=18799,request_id='r',session_id='s',baseline={},authority={},ledger={},budget=budget)
    result=a.execute_case(context,p4)
    assert result['overall']=='FAIL' and result['work_cli_attempts']==1
    assert 'Deadline' in result['first_failure']
    assert result['effective_client_seconds']==275
    assert a.load(tmp_path/'product-result.json')['marker']=='first'
    assert (tmp_path/'first-product.raw').exists()
    assert result['timing_eligibility']=='UNOBSERVED_NEVER_TIMED_PASS'

def test_cleanup_discovers_later_matching_child_without_count_truncation(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={10,11}
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    argv=['-B','samecase']; command=json.dumps([sys.executable,*argv])
    monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text))
    monkeypatch.setattr(p4,'process_times',lambda proc:(1000010,0))
    def checkout(argv,**kwargs):
        import base64
        return json.dumps([dict(ProcessId=pid,ParentProcessId=10 if pid==11 else 0,CommandLineBase64=base64.b64encode(command.encode('utf-16-le')).decode('ascii')) for pid in sorted(active)]).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    proc=types.SimpleNamespace(pid=10,wait=lambda timeout=None:0)
    owned=p4.Owned(tmp_path,{})
    owned.launchers=[dict(proc=proc,identity=p4.identity(10),argv=argv,role='server')]
    owned.known[10]=dict(identity=p4.identity(10),argv=argv,role='server',parent=0)
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='PASS' and 11 in owned.known
    assert len([c for c in calls if c[0]=='terminate'])==2

@pytest.mark.parametrize('failure',['nested','drift'])
def test_private_cleanup_unknown_nested_or_reused_identity_never_authorizes_kill(tmp_path,monkeypatch,failure):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={11,12} if failure=='nested' else {11}
    kernel,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4.subprocess,'check_output',lambda *args,**kwargs:json.dumps([dict(ProcessId=pid,ParentProcessId=11 if pid==12 else 0,CommandLineBase64='') for pid in sorted(active)]).encode('ascii'))
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    owned.known[11]=dict(identity=p4.identity(11),argv=[],role='server',parent=0)
    if failure=='drift': owned.known[11]['identity']['created_filetime']-=1
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='FAIL'
    assert (12 if failure=='nested' else 11) in active
    assert ('terminate',12 if failure=='nested' else 11) not in calls

def test_clipped_wait_preserves_timeout_exception_and_private_sleep_overshoot(monkeypatch):
    import subprocess
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    proc=types.SimpleNamespace(_handle=object())
    def wait(timeout=None): raise subprocess.TimeoutExpired('unchanged command',timeout)
    proc.wait=wait
    fake_time=types.SimpleNamespace(monotonic=lambda:clock()/1000000000,sleep=lambda seconds:clock.advance(seconds+1))
    monkeypatch.setattr(p4,'time',fake_time)
    with a.PrivateIO(p4,budget) as io:
        io.wrap_waits(types.SimpleNamespace(launchers=[dict(proc=proc)]))
        with pytest.raises(subprocess.TimeoutExpired) as caught: proc.wait(timeout=3)
        assert caught.value.timeout==3 and caught.value.cmd=='unchanged command'
        clock.value=budget.cutoff_ns()-1000000000
        with pytest.raises(TimeoutError,match='Late'): p4.time.sleep(2)
    assert proc.wait is wait and p4.time is fake_time

def test_fix1_h05_unrelated_protected_five_rejected(monkeypatch):
    p4=a.load_p4(); unrelated=[dict(pid=p,created_filetime=100+p,exe='python') for p in range(1,6)]
    monkeypatch.setattr(p4,'identity',lambda pid:unrelated[pid-1])
    monkeypatch.setattr(p4,'protected',lambda:[dict(pid=p,created_filetime=100+p,exe='python') for p in range(11,16)])
    proof=dict(precision='FILETIME100ns',candidate=a.CANDIDATE,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=unrelated)
    with pytest.raises(ValueError,match='protected member'): a.check_native_baseline(proof,p4)

def test_fix1_h06_alternate_interpreter_same_flags_rejected(monkeypatch):
    monkeypatch.setattr(sys,'executable','C:/other/python.exe')
    with pytest.raises(ValueError,match='interpreter'): a.check_inputs()

@pytest.mark.parametrize('fault',['flags','identity','attempt','replay','none'])
def test_fix1_h01_one_use_native_child_clearance(tmp_path,monkeypatch,fault):
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4()
    key=dict(pid=77,created_filetime=123,exe=sys.executable)
    monkeypatch.setattr(p4,'identity',lambda pid:key)
    context=dict(folder=tmp_path,port=18799,budget=b,mode='inert',authority={},request_id='r',session_id='s')
    a.save_new(tmp_path/'attempt.json',dict(parent_timing=b.timing()))
    argv=a.inert_argv(tmp_path,18799)
    record=dict(mode='inert',folder=str(tmp_path),timing=b.timing(),argv=argv,attempt_sha256=a.sha(tmp_path/'attempt.json'),authority_sha256='authority',members=[dict(identity=key,role='server',parent=1)])
    a.save_new(tmp_path/'child-clearance.json',record)
    supplied=list(argv)
    if fault=='flags': supplied.remove('--runtime-root')
    elif fault=='identity': monkeypatch.setattr(p4,'identity',lambda pid:dict(key,created_filetime=124))
    elif fault=='attempt': (tmp_path/'attempt.json').write_text('{}')
    elif fault=='replay': a.save_new(tmp_path/'child-clearance.consumed.json',{})
    if fault=='none': assert a.consume_clearance(context,p4,supplied,'authority')==key
    else:
        with pytest.raises((ValueError,FileExistsError)): a.consume_clearance(context,p4,supplied,'authority')

@pytest.mark.parametrize('rows',['empty','subset','parent','none'])
def test_fix1_h04_native_member_set_not_vacuous(tmp_path,monkeypatch,rows):
    p4=a.load_p4(); root=dict(pid=1,created_filetime=101,exe=sys.executable); child=dict(pid=2,created_filetime=102,exe=sys.executable)
    monkeypatch.setattr(p4,'identity',lambda pid:{1:root,2:child}[pid]); monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text)); monkeypatch.setattr(p4,'process_times',lambda proc:(101,0))
    argv=['-B','script']; owned=types.SimpleNamespace(known={1:dict(identity=root,role='server',parent=0),2:dict(identity=child,role='server',parent=1)},launchers=[dict(proc=types.SimpleNamespace(pid=1),identity=root,argv=argv,role='server')])
    snapshot={1:dict(ParentProcessId=0,CommandLine=json.dumps([sys.executable,*argv])),2:dict(ParentProcessId=99 if rows=='parent' else 1,CommandLine=json.dumps([sys.executable,*argv]))}
    if rows=='empty': snapshot={}
    elif rows=='subset': snapshot.pop(1)
    listener=dict(identity=child,argv=argv,role='server')
    if rows=='none': assert a.validate_native_members(owned,p4,snapshot,listener,argv)['live_pids']==[1,2]
    else:
        with pytest.raises(ValueError): a.validate_native_members(owned,p4,snapshot,listener,argv)

def test_fix1_h12_socket_timeout_reclipped_at_connect(monkeypatch):
    clock=Clock(); b=a.Deadline(clock=clock); b.phase='cleanup'; clock.value=b.cutoff_ns()-1000000000
    p4=a.load_p4(); waits=[]
    class Probe:
        def __init__(self): clock.advance(.8)
        def settimeout(self,value): waits.append(value)
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    with a.PrivateIO(p4,b) as io:
        probe=p4.socket.socket(); probe.settimeout(1)
        try: probe.connect_ex(('127.0.0.1',18799))
        finally: probe.close()
    assert waits[-1]==pytest.approx(.2)

@pytest.mark.parametrize('field',['request_id','session_id','task_id','status','artifacts','none'])
def test_fix1_h13_service_cli_invariants(field):
    first=dict(request_id='r',session_id='s',task_id='t',status='succeeded',artifacts=[dict(path='p',sha256='h',verified=True)])
    service=json.loads(json.dumps(first))
    if field!='none': service[field]=[] if field=='artifacts' else 'different'
    if field=='none': a.reconcile_results(first,service)
    else:
        with pytest.raises(ValueError,match='service/CLI'): a.reconcile_results(first,service)

def test_fix1_h08_first_cause_cleanup_then_boundary_never_replaced():
    b=a.Deadline(); errors=[]
    a.record_failure(b,errors,'cleanup','returned FAIL',effects_unknown=True)
    a.record_failure(b,errors,'final-boundary','later drift')
    assert b.failure=='cleanup: returned FAIL' and errors[0]['effects_unknown']

def test_fix1_h14_observer_late_first_read_stops_following_io(tmp_path,monkeypatch):
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget; reads=[]
    def read(path): reads.append(path); clock.value=b.cutoff_ns('seal')+1; return {}
    monkeypatch.setattr(a,'load',read)
    outcome=invocation.call(lambda:dict(folder=str(tmp_path)))
    assert len(reads)==1 and not outcome['witness']['eligible']

def test_fix1_genuine_synthetic_export_and_external_readback(tmp_path,monkeypatch,sdk_io,mock_jar):
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch)
    verified=a.verify_exports(tmp_path,result,a.load_p4())
    assert verified['native_POST_attempts']==5 and len(verified['inventory'])==1
    assert a.read_completed(tmp_path,a.load(tmp_path/'trusted-export.json'))['runtime']==ledger._runtime_final

@pytest.mark.parametrize('size',[3*1024*1024,4*1024*1024])
def test_fix1_h07_sizable_and_max_safe_raw_representation(tmp_path,monkeypatch,sdk_io,mock_jar,size):
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    empty=json.dumps(dict(events=[],padding=''),separators=(',',':')).encode()
    raw=json.dumps(dict(events=[],padding='a'*(size-len(empty))),separators=(',',':')).encode()
    # Representation unit after a safe-completion boundary; this padded packet
    # is not claimed to be a valid product replay. The genuine companion above is.
    a.preserve_completed_members(tmp_path,raw,ledger.issued_snapshot,ledger._collection,result,5)
    exported=a.load(tmp_path/'trusted-export.json')
    assert len(raw)==size and a.read_completed(tmp_path,exported)['runtime']==raw
    assert (tmp_path/'trusted-export.json').stat().st_size<4096

def test_fix1_h07_unsafe_completed_values_never_exported(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.work_navigation import canonical_v3
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final); packet['wires'][-1]['raw_response']=escaped_scanner_fixture()
    ledger._runtime_final=canonical_v3(packet)
    with pytest.raises(ValueError): a.export_completed(tmp_path,ledger,result)
    assert not list(tmp_path.glob('trusted-*.raw'))

@pytest.mark.parametrize('fault',['remove','replace','extra'])
def test_fix1_h03_closed_output_drift_rejected(tmp_path,fault):
    p4=a.load_p4(); task='12345678-1234-4234-8234-123456789abc'; output=tmp_path/'outputs'/task; output.mkdir(parents=True)
    path=output/'research.md'; path.write_bytes(b'accepted')
    result=dict(task_id=task,artifacts=[dict(path=str(path),sha256=a.sha(path))]); accepted=p4.output_inventory(tmp_path)
    if fault=='remove': path.unlink()
    elif fault=='replace': path.write_bytes(b'changed')
    else: (output/'extra.md').write_bytes(b'extra')
    with pytest.raises(ValueError,match='output drift'): a.validate_final_outputs(tmp_path,result,accepted,p4)

@pytest.mark.parametrize('which',['harness','approval','authority','baseline'])
def test_fix1_h09_late_operational_drift_rejected(tmp_path,monkeypatch,which):
    paths=[]
    for name in ('harness','approval','authority','baseline'):
        path=tmp_path/name; path.write_text(name); paths.append(path)
    monkeypatch.setattr(a,'check_inputs',lambda:{})
    monkeypatch.setattr(a,'operational_paths',lambda mode:paths)
    budget=a.Deadline(); admitted=dict(mode='inert',pins=a.operational_pins('inert',budget))
    (tmp_path/which).write_text('late drift')
    with pytest.raises(ValueError,match='pin drift'): a.compare_operational_pins(admitted,budget)

def test_fix1_h06_cached_sdk_import_origin_rejected(monkeypatch):
    fake=types.ModuleType('openjarvis.agents.native_react'); fake.__file__='C:/unapproved/native_react.py'
    monkeypatch.setitem(sys.modules,'openjarvis.agents.native_react',fake)
    with pytest.raises(ValueError,match='Import origin'): a.check_import_origins()

@pytest.mark.parametrize('fault',['harness','input','addition','none'])
def test_fix1_h10_driver_drift_fails_even_with_pytest_zero(tmp_path,monkeypatch,fault):
    spec=importlib.util.spec_from_file_location('driver_control',Path(__file__).with_name('run_checks.py'))
    driver=importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
    here=tmp_path/'harness'; here.mkdir(); input_file=tmp_path/'input'; input_file.write_bytes(b'original')
    for source in Path(__file__).parent.iterdir():
        if source.is_file(): (here/source.name).write_bytes(source.read_bytes())
    monkeypatch.setattr(driver,'HERE',here); monkeypatch.setattr(driver,'V',tmp_path)
    monkeypatch.setattr(driver,'snapshot',lambda:{str(input_file):driver.digest(input_file)})
    monkeypatch.setattr(sys,'argv',['run_checks.py','adapter'])
    def pytest_process(*args,**kwargs):
        if fault=='harness': (here/'README.md').write_bytes(b'changed')
        elif fault=='input': input_file.write_bytes(b'changed')
        elif fault=='addition': (here/'seventh.txt').write_bytes(b'extra')
        return types.SimpleNamespace(returncode=0,stdout=b'controlled pytest success',stderr=b'')
    monkeypatch.setattr(driver.subprocess,'run',pytest_process)
    status=driver.main(); receipt=a.load(next((tmp_path/'code').glob('harness-preparation-*/receipt.json')))
    assert (status==0)==(fault=='none') and receipt['pytest_exit_code']==0
    assert receipt['exit_code']==status

def test_fix1_h11_import_path_restored_on_failure():
    original=list(sys.path)
    with pytest.raises(ValueError):
        with a.candidate_import_path():
            assert sys.path[0]==str(a.C); raise ValueError('injected')
    assert sys.path==original

@pytest.mark.parametrize('fault',['none','protected-empty','native-subset','cleanup-subset'])
def test_fix1_h02_substantive_closed_witness_positive_and_faults(tmp_path,monkeypatch,fault):
    import base64,os
    from collections import OrderedDict
    original_v=a.V; original_here=a.HERE
    virtual=tmp_path/'virtual-root'; here=virtual/'harness'; here.mkdir(parents=True)
    for source in original_here.iterdir():
        if source.is_file(): (here/source.name).write_bytes(source.read_bytes())
    for name in ('source10-candidate-manifest.json','harness-preparation-authority.json'):
        (virtual/name).write_bytes((original_v/name).read_bytes())
    (virtual/'harness-deadline-design').mkdir()
    (virtual/'harness-deadline-design/root-decision.json').write_bytes((original_v/'harness-deadline-design/root-decision.json').read_bytes())
    monkeypatch.setattr(a,'V',virtual); monkeypatch.setattr(a,'HERE',here)
    package=a.load(here/'manifest.json')
    package['files']={name:a.sha(here/name) for name in package['files']}
    (here/'manifest.json').write_text(json.dumps(package),encoding='utf8')
    a.save_new(virtual/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=a.sha(here/'manifest.json')))
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget
    folder=virtual/'inert'/b.run_id; folder.mkdir(parents=True)
    p4=a.load_p4(); active=set(); _,calls=native_kernel(monkeypatch,p4,active,clock)
    protected=[p4.identity(pid) for pid in range(51,56)]
    monkeypatch.setattr(p4,'protected',lambda:protected)
    monkeypatch.setattr(p4,'process_times',lambda proc:(1000001,0))
    monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text))
    monkeypatch.setattr(a,'load_p4',lambda:p4)
    authority=dict(kind='source10_inert_qualification',folder=str(folder),port=18799,parent_timing=b.timing())
    a.save_new(virtual/'inert-authority.json',authority)
    baseline=dict(protected=protected,candidate=a.CANDIDATE,precision='FILETIME100ns',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
    a.save_new(virtual/'inert-native-baseline.json',baseline)
    argv=a.inert_argv(folder,18799); snapshot_live=[True]
    command=json.dumps([str(a.PY),*argv])
    def checkout(cmd,**kwargs):
        if 'Get-NetTCPConnection' in cmd[-1]: return '[]'
        rows=[dict(ProcessId=pid,ParentProcessId=0 if pid==1 else 1,CommandLineBase64=base64.b64encode(command.encode('utf-16-le')).decode('ascii')) for pid in (1,2)] if snapshot_live[0] else []
        return json.dumps(rows).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    def entry():
        admitted=a.admitted_record('inert',folder,18799,authority,baseline,b)
        a.save_new(folder/'admission.json',admitted)
        a.save_new(folder/'attempt.json',dict(parent_timing=b.timing()))
        owned=p4.Owned(folder,{}); b.owned=owned
        proc=types.SimpleNamespace(pid=1,wait=lambda timeout=None:0)
        owned.launchers=[dict(proc=proc,identity=p4.identity(1),argv=argv,role='server')]
        owned.known[1]=dict(identity=p4.identity(1),argv=argv,role='server',parent=0)
        owned.logs=[open(folder/'server.stdout','w'),open(folder/'server.stderr','w')]
        context=dict(mode='inert',folder=folder,port=18799,budget=b)
        with a.PrivateIO(p4,b) as io:
            a.issue_clearance(context,p4,owned,argv,a.sha(virtual/'inert-authority.json'))
            identity=p4.identity
            with monkeypatch.context() as child:
                child.setattr(p4,'identity',lambda pid:identity(2) if pid==os.getpid() else identity(pid))
                a.consume_clearance(context,p4,argv,a.sha(virtual/'inert-authority.json'))
            listener=dict(port=18799,identity=identity(2),role='server',argv=argv)
            a.save_new(folder/'listener.json',listener)
            a.record_native_members(folder,p4,owned,argv,b)
            a.save_new(folder/'argv-roundtrip.json',dict(question=a.corpus()['query'],argv=argv[4:]))
            for name in ('protected-before.json','protected-after.json'): a.save_new(folder/name,protected)
            for name in ('boundary-before.json','boundary-after.json'): a.save_new(folder/name,dict(pins=admitted['pins'],protected=protected))
            snapshot_live[0]=False
            cleanup=io.cleanup(owned,18799)
        if fault=='protected-empty': (folder/'protected-after.json').write_text('[]')
        elif fault=='native-subset':
            malformed=a.load(folder/'native-members.json'); malformed['snapshot'].pop('1')
            (folder/'native-members.json').write_text(json.dumps(malformed))
        elif fault=='cleanup-subset':
            malformed=a.load(folder/'cleanup.json'); malformed['processes'].pop()
            (folder/'cleanup.json').write_text(json.dumps(malformed))
        b.phase='seal'
        terminal=dict(kind='inert',folder=str(folder),run_id=b.run_id,timing=b.timing(),overall='READY_FOR_ROOT_TIMING_WITNESS',cleanup=cleanup,errors=[],first_failure=None)
        a.save_new(folder/'terminal.json',terminal); a.seal_index(folder,b,p4)
        return terminal
    outcome=invocation.call(entry)
    assert outcome['witness']['eligible']==(fault=='none'),outcome['witness']
    if fault=='none':
        assert outcome['witness']['seal_index_sha256']==a.sha(folder/'seal-index.json')
        assert outcome['witness']['member_hashes'] and outcome['witness']['kind']=='inert'

@pytest.mark.parametrize('fault',['missing-isolated','port','extra-policy','duplicate','none'])
def test_fix1_h01_actual_child_entry_dispatch_is_canonical_once(tmp_path,monkeypatch,fault):
    import ddgs,httpx,socket
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4(); key=dict(pid=77,created_filetime=123,exe=str(a.PY))
    monkeypatch.setattr(p4,'identity',lambda pid:key)
    context=dict(mode='actual',folder=tmp_path,port=18799,budget=b,request_id='r',session_id='s')
    a.save_new(tmp_path/'attempt.json',dict(parent_timing=b.timing()))
    argv=a.candidate_argv(context)[0]
    a.save_new(tmp_path/'child-clearance.json',dict(mode='actual',folder=str(tmp_path),timing=b.timing(),argv=argv,attempt_sha256=a.sha(tmp_path/'attempt.json'),authority_sha256='authority',members=[dict(role='server',identity=key,parent=1)]))
    supplied=list(argv)
    if fault=='missing-isolated': supplied.remove('--isolated')
    elif fault=='port': supplied[supplied.index('--port')+1]='11434'
    elif fault=='extra-policy': supplied+=['--work-target-policy','unapproved.json']
    elif fault=='duplicate': supplied+=['--child-server',str(tmp_path)]
    calls=[]; old_args=list(sys.argv); old_paths=list(sys.path)
    for obj,name in ((ddgs,'DDGS'),(httpx,'request'),(socket,'getaddrinfo'),(WorkLedger,'__init__'),(WorkLedger,'_freeze_runtime_inputs'),(WorkService,'submit_work')):
        monkeypatch.setattr(obj,name,getattr(obj,name))
    def dispatched(name,**kwargs): calls.append((name,list(sys.argv)))
    if fault=='none':
        a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert calls==[('src.brain.agent_server',['src.brain.agent_server',*argv[6:]])]
        with pytest.raises(FileExistsError): a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert len(calls)==1
    else:
        with pytest.raises(ValueError): a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert not calls and not (tmp_path/'child-clearance.consumed.json').exists()
    assert sys.argv==old_args and sys.path==old_paths
