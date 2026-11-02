"""PREPARED ONLY. Requires a separately issued root inert authority; never model/CLI."""
from pathlib import Path
import json
import sys
import time
import adapter as a

def main():
    authority,folder,p4,baseline=a.inert_admit()
    folder.mkdir(parents=True,exist_ok=False)
    a.save_new(folder/'attempt.json',dict(kind='inert',authority_sha256=a.sha(a.V/'inert-authority.json')))
    owned=None; errors=[]; cleanup=dict(status='FAIL'); start=time.monotonic()
    try:
        env=p4.environment(folder); env.pop('ULTIMA_CORPUS_WIRE_ROOT',None)
        sys.path.insert(0,str(a.C)); argv=a.inert_argv(folder,authority['port'])
        owned=p4.Owned(folder,env); owned.launch(argv,'server')
        deadline=time.monotonic()+30
        while not p4.listener_owner(authority['port']):
            a.require(time.monotonic()<deadline,'Inert readiness timeout'); time.sleep(.1)
        p4.assert_listener(owned,authority['port'],argv)
        a.require(p4.get_json(f"http://127.0.0.1:{authority['port']}/inert")==dict(inert=True),'Inert loopback proof')
        roundtrip=a.load(folder/'argv-roundtrip.json')
        a.require(roundtrip['question']==a.corpus()['query'],'Exact original query roundtrip')
        # P4's raw UTF16LE observation and parser prove native child argv as well.
        snapshot=p4.process_snapshot([x['identity']['pid'] for x in owned.known.values()],folder/'native-argv.json')
        a.require(all(p4.argv_parse(row['CommandLine'])[1:]==argv for row in snapshot.values()),'Owned native argv mismatch')
        a.save_new(folder/'protected-before.json',baseline)
    except Exception as exc: errors.append(dict(stage='inert',type=type(exc).__name__,message=str(exc)))
    finally:
        if owned:
            try: cleanup=owned.cleanup(authority['port'])
            except Exception as exc: cleanup=dict(status='FAIL',error=type(exc).__name__)
        try:
            after=[p4.identity(x['pid']) for x in baseline]
            a.save_new(folder/'protected-after.json',after); a.require(after==baseline,'Protected identity changed'); a.check_inputs()
        except Exception as exc: errors.append(dict(boundaries=type(exc).__name__))
        if time.monotonic()-start>315: errors.append(dict(outer='315 seconds exceeded'))
        terminal=dict(kind='inert',overall='PASS' if not errors and cleanup['status']=='PASS' else 'FAIL',cleanup=cleanup,errors=errors,elapsed_seconds=time.monotonic()-start,outer_seconds=315,model_calls=0,product_cli=0,actual=False,T2='NOT_PASSED')
        a.save_new(folder/'terminal.json',terminal)
    print(json.dumps(terminal)); return 0 if terminal['overall']=='PASS' else 2

if __name__=='__main__': raise SystemExit(main())
