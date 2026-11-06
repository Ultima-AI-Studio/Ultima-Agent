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
                f.clock[0]=ORIGIN+3
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
