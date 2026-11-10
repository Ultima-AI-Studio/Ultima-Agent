"""Fresh-process real SDK import through the worker/reader ownership boundary.

Synthetic admission authorizes initialization in this probe only. The sentinel
stops before product imports, research submission, DNS or any runtime allocation.
"""
from contextlib import contextmanager
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import sys
import time
import traceback
import uuid

ROOT=Path(__file__).resolve().parents[1]
PY=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')


class ImportBoundaryReached(Exception):
    pass


def main():
    role,location,result_path=sys.argv[1:]
    assert role in ('worker','reader')
    result=Path(result_path)
    assert not result.exists()
    receipt=dict(scope='REAL_SDK_COLD_IMPORT_ONLY',role=role,pid=os.getpid(),
        isolated=bool(sys.flags.isolated),bytecode_disabled=bool(sys.flags.dont_write_bytecode),
        runtime_authority=False,admission='SYNTHETIC_INIT_ONLY',profile_invocations=0,
        research_submissions=0,model_calls=0,native_OS_activity=None,
        audit_events=[],refused_io=[],eager_audit={},outcome='FAIL')
    def guard(event,args):
        if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.startfile','os.startfile/2','os.posix_spawn','os.spawn'):
            receipt['audit_events'].append(event)
            if event!='socket.gethostname':
                receipt['refused_io'].append(event)
                raise RuntimeError('Cold import probe refuses external I/O: '+event)
    sys.addaudithook(guard)
    try:
        assert Path(sys.executable).resolve()==PY.resolve()
        assert sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.utf8_mode and not sys.flags.optimize
        assert not any(n=='httpx' or n.startswith('httpx.') or n=='ollama' or n.startswith('ollama.') for n in sys.modules)
        assert getattr(platform,'_uname_cache',None) is None,'Platform was warmed before the probe'
        receipt['platform_cache_cold']=True
        receipt['real_sdk_not_preloaded']=True
        source=ROOT/'profile-preparation/profile.py'
        receipt['profile_source_sha256']=hashlib.sha256(source.read_bytes()).hexdigest()
        spec=importlib.util.spec_from_file_location('cold_profile',source)
        profile=importlib.util.module_from_spec(spec);spec.loader.exec_module(profile)
        pins=profile.read_pins(ROOT/'profile-preparation/manifest.json')
        receipt['profile_manifest_sha256']=pins['profile_manifest_sha256']
        # Match Context.pins(): preserve the archived path in the base manifest
        # and derive the current package path only in the enclosing entry.
        pins['import_path']=[str(ROOT/'profile-preparation'),*pins['import_path'][1:]]
        area=Path(location).resolve();area.mkdir(exist_ok=False)
        case=area/'case';case.mkdir()
        reader=area/'reader';reader.mkdir()
        pins['reader_root']=str(reader);pins['worker_evidence_roots']=[str(case)]
        pins['ssrf_backend']='rust'
        os.chdir(pins['package_root']);sys.path[:]=pins['import_path']
        profile.check_preloaded(pins)
        original=profile.own_ollama_types

        @contextmanager
        def stop_after_ownership(pinned,audit):
            receipt['eager_audit']=audit
            with original(pinned,audit) as state:
                import httpx
                package=state['module'];owner=state['owner']
                assert type(owner) is package.Client and type(owner._client) is httpx.Client
                assert state['closed'] and owner._client.is_closed
                receipt['real_types_and_early_close']=True
                receipt['ollama_origin']=package.__file__
                receipt['httpx_origin']=httpx.__file__
            # Exit the actual ownership context normally, then stop the caller.
            # Throwing inside it would deliberately dirty its cleanup receipt.
            assert audit['eager']['clean'] and audit['eager']['closed']
            raise ImportBoundaryReached()
            yield  # contextmanager never exposes a usable workload scope

        profile.own_ollama_types=stop_after_ownership
        class InitOnlyControls(profile.RootControls):
            def admit(self,folder,pinned):
                origin=time.monotonic_ns()
                grant={key:'a'*64 for key in profile._ADMISSION_FIELDS}
                grant.update(run_id=str(uuid.uuid4()),entry_nonce=str(uuid.uuid4()),worker_pid=os.getpid(),
                    worker_creation_filetime=1,origin_ns=origin,work_deadline_ns=origin+275*10**9,
                    cleanup_deadline_ns=origin+310*10**9,seal_deadline_ns=origin+315*10**9,
                    case_root=str(folder),worker_executable=str(PY),candidate=profile.CANDIDATE,
                    model_digest=profile.MODEL_DIGEST,scope='ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE',
                    consumed=1,max_submissions=1,retry=0,actual_http_allowed=0,actual_11434_allowed=0,
                    actual_inference_allowed=0,ssrf_fail_open_present=False,ssrf_backend='rust')
                for key in ('profile_manifest_sha256','candidate_manifest_sha256','corpus_sha256'):grant[key]=pinned[key]
                return grant
        try:
            scope=profile.private_scope(case,pins,InitOnlyControls()) if role=='worker' else profile.reader_scope(case,pins)
            with scope:
                raise AssertionError('Probe unexpectedly reached workload scope')
        except ImportBoundaryReached:
            receipt['boundary_stopped']=True
        else:raise AssertionError('Ownership boundary was not reached')
        assert not receipt['refused_io']
        assert receipt['audit_events'].count('socket.gethostname')>=1,'Real cold metadata path was not observed'
        assert all(event=='socket.gethostname' for event in receipt['audit_events'])
        eager=receipt['eager_audit']['eager']
        assert eager['constructors']==1 and eager['clean'] and eager['closed']
        assert eager['import_attempts']==eager['pinned_send_calls']==eager['later_attempts']==0
        assert not any(n.startswith('openjarvis') or n.startswith('src.brain') for n in sys.modules)
        assert not list(area.rglob('research.md'))
        receipt['outcome']='PASS'
    except BaseException as exc:
        receipt['error_type']=type(exc).__name__
        receipt['error']=str(exc)
        receipt['traceback']=traceback.format_exc()
    with result.open('x',encoding='utf-8') as stream:json.dump(receipt,stream,ensure_ascii=False,indent=2)
    print(json.dumps(dict(role=role,outcome=receipt['outcome'],result=str(result))))
    return 0 if receipt['outcome']=='PASS' else 1


if __name__=='__main__':raise SystemExit(main())
