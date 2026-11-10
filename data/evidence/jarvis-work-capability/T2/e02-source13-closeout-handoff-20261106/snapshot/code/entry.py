import time
ENTRY_NS=time.monotonic_ns()

import json
import os
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from package_io import require,load,save_new,sha,safe_path
from controls import Context,WorkerControls,ReaderControls,PROFILE,PY,same,exact,native_key

ROOT=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-audit-closeout-20261106')
FORBIDDEN={'OLLAMA_HOST','OLLAMA_API_KEY','OLLAMA_MODELS','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP',
    'OPENJARVIS_HOME','OPENJARVIS_CONFIG','XDG_DATA_HOME','XDG_CACHE_HOME','TMP','TEMP','TMPDIR','OPENJARVIS_SSRF_FAIL_OPEN'}


def clean_environment(values):
    return {k:v for k,v in values.items() if k.upper() not in FORBIDDEN and not k.upper().endswith('_PROXY')}


def bootstrap(context,callback):
    pins=context.pins();previous=list(sys.path);cwd=Path.cwd()
    require(clean_environment(dict(os.environ))==dict(os.environ),'Child environment was not sanitized before launch')
    require(not any(k in sys.modules for k in ('sitecustomize','usercustomize')),'Child startup injection')
    try:
        os.chdir(pins['package_root']);sys.path[:]=pins['import_path']
        PROFILE.check_preloaded(pins)
        return callback(pins)
    finally:sys.path[:]=previous;os.chdir(cwd)


def hello(context,role):
    return dict(schema=1,role=role,run_id=context.run_id,entry_nonce=context.release['entry_nonce'],
        pid=os.getpid(),executable=str(PY),root_manifest_sha256=context.manifest_sha)


def check_hello(ctx,role,value):
    exact(value,{'schema','role','run_id','entry_nonce','pid','executable','root_manifest_sha256'},'Child HELLO')
    require(type(value['schema']) is int and value['schema']==1 and value['role']==role and value['run_id']==ctx.run_id
        and value['entry_nonce']==ctx.release['entry_nonce'] and type(value['pid']) is int and value['pid']>0
        and value['executable']==str(PY) and value['root_manifest_sha256']==ctx.manifest_sha,'Child HELLO binding')


def available(path):
    if not path.exists() or not path.stat().st_size:return False
    try:load(path)
    except json.JSONDecodeError:return False  # exclusive creation may still be writing
    return True


def protected_record(ctx,native,name,origin):
    rows=native.protected()
    save_new(ctx.control/name,dict(schema=1,observed_at_ns=ctx.clock(),identities=rows))
    ctx.protected(name,origin)


def start(ctx,native,role,origin):
    native.require_cleanup_room(additional=2)
    native.start(role);path=ctx.control/(role+'-hello.json')
    while not available(path):
        native.require_cleanup_room()
        ctx._time(origin,275 if role=='worker' else 315,exclusive=True);native.pause()
    value=load(path);check_hello(ctx,role,value)
    native.require_cleanup_room()
    observed=native.qualify(role,value)
    exact(observed,{'identity','launcher','parent_pid','argv_sha256'},'Native role observation')
    native_key(observed['identity']);native_key(observed['launcher'])
    require(observed['identity']['pid']==value['pid'],'HELLO is not native process authority')
    native.require_cleanup_room()
    return observed


def wait_worker(ctx,native,origin):
    seen=set()
    while True:
        native.require_cleanup_room()
        value=native.poll('worker')
        for label,name,seconds in (('work','service-first-result.json',275),('cleanup','profile-first-result.json',310)):
            if label not in seen:
                if available(ctx.case/name):ctx.record_progress(label);seen.add(label)
                else:ctx._time(origin,seconds,exclusive=label=='work')
        if value is not None:
            require(seen=={'work','cleanup'},'Worker exited before complete independent progress')
            return value
        ctx._time(origin,315);native.pause()


def check_reader(ctx,value,identity,native_exit,origin):
    exact(native_exit,{'identity','role','signaled','exit_code','observed_at_ns'},'Reader native exit')
    require(same(native_exit['identity'],identity) and native_exit['role']=='reader' and native_exit['signaled'] is True
        and type(native_exit['exit_code']) is int and native_exit['exit_code']==0,'Reader actual exit failed')
    require(type(native_exit['observed_at_ns']) is int and origin<=native_exit['observed_at_ns']<=ctx._time(origin,315),
        'Reader exit outside original cutoff')
    exact(value,{'schema','run_id','entry_nonce','result','observations'},'Reader return')
    require(type(value['schema']) is int and value['schema']==1 and value['run_id']==ctx.run_id
        and value['entry_nonce']==ctx.release['entry_nonce'],'Reader return identity')
    rows=value['observations'];require(type(rows) is list and len(rows)==2,'Exactly two original readbacks')
    first=load(ctx.case/'profile-first-result.json');current=ctx.readback(ctx.case,first)
    for index,row in enumerate(rows):
        PROFILE.observation_gate(first,row,ctx.closed_hashes(),rows[index-1] if index else None,expected_backend=ctx.pins()['ssrf_backend'])
        require(all(row[k]==current[k] for k in row if k!='observed_at_ns') and origin<=row['observed_at_ns']<=native_exit['observed_at_ns'],
            'Reader references differ from independent final root reopen')
    result=value['result']
    exact(result,{'status','outer_root_gate','ack_attempted','ack_admitted','ack_verified','ssrf','observed_at_ns','released_members'},'Original reader candidate')
    require(result['status']=='candidate_mechanical_verified' and result['outer_root_gate']=='NOT_ISSUED'
        and all(result[k] is True for k in ('ack_attempted','ack_admitted','ack_verified'))
        and result['observed_at_ns']==rows[-1]['observed_at_ns'],'Original reader did not verify candidate')
    PROFILE.validate_ssrf_receipt(result['ssrf'],'reader',complete=True,expected_backend=ctx.pins()['ssrf_backend'])
    export=load(ctx.case/'trusted-export.json')
    require(same(result['released_members'],[export['members'][role] for role in ('runtime','views','replay','collection')]),'Reader released member drift')
    return result


def execute(context,origin,backend_factory):
    ctx=context
    ctx._release(True);ctx._time(origin,275,exclusive=True)
    require(not (ctx.root/'release/consumed.json').exists() and not ctx.run.exists(),'Single fresh allocation/run only')
    native=backend_factory(ctx,origin)
    try:ctx.consume(native.root_identity(),origin)
    except BaseException:native.close();raise
    status='FAIL';error=None;cleanup=None;reader_exit=None
    try:
        for folder in (ctx.control,ctx.case,ctx.reader,ctx.process):safe_path(folder).mkdir(parents=True,exist_ok=False)
        protected_record(ctx,native,'protected-before.json',origin)
        backend=native.normal_backend()
        worker=start(ctx,native,'worker',origin)
        ctx.issue_worker(worker['identity'],worker['launcher'],worker['parent_pid'],worker['argv_sha256'],backend)
        worker_exit=wait_worker(ctx,native,origin)
        protected_record(ctx,native,'protected-after.json',origin)
        ctx.seal_worker(worker_exit)
        first=load(ctx.case/'profile-first-result.json')
        PROFILE.observation_gate(first,ctx.readback(ctx.case,first),ctx.closed_hashes(),expected_backend=backend)
        reader=start(ctx,native,'reader',origin)
        save_new(ctx.control/'reader-go.json',dict(schema=1,run_id=ctx.run_id,entry_nonce=ctx.release['entry_nonce'],
            root_manifest_sha256=ctx.manifest_sha,native=reader,worker_observation_sha256=sha(ctx.control/'worker-observation.json')))
        while reader_exit is None:
            native.require_cleanup_room()
            ctx._time(origin,315);reader_exit=native.poll('reader')
            if reader_exit is None:native.pause()
        save_new(ctx.control/'reader-exit.json',reader_exit)
        check_reader(ctx,load(ctx.control/'reader-result.json'),reader['identity'],reader_exit,origin)
        status='PENDING_RESULT_REVIEW'
    except Exception as exc:error=dict(type=type(exc).__name__,message=str(exc)[:500])
    finally:
        try:
            cleanup=native.cleanup()
            require(cleanup.get('status')=='PASS' and cleanup.get('logs_closed') is True
                and cleanup.get('unregistered_launch_possible') is False,'Owned cleanup not proven')
            protected_record(ctx,native,'protected-final.json',origin)
            ctx._fresh_inputs();ctx._time(origin,315)
            if status=='PENDING_RESULT_REVIEW':check_reader(ctx,load(ctx.control/'reader-result.json'),reader['identity'],reader_exit,origin)
        except Exception as exc:
            status='FAIL';error=error or dict(type=type(exc).__name__,message=str(exc)[:500])
        finally:native.close()
    result=dict(schema=1,run_id=ctx.run_id,status=status,mechanical='PASS' if status=='PENDING_RESULT_REVIEW' else 'FAIL',
        e02='NOT_PASSED',acceptance_credit=False,origin_ns=origin,observed_at_ns=ctx.clock(),error=error,cleanup=cleanup)
    save_new(ctx.control/'terminal.json',result)
    if status=='PENDING_RESULT_REVIEW':
        try:ctx._time(origin,315)
        except Exception as exc:
            result=dict(result,status='FAIL',mechanical='FAIL',error=dict(type=type(exc).__name__,message=str(exc)))
            save_new(ctx.control/'late-terminal-failure.json',result)
    return result


def child(ctx,role):
    a,_=ctx.allocation();origin=a['origin_ns']
    ctx._time(origin,275 if role=='worker' else 315,exclusive=True)
    save_new(ctx.control/(role+'-hello.json'),hello(ctx,role))
    path=ctx.control/('entry-grant.json' if role=='worker' else 'reader-go.json')
    while not available(path):
        ctx._time(origin,275 if role=='worker' else 315,exclusive=True);time.sleep(.02)
    if role=='worker':
        result=bootstrap(ctx,lambda pins:PROFILE.run_profile(ctx.case,pins,WorkerControls(ctx)))
        return 0 if result.get('status')=='candidate' else 1
    go=load(path);exact(go,{'schema','run_id','entry_nonce','root_manifest_sha256','native','worker_observation_sha256'},'Reader go')
    require(type(go['schema']) is int and go['schema']==1 and go['run_id']==ctx.run_id and go['entry_nonce']==ctx.release['entry_nonce']
        and go['root_manifest_sha256']==ctx.manifest_sha and go['native']['identity']['pid']==os.getpid()
        and go['worker_observation_sha256']==sha(ctx.control/'worker-observation.json'),'Root reader grant mismatch')
    controls=ReaderControls(ctx)
    def read_original(pins):
        adapter=PROFILE.load_adapter(pins);p4=adapter.load_p4()
        return PROFILE.read_profile(ctx.case,load(ctx.case/'profile-first-result.json'),p4,controls=controls,pins=pins)
    result=bootstrap(ctx,read_original)
    ctx._time(origin,315)
    save_new(ctx.control/'reader-result.json',dict(schema=1,run_id=ctx.run_id,entry_nonce=ctx.release['entry_nonce'],result=result,observations=controls.observations))
    return 0 if result.get('status')=='candidate_mechanical_verified' else 1


def main(argv):
    require(Path(__file__).resolve()==ROOT/'code/entry.py' and Path(sys.executable).resolve()==PY.resolve()
        and sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.utf8_mode and not sys.flags.optimize,'Fixed isolated entry required')
    require('OPENJARVIS_SSRF_FAIL_OPEN' not in {k.upper() for k in os.environ},'Parent SSRF override refused')
    if argv:
        require(len(argv)==4 and argv[0]=='--role' and argv[1] in ('worker','reader') and argv[2]=='--run-id','Fixed child argv only')
        ctx=Context(ROOT,argv[3]);return child(ctx,argv[1])
    ctx=Context(ROOT,load(ROOT/'release/release.json')['run_id'])
    # Loading the native helper is forbidden until the concrete release validates.
    ctx._release(True)
    from native_observation import NativeBackend
    result=execute(ctx,ENTRY_NS,NativeBackend)
    print(json.dumps(result,ensure_ascii=False))
    return 0 if result['status']=='PENDING_RESULT_REVIEW' else 1


if __name__=='__main__':raise SystemExit(main(sys.argv[1:]))
