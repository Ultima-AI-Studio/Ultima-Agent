import ast
import hashlib
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def put(path, value):
    path.write_text(json.dumps(value), encoding='utf-8')


def actual_function(path, name, namespace):
    tree=ast.parse(path.read_text(encoding='utf-8-sig'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name==name)
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<isolated actual '+name+'>','exec'),namespace)
    return namespace[name]


def backend(tmp_path, *, drift=None):
    module=importlib.import_module('acceptance_backend');entry=importlib.import_module('acceptance_entry')
    io=importlib.import_module('package_io');here=Path(__file__).parent
    (tmp_path/'inputs').mkdir()
    baseline=json.loads((here.parent/'inputs/protected-baseline.json').read_text(encoding='utf-8'))
    expected=baseline['protected5']+baseline['protected_listener_pair']
    commands={row['pid']:'test-command-'+str(i) for i,row in enumerate(expected)}
    for row in expected:row['command_line_sha256']=hashlib.sha256(commands[row['pid']].encode('utf-16le')).hexdigest()
    put(tmp_path/'inputs/protected-baseline.json',baseline)
    snapshots={row['pid']:dict(ProcessId=row['pid'],ParentProcessId=row['parent_pid'],
                              CreationFileTime=row['created_filetime'],CommandLine=commands[row['pid']]) for row in expected}
    if drift=='command':snapshots[expected[0]['pid']]['CommandLine']='changed'
    if drift=='cim':snapshots[expected[0]['pid']]['CreationFileTime']+=1000
    calls=[]
    def candidate():
        calls.append(('candidate',));return {'candidate':entry.HEAD,'candidate_manifest_sha256':entry.CANDIDATE_MANIFEST,
                                           'model_digest':entry.DIGEST,'code_gate':'PASS'}
    model_manifest=Path.home()/'.ollama/models/manifests/registry.ollama.ai/library'/entry.MODEL/'latest'
    tags={'models':[{'name':entry.MODEL,'digest':entry.DIGEST,'details':{'parameter_size':'8.2B'}}]}
    if drift=='model':tags['models'][0]['digest']='wrong'
    def get_json(url):
        calls.append(('get',url))
        if url.endswith('/api/version'):return {'version':'0.32.15'}
        if url.endswith('/api/tags'):return tags
        assert url=='http://127.0.0.1:18759/health'
        return {'ok':True,'model':entry.MODEL,'agent':'native_react'}
    old=SimpleNamespace(PROTECTED_BASELINE=None,E03_QUERY='original fixed request',
                        protected_entries=actual_function(here.parent/'preparation-support/acceptance_adapter.py','protected_entries',{}),
                        metadata_valid=actual_function(here.parent/'preparation-support/acceptance_adapter.py','metadata_valid',
                                                       {'MODEL':entry.MODEL,'DIGEST':entry.DIGEST,'hashlib':hashlib}),
                        source_check=candidate)
    targets=[dict(hwnd=i+1,control_hwnd=i+3,pid=12,process_created_filetime=99,title='fixture'+str(i),**{'class':'Edit'}) for i in range(2)]
    texts=['source','UNRELATED OWNED FIXTURE — DO NOT CHANGE']
    rows=[dict(t,text=texts[i],start_utf16=0,end_utf16=len(texts[i]) if i==0 else 0) for i,t in enumerate(targets)]
    class Owned:
        known={12:{'role':'fixture','identity':{'created_filetime':99}}}
        def launch(self,argv,role):
            calls.append(('launch',role,argv))
            if role=='fixture':
                put(self.folder/'fixture.json',{'pid':12,'targets':targets})
                initial=[]
                for i,t in enumerate(targets):
                    check={'verified':True,'utf16_units':len(texts[i]),'sha256_utf16le':hashlib.sha256(texts[i].encode('utf-16le')).hexdigest(),
                           'start_utf16':0,'end_utf16':len(texts[i]) if i==0 else 0}
                    initial.append(dict(index=i,hwnd=t['hwnd'],control_hwnd=t['control_hwnd'],before_activation=check,after_activation=check))
                put(self.folder/'fixture-initial-readback.json',{'status':'PASS','targets':initial})
                put(self.folder/'manual-start.json',dict(schema=1,status='ACCEPTED',pid=12,window_hwnd=targets[0]['hwnd'],
                    button_hwnd=77,keyboard_clear=True,cross_thread_attached=False,requested_by='owned_start_button',
                    ready_at='2026-11-05T12:00:00+00:00',accepted_at='2026-11-05T12:00:01+00:00',
                    timeout_seconds=15,elapsed_seconds=1))
            if role=='cli':put(self.folder/'cli.stdout',{'trace':[{'type':'inference_end','data':{'model':entry.MODEL}}]})
            return SimpleNamespace(returncode=0,wait=lambda timeout:calls.append(('wait',timeout)))
        def discover(self):calls.append(('discover',))
        def flush(self):calls.append(('flush',))
        def cleanup(self,port):
            assert (self.folder/'stop').exists();calls.append(('cleanup',port));return {'status':'PASS'}
    class Case:
        def __init__(self,case,folder,env):
            assert case==entry.CASE
            self.owned=Owned();self.owned.folder=folder;self.port=None;self.cli_count=0;self.result=None;self.fixture_ready=False
        def observe(self,label):
            calls.append(('observe',label));value=json.loads(json.dumps(rows))
            if label=='dispatch-baseline' and drift in ('text','identity','selection'):
                if drift=='text':value[0]['text']=''
                if drift=='identity':value[0]['pid']+=1
                if drift=='selection':value[0]['end_utf16']=0
            return value
        def command(self):calls.append(('activate',))
        def effects(self):calls.append(('effects',));return {'outputs':[],'windows':rows,'cli_count':self.cli_count}
    namespace={'old':old,'P':tmp_path/'code','load':io.load,'require':io.require,'sha':io.sha}
    controller=SimpleNamespace(ROOT=tmp_path/'candidate',old=old,Case=Case,
        candidate_guard=SimpleNamespace(verify_current_candidate=candidate),
        source_check=actual_function(here/'controller.py','source_check',namespace),
        snapshot_identity_matches=actual_function(here/'controller.py','snapshot_identity_matches',{}),
        protected=lambda:[{k:row[k] for k in ('pid','created_filetime','exe')} for row in expected],
        process_snapshot=lambda pids:snapshots, get_json=get_json,
        listener_owner=lambda port:[-1 if drift=='listener' else expected[0]['pid']],
        assert_listener=lambda *args:calls.append(('assert-listener',)),
        environment=lambda folder:{}, IDENTITY=('hwnd','control_hwnd','pid','process_created_filetime','title','class'),
        validate_fixture_readback=actual_function(here/'controller.py','validate_fixture_readback',{'require':io.require,'hashlib':hashlib}),
        fixture_command=actual_function(here/'controller.py','fixture_command',{'P':tmp_path/'code','ROOT':tmp_path/'candidate'}),
        validate_fixture_audit=lambda *args,**kwargs:dict(status='PASS'),
        read_artifacts=lambda *args:[],output_inventory=lambda folder:[],
        mechanical=lambda *args:dict(mechanical='PASS',facts='PENDING_ROOT_INDEPENDENT_REVIEW'),
        reconcile_effects=lambda *args:calls.append(('reconcile',)))
    old.wait_cli=actual_function(here.parent/'preparation-support/acceptance_adapter.py','wait_cli',{'CLI_TIMEOUT':315})
    harness=SimpleNamespace(CASES={'e03':{'text':'source'}},wait_for=lambda predicate,seconds:predicate())
    native=module.AcceptanceBackend(tmp_path,controller=controller,harness=harness,port_picker=lambda:18759,model_manifest=model_manifest)
    return native,calls


def start(native,tmp_path):
    native.inspect();folder=tmp_path/'actual/e03-round2';folder.mkdir(parents=True);native.start(folder)


def test_original_fixture_server_cli_path_and_final_revalidation_order(tmp_path):
    native,calls=backend(tmp_path)
    with pytest.raises(FileNotFoundError):native.controller.source_check()
    start(native,tmp_path)
    result=native.product(lambda:calls.append(('revalidate',)),lambda:calls.append(('admit-cli',)))
    assert result=={'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}
    native.effects();assert native.close()['status']=='PASS';assert native.audit()['status']=='PASS'
    launches=[row for row in calls if row[0]=='launch']
    assert [row[1] for row in launches]==['fixture','server','cli']
    cli=launches[-1][2]
    assert cli[:6]==['-B','-m','src.brain.cli','--work','--current-window','--replace-selection']
    assert cli[-1]=='original fixed request'
    assert calls.index(('revalidate',))<calls.index(('activate',))<calls.index(('observe','dispatch-baseline'))<calls.index(('admit-cli',))<calls.index(launches[-1])
    assert ('wait',315) in calls and ('reconcile',) in calls and native.cli_count==1
    argv=json.loads((tmp_path/'actual/e03-round2/argv.json').read_text(encoding='utf-8'))
    assert (argv['CLI_timeout'],argv['SDK_timeout'],argv['controller_wait'])==(300,1800,315)


@pytest.mark.parametrize('drift',['text','identity','selection'])
def test_changed_dispatch_baseline_refuses_before_cli(tmp_path,drift):
    native,calls=backend(tmp_path,drift=drift);start(native,tmp_path)
    with pytest.raises(ValueError):native.product(lambda:None,lambda:None)
    assert not any(row[:2]==('launch','cli') for row in calls)
    assert native.cli_count==0
    native.effects();assert native.close()['status']=='PASS'


@pytest.mark.parametrize('drift',['command','cim','model','listener'])
def test_native_protection_and_model_drift_stop_before_ui(tmp_path,drift):
    native,calls=backend(tmp_path,drift=drift)
    with pytest.raises(ValueError):native.inspect()
    assert not any(row[0]=='launch' for row in calls)


def test_failed_final_release_check_does_not_activate_or_submit(tmp_path):
    native,calls=backend(tmp_path);start(native,tmp_path)
    def reject():raise ValueError('expired proof')
    with pytest.raises(ValueError,match='expired proof'):native.product(reject,lambda:None)
    assert ('activate',) not in calls and native.cli_count==0
    native.effects();native.close()


def test_uninspected_backend_cannot_start_fixture(tmp_path):
    native,calls=backend(tmp_path);folder=tmp_path/'actual/e03-round2';folder.mkdir(parents=True)
    with pytest.raises(ValueError,match='preflight'):native.start(folder)
    assert calls==[]


@pytest.mark.parametrize('fault',['missing','pid','window','keyboard','automatic'])
def test_invalid_operator_handoff_refuses_before_baseline_or_product(tmp_path,fault):
    native,calls=backend(tmp_path);native.inspect()
    folder=tmp_path/'actual/e03-round2';folder.mkdir(parents=True)
    def ready(predicate,seconds):
        value=predicate();path=folder/'manual-start.json'
        if fault=='missing':path.unlink()
        else:
            data=json.loads(path.read_text(encoding='utf-8'))
            key,replacement={'pid':('pid',99),'window':('window_hwnd',99),'keyboard':('keyboard_clear',False),
                             'automatic':('requested_by','automatic')}[fault]
            data[key]=replacement;put(path,data)
        return value
    native.harness.wait_for=ready
    with pytest.raises((FileNotFoundError,ValueError)):native.start(folder)
    assert ('observe','baseline') not in calls and native.cli_count==0
    assert not any(row[:2]==('launch','server') for row in calls)


def test_stop_marker_error_still_attempts_reviewed_owned_cleanup(tmp_path,monkeypatch):
    native,calls=backend(tmp_path);start(native,tmp_path)
    (native.folder/'stop').touch()
    def fail_touch():raise OSError('stop marker write failed')
    module=importlib.import_module('acceptance_backend')
    monkeypatch.setattr(module,'safe_path',lambda path:SimpleNamespace(touch=fail_touch))
    result=native.close()
    assert result['status']=='FAIL' and result['stop_error']
    assert any(row[0]=='cleanup' for row in calls)


def test_persistent_stop_error_runs_actual_owned_cleanup_and_retains_failure(tmp_path,monkeypatch):
    import io
    import subprocess
    import time
    native,calls=backend(tmp_path);start(native,tmp_path)
    owner=native.context.owned
    tree=ast.parse((Path(__file__).parent/'controller.py').read_text(encoding='utf-8-sig'))
    cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='Owned')
    cleanup=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='cleanup')
    identities=[dict(pid=500+i,created_filetime=100+i,exe='owned-test.exe') for i in range(3)]
    live={row['pid']:row for row in identities};terminated=[];waited=[]
    def terminate(key):
        assert live[key['pid']]==key
        terminated.append(key);del live[key['pid']]
    namespace={'subprocess':subprocess,'time':time,'process_snapshot':lambda:dict(live),
               'terminate_owned':terminate,'require':importlib.import_module('package_io').require,'save':put}
    exec(compile(ast.Module(body=[cleanup],type_ignores=[]),'<actual Owned.cleanup>','exec'),namespace)
    owner.cleanup=lambda port:namespace['cleanup'](owner,port)
    owner.errors=[];owner.auxiliary={};owner.logs=[io.StringIO(),io.StringIO()]
    owner.known={row['pid']:{'identity':row} for row in identities}
    owner.launchers=[dict(role=role,proc=SimpleNamespace(pid=row['pid'],wait=lambda timeout:waited.append(timeout)))
                     for role,row in zip(('fixture','server','cli'),identities)]
    original_touch=Path.touch;attempts=[]
    def persistent_failure(path,*args,**kwargs):
        if path==native.folder/'stop':
            attempts.append(path);raise OSError('persistent marker write failure')
        return original_touch(path,*args,**kwargs)
    monkeypatch.setattr(Path,'touch',persistent_failure)
    result=native.close()
    assert result['status']=='FAIL' and len(attempts)==2
    assert terminated==identities and not live and len(waited)==4
    assert all(stream.closed for stream in owner.logs)
    receipt=json.loads((native.folder/'cleanup.json').read_text(encoding='utf-8'))
    assert receipt['status']=='FAIL' and all(row['absent'] for row in receipt['processes'])
    assert any('stop_marker_error' in row for row in receipt['errors'])


@pytest.mark.parametrize('phase',['command','observe'])
@pytest.mark.parametrize('gate',['proof','authority'])
def test_command_or_observe_expiry_denies_cli_using_real_admission(tmp_path,monkeypatch,phase,gate):
    import datetime as dt
    from test_acceptance_entry import NOW,package
    native,calls=backend(tmp_path)
    entry,authority,proof=package(tmp_path,monkeypatch)
    if gate=='authority':
        authority['expires_at']=(NOW+dt.timedelta(seconds=1)).isoformat()
        put(tmp_path/'release/authority.json',authority)
    initial=59 if gate=='proof' else 0;expired=61 if gate=='proof' else 2
    monkeypatch.setattr(entry,'utcnow',lambda:NOW+dt.timedelta(seconds=initial))
    native.inspected=True;native.inspect=lambda:proof
    original_start=native.start
    def slow_start(folder):
        original_start(folder)
        original_command=native.context.command;original_observe=native.context.observe
        def command():
            original_command()
            if phase=='command':monkeypatch.setattr(entry,'utcnow',lambda:NOW+dt.timedelta(seconds=expired))
        def observe(label):
            result=original_observe(label)
            if phase=='observe' and label=='dispatch-baseline':
                monkeypatch.setattr(entry,'utcnow',lambda:NOW+dt.timedelta(seconds=expired))
            return result
        native.context.command=command;native.context.observe=observe
    native.start=slow_start
    result=entry.run_once(tmp_path,backend_factory=lambda root:native)
    assert result['overall']=='FAIL' and result['work_cli_count']==0
    assert ('observe','dispatch-baseline') in calls
    assert not any(row[:2]==('launch','cli') for row in calls)
    assert result['cleanup']['status']=='PASS'
    assert json.loads((tmp_path/'release/preflight/test.json').read_text(encoding='utf-8'))==proof


@pytest.mark.parametrize('change',['binding','clock_during_check'])
def test_final_submission_check_rechecks_binding_and_samples_time_after_reads(tmp_path,monkeypatch,change):
    import datetime as dt
    from test_acceptance_entry import NOW,package
    native,calls=backend(tmp_path);entry,authority,proof=package(tmp_path,monkeypatch)
    native.inspected=True;native.inspect=lambda:proof
    original_start=native.start;verify=entry.verify_package
    def start_and_change(folder):
        original_start(folder);observe=native.context.observe
        def modified(label):
            result=observe(label)
            if label=='dispatch-baseline':
                if change=='binding':
                    authority['scope']='fixture-only-diagnostic';put(tmp_path/'release/authority.json',authority)
                else:
                    def slow_verify(root):
                        value=verify(root)
                        monkeypatch.setattr(entry,'utcnow',lambda:NOW+dt.timedelta(seconds=61))
                        return value
                    monkeypatch.setattr(entry,'verify_package',slow_verify)
            return result
        native.context.observe=modified
    native.start=start_and_change
    result=entry.run_once(tmp_path,backend_factory=lambda root:native)
    assert result['overall']=='FAIL' and result['work_cli_count']==0
    assert ('observe','dispatch-baseline') in calls
    assert not any(row[:2]==('launch','cli') for row in calls)
    assert result['cleanup']['status']=='PASS'
