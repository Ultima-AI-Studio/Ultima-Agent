"""Concrete record/consumer checks. Native identities and runtime records are synthetic."""
from copy import deepcopy
from datetime import datetime, timezone, timedelta
import hashlib
import json
import os
from pathlib import Path
from types import SimpleNamespace
import pytest
import controls as c

RUN='11111111-1111-4111-8111-111111111111'
NONCE='22222222-2222-4222-8222-222222222222'
ORIGIN=1_000_000_000
ROOT_KEY={'pid':917,'created_filetime':134384100000000001,'exe':r'C:\Python\python.exe'}
WORKER={'pid':os.getpid(),'created_filetime':134384100000000123,'exe':r'C:\Python\python.exe'}
LAUNCHER={'pid':918,'created_filetime':134384100000000100,'exe':str(c.PY)}
ROLES=['ollama','brain_primary','brain_runtime_child','voice_primary','voice_runtime_child',
       'voice_listener_primary','voice_listener_runtime_child']
FIXED=datetime(2026,11,6,0,0,tzinfo=timezone.utc)


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def put(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(value,ensure_ascii=False,allow_nan=False),encoding='utf-8')
def get(path):return json.loads(path.read_bytes())


def fixture(tmp_path):
    root=tmp_path/'root'; root.mkdir()
    control=root/'runs'/RUN/'control';control.mkdir(parents=True)
    case=root/'runs'/RUN/'worker'/'case';case.mkdir(parents=True)
    (root/'runs'/RUN/'reader').mkdir()
    (root/'runs'/RUN/'process').mkdir()
    expected=[dict(pid=70+i,created_filetime=134384100000000000+i,exe=r'C:\Python\protected.exe',
                   parent_pid=20+i,command_line_sha256=hashlib.sha256(str(i).encode()).hexdigest()) for i in range(7)]
    entries=[dict(row,role=ROLES[i],created_utc='2026-11-06T00:00:00+00:00') for i,row in enumerate(expected)]
    baseline=root/'inputs/protected-baseline.json'
    put(baseline,dict(protected5=entries[:5],protected_listener_pair=entries[5:],protected_process_count=7))
    base=get(c.BASE_MANIFEST)
    files={str(c.BASE_MANIFEST):digest(c.BASE_MANIFEST),str(baseline):digest(baseline)}
    files.update({str(p):digest(p) for p in Path(c.__file__).parent.glob('*.py') if not p.name.startswith('test_')})
    manifest=dict(schema=1,kind='SOURCE13_PROFILE_ROOT_PREPARATION',runtime_released=False,candidate=c.CANDIDATE,
        model_digest=c.MODEL_DIGEST,base_profile_manifest_path=str(c.BASE_MANIFEST),base_profile_manifest_sha256=digest(c.BASE_MANIFEST),
        import_path=[str(c.BASE_MANIFEST.parent),*base['import_path'][1:]],protected_baseline_path=str(baseline),files=files)
    put(root/'entry-manifest.json',manifest)
    review=dict(reviewer='root-independent',scope='e02-source13-root-entry-preparation',verdict='PASS',
                manifest_sha256=digest(root/'entry-manifest.json'),runtime_authority=False)
    put(root/'review/independent-preparation-review.json',review)
    put(root/'verification/code-preparation-gate.json',dict(verdict='PASS_PREPARATION_ONLY',
        manifest_sha256=digest(root/'entry-manifest.json'),review_sha256=digest(root/'review/independent-preparation-review.json'),actual_authority=False))
    approval=dict(schema=1,kind='USER_EXPLICIT_APPROVAL',scope=c.SCOPE,approved=True,source='user_reply',
        answer='SYNTHETIC CONTRACT FIXTURE ONLY',recorded_at=FIXED.isoformat(),profile_limit=1,result_review_limit=1,
        actual_inference_allowed=0,actual_http_allowed=0,actual_11434_allowed=0,ssrf_dns_host='raw.githubusercontent.com',UI=0,audio=0)
    put(root/'release/user-approval.json',approval)
    release=dict(schema=1,kind='SOURCE13_PROFILE_ROOT_RELEASE',scope=c.SCOPE,run_id=RUN,entry_nonce=NONCE,
        candidate=c.CANDIDATE,model_digest=c.MODEL_DIGEST,root_manifest_sha256=digest(root/'entry-manifest.json'),
        approval_sha256=digest(root/'release/user-approval.json'),preparation_review_sha256=digest(root/'review/independent-preparation-review.json'),
        issued_at=FIXED.isoformat(),expires_at=(FIXED+timedelta(seconds=120)).isoformat(),max_submissions=1,retry=0,
        actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,ssrf_dns_host='raw.githubusercontent.com',UI=0,audio=0)
    put(root/'release/release.json',release)
    now=[ORIGIN+1]
    context=c.Context(root,RUN,clock=lambda:now[0],utc=lambda:FIXED+timedelta(seconds=1))
    return SimpleNamespace(root=root,control=control,case=case,expected=expected,context=context,clock=now)


def admitted(f):
    f.context.consume(ROOT_KEY,ORIGIN)
    put(f.control/'protected-before.json',dict(schema=1,observed_at_ns=ORIGIN+1,identities=f.expected))
    f.context.issue_worker(WORKER,LAUNCHER,LAUNCHER['pid'],'a'*64,'python')


def closed(f,code=0):
    admitted(f)
    first=dict(run_id=RUN,entry_nonce=NONCE,worker_pid=WORKER['pid'],worker_creation_filetime=WORKER['created_filetime'])
    put(f.case/'profile-first-result.json',first)
    put(f.case/'profile-observations.json',{'capture':'synthetic'})
    put(f.case/'runtime-inputs.json',{'runtime':'synthetic'})
    files={p.name:{'bytes':p.stat().st_size,'sha256':digest(p)} for p in f.case.iterdir() if p.name!='profile-first-result.json'}
    put(f.case/'closed-index.json',dict(format=1,files=files))
    f.clock[0]=ORIGIN+3
    put(f.control/'protected-after.json',dict(schema=1,observed_at_ns=ORIGIN+2,identities=f.expected))
    f.context.seal_worker(dict(identity=WORKER,role='worker',signaled=True,exit_code=code,observed_at_ns=ORIGIN+2))
    return first


def test_admission_is_accepted_by_unchanged_profile_consumer(tmp_path,monkeypatch):
    f=fixture(tmp_path);admitted(f)
    grant=c.WorkerControls(f.context).admit(f.case,f.context.pins())
    monkeypatch.setattr(c.PROFILE.time,'monotonic_ns',lambda:f.clock[0])
    c.PROFILE.validate_admission(grant,f.case,f.context.pins())
    assert grant['worker_executable']==str(c.PY)
    assert grant['worker_creation_filetime']==134384100000000123
    assert grant['work_deadline_ns']==276_000_000_000
    assert grant['cleanup_deadline_ns']==311_000_000_000 and grant['seal_deadline_ns']==316_000_000_000
    assert grant['actual_inference_allowed']==0 and grant['candidate']=='269aca511d88412dbb9c15d23911138469a37aa2'


def test_allocation_is_exclusive_across_context_instances(tmp_path):
    f=fixture(tmp_path);f.context.consume(ROOT_KEY,ORIGIN)
    before=(f.root/'release/consumed.json').read_bytes()
    other=c.Context(f.root,RUN,clock=lambda:ORIGIN+2,utc=lambda:FIXED+timedelta(seconds=2))
    with pytest.raises((ValueError,FileExistsError)):other.consume(ROOT_KEY,ORIGIN)
    assert (f.root/'release/consumed.json').read_bytes()==before


def test_absent_consumption_refuses_before_sdk_exposure(tmp_path):
    f=fixture(tmp_path)
    with pytest.raises((ValueError,FileNotFoundError)):
        c.WorkerControls(f.context).admit(f.case,f.context.pins())


def test_worker_capability_cannot_admit_twice(tmp_path):
    f=fixture(tmp_path);admitted(f);control=c.WorkerControls(f.context)
    control.admit(f.case,f.context.pins())
    with pytest.raises(ValueError):control.admit(f.case,f.context.pins())


@pytest.mark.parametrize('change', ['candidate','model','manifest','profile','unknown','five','pid','clock','expired','proxy_pins'])
def test_worker_rejects_mismatched_root_binding(tmp_path,change):
    f=fixture(tmp_path);admitted(f);pins=f.context.pins()
    grant=f.control/'entry-grant.json';data=get(grant)
    if change=='candidate':data['candidate']='118ba152b007c30d358c8bc44c51aabe8ae820f0'
    elif change=='model':data['model_digest']='f'*64
    elif change=='manifest':data['root_manifest_sha256']='e'*64
    elif change=='profile':pins['profile_manifest_sha256']='d'*64
    elif change=='unknown':data['verified']=True
    elif change=='pid':data['worker_native']['pid']+=1
    elif change=='clock':data['origin_ns']+=1
    elif change=='expired':f.clock[0]=ORIGIN+275_000_000_000
    elif change=='five':
        value=get(f.control/'protected-before.json');value['identities']=value['identities'][:5];put(f.control/'protected-before.json',value)
    elif change=='proxy_pins':pins['import_path'][0]=str(tmp_path)
    put(grant,data)
    with pytest.raises(ValueError):c.WorkerControls(f.context).admit(f.case,pins)


def test_current_import_path_is_derived_without_mutating_old_manifest(tmp_path):
    f=fixture(tmp_path);before=c.BASE_MANIFEST.read_bytes();pins=f.context.pins()
    assert pins['import_path'][0]==str(c.BASE_MANIFEST.parent)
    assert pins['import_path'][0]!=get(c.BASE_MANIFEST)['import_path'][0]
    assert c.BASE_MANIFEST.read_bytes()==before


def test_two_reader_observations_match_original_consumer_and_origin(tmp_path):
    f=fixture(tmp_path);first=closed(f);reader=c.ReaderControls(f.context)
    first_read=reader.readback(f.case,first)
    f.clock[0]=ORIGIN+315_000_000_000
    final=reader.readback(f.case,first)
    c.PROFILE.validate_readback(first_read,first,{})
    c.PROFILE.validate_readback(final,first,{},first_read)
    assert first_read['observed_at_ns']==ORIGIN+3 and final['observed_at_ns']==316_000_000_000
    assert final['python_exit_code']==0 and reader.calls==2
    with pytest.raises(ValueError):reader.readback(f.case,first)


@pytest.mark.parametrize('change', ['exit','signal','identity','claim','file','clock','timeback','late','capture','extra_exit'])
def test_reader_rejects_unobserved_or_mutated_completion(tmp_path,change):
    f=fixture(tmp_path);first=closed(f);reader=c.ReaderControls(f.context)
    observation=f.control/'worker-observation.json';value=get(observation)
    if change=='exit':value['native_exit']['exit_code']=7
    elif change=='signal':value['native_exit']['signaled']=False
    elif change=='identity':value['native_exit']['identity']['created_filetime']+=1
    elif change=='claim':first['python_exit_code']=0
    elif change=='clock':value['origin_ns']+=10
    elif change=='timeback':value['native_exit']['observed_at_ns']=ORIGIN-1
    elif change=='late':f.clock[0]=ORIGIN+315_000_000_000+1
    elif change=='extra_exit':value['native_exit']['worker_reported_success']=True
    elif change=='file':(f.case/'runtime-inputs.json').write_text('{}',encoding='utf8')
    elif change=='capture':(f.case/'profile-observations.json').write_text('{}',encoding='utf8')
    put(observation,value)
    with pytest.raises(ValueError):reader.readback(f.case,first)


def test_final_readback_refuses_drift_even_with_same_first_reference(tmp_path):
    f=fixture(tmp_path);first=closed(f);reader=c.ReaderControls(f.context)
    reader.readback(f.case,first)
    path=f.control/'protected-after.json';value=get(path);value['identities'][0]['parent_pid']+=1;put(path,value)
    with pytest.raises(ValueError):reader.readback(f.case,first)


@pytest.mark.parametrize('change',['approval_absent','dns_not_approved','review_failed','larger_model','expired_release','boolean_cap'])
def test_release_defaults_closed_for_missing_or_mismatched_authority(tmp_path,change):
    f=fixture(tmp_path);path=f.root/'release/release.json';value=get(path)
    if change=='approval_absent':(f.root/'release/user-approval.json').unlink()
    elif change=='dns_not_approved':value['ssrf_dns_host']=None
    elif change=='review_failed':
        path=f.root/'review/independent-preparation-review.json';value=get(path);value['verdict']='FAIL'
    elif change=='larger_model':value['model_digest']='0'*64
    elif change=='expired_release':value['expires_at']=(FIXED-timedelta(seconds=1)).isoformat()
    elif change=='boolean_cap':value['max_submissions']=True
    put(path,value)
    with pytest.raises((ValueError,FileNotFoundError)):
        c.Context(f.root,RUN,clock=lambda:ORIGIN+1,utc=lambda:FIXED+timedelta(seconds=1)).consume(ROOT_KEY,ORIGIN)
