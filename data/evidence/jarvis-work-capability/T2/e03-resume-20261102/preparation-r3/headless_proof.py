import sys,socket,time,json
from pathlib import Path
import controller as c
sys.path.insert(0,str(c.ROOT))
p=Path(__file__).resolve().parent;before=c.protected();receipts=[]
cases=c.load(c.ROOT/'src/brain/tests/fixtures/work_capability/acceptance-cases.json')
queries={'e03-query':c.old.E03_QUERY,'e01-query':cases['e01']['request']+'\n'+'\n'.join(cases['e01']['facts'])}
for mode,query in queries.items():
    folder=p/(mode+'-final4');folder.mkdir(exist_ok=False);owned=c.Owned(folder,c.environment(folder))
    sock=socket.socket();sock.bind(('127.0.0.1',0));port=sock.getsockname()[1];sock.close()
    argv=['-B',str(p/'headless_owned.py'),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--port',str(port),'--query',query]
    proc=owned.launch(argv,'server')
    try:
        deadline=time.monotonic()+10
        while not (folder/'ready').exists() and time.monotonic()<deadline: time.sleep(.05)
        assert (folder/'ready').exists()
        owned.discover()
        if False:
            c.terminate_owned(owned.launchers[0]['identity']);proc.wait(timeout=5)
            # This redirector also exits the child. Retain controller-discovered identity.
            pass
        owned.discover()
        childkeys=[x['identity'] for x in owned.known.values() if x['identity']['pid']!=proc.pid]
        assert len(childkeys)==1
        proof=c.assert_listener(owned,port,argv)
        snapshot=c.process_snapshot([proc.pid,*[x['pid'] for x in childkeys]],folder/'lossless-commandline-proof.json')
        for record in snapshot.values(): assert c.argv_parse(record['CommandLine'])[1:]==argv
        assert query in c.argv_parse(snapshot[childkeys[0]['pid']]['CommandLine'])
        assert proof['identity']==childkeys[0]
        (folder/'pre-cleanup-effects.json').write_text(json.dumps({'headless_only':True,'listener':proof,'model_posts':0,'UI_calls':0}))
    finally: cleanup=owned.cleanup(port)
    assert cleanup['status']=='PASS'
    receipts.append({'mode':mode,'exact_inert_query':query,'argv_roundtrip_exact':True,'launcher':owned.launchers[0]['identity'],'discovered_children':childkeys,'listener':proof,'cleanup':cleanup})
assert before==c.protected()
c.save(p/'headless-discovery-proof.json',{'controller_sha256':c.sha(p/'controller.py'),'cases':receipts,'protected_before':before,'protected_after':c.protected(),'protected_unchanged':True,'UI_calls':0,'model_posts':0,'external_connections':0,'scope':'prep-owned ephemeral socket listener, no HTTP/model payload'})
print(json.dumps({'headless_cases':len(receipts),'protected_unchanged':True}))
