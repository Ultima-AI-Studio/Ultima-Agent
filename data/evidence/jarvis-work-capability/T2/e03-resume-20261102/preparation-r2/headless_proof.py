import sys,socket,time,json
from pathlib import Path
import controller as c
sys.path.insert(0,str(c.ROOT))
p=Path(__file__).resolve().parent;before=c.protected();receipts=[]
for mode in ('normal-discovery','exited-launcher-discovery'):
    folder=p/(mode+'-final');folder.mkdir(exist_ok=False);owned=c.Owned(folder,c.environment(folder))
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    argv=['-B',str(p/'headless_owned.py'),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--port',str(port)]
    proc=owned.launch(argv,'server')
    try:
        deadline=time.monotonic()+10
        while not (folder/'ready').exists() and time.monotonic()<deadline: time.sleep(.05)
        assert (folder/'ready').exists()
        owned.discover()
        if mode=='exited-launcher-discovery':
            c.terminate_owned(owned.launchers[0]['identity']);proc.wait(timeout=5)
            # This redirector also exits the child. Retain controller-discovered identity.
            pass
        owned.discover()
        childkeys=[x['identity'] for x in owned.known.values() if x['identity']['pid']!=proc.pid]
        assert len(childkeys)==1
        proof=c.assert_listener(owned,port,argv) if mode=='normal-discovery' else {'launcher_exited':True,'children_retained_after_exit':True,'actual_live_orphan_proven':False}
        if mode=='normal-discovery': assert proof['identity']==childkeys[0]
        (folder/'pre-cleanup-effects.json').write_text(json.dumps({'headless_only':True,'listener':proof,'model_posts':0,'UI_calls':0}))
    finally: cleanup=owned.cleanup(port)
    assert cleanup['status']=='PASS'
    receipts.append({'mode':mode,'launcher':owned.launchers[0]['identity'],'discovered_children':childkeys,'listener':proof,'cleanup':cleanup})
assert before==c.protected()
c.save(p/'headless-discovery-proof.json',{'controller_sha256':c.sha(p/'controller.py'),'cases':receipts,'protected_before':before,'protected_after':c.protected(),'protected_unchanged':True,'UI_calls':0,'model_posts':0,'external_connections':0,'scope':'prep-owned ephemeral socket listener, no HTTP/model payload'})
print(json.dumps({'headless_cases':len(receipts),'protected_unchanged':True}))
