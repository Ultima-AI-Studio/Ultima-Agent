"""PREPARED ONLY. Requires a separately issued root inert authority; never model/CLI."""
from pathlib import Path
import json
import sys
import time
import adapter as a

def run_inert():
    budget=a.entry_budget()
    authority,folder,p4,baseline=a.inert_admit(budget=budget)
    budget.call('inert exclusive root',folder.mkdir,parents=True,exist_ok=False)
    budget.call('inert claim close',a.save_new,folder/'attempt.json',dict(kind='inert',parent_timing=budget.timing(),authority_sha256=a.sha(a.V/'inert-authority.json')))
    owned=None; errors=[]; cleanup=dict(status='FAIL')
    with a.PrivateIO(p4,budget) as io:
        try:
            env=budget.call('inert environment',p4.environment,folder); env.pop('ULTIMA_CORPUS_WIRE_ROOT',None)
            sys.path.insert(0,str(a.C)); argv=budget.call('inert argv',a.inert_argv,folder,authority['port'])
            owned=budget.call('inert Owned constructor',p4.Owned,folder,env); io.launch(owned,argv,'server')
            a.ready_listener(p4,owned,authority['port'],argv,budget)
            budget.pre('fixed inert get_json',full_ns=2000000000)
            response=p4.get_json(f"http://127.0.0.1:{authority['port']}/inert")
            budget.post('fixed inert get_json'); a.require(response==dict(inert=True),'Inert loopback proof')
            roundtrip=budget.call('inert argv readback',a.load,folder/'argv-roundtrip.json')
            a.require(roundtrip['question']==a.corpus()['query'],'Exact original query roundtrip')
            snapshot=p4.process_snapshot([x['identity']['pid'] for x in owned.known.values()],folder/'native-argv.json')
            a.require(all(p4.argv_parse(row['CommandLine'])[1:]==argv for row in snapshot.values()),'Owned native argv mismatch')
            budget.post('inert native argv'); budget.call('inert before identities close',a.save_new,folder/'protected-before.json',baseline)
        except Exception as exc:
            errors.append(dict(stage='inert',type=type(exc).__name__,message=str(exc))); budget.failure=budget.failure or type(exc).__name__
        finally:
            budget.phase='cleanup'
            if owned:
                try: cleanup=io.cleanup(owned,authority['port'])
                except Exception as exc: cleanup=dict(status='FAIL',effects_unknown=True,error=type(exc).__name__)
            budget.phase='seal'
            try:
                after=budget.call('inert final native identities',lambda:[p4.identity(x['pid']) for x in baseline])
                budget.call('inert after identities close',a.save_new,folder/'protected-after.json',after)
                a.require(after==baseline,'Protected identity changed'); budget.call('inert final pins',a.check_inputs)
            except Exception as exc: errors.append(dict(boundaries=type(exc).__name__))
            terminal=dict(kind='inert',folder=str(folder),run_id=budget.run_id,timing=budget.timing(),timing_eligibility='UNOBSERVED_NEVER_TIMED_PASS',overall='READY_FOR_ROOT_TIMING_WITNESS' if not errors and cleanup['status']=='PASS' else 'FAIL',cleanup=cleanup,errors=errors,first_failure=budget.failure,io_events=io.events,launch_attempts=io.launch_attempts,model_calls=0,product_cli=0,actual=False,T2='NOT_PASSED')
            try:
                budget.call('inert immutable terminal close',a.save_new,folder/'terminal.json',terminal); a.seal_index(folder,budget,p4)
            except Exception as exc:
                terminal['overall']='FAIL'; terminal['errors'].append(dict(seal=type(exc).__name__))
                if not (folder/'terminal.json').exists(): a.save_new(folder/'terminal.json',terminal)
    return terminal

def main():
    terminal=run_inert()
    print(json.dumps(terminal))
    # A standalone child return never supplies the trusted enclosing witness.
    return 2

if __name__=='__main__': raise SystemExit(main())
