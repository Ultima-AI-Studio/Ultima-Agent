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

def documents():
    now=dt.datetime.now(dt.timezone.utc)
    authority=dict(schema=10,kind='source10_execution',issuer='root',case='E02-controlled-1',candidate='118ba152b007c30d358c8bc44c51aabe8ae820f0',candidate_manifest_sha256='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50',issued_at=now.isoformat(),expires_at=(now+dt.timedelta(seconds=90)).isoformat(),budgets=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,outer_seconds=315,retry=0),native_precision='FILETIME100ns',actual=True)
    ledger=dict(schema=10,released_case='E02-controlled-1',consumed=['E02-controlled-1'],attempts=1,retry=0)
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

@pytest.mark.parametrize('failure',['timeout','nonzero','invalidJSON','partialpacket','missingEND','cleanup'])
def test_adapter_first_failure_retained_and_no_next_case(tmp_path,monkeypatch,failure):
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
        def connect_ex(self,address): return 1
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    a.save_new(tmp_path/'runtime-inputs.json',{})
    a.save_new(tmp_path/'trusted-export.json',dict(complete=failure!='missingEND',END=failure!='missingEND',runtime_final='e30=',issued_snapshot={}))
    monkeypatch.setattr(a,'check_inputs',lambda: {})
    monkeypatch.setattr(a,'check_native_baseline',lambda *args: [])
    launches=[]
    class Proc:
        pid=7890; returncode=2 if failure=='nonzero' else 0
        def wait(self,timeout=None):
            if failure=='timeout' and timeout and timeout>3: raise TimeoutError('CLI timeout')
            return self.returncode
    def launch(argv,env,out,err):
        launches.append(argv)
        if '--research' in argv: out.write('{broken' if failure=='invalidJSON' else json.dumps(dict(status='failed' if failure=='nonzero' else 'succeeded',marker='first',request_id='r',session_id='s'))); out.flush()
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
