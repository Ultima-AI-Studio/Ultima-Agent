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
    native.inspect();folder=tmp_path/'actual/e03-round1';folder.mkdir(parents=True);native.start(folder)


def test_original_fixture_server_cli_path_and_final_revalidation_order(tmp_path):
    native,calls=backend(tmp_path)
    with pytest.raises(FileNotFoundError):native.controller.source_check()
    start(native,tmp_path)
    result=native.product(lambda:calls.append(('revalidate',)))
    assert result=={'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}
    native.effects();assert native.close()['status']=='PASS';assert native.audit()['status']=='PASS'
    launches=[row for row in calls if row[0]=='launch']
    assert [row[1] for row in launches]==['fixture','server','cli']
    cli=launches[-1][2]
    assert cli[:6]==['-B','-m','src.brain.cli','--work','--current-window','--replace-selection']
    assert cli[-1]=='original fixed request'
    assert calls.index(('revalidate',))<calls.index(('activate',))<calls.index(('observe','dispatch-baseline'))<calls.index(launches[-1])
    assert ('wait',315) in calls and ('reconcile',) in calls and native.cli_count==1
    argv=json.loads((tmp_path/'actual/e03-round1/argv.json').read_text(encoding='utf-8'))
    assert (argv['CLI_timeout'],argv['SDK_timeout'],argv['controller_wait'])==(300,1800,315)


@pytest.mark.parametrize('drift',['text','identity','selection'])
def test_changed_dispatch_baseline_refuses_before_cli(tmp_path,drift):
    native,calls=backend(tmp_path,drift=drift);start(native,tmp_path)
    with pytest.raises(ValueError):native.product(lambda:None)
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
    with pytest.raises(ValueError,match='expired proof'):native.product(reject)
    assert ('activate',) not in calls and native.cli_count==0
    native.effects();native.close()


def test_uninspected_backend_cannot_start_fixture(tmp_path):
    native,calls=backend(tmp_path);folder=tmp_path/'actual/e03-round1';folder.mkdir(parents=True)
    with pytest.raises(ValueError,match='preflight'):native.start(folder)
    assert calls==[]


def test_stop_marker_error_still_attempts_reviewed_owned_cleanup(tmp_path,monkeypatch):
    native,calls=backend(tmp_path);start(native,tmp_path)
    (native.folder/'stop').touch()
    def fail_touch():raise OSError('stop marker write failed')
    module=importlib.import_module('acceptance_backend')
    monkeypatch.setattr(module,'safe_path',lambda path:SimpleNamespace(touch=fail_touch))
    result=native.close()
    assert result['status']=='FAIL' and result['stop_error']
    assert any(row[0]=='cleanup' for row in calls)
