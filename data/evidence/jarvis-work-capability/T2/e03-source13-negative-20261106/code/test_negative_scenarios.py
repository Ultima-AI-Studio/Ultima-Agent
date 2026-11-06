"""Actual frozen provider and actual Case.negative, with native I/O replaced only."""
import ast
import copy
import importlib.util
import inspect
import json
from pathlib import Path
import sys
from types import SimpleNamespace

import pytest

from package_io import load, require
from test_acceptance_entry import put


SOURCE = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent\src\brain\work_context.py')


def scenario(tmp_path, monkeypatch, fault=None):
    spec=importlib.util.spec_from_file_location('offline_frozen_work_context',SOURCE)
    product=importlib.util.module_from_spec(spec);spec.loader.exec_module(product)
    targets=[dict(hwnd=i+1,control_hwnd=i+3,pid=12,process_created_filetime=99,
                  title='fixture'+str(i),**{'class':'Edit'}) for i in range(2)]
    rows=[dict(t,text='source' if i==0 else 'unrelated',start_utf16=0,end_utf16=6 if i==0 else 0,
               editable=True,password=False) for i,t in enumerate(targets)]
    baseline=copy.deepcopy(rows);calls=[];state={'focus':0,'phase':'initial'}
    policy=dict(version=1,targets=[dict(targets[0],allowed_operations=['capture','replace_selection'],max_age_seconds=300)])
    put(tmp_path/'policy.json',policy);put(tmp_path/'fixture.json',{'targets':targets})
    class Native:
        def focused(self):
            t=targets[state['focus']];return t['hwnd'],t['control_hwnd']
        def identity(self,target,foreground=True):
            if foreground and self.focused()!=(target['hwnd'],target['control_hwnd']):
                raise ValueError('Foreground/focus changed')
            require(all(target[k]==targets[0][k] for k in product.IDENTITY),'Bound target changed')
        def observe(self,target,foreground=True):
            calls.append(('native-observe',target['hwnd'],foreground,state['phase']))
            self.identity(target,foreground)
            return copy.deepcopy(rows[0])
        def replace(self,target,content):
            calls.append(('native-write',target['hwnd']))
            raise RuntimeError('Offline native write trap')
    native=Native();instances=[]
    original=product.WorkContextProvider
    class Provider(original):
        def __init__(self,*args,**kwargs):
            super().__init__(*args,**kwargs);instances.append(self)
        def capture_work_context(self):
            if fault=='capture':raise RuntimeError('capture failed')
            return super().capture_work_context()
        def validate_work_target(self,capture):
            if fault=='false-validation':return False
            return super().validate_work_target(capture)
        def replace_selection(self,capture,content,*,before_send):
            calls.append(('replace-attempt',state['phase']))
            if fault=='unexpected-refusal':raise RuntimeError('provider failure')
            if fault=='false-success':return {'verified':True}
            if fault=='unrelated-value-error':raise ValueError('Capture expired')
            if fault=='send-marker':before_send()
            return super().replace_selection(capture,content,before_send=before_send)
        def release(self,capture):
            calls.append(('release',state['phase']))
            super().release(capture)
            if fault=='release':raise RuntimeError('release failed')
    product.WorkContextProvider=Provider;product.Win32Edit=lambda:native
    monkeypatch.setitem(sys.modules,'src.brain.work_context',product)
    def command(index=0,select=True):
        state['phase']='focus' if index else ('reset' if select else 'selection')
        calls.append(('command',state['phase']))
        if fault=='reset' and state['phase']=='reset':raise RuntimeError('reset failed')
        if fault=='change' and state['phase']=='focus':raise RuntimeError('change failed')
        if fault!='no-change' or state['phase']=='reset':
            state['focus']=index
            if index==0:rows[0]['end_utf16']=6 if select else 0
    def observe(label):
        calls.append(('observe',label))
        if fault=='readback' and label.endswith('-after'):raise RuntimeError('readback failed')
        value=copy.deepcopy(rows)
        if fault=='changed-text' and label.endswith('-after'):value[1]['text']='changed'
        return value
    def inventory(folder):
        if fault=='files' and state['phase'] in ('focus','selection'):return [{'path':'unexpected'}]
        return []
    tree=ast.parse((Path(__file__).parent/'controller.py').read_text(encoding='utf-8-sig'))
    cls=next(x for x in tree.body if isinstance(x,ast.ClassDef) and x.name=='Case')
    node=next(x for x in cls.body if isinstance(x,ast.FunctionDef) and x.name=='negative')
    ns={'load':load,'save':put,'require':require,'output_inventory':inventory,'IDENTITY':product.IDENTITY}
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual Case.negative>','exec'),ns)
    context=SimpleNamespace(folder=tmp_path,command=command,observe=observe)
    def admission():
        calls.append(('admission',state['phase']))
        packet=load(tmp_path/'negative-observations.json');record=packet['scenarios'][-1]
        assert 'changed_windows' in record and 'foreground' in record
        if fault=='admission-'+state['phase']:raise ValueError('Expired case proof')
    def run():
        method=ns['negative']
        # Old implementation is exercised as-is during RED; no skipped tests.
        if 'before_attempt' in inspect.signature(method).parameters:
            return method(context,baseline,before_attempt=admission)
        return method(context,baseline)
    return run,calls,context,instances


def test_focus_reobserves_same_target_then_selection_rejects_without_native_write(tmp_path,monkeypatch):
    run,calls,context,instances=scenario(tmp_path,monkeypatch)
    assert run()=={'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}
    evidence=load(tmp_path/'negative-evidence.json');focus,selection=evidence['cases']
    assert [x['scenario'] for x in evidence['cases']]==['focus','selection']
    assert focus['target_revalidation'] is True and focus['operation']=='validate_work_target'
    assert selection['operation']=='replace_selection' and selection['refusal']['rejected'] is True
    assert [x['completion'] for x in evidence['cases']]==['PASS','PASS']
    assert all(x['capture_released'] for x in evidence['cases'])
    assert evidence['mutation_sends']==[] and evidence['native_write_attempts']==[]
    assert evidence['authorized_outputs']==[] and evidence['model_requests']==0
    assert not any(x[0]=='native-write' for x in calls)
    assert calls.count(('admission','focus'))==calls.count(('admission','selection'))==1
    assert calls.count(('replace-attempt','selection'))==1
    for phase in ('focus','selection'):
        observed=[x for x in calls if x[0]=='native-observe' and x[-1]==phase]
        assert observed and all(x[1:3]==(1,False) for x in observed)
        assert calls.index(('admission',phase))<calls.index(observed[0])
    assert not instances[0]._captures and context.accepted_effects['cli_count']==0


@pytest.mark.parametrize('fault',[
    'reset','capture','change','no-change','false-validation','unexpected-refusal','false-success',
    'unrelated-value-error','send-marker','changed-text','files','readback','release',
    'admission-focus','admission-selection',
])
def test_failure_retains_partial_observation_and_never_counts_negative_pass(tmp_path,monkeypatch,fault):
    run,calls,context,instances=scenario(tmp_path,monkeypatch,fault)
    with pytest.raises((ValueError,RuntimeError)):run()
    assert not (tmp_path/'negative-evidence.json').exists()
    packet=load(tmp_path/'negative-observations.json');last=packet['scenarios'][-1]
    assert last['completion']=='FAIL' and last.get('unobserved_reason')
    assert not any(x[0]=='native-write' for x in calls)
    if fault.startswith('admission-'):
        assert 'admission_unknown' in last and 'refusal' not in last
        phase=fault.split('-',1)[1]
        assert not any(x[0]=='native-observe' and x[-1]==phase for x in calls)
        assert not any(x==('replace-attempt',phase) for x in calls)
    if instances:assert not instances[0]._captures
