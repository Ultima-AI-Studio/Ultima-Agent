import json,subprocess,sys,time
from pathlib import Path
import acceptance_adapter as a
p=Path(__file__).resolve().parent
before=a.protected(); cases=[]
for mode in ('stopfile','exact-identity-termination'):
    folder=p/('headless-'+mode); folder.mkdir(exist_ok=False)
    out=(folder/'stdout.log').open('w'); err=(folder/'stderr.log').open('w')
    proc=subprocess.Popen([sys.executable,'-B',str(p/'owned_headless.py'),str(folder)],cwd=folder,env=a.environment(folder),stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    parent_key=a.identity(proc.pid); known={proc.pid:parent_key}
    try:
        deadline=time.monotonic()+10
        while not (folder/'child.json').exists() and time.monotonic()<deadline: time.sleep(.05)
        child=a.load(folder/'child.json'); snapshot=a.process_snapshot(); key=a.identity(child['pid']); known[key['pid']]=key
        assert child['pid']==proc.pid or snapshot[child['pid']]['ParentProcessId']==proc.pid
        assert key['pid'] not in {x['pid'] for x in before}
        if mode=='stopfile': (folder/'stop').touch(); proc.wait(timeout=5)
        else:
            a.terminate_owned(key)
            try: proc.wait(timeout=5)
            except subprocess.TimeoutExpired: a.terminate_owned(parent_key); proc.wait(timeout=5)
        snapshot_after=a.process_snapshot()
        assert all(pid not in snapshot_after for pid in known)
        cases.append({'mode':mode,'launcher':parent_key,'actual_child':key,'argv':snapshot[child['pid']]['CommandLine'],'all_owned_absent':True,'exit':proc.returncode})
    finally:
        (folder/'stop').touch()
        for pid,key in known.items():
            if pid in a.process_snapshot(): a.terminate_owned(key)
        out.close();err.close()
a.save(p/'headless-lifecycle-proof.json',{'cases':cases,'protected_before':before,'protected_after':a.protected(),'protected_unchanged':a.protected()==before,'model_calls':0,'UI_calls':0,'network_calls':0})
print(json.dumps({'cases':len(cases),'protected_unchanged':True}))
