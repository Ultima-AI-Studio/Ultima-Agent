"""Fresh pinned urllib3 import; local IPv6 probe only, no product workload."""
from pathlib import Path
import hashlib,importlib.util,json,os,socket,sys,traceback
Q=Path(__file__).resolve().parents[1]
result=Path(sys.argv[1]);receipt=dict(scope='REAL_URLLIB3_LOCAL_CAPABILITY_IMPORT_ONLY',pid=os.getpid(),outcome='FAIL',profile_runs=0,model_calls=0,events=[],closed_at_return=[],unclean_before_close=[])
audit=None
try:
    assert sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.utf8_mode and sys.getprofile() is None
    assert not any(n=='urllib3' or n.startswith('urllib3.') for n in sys.modules)
    path=Q/'profile-preparation/profile.py';spec=importlib.util.spec_from_file_location('exact_probe_profile',path)
    p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)
    pins=p.read_pins(Q/'profile-preparation/manifest.json')
    origin=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Lib\site-packages\urllib3\util\connection.py')
    assert hashlib.sha256(origin.read_bytes()).hexdigest()==pins['files'][str(origin)]
    audit=p.WorkerAudit()
    def observed(event,args):
        if event.startswith(('socket.','subprocess.')):receipt['events'].append(event)
    def returned(frame,event,arg):
        if (event=='call' and frame.f_code.co_name=='close'
                and frame.f_locals.get('self') is getattr(audit,'_probe_socket',None)
                and getattr(audit,'_probe_socket',None) is not None):
            receipt['unclean_before_close'].append(not p.audit_closeout(audit)['clean'])
        if event=='return' and frame.f_code.co_name=='_has_ipv6' and Path(frame.f_code.co_filename)==origin:
            sock=frame.f_locals.get('sock')
            receipt['closed_at_return'].append(isinstance(sock,socket.SocketType) and sock.fileno()==-1)
    sys.addaudithook(observed);sys.addaudithook(audit);sys.setprofile(returned)
    try:module=importlib.import_module('urllib3.util.connection')
    finally:sys.setprofile(None)
    assert Path(module.__file__)==origin
    receipt['audit']=p.audit_closeout(audit)
    assert receipt['audit']['clean'] and receipt['audit']['denied']=={}
    assert audit.expected=={'socket.__new__':1,'socket.bind':1}
    assert receipt['events']==['socket.__new__','socket.bind']
    assert receipt['closed_at_return']==[True]
    assert receipt['unclean_before_close']==[True]
    receipt['outcome']='PASS'
except BaseException as exc:
    receipt.update(error_type=type(exc).__name__,error=str(exc),traceback=traceback.format_exc())
finally:
    sys.setprofile(None)
    if audit is not None:audit.enabled=False
with result.open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(outcome=receipt['outcome'],result=str(result))))
raise SystemExit(0 if receipt['outcome']=='PASS' else 1)
