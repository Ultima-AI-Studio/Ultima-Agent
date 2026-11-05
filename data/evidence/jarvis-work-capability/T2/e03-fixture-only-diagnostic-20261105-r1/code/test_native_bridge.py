import hashlib
import ast
import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest


def bridge(tmp_path, *, command_drift=False, cim_drift=False):
    native = importlib.import_module('native_bridge')
    (tmp_path / 'inputs').mkdir()
    rows = [dict(pid=100+i, role=str(i), parent_pid=90, exe='test-python.exe', created_filetime=1000+i,
                 command_line_sha256=hashlib.sha256(('owned-'+str(i)).encode('utf-16le')).hexdigest())
            for i in range(7)]
    baseline = dict(protected5=rows[:5], protected_listener_pair=rows[5:])
    (tmp_path/'inputs/protected-baseline.json').write_text(json.dumps(baseline), encoding='utf-8')
    calls=[]
    identities=[{k: row[k] for k in ('pid','created_filetime','exe')} for row in rows]
    snapshots={row['pid']:dict(ProcessId=row['pid'], CreationFileTime=row['created_filetime']+(1000 if cim_drift else 0),
                               ParentProcessId=90, CommandLine=('wrong' if command_drift else 'owned-'+str(i)))
               for i,row in enumerate(rows)}
    tree=ast.parse(Path(__file__).with_name('controller.py').read_text(encoding='utf-8-sig'))
    node=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='snapshot_identity_matches')
    namespace={}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<isolated existing identity predicate>','exec'),namespace)
    targets=[dict(hwnd=1+i, control_hwnd=3+i, pid=12, process_created_filetime=99,
                  title='fixture'+str(i), **{'class':'Edit'}) for i in range(2)]
    observations=[dict(target, text='source' if i==0 else 'UNRELATED OWNED FIXTURE — DO NOT CHANGE',
                       start_utf16=0,end_utf16=6 if i==0 else 0) for i,target in enumerate(targets)]
    class Owned:
        known={12:{'role':'fixture','identity':{'created_filetime':99}}}
        def launch(self, argv, role):
            calls.append(('launch',role,argv))
            (self.folder/'fixture.json').write_text(json.dumps({'pid':12,'targets':targets}),encoding='utf-8')
            (self.folder/'fixture-initial-readback.json').write_text('{}',encoding='utf-8')
        def discover(self): calls.append(('discover',))
        def cleanup(self, port=None):
            assert port is None
            assert (self.folder/'stop').exists()
            calls.append(('cleanup',)); return {'status':'PASS'}
    class Case:
        def __init__(self, case, folder, env):
            self.owned=Owned(); self.owned.folder=folder
            self.port=None; self.cli_count=0
        def observe(self,label):
            calls.append(('observe',label)); return observations
    class Timer:
        def __init__(self, seconds, callback):
            assert seconds==30; self.callback=callback
        def start(self): calls.append(('watchdog-start',))
        def cancel(self): calls.append(('watchdog-cancel',))
    controller=SimpleNamespace(
        ROOT=tmp_path/'candidate',
        old=SimpleNamespace(protected_entries=lambda b:b['protected5']+b['protected_listener_pair']),
        protected=lambda:identities, process_snapshot=lambda pids:snapshots,
        snapshot_identity_matches=namespace['snapshot_identity_matches'],
        source_check=lambda:{'candidate':'7975e477665c02820fa235b73d203718bd33b2c9'},
        environment=lambda folder:{}, Case=Case,
        validate_fixture_readback=lambda *args:'PASS',
        validate_fixture_audit=lambda *args,**kwargs:{'status':'PASS'},
        IDENTITY=('hwnd','control_hwnd','pid','process_created_filetime','title','class'))
    harness=SimpleNamespace(CASES={'e03':{'text':'source'}}, wait_for=lambda predicate,seconds:predicate())
    return native.NativeBridge(tmp_path, controller=controller, harness=harness, timer_factory=Timer),calls


def test_native_bridge_uses_only_fixture_and_original_observer(tmp_path):
    native,calls=bridge(tmp_path)
    before=native.preflight()
    folder=tmp_path/'case'; folder.mkdir()
    native.start(folder)
    observed=native.capture()
    assert native.close()['status']=='PASS'
    assert native.postflight(before)['status']=='PASS'
    assert native.audit()['status']=='PASS'
    launches=[x for x in calls if x[0]=='launch']
    assert len(launches)==1 and launches[0][1]=='fixture'
    assert launches[0][2]==['-B',str(tmp_path/'code/fixture_adapter.py'),'--fixture',str(folder),
                           '--candidate-root',str(tmp_path/'candidate')]
    assert [x for x in calls if x[0]=='observe']==[('observe','baseline')]
    assert observed['phenomenon']=='UNCHANGED'
    assert 'source' not in json.dumps(observed)


def test_protected_command_drift_stops_before_fixture(tmp_path):
    native,calls=bridge(tmp_path,command_drift=True)
    with pytest.raises(ValueError): native.preflight()
    assert calls==[]


def test_protected_pid_reuse_between_native_and_cim_reads_is_rejected(tmp_path):
    native,calls=bridge(tmp_path,cim_drift=True)
    with pytest.raises(ValueError): native.preflight()
    assert calls==[]


def test_watchdog_writes_only_owned_stop_marker(tmp_path):
    native,calls=bridge(tmp_path)
    folder=tmp_path/'case'; folder.mkdir()
    native.preflight()
    native.start(folder)
    native.timer.callback()
    assert native.deadline_triggered and (folder/'stop').exists()
    assert not any(x[0]=='observe' for x in calls)
    native.close()


def test_start_requires_completed_readonly_preflight(tmp_path):
    native,calls=bridge(tmp_path)
    folder=tmp_path/'case'; folder.mkdir()
    with pytest.raises(ValueError, match='preflight'):
        native.start(folder)
    assert calls==[]


def test_unexpected_product_scope_still_cleans_only_owned_tree(tmp_path):
    native,calls=bridge(tmp_path)
    native.preflight()
    folder=tmp_path/'case'; folder.mkdir()
    native.start(folder)
    native.context.cli_count=1
    assert native.close()['status']=='FAIL'
    assert ('cleanup',) in calls
