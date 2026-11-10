"""Source10 one-case evidence adapter. Preparation is never execution authority."""
from pathlib import Path
import argparse
import base64
from dataclasses import asdict
import datetime as dt
import hashlib
import importlib.util
import json
import os
import socket
import sys
import time
import uuid
import errno
import re
import stat
import math
from contextvars import ContextVar
from contextlib import contextmanager

HERE=Path(__file__).resolve().parent
V=HERE.parent
T=V.parent
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')
P4=T/'e01-source13-round3-20261106/code/controller.py'
P1=P4.parent.parent/'preparation-support/acceptance_adapter.py'
MANIFEST_SHA='5badf78414d3cb6a13145b98dbc1e3fa0ce08e4e5f79fc2948244e2118f16121'
PREPARATION_SHA='38a38c9c0c2e27cc998603fef60ee64efd44a07661167500f7274c0e807a69f6'
CANDIDATE='269aca511d88412dbb9c15d23911138469a37aa2'
MODEL='qwen3-8b-uncensored'
CASE='E02-controlled-1'
BUDGETS=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,outer_seconds=315,retry=0)
CORPUS=T/'source6-native-reference/controlled-corpus-inputs/corpus.json'
CAP=4*1024*1024
PY=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')
CLOCK_DOMAIN='monotonic_ns;same-host='+socket.gethostname()
_ENCLOSING=ContextVar('source10_root_enclosing',default=None)
_OBSERVING=ContextVar('source10_root_observing',default=None)

INPUTS_PATH=V/'inputs/input-manifest.json'
BINDINGS_PATH=V/'code/bindings.py'
BINDINGS_SHA='831c1b303c55e77fcfcd9e9742e1e4bd9995b553df36848e067fc3da84526c45'
PROTECTED_BASELINE=T/'e02-source13-exact-probe-20261106/inputs/protected-baseline.json'
SDK_SOURCES=('H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\_rust_bridge.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\agents\\_stubs.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\agents\\native_react.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\agents\\prompt_loader.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\cli\\ask.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\core\\config.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\core\\events.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\core\\registry.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\core\\types.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\engine\\_base.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\engine\\_stubs.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\engine\\ollama.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\sdk.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\security\\capabilities.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\security\\guardrails.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\security\\runtime.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\security\\scanner.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\telemetry\\instrumented_engine.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\tools\\_stubs.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\tools\\description_loader.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\tools\\file_read.py', 'H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Lib\\site-packages\\openjarvis\\tools\\file_write.py')
if hashlib.sha256(BINDINGS_PATH.read_bytes()).hexdigest()!=BINDINGS_SHA:raise ValueError('Binding source drift')
_binding_spec=importlib.util.spec_from_file_location('source13_real_input_bindings',BINDINGS_PATH)
bindings=importlib.util.module_from_spec(_binding_spec);_binding_spec.loader.exec_module(bindings)


class Deadline:
    """One integer-nanosecond invocation allowance. Earlier origins only."""
    def __init__(self,*,clock=time.monotonic_ns):
        self.clock=clock; self.local_entry_ns=clock(); self.origin_ns=self.local_entry_ns
        self.run_id=str(uuid.uuid4()); self.phase='work'; self.events=[]; self.failure=None
    def cutoff_ns(self,phase=None): return self.origin_ns+{'work':275,'cleanup':310,'seal':315}[phase or self.phase]*1000000000
    def remaining_ns(self,phase=None): return self.cutoff_ns(phase)-self.clock()
    def fail(self,reason):
        self.failure=self.failure or reason
        raise TimeoutError(reason)
    def pre(self,label,*,full_ns=0):
        left=self.remaining_ns()
        if left<=0 or left<full_ns: self.fail('Deadline admission: '+label)
        return left
    def post(self,label):
        if self.remaining_ns()<0: self.fail('Late return: '+label)
    def clip(self,seconds,label): return min(seconds,self.pre(label)/1000000000)
    def call(self,label,function,*args,**kwargs):
        self.pre(label)
        try: result=function(*args,**kwargs)
        except Exception as exc:
            self.failure=self.failure or label+': '+str(exc); raise
        self.post(label); return result
    def adopt_parent(self,timing):
        require(timing.get('clock_domain')==CLOCK_DOMAIN and timing.get('run_id')==self.run_id,'Parent clock/run binding')
        origin=timing.get('origin_ns')
        require(type(origin) is int and 0<=origin<=self.origin_ns,'No renewed parent origin')
        self.origin_ns=origin; self.pre('earlier parent admission')
    def timing(self): return dict(run_id=self.run_id,origin_ns=self.origin_ns,clock_domain=CLOCK_DOMAIN,work_cutoff_ns=self.cutoff_ns('work'),cleanup_cutoff_ns=self.cutoff_ns('cleanup'),outer_cutoff_ns=self.cutoff_ns('seal'))

class TimingObservation:
    """Only trusted enclosing caller may adjudicate; child never emits timed PASS."""
    def __init__(self,budget): self.budget=budget; self.finished=False
    def finish(self,terminal_digest,proofs):
        require(not self.finished,'Observation already final; no promotion'); self.finished=True
        observed=self.budget.clock()
        return dict(**self.budget.timing(),observed_ns=observed,terminal_sha256=terminal_digest,
            eligible=bool(terminal_digest and all(proofs.get(k) is True for k in ('cleanup','closed','pins','protected','readback')) and not self.budget.failure and self.budget.origin_ns<=observed<=self.budget.cutoff_ns('seal')),
            proofs=proofs,observer='trusted-root-enclosing-contract',permanent=True)

class PrivateIO:
    """Borrow bindings on one fresh P4 object, never a shared stdlib/P1/helper."""
    def __init__(self,p4,budget):
        self.p4=p4; self.budget=budget; self.saved={}; self.waits=[]; self.probes=[]
        self.port_closed=False; self.events=[]; self.launch_attempts=[]
    def __enter__(self):
        owner=self; p4=self.p4; b=self.budget
        for name in ('subprocess','time','socket','terminate_owned','save'): self.saved[name]=getattr(p4,name)
        class Delegate:
            def __init__(self,original): self.original=original
            def __getattr__(self,name): return getattr(self.original,name)
        class Process(Delegate):
            def check_output(self,argv,**kwargs):
                # Only the exact original checked P4 PowerShell command families.
                require(argv[:4]==['powershell.exe','-NoProfile','-NonInteractive','-Command'] and len(argv)==5,'Private subprocess command')
                script=argv[4]
                suffix=' | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CreationFileTime=[Int64]$_.CreationDate.ToFileTimeUtc();CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
                snapshot=re.fullmatch(r'Get-CimInstance Win32_Process(?: -Filter "ProcessId=[1-9][0-9]*(?: OR ProcessId=[1-9][0-9]*)*")?'+re.escape(suffix),script)
                listener=re.fullmatch(r'@\(Get-NetTCPConnection -State Listen -LocalPort [0-9]+ -ErrorAction SilentlyContinue \| Select-Object -ExpandProperty OwningProcess\) \| ConvertTo-Json -Compress',script)
                require(snapshot or listener,'Only pinned P4 snapshot/listener I/O')
                requested=kwargs['timeout']; kwargs['timeout']=b.clip(requested,'P4 check_output')
                owner.events.append(dict(io='check_output',argv=argv,timeout=kwargs['timeout'],phase=b.phase))
                try: result=self.original.check_output(argv,**kwargs)
                except Exception as exc:
                    b.failure=b.failure or b.phase+' check_output: '+str(exc); raise
                b.post('P4 check_output'); return result
        class ClockIO(Delegate):
            def sleep(self,seconds):
                result=self.original.sleep(b.clip(seconds,'P4 sleep')); b.post('P4 sleep'); return result
        class Probe:
            def __init__(self,raw,allowance,expires_ns): self.raw=raw; self.allowance=allowance; self.expires_ns=expires_ns; self.closed=False
            def settimeout(self,seconds):
                # P4's hint precedes its try/finally; scope finally owns closure
                # even when construction has exhausted either admission deadline.
                remaining=(self.expires_ns-b.clock())/1000000000
                if remaining<=0: b.fail('Port proof allocation expired before timeout hint')
                return self.raw.settimeout(b.clip(min(seconds,remaining),'cleanup port timeout hint'))
            def connect_ex(self,address):
                # One shared private proof: construction/setup spend allocation,
                # and the immutable P4 settimeout(1) hint cannot renew it.
                remaining=(self.expires_ns-b.clock())/1000000000
                if remaining<=0: b.fail('Port proof allocation expired before connect')
                self.raw.settimeout(b.clip(min(3,remaining),'cleanup port connect'))
                b.pre('cleanup port connect admission after setup')
                if b.clock()>=self.expires_ns: b.fail('Port proof allocation expired after setup')
                code=self.raw.connect_ex(address)
                owner.port_closed=(code in {errno.ECONNREFUSED,10061})
                owner.events.append(dict(io='port',code=code,definitive_refusal=owner.port_closed))
                try:
                    b.post('cleanup port probe')
                    if b.clock()>self.expires_ns: b.fail('Late return: port proof allocation')
                except Exception: owner.port_closed=False; raise
                return code
            def close(self):
                try: return self.raw.close()
                finally: self.closed=True
        class SocketIO(Delegate):
            def socket(self,*args,**kwargs):
                allocated_ns=b.clock()
                allowance=b.clip(3,'cleanup socket allocation')
                expires_ns=allocated_ns+int(allowance*1000000000)
                raw=self.original.socket(*args,**kwargs)
                probe=Probe(raw,allowance,expires_ns); owner.probes.append(probe); return probe
        def terminate(key):
            b.pre('full original P1 termination',full_ns=10000000000)
            event=dict(io='terminate_owned',identity=key,entered=True,returned=False); owner.events.append(event)
            try:
                result=owner.saved['terminate_owned'](key); event['returned']=True
                b.post('original P1 termination'); return result
            except Exception as exc:
                b.failure=b.failure or b.phase+' terminate_owned: '+str(exc); raise
            finally: event['observed_ns']=b.clock(); event['late']=b.remaining_ns()<0
        def save(path,value): return b.call('P4 evidence save',owner.saved['save'],path,value)
        p4.subprocess=Process(self.saved['subprocess']); p4.time=ClockIO(self.saved['time']); p4.socket=SocketIO(self.saved['socket']); p4.terminate_owned=terminate; p4.save=save
        return self
    def wrap_waits(self,owned):
        for item in owned.launchers:
            proc=item['proc']
            if any(p is proc for p,_,_,_ in self.waits): continue
            original=proc.wait; present='wait' in vars(proc); value=vars(proc).get('wait')
            self.waits.append((proc,original,present,value))
            def wait(timeout=None,_original=original):
                clipped=self.budget.clip(timeout if timeout is not None else 300,'registered Popen.wait')
                self.events.append(dict(io='wait',requested=timeout,effective=clipped,phase=self.budget.phase))
                result=_original(timeout=clipped); self.budget.post('registered Popen.wait'); return result
            proc.wait=wait
    def launch(self,owned,argv,role):
        self.budget.pre('Owned launch '+role)
        event=dict(role=role,attempted=True,registered=False,possible_live_effect=True); self.launch_attempts.append(event)
        try:
            # No adapter exception in the creation -> original registration gap.
            result=owned.launch(argv,role); event['registered']=True
            self.budget.post('Owned launch '+role); return result
        except Exception as exc:
            self.budget.failure=self.budget.failure or 'launch '+role+': '+str(exc); raise
        finally:
            self.wrap_waits(owned)
            event['registered_launchers']=len(owned.launchers); event['known_identities']=len(owned.known)
    def cleanup(self,owned,port):
        self.budget.phase='cleanup'; self.budget.pre('cleanup entry'); self.wrap_waits(owned)
        try: result=owned.cleanup(port)
        except Exception as exc:
            self.budget.failure=self.budget.failure or 'cleanup: '+str(exc)
            result=dict(status='FAIL',error=str(exc),error_type=type(exc).__name__,effects_unknown=True)
        result=dict(result)
        result['port_definitively_closed']=self.port_closed
        result['logs_closed']=all(stream.closed for stream in owned.logs)
        if any(not item['registered'] for item in self.launch_attempts):
            result['status']='FAIL'; result['effects_unknown']=True; result['unregistered_launch_possible']=True
        if not self.port_closed or not result['logs_closed'] or self.budget.remaining_ns()<0: result['status']='FAIL'; result['effects_unknown']=True
        return result
    def __exit__(self,*exc):
        try:
            for proc,original,present,value in reversed(self.waits):
                if present: proc.wait=value
                else: del proc.wait
            for probe in self.probes:
                if not probe.closed: probe.close()
        finally:
            for name,value in self.saved.items(): setattr(self.p4,name,value)

def require(ok,message):
    if not ok: raise ValueError(message)

def record_failure(budget,errors,stage,cause,**evidence):
    reason=str(cause); budget.failure=budget.failure or stage+': '+reason
    errors.append(dict(stage=stage,cause=reason,**evidence))

def reconcile_results(cli,service):
    fields=('request_id','session_id','task_id','status','artifacts')
    require(all(k in cli and k in service and cli[k]==service[k] for k in fields),'First service/CLI result mismatch')

def observed_io(label,function):
    budget=_OBSERVING.get()
    return budget.call(label,function) if budget is not None else function()

def sha(path): return observed_io('observed hash '+str(path),lambda:hashlib.sha256(Path(path).read_bytes()).hexdigest())

def strict_json(value):
    def unique(items):
        result={}
        for key,item in items:
            require(key not in result,'Duplicate export JSON member'); result[key]=item
        return result
    def nonfinite(value): raise ValueError('Nonfinite export JSON constant')
    return json.loads(value,object_pairs_hook=unique,parse_constant=nonfinite)

def load(path):
    def read():
        with Path(path).open('rb') as stream: return stream.read(CAP+1)
    raw=observed_io('observed JSON '+str(path),read)
    require(len(raw)<=CAP,'Evidence byte cap')
    return strict_json(raw.decode('utf-8-sig'))

def save_new(path,value):
    raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False).encode('utf8')
    require(len(raw)<=CAP,'Evidence byte cap')
    with Path(path).open('xb') as stream: stream.write(raw)

def check_inputs():
    require(Path(sys.executable).resolve()==PY.resolve(),'Exact authorized interpreter required')
    require(not sys.flags.optimize and sys.flags.dont_write_bytecode and sys.flags.utf8_mode==1,'Python -B -X utf8 required')
    require(sha(INPUTS_PATH)==MANIFEST_SHA and sha(BINDINGS_PATH)==BINDINGS_SHA,'Source13 input/source drift')
    require(sha(V/'inputs/scope.json')==PREPARATION_SHA,'Offline preparation scope drift')
    fixed=bindings.load_inputs(INPUTS_PATH)
    return dict(fixed['files'],**{str(INPUTS_PATH):MANIFEST_SHA,str(BINDINGS_PATH):BINDINGS_SHA,str(V/'inputs/scope.json'):PREPARATION_SHA})

def check_import_origins():
    from importlib.machinery import PathFinder
    for raw in SDK_SOURCES:
        path=Path(raw); site=next(p for p in path.parents if p.name=='site-packages')
        name='.'.join(path.relative_to(site).with_suffix('').parts)
        cached=sys.modules.get(name)
        if cached is not None: require(Path(getattr(cached,'__file__','')).resolve()==path.resolve(),'Import origin '+name)
        search=sys.path
        for index in range(1,len(name.split('.'))+1):
            prefix='.'.join(name.split('.')[:index]); spec=PathFinder.find_spec(prefix,search)
            require(spec is not None,'Missing pinned import '+prefix)
            parent=sys.modules.get(prefix)
            if parent is not None and spec.submodule_search_locations is not None:
                require({str(Path(p).resolve()) for p in getattr(parent,'__path__',[])}=={str(Path(p).resolve()) for p in spec.submodule_search_locations},'Import package origin '+prefix)
            search=spec.submodule_search_locations
        require(Path(spec.origin).resolve()==path.resolve(),'Pinned import origin '+name)
    helper=sys.modules.get('src.brain.tests.work_context_acceptance')
    if helper is not None: require(Path(helper.__file__).resolve()==C/'src/brain/tests/work_context_acceptance.py','Candidate helper import origin')

@contextmanager
def candidate_import_path():
    previous=list(sys.path)
    try:
        sys.path.insert(0,str(C)); yield
    finally: sys.path[:]=previous

def load_p4():
    require(sha(P4)=='5e7a636c0e1f7330bf140fa212c2d51569b389aac93cb9b84840b51ba5ade2ea','P4 drift')
    require(sha(P1)=='585baca27b572364e2078e960281f20261f675738299df5633e91b74a4ca19cc','P1 drift')
    cached=sys.modules.get('acceptance_adapter')
    require(cached is None or Path(getattr(cached,'__file__','')).resolve()==P1.resolve(),'Unexpected cached acceptance_adapter')
    if cached is not None: require(getattr(cached,'__source10_verified_sha__',None)==sha(P1),'Unverified cached acceptance_adapter')
    spec=importlib.util.spec_from_file_location('source10_p4_definitions',P4)
    module=importlib.util.module_from_spec(spec); paths=list(sys.path)
    try:
        sys.path.insert(0,str(P4.parent))
        spec.loader.exec_module(module)
    finally: sys.path[:]=paths
    require(Path(module.old.__file__).resolve()==P1.resolve(),'P1 import origin')
    module.old.__source10_verified_sha__=sha(P1)
    module.old.PROTECTED_BASELINE=PROTECTED_BASELINE
    return module

def stamp(value):
    result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None,'Timezone required'); return result

def validate_documents(a,l,now):
    require(a.get('schema')==11 and l.get('schema')==11 and a.get('kind')=='source10_execution' and a.get('issuer')=='root' and a.get('actual') is True,'Root source10 schema11 execution required')
    require(a.get('case')==CASE and a.get('candidate')==CANDIDATE and a.get('candidate_manifest_sha256')==MANIFEST_SHA,'Candidate/source mismatch')
    require(a.get('budgets')==BUDGETS and not a.get('overrides'),'Exact original budgets/defaults required')
    require(a.get('model',MODEL)==MODEL,'Model mismatch')
    require(a.get('native_precision')=='FILETIME100ns','Fresh exact native baseline required')
    issued,expiry=stamp(a['issued_at']),stamp(a['expires_at'])
    require(issued<=now<expiry and 0<(expiry-issued).total_seconds()<=120,'Expired admission')
    require(l.get('released_case')==CASE and l.get('consumed')==[CASE] and l.get('attempts')==1 and l.get('retry')==0,'One preconsumed case only')
    require(a.get('schedule')==dict(work_seconds=275,cleanup_seconds=310,outer_seconds=315,ruling_sha256='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'),'Root deadline schedule binding')
    timing=a.get('parent_timing',{})
    require(timing.get('clock_domain')==CLOCK_DOMAIN and type(timing.get('origin_ns')) is int and timing['origin_ns']>0 and isinstance(timing.get('run_id'),str) and isinstance(timing.get('parent_identity'),dict),'Trusted parent timing required')

def validate_inert_documents(authority,now):
    require(authority.get('schema')==11 and authority.get('kind')=='source10_inert_qualification' and authority.get('issuer')=='root','Separate root inert authority required')
    require(authority.get('candidate_manifest_sha256')==MANIFEST_SHA and authority.get('actual') is False and authority.get('model_calls')==0 and authority.get('native11434') is False,'Inert scope')
    require(authority.get('schedule')==dict(work_seconds=275,cleanup_seconds=310,outer_seconds=315,ruling_sha256='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'),'Inert deadline schedule')
    issued,expiry=stamp(authority['issued_at']),stamp(authority['expires_at'])
    require(issued<=now<expiry and 0<(expiry-issued).total_seconds()<=120,'Expired inert admission')

def check_native_baseline(proof,p4):
    require(proof.get('precision')=='FILETIME100ns' and proof.get('candidate')==CANDIDATE,'Native baseline binding')
    require(0<=(dt.datetime.now(dt.timezone.utc)-stamp(proof['recorded_at'])).total_seconds()<=60,'Stale native baseline')
    identities=proof['protected']
    validate_protected_members(identities,p4)
    return identities

def validate_protected_members(identities,p4):
    require(type(identities) is list and len(identities)==7 and len({x['pid'] for x in identities})==7,'Exact protected member inventory: seven required')
    baseline=load(PROTECTED_BASELINE)
    rows=baseline.get('protected5',[])+baseline.get('protected_listener_pair',[])
    require(baseline.get('protected_process_count')==7 and len(rows)==7,'Seven accepted protected baseline rows')
    expected=[{k:row[k] for k in ('pid','created_filetime','exe')} for row in rows]
    require({x['pid']:x for x in identities}=={x['pid']:x for x in expected},'Exact protected member binding')
    require({x['pid']:x for x in p4.protected()}=={x['pid']:x for x in expected},'Protected live inventory drift')
    require(all(type(x['created_filetime']) is int and x['created_filetime']>0 and p4.identity(x['pid'])==x for x in identities),'Exact native identity drift')
    snapshot=p4.process_snapshot(pids=sorted(x['pid'] for x in identities))
    for row,key in zip(rows,expected):
        current=snapshot.get(row['pid'])
        require(current is not None and current['ParentProcessId']==row['parent_pid'],'Protected parent drift')
        require(p4.snapshot_identity_matches(key,current),'Protected CIM identity drift')
        require(hashlib.sha256(current['CommandLine'].encode('utf-16le')).hexdigest()==row['command_line_sha256'],'Protected command drift')
    return identities

def package_check(p4):
    package=load(HERE/'manifest.json')
    require(set(package['files'])=={'adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md'},'Exact six-file package')
    for name,digest in package['files'].items(): require(sha(p4.no_reparse(HERE/name))==digest,'Harness drift')
    approval=load(p4.no_reparse(V/'harness-approval.json'))
    require(approval.get('reviewer')=='root-independent' and approval.get('overall')=='PASS' and approval.get('manifest_sha256')==sha(HERE/'manifest.json'),'Independent harness approval required')

def operational_paths(mode):
    common=[HERE/name for name in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json')]
    common+=[V/'harness-approval.json',PROTECTED_BASELINE]
    return common+([V/'inert-authority.json',V/'inert-native-baseline.json'] if mode=='inert' else [V/'controller-authority'/f'{CASE}.json',V/'controller-ledger.json',V/'native-preflight'/f'{CASE}.json'])

def operational_pins(mode,budget):
    pins=budget.call('operational source pins',check_inputs)
    for path in operational_paths(mode): pins[str(path)]=budget.call('operational raw pin',sha,path)
    budget.call('operational import origins',check_import_origins)
    return pins

def admitted_record(mode,folder,port,authority,baseline,budget):
    pins=operational_pins(mode,budget)
    record=dict(mode=mode,folder=str(folder),port=port,authority=authority,baseline=baseline,timing=budget.timing(),pins=pins)
    require(not hasattr(budget,'admitted'),'One admitted allocation only'); budget.admitted=record
    return record

def compare_operational_pins(admitted,budget):
    current=operational_pins(admitted['mode'],budget)
    require(current==admitted['pins'],'Admitted operational pin drift')
    return current

def bind_parent(budget,authority,p4):
    timing=authority['parent_timing']; expected=timing['parent_identity']
    if _ENCLOSING.get() is not None: require(budget.run_id==timing['run_id'] and budget.origin_ns==timing['origin_ns'],'Enclosing authority origin mismatch')
    else: budget.run_id=p4.uuid_text(timing['run_id'])
    budget.adopt_parent(timing)
    require(budget.call('trusted native parent identity',p4.identity,expected['pid'])==expected,'Trusted enclosing native parent identity')

def entry_budget():
    local=Deadline(); parent=_ENCLOSING.get()
    if parent is None: return local
    require(parent.origin_ns<=local.local_entry_ns,'Enclosing origin cannot renew'); return parent

def admit(authority_path,ledger_path,*,child=False,budget=None):
    budget=budget or entry_budget()
    budget.call('source admission',check_inputs)
    require(Path(authority_path).absolute()==V/'controller-authority'/f'{CASE}.json' and Path(ledger_path).absolute()==V/'controller-ledger.json','Canonical source10 authority/ledger paths required')
    p4=budget.call('pinned P4 import',load_p4)
    a=budget.call('authority read',load,p4.no_reparse(authority_path)); l=budget.call('ledger read',load,p4.no_reparse(ledger_path))
    validate_documents(a,l,dt.datetime.now(dt.timezone.utc)); bind_parent(budget,a,p4)
    budget.call('package admission',package_check,p4); budget.call('operational import admission',check_import_origins)
    require(a.get('ledger_sha256')==sha(ledger_path) and a.get('approval_sha256')==sha(V/'harness-approval.json'),'Ledger/approval binding')
    proofpath=p4.no_reparse(V/'native-preflight'/f'{CASE}.json'); proof=budget.call('native proof read',load,proofpath)
    require(a.get('native_preflight_sha256')==sha(proofpath),'Native preflight binding'); budget.call('native admission baseline',check_native_baseline,proof,p4)
    m=bindings.load_inputs(INPUTS_PATH)
    local_manifest=budget.call('local model manifest read',Path(m['model_manifest_path']).read_bytes)
    budget.call('local native metadata verification',p4.old.metadata_valid,dict(ok=True,model=MODEL,agent='native_react'),proof['version'],proof['tags'],local_manifest)
    folder=p4.no_reparse(V/'actual'/CASE)
    require(a.get('folder')==str(folder) and type(a.get('port')) is int and 1024<=a['port']<=65535 and a['port']!=11434,'Case root/port')
    if child: require((folder/'attempt.json').exists(),'Claimed child only')
    else:
        require(not folder.exists(),'First case already attempted')
        require(not (V/'actual').exists() or not list((V/'actual').iterdir()),'Unexpected sibling case')
        with PrivateIO(p4,budget): require(not p4.listener_owner(a['port']),'Port occupied')
    budget.post('case admission')
    admitted=admitted_record('actual',folder,a['port'],a,proof,budget)
    return dict(folder=folder,port=a['port'],request_id=str(uuid.uuid4()),session_id=str(uuid.uuid4()),baseline=proof,authority=a,ledger=l,budget=budget,mode='actual',admitted=admitted),p4

def corpus():
    require(sha(CORPUS)=='9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002','Original corpus drift')
    data=load(CORPUS)
    require(len(data['sources'])==4 and all(hashlib.sha256(s['body'].encode('utf8')).hexdigest()==s['decoded_body_sha256'] for s in data['sources']),'Original source bytes')
    return data

def candidate_argv(context):
    folder,port=context['folder'],context['port']
    server=['-B','-X','utf8',str(HERE/'adapter.py'),'--child-server',str(folder),'--port',str(port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--isolated','--work-research']
    cli=['-B','-X','utf8','-m','src.brain.cli','--work','--research','--request-id',context['request_id'],'--session-id',context['session_id'],'--server-url',f'http://127.0.0.1:{port}','--json',corpus()['query']]
    return server,cli

def issue_clearance(context,p4,owned,argv,authority_sha256):
    b=context['budget']; deadline=min(b.clock()+30000000000,b.cutoff_ns())
    roots={x['proc'].pid for x in owned.launchers if x['role']=='server'}
    require(len(roots)==1,'One retained native launcher required')
    root_pid=next(iter(roots))
    while True:
        b.call('clearance original discovery',owned.discover)
        bases=[item for pid,item in owned.known.items() if item['role']=='server' and pid!=root_pid]
        require(len(bases)<=1 and all(item['parent']==root_pid for item in bases),'A unique native base is required; ambiguous server siblings')
        if len(bases)==1: break
        if b.clock()>=deadline: b.fail('Validated native base clearance missing')
        p4.time.sleep(min(.01,(deadline-b.clock())/1000000000))
    members=[]
    for item in owned.known.values():
        if item['role']!='server': continue
        actual=item['argv'] if isinstance(item['argv'],list) else p4.argv_parse(item['argv'])[1:]
        require(actual==argv and p4.identity(item['identity']['pid'])==item['identity'],'Registered child clearance identity/argv')
        members.append(dict(identity=item['identity'],role='server',parent=item['parent']))
    require(members,'No validated native child clearance')
    require(len(members)==2 and root_pid in owned.known,'Exact launcher and unique native base clearance')
    record=dict(mode=context['mode'],folder=str(context['folder']),timing=b.timing(),argv=argv,
        authority_sha256=authority_sha256,attempt_sha256=sha(context['folder']/'attempt.json'),members=members,launcher_identity=owned.known[root_pid]['identity'],base_identity=bases[0]['identity'])
    b.call('one-shot clearance close',save_new,context['folder']/'child-clearance.json',record)
    b.call('closed clearance publication',write_raw_new,context['folder']/'child-clearance.ready',b'')

def consume_clearance(context,p4,argv,authority_sha256):
    b=context['budget']; folder=context['folder']
    expected=(inert_argv(folder,context['port']) if context['mode']=='inert' else candidate_argv(context)[0])
    require(argv==expected,'Exact full authorized child argv required')
    deadline=min(b.clock()+30000000000,b.cutoff_ns())
    while not (folder/'child-clearance.ready').exists():
        b.pre('native child clearance wait')
        if b.clock()>=deadline: b.fail('Native child clearance missing')
        time.sleep(min(.01,(deadline-b.clock())/1000000000))
    record=b.call('native clearance read',load,p4.no_reparse(folder/'child-clearance.json'))
    require(read_raw(folder/'child-clearance.ready')==b'','Closed clearance publication marker')
    require(record['mode']==context['mode'] and record['folder']==str(folder) and record['timing']==b.timing() and record['argv']==expected,'Child clearance binding')
    require(record['authority_sha256']==authority_sha256 and record['attempt_sha256']==sha(folder/'attempt.json'),'Child attempt/authority binding')
    own=p4.identity(os.getpid())
    root=record['launcher_identity']; base=record['base_identity']; members=record['members']
    require(len(members)==2 and root['pid']!=base['pid'] and own==base and any(m.get('role')=='server' and m.get('identity')==base and m.get('parent')==root['pid'] for m in members) and any(m.get('identity')==root for m in members),'Only intended native base may consume clearance')
    b.call('exclusive clearance consumption',save_new,folder/'child-clearance.consumed.json',dict(identity=own,clearance_sha256=sha(folder/'child-clearance.json'),argv=argv,timing=b.timing()))
    return own

def validate_native_members(owned,p4,snapshot,listener,argv):
    members={pid:item for pid,item in owned.known.items() if item['role']=='server'}
    launchers=[item for item in owned.launchers if item['role']=='server']
    require(len(launchers)==1 and len(members)==2,'Unique native redirector/base members required')
    root=launchers[0]; root_pid=root['identity']['pid']; created,exited=p4.process_times(root['proc'])
    require(created==root['identity']['created_filetime'],'Native retained launcher identity')
    live=set(members)-({root_pid} if exited else set())
    require(set(snapshot)==live and live,'Exact live native member set required')
    for pid,row in snapshot.items():
        item=members[pid]; require(p4.identity(pid)==item['identity'],'Native live identity drift')
        require(row['ParentProcessId']==item['parent'] and p4.argv_parse(row['CommandLine'])[1:]==argv,'Native parent/argv relationship')
        if pid!=root_pid: require(item['parent']==root_pid and created<=item['identity']['created_filetime'] and (not exited or item['identity']['created_filetime']<=exited),'Native base/redirector relationship')
    listener_pid=listener['identity']['pid']
    require(listener_pid in live and listener_pid!=root_pid and listener['identity']==members[listener_pid]['identity'] and members[listener_pid]['parent']==root_pid and listener['argv']==argv,'Native base listener binding')
    return dict(live_pids=sorted(live),members=list(members.values()),launcher_identity=root['identity'],launcher_exit_filetime=exited,listener=listener)

def ready_listener(p4,owned,port,argv,budget):
    deadline=min(budget.clock()+30000000000,budget.cutoff_ns())
    while True:
        owners=p4.listener_owner(port)
        if budget.clock()>deadline: budget.fail('Late listener readiness')
        if owners: break
        if budget.clock()==deadline: budget.fail('No listener at readiness cutoff')
        p4.time.sleep(min(.1,(deadline-budget.clock())/1000000000))
    budget.call('unique owned listener',p4.assert_listener,owned,port,argv)
    if budget.clock()>deadline: budget.fail('Late listener identity proof')

def record_native_members(folder,p4,owned,argv,budget):
    listener=budget.call('native listener record',load,folder/'listener.json')
    members={pid:item for pid,item in owned.known.items() if item['role']=='server'}
    snapshot=p4.process_snapshot(list(members),folder/'native-argv.json')
    record=validate_native_members(owned,p4,snapshot,listener,argv)
    record['snapshot']=snapshot; record['argv']=argv
    budget.native_members=strict_json(json.dumps(record))
    budget.call('native members close',save_new,folder/'native-members.json',record)

def observe_inert_exchange(folder,p4,owned,argv,port,budget):
    require(getattr(budget,'admitted',{}).get('mode')=='inert' and budget.admitted['folder']==str(folder) and budget.admitted['port']==port,'Admitted inert exchange binding')
    listener=budget.call('inert exchange owned listener',p4.assert_listener,owned,port,argv)
    endpoint=f'http://127.0.0.1:{port}/inert'
    budget.pre('fixed inert exchange',full_ns=2000000000); before=budget.clock()
    response=p4.get_json(endpoint)
    after=budget.clock(); budget.post('fixed inert exchange')
    require(type(response) is dict and set(response)=={'inert'} and response['inert'] is True,'Inert exchange response mismatch')
    record=dict(mode='inert',method='GET',endpoint=endpoint,listener=listener,response=response,before_ns=before,after_ns=after,timing=budget.timing())
    budget.inert_exchange=strict_json(json.dumps(record))
    budget.call('inert exchange close',save_new,folder/'inert-exchange.json',record)
    return record

def validate_inert_exchange(record,expected,admitted,listener,budget):
    require(isinstance(expected,dict) and record==expected,'Trusted parent inert exchange absent/mismatch')
    require(type(record['response']) is dict and set(record['response'])=={'inert'} and record['response']['inert'] is True,'Closed inert exchange response type')
    require(record['mode']=='inert' and record['method']=='GET' and record['endpoint']==f"http://127.0.0.1:{admitted['port']}/inert" and record['listener']==listener and record['response']==dict(inert=True) and record['timing']==budget.timing(),'Closed inert exchange binding')
    require(type(record['before_ns']) is int and type(record['after_ns']) is int and budget.origin_ns<=record['before_ns']<=record['after_ns']<=budget.cutoff_ns('work') and record['after_ns']<=budget.clock(),'Closed inert exchange timing')

def capture_first(folder,owned,budget):
    owned.flush()
    with (folder/'cli.stdout').open('rb') as stream: raw=stream.read(CAP+1)
    require(len(raw)<=CAP,'CLI result byte cap')
    if not (folder/'first-product.raw').exists():
        with (folder/'first-product.raw').open('xb') as stream: stream.write(raw)
    product=load(folder/'cli.stdout')
    if not (folder/'product-result.json').exists(): save_new(folder/'product-result.json',product)
    return product

def execute_case(context,p4):
    budget=context.get('budget') or entry_budget()
    budget.pre('exclusive claim')
    folder=context['folder']; folder.mkdir(parents=True,exist_ok=True)
    budget.call('attempt close',save_new,folder/'attempt.json',dict(case=CASE,request_id=context['request_id'],session_id=context['session_id'],retry=False,parent_timing=budget.timing()))
    errors=[]; product=None; cleanup={'status':'FAIL'}; owned=None; work_attempts=0; counts=None; before=None; native_before=[]; effective_client=None
    with candidate_import_path(), PrivateIO(p4,budget) as io:
        try:
            before=(budget.call('before operational pins',compare_operational_pins,context['admitted'],budget) if context.get('admitted') else budget.call('before pins',check_inputs))
            native_before=budget.call('before exact identities',check_native_baseline,context['baseline'],p4)
            budget.call('boundary before close',save_new,folder/'boundary-before.json',dict(pins=before,protected=native_before))
            if context.get('admitted'): budget.call('admitted evidence close',save_new,folder/'admission.json',context['admitted'])
            env=budget.call('isolated environment',p4.environment,folder); env.pop('ULTIMA_CORPUS_WIRE_ROOT',None)
            server,cli=budget.call('candidate argv',candidate_argv,context)
            budget.call('argv close',save_new,folder/'argv.json',dict(server=server,cli=cli,budgets=BUDGETS,schedule=budget.timing()))
            owned=budget.call('Owned constructor',p4.Owned,folder,env); budget.owned=owned; io.launch(owned,server,'server')
            if context.get('admitted'): issue_clearance(context,p4,owned,server,sha(V/'controller-authority'/f'{CASE}.json'))
            ready_listener(p4,owned,context['port'],server,budget)
            if context.get('admitted'): record_native_members(folder,p4,owned,server,budget)
            budget.call('dispatch pins',check_inputs); budget.call('dispatch native baseline',check_native_baseline,context['baseline'],p4)
            dispatch=budget.clock(); budget.pre('productive dispatch')
            effective_client=min(300,budget.remaining_ns()/1000000000)
            budget.call('effective schedule close',save_new,folder/'effective-schedule.json',dict(**budget.timing(),dispatch_ns=dispatch,effective_client_seconds=effective_client,original_client_maximum_seconds=300,service_maximum_seconds=260))
            work_attempts+=1; proc=io.launch(owned,cli,'cli')
            proc.wait(timeout=min(300-(budget.clock()-dispatch)/1000000000,budget.remaining_ns()/1000000000))
            if budget.remaining_ns()<=0:
                # First-outcome preservation uses the reserved cleanup slice;
                # normal packet validation still cannot start at/after275.
                budget.phase='cleanup'
            product=budget.call('first product close',capture_first,folder,owned,budget)
            budget.phase='work'
            require(product.get('request_id')==context['request_id'] and product.get('session_id')==context['session_id'],'First result request/session mismatch')
            require(proc.returncode==0,'CLI nonzero; no retry')
            counts=budget.call('packet and external readback',verify_exports,folder,product,p4)
            require(product.get('status')=='succeeded','First product result failed')
        except Exception as exc:
            record_failure(budget,errors,'work',exc)
        finally:
            budget.phase='cleanup'
            if owned:
                try:
                    if (folder/'cli.stdout').exists() and product is None: product=budget.call('partial first product capture',capture_first,folder,owned,budget)
                except Exception as exc: record_failure(budget,errors,'first-raw',exc)
            try: inventory=budget.call('pre-cleanup effects',p4.output_inventory,folder)
            except Exception as exc: inventory={'effects_unknown':type(exc).__name__}; record_failure(budget,errors,'effects',exc,effects_unknown=True)
            if counts and 'inventory' in counts:
                try: compare_pre_cleanup(counts['inventory'],inventory,p4)
                except Exception as exc: record_failure(budget,errors,'pre-cleanup-effects',exc,accepted=counts['inventory'],observed=inventory)
            try: budget.call('effects close',save_new,folder/'pre-cleanup-effects.json',inventory)
            except Exception as exc: record_failure(budget,errors,'effects-close',exc,effects_unknown=True)
            if owned:
                try: cleanup=io.cleanup(owned,context['port'])
                except Exception as exc: cleanup=dict(status='FAIL',effects_unknown=True,error=str(exc))
            if cleanup['status']!='PASS': record_failure(budget,errors,'cleanup','returned FAIL',effects_unknown=True,cleanup=cleanup)
            budget.phase='seal'
            try:
                final_pins=(budget.call('final operational pins',compare_operational_pins,context['admitted'],budget) if context.get('admitted') else budget.call('final pins',check_inputs))
                require(final_pins==before,'Input drift during run')
                final_protected=budget.call('final protected identities',lambda:[p4.identity(x['pid']) for x in native_before])
                require(final_protected==native_before,'Protected identity drift')
                budget.call('boundary after close',save_new,folder/'boundary-after.json',dict(pins=before,protected=final_protected))
                if counts and 'inventory' in counts:
                    post=budget.call('post-cleanup output readback',validate_final_outputs,folder,product,counts['inventory'],p4)
                    budget.call('post-cleanup output evidence close',save_new,folder/'post-cleanup-effects.json',post)
            except Exception as exc: record_failure(budget,errors,'final-boundary',exc,effects_unknown=True)
            if budget.remaining_ns()<0: record_failure(budget,errors,'outer','315 seconds eligibility expired')
            post_attempts=(counts or {}).get('native_POST_attempts')
            if post_attempts is None and (folder/'trusted-export.json').exists():
                try:
                    observed=load(folder/'trusted-export.json').get('native_POST_attempts')
                    if type(observed) is int and 0<=observed<=8: post_attempts=observed
                except Exception: pass
            terminal=dict(case=CASE,folder=str(folder),run_id=budget.run_id,timing=budget.timing(),timing_eligibility='UNOBSERVED_NEVER_TIMED_PASS',effective_client_seconds=effective_client,overall='PENDING_ROOT_INDEPENDENT_REVIEW' if product and not errors and cleanup['status']=='PASS' else 'FAIL',product_status=(product or {}).get('status'),product_result_sha256=sha(folder/'product-result.json') if (folder/'product-result.json').exists() else None,service_first_result_sha256=sha(folder/'service-first-result.json') if (folder/'service-first-result.json').exists() else None,cleanup=cleanup,errors=errors,first_failure=budget.failure,work_cli_attempts=work_attempts,application_native_POST_attempts=post_attempts,actual_native_start_count=None,next_case=False,retry=False,T2='NOT_PASSED',io_events=io.events,launch_attempts=io.launch_attempts)
            try:
                budget.call('immutable terminal close',save_new,folder/'terminal.json',terminal)
                seal_index(folder,budget,p4)
            except Exception as exc:
                record_failure(budget,errors,'seal',exc); terminal['first_failure']=budget.failure; terminal['overall']='FAIL'
                # Late diagnostics never create a timely success or rewrite first data.
                if not (folder/'terminal.json').exists(): save_new(folder/'terminal.json',terminal)
    return terminal

def write_raw_new(path,raw):
    require(type(raw) is bytes and len(raw)<=CAP,'Raw member byte cap')
    with Path(path).open('xb') as stream: stream.write(raw)

def read_raw(path):
    def read():
        with Path(path).open('rb') as stream: return stream.read(CAP+1)
    raw=observed_io('observed raw '+str(path),read)
    require(len(raw)<=CAP,'Raw member byte cap'); return raw

def export_completed(folder,ledger,result):
    raw=ledger._runtime_final; require(type(raw) is bytes and len(raw)<=CAP,'Final packet export cap')
    from src.brain.work_research import verify_runtime_packet
    # The real verifier scans decoded semantic values. Re-scanning serialized
    # ledger event JSON would misclassify trusted numeric timestamps as PII.
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    validate_export_structure(strict_json(raw),ledger._policy.scanners)
    return preserve_completed_members(folder,raw,ledger.issued_snapshot,ledger._collection,result,getattr(getattr(ledger,'_runtime_transport',None),'posts',None))

def validate_export_structure(packet,scanners):
    """Closed producer structures plus scanning of EVERY decoded string value.

    Replay binds the issued inputs, schema and transcript. Check producer types
    on residual fields before treating their primitive values as non-text.
    """
    def closed(value,names):
        require(type(value) is dict and set(value)==set(names.split()),'Unexpected export fields/type')
    def fields(value,names,*types):
        for name in names.split():
            require(type(value[name]) in types,'Producer field type: '+name)
    closed(packet,'binding clock_domain events execution issued_manifest nonce prewrite_packet prewrite_sha256 prompt system_original timeline transport v views_sha256 wires')
    require(type(packet['v']) is int and packet['v']==3 and type(packet['wires']) is list and type(packet['events']) is list and type(packet['timeline']) is list,'Export typed packet')
    closed(packet['transport'],'admitted completed generations gets post_bytes posts receipts')
    closed(packet['transport']['admitted'],'chat metadata')
    closed(packet['execution'],'effects files intent')
    fields(packet['execution'],'effects files',list)
    intent=packet['execution']['intent']
    if intent is not None:
        closed(intent,'adapter_uuid args_hash binding bytes dispatch_uuid file_call_id path report_call_id seq sha256')
        fields(intent,'adapter_uuid args_hash dispatch_uuid file_call_id path report_call_id sha256',str)
        fields(intent,'bytes seq',int)
    for file in packet['execution']['files']:
        text='call_id content dispatch_uuid path report_call_id request_id result session_id task_id tool_name'
        closed(file,text+' success')
        fields(file,text,str)
        fields(file,'success',bool)
    for effect in packet['execution']['effects']:
        text='dispatch_id file_call_id path report_call_id request_id session_id state task_id'
        closed(effect,text); fields(effect,text,str)
    for wire in packet['wires']:
        closed(wire,'entity generation hashes identity raw raw_envelope raw_response sampler_schema secured_envelope secured_messages strict_schema')
        fields(wire,'generation',int)
        closed(wire['hashes'],'entity messages sampler strict')
        closed(wire['identity'],'local_manifest_sha256 tags_response version_response')
    transport=packet['transport']
    fields(transport,'completed generations gets post_bytes posts',int)
    fields(transport['admitted'],'chat metadata',int)
    for receipt in transport['receipts']:
        closed(receipt,'admission_error admitted downloaded entity_bytes entity_sha256 error inspected kind method path peer_bytes response_sha256 retained send_reserved socket_bytes status timeout_json')
        fields(receipt,'admitted entity_bytes inspected retained status',int)
        fields(receipt,'downloaded',int,type(None))
        fields(receipt,'peer_bytes socket_bytes',type(None))  # Unmeasured by _ResearchTransport.exchange.
        fields(receipt,'error admission_error',str,type(None))
        fields(receipt,'send_reserved',bool)
    extras={'claim':'adapter_uuid dispatch_uuid seq','expect':'args_hash name seq','file_end':'file_call_id','freeze':'seq','generation':'generation','intent':'file_call_id seq','promote':'seq wire_hash','return':'generation receipt_index','sdk_end':'event_index seq','sdk_start':'event_index seq','secured':'generation','send':'generation receipt_index'}
    for event in packet['timeline']:
        require(event.get('kind') in extras,'Unknown export timeline kind')
        closed(event,'at deadline kind order '+extras[event['kind']])
        for name in ('order','seq','event_index','receipt_index','generation'):
            if name in event: fields(event,name,int)
        for name in ('at','deadline'):
            require(type(event[name]) is str and math.isfinite(float(event[name])) and repr(float(event[name]))==event[name],'Typed export clock')
    def prose(value):
        """Data stays its declared type; never infer serialization from names/text."""
        if isinstance(value,dict):
            for key,item in value.items():
                require(type(key) is str,'Export string key'); prose(key); prose(item)
        elif isinstance(value,list):
            for item in value: prose(item)
        elif isinstance(value,str):
            require(all(scanner.scan(value).clean for scanner in scanners),'Unsafe export decoded value')
        else:
            require(value is None or type(value) in (int,float,bool),'Unexpected export value type')
            if type(value) is float: require(math.isfinite(value),'Nonfinite export value')
    def object_json(value):
        require(type(value) is str,'Producer serialized JSON string required')
        decoded=strict_json(value); require(type(decoded) is dict,'Producer serialized JSON object required')
        return decoded
    def messages(values):
        require(type(values) is list,'Producer message list required')
        for index,message in enumerate(values):
            closed(message,'role content'); role=message['role']; content=message['content']
            require(type(role) is str and type(content) is str,'Producer message types')
            prose(role)
            if index>=3 and index%2==1 and role=='user':
                require(values[index-1]['role']=='assistant' and content.startswith('Observation: '),'Producer SDK observation position/role')
                prose(object_json(content[13:]))
            elif index>=2 and index%2==0 and role=='assistant':
                prose(object_json(content))
            else:
                # System, original user request and ordinary free prose stay text.
                prose(content)
    def native(value):
        require(type(value) is dict,'Producer native response object')
        message=value['message']; closed(message,'role content')
        require(message['role']=='assistant','Producer native response role')
        for key,item in value.items():
            if key!='message': prose(key); prose(item)
        prose(message['role']); prose(object_json(message['content']))
    # Each decoder below is attached to ONE exact producer slot. No suffix,
    # terminal-name or leading-prose heuristic selects decoding anywhere else.
    for key,value in packet.items():
        if key not in ('prewrite_packet','events','wires','timeline','transport'): prose(key); prose(value)
    if packet['prewrite_packet'] is not None: validate_export_structure(object_json(packet['prewrite_packet']),scanners)
    for event in packet['timeline']:
        for key,value in event.items():
            prose(key)
            if key not in ('at','deadline'): prose(value)  # EXACT closed producer clock fields validated above.
    for raw_event in packet['events']:
        event=object_json(raw_event); closed(event,'data timestamp type')
        require(type(event['timestamp']) in (float,int) and event['type'] in ('tool_call_start','tool_call_end'),'Typed export event')
        data=event['data']; closed(data,'agent arguments tool' if event['type']=='tool_call_start' else 'agent latency metadata result success tool')
        if event['type']=='tool_call_end':
            fields(data,'latency',float)  # SDK ToolExecutor records time.time() - t0.
            fields(data['metadata'],'seq generation',int)
            if data['tool']=='ultima_work_research_write':
                visible=object_json(data['result'])
                text='adapter_uuid dispatch_uuid file_call_id path replay_sha256 report_call_id runtime_sha256 sha256'
                closed(visible,text+' binding generation protocol_version seq')
                fields(visible,text,str)
                fields(visible,'generation protocol_version seq',int)
                fields(data['metadata'],'protocol_version',int)
        prose(event['type']); prose(event['timestamp'])
        for key,value in data.items():
            prose(key)
            prose(object_json(value) if event['type']=='tool_call_end' and key=='result' else value)
    for wire in packet['wires']:
        entity=object_json(wire['entity'])
        for key,value in entity.items():
            prose(key)
            if key=='messages': messages(value)
            else: prose(value)
        messages(wire['secured_messages']); native(wire['raw']); native(object_json(wire['raw_response']))
        for key in ('generation','hashes','raw_envelope','sampler_schema','secured_envelope','strict_schema'): prose(wire[key])
        prose(wire['identity']['local_manifest_sha256'])
        prose(object_json(wire['identity']['version_response']))
        tags=object_json(wire['identity']['tags_response'])
        # ListResponse.Model and ModelDetails declare optional metadata slots.
        for model in tags['models']:
            if 'modified_at' in model: fields(model,'modified_at',str,type(None))
            details=model.get('details')
            if details is not None:
                require(type(details) is dict,'Producer model details object required')
                for key,value in details.items():
                    if key=='families' and value is not None:
                        require(type(value) is list and all(type(family) is str for family in value),'Producer model families type')
                    else:
                        require(key in ('parent_model','format','family','families','parameter_size','quantization_level')
                                and (value is None or type(value) is str),'Producer model detail type')
        prose(tags)
    for key,value in packet['transport'].items():
        if key!='receipts': prose(key); prose(value)
    for receipt in packet['transport']['receipts']:
        for key,value in receipt.items():
            prose(key)
            prose(object_json(value) if key=='timeout_json' and value is not None else value)

def preserve_completed_members(folder,raw,issued_snapshot,collection,result,posts):
    require(type(raw) is bytes and len(raw)<=CAP,'Final packet export cap'); packet=strict_json(raw)
    snapshot=asdict(issued_snapshot)
    blobs={'runtime':raw,'views':snapshot.pop('views_json'),'replay':snapshot.pop('replay_json'),
        'collection':json.dumps(asdict(collection),ensure_ascii=False,separators=(',',':')).encode('utf8')}
    members={}
    for role,body in blobs.items():
        name='trusted-'+role+'.raw'; write_raw_new(folder/name,body)
        members[role]=dict(name=name,bytes=len(body),sha256=sha(folder/name))
    ends=[strict_json(e) for e in packet['events'] if strict_json(e).get('type')=='tool_call_end']
    save_new(folder/'trusted-export.json',dict(format=2,complete=True,END=any(e.get('data',{}).get('tool')=='ultima_work_research_write' and e['data'].get('success') is True for e in ends),members=members,
        issued_snapshot=snapshot,native_POST_attempts=posts,ack_admitted=result.get('status')=='succeeded'))

def read_completed(folder,exported):
    require(exported.get('format')==2 and set(exported.get('members',{}))=={'runtime','views','replay','collection'},'Export members required')
    blobs={}
    for role,item in exported['members'].items():
        require(item['name']=='trusted-'+role+'.raw' and type(item['bytes']) is int and 0<=item['bytes']<=CAP,'Export member binding')
        body=read_raw(folder/item['name']); require(len(body)==item['bytes'] and hashlib.sha256(body).hexdigest()==item['sha256'],'Export member digest')
        blobs[role]=body
    return blobs

def verify_exports(folder,result,p4,*,readonly=False):
    from src.brain.work_tools import WorkBinding,ResearchRuntimeInputs
    from src.brain.work_navigation import IssuedSnapshotV3,resolve_v3,render_v3
    from src.brain.work_research import ResearchCollection,verify_runtime_packet
    exported=load(folder/'trusted-export.json'); inputs=load(folder/'runtime-inputs.json')
    require(exported.get('complete') is True and exported.get('END') is True,'Missing complete packet or END')
    reconcile_results(result,load(folder/'service-first-result.json'))
    blobs=read_completed(folder,exported); raw=blobs['runtime']
    s=exported['issued_snapshot']; s['binding_key']=tuple(s['binding_key'])
    s['views_json']=blobs['views']; s['replay_json']=blobs['replay']
    snapshot=IssuedSnapshotV3(**s); inputs['binding_key']=tuple(inputs['binding_key']); runtime_inputs=ResearchRuntimeInputs(**inputs)
    binding=WorkBinding(Path(inputs['root']),*inputs['binding_key'])
    require(inputs['binding_key']==tuple(result[k] for k in ('request_id','session_id','task_id')),'Independent input binding mismatch')
    require(Path(inputs['root'])==folder/'outputs'/result['task_id'],'Independent root mismatch')
    collection=ResearchCollection(**strict_json(blobs['collection']))
    frozen=corpus()['sources']; actual_sources=strict_json(collection.catalogue_json)
    require([(s['final_url'],s['body'],s['decoded_body_sha256']) for s in actual_sources]==[(s['final_url'],s['body'],s['decoded_body_sha256']) for s in frozen],'Original four-source corpus mismatch')
    attempts=strict_json(collection.attempts_json)
    require(sum(x['tool_name']=='ultima_work_web_search' for x in attempts)==1 and sum(x['tool_name']=='ultima_work_http_get' for x in attempts)==4,'Original collection attempt caps')
    packet=verify_runtime_packet(binding,snapshot,collection,raw,require_ack=True,runtime_inputs=runtime_inputs)
    from openjarvis.security.scanner import SecretScanner,PIIScanner
    factories={c.__module__+'.'+c.__qualname__:c for c in (SecretScanner,PIIScanner)}
    scanner_policy=strict_json(snapshot.replay_json)['policy']
    validate_export_structure(packet,tuple(factories[item['name']]() for item in scanner_policy['scanners']))
    require(1<=packet['transport']['posts']<=8,'POST attempt bound')
    resolved,bindings=resolve_v3(packet['wires'][-2]['secured_envelope']['action_input'],snapshot,collection)
    rendered=render_v3(resolved,collection.catalogue_json,bindings=bindings)
    verify_readback(folder,result,p4,rendered.content,readonly=readonly)
    require(exported['ack_admitted'] is True,'Final ACK missing')
    inventory=output_inventory(folder,p4)
    if not readonly: save_new(folder/'accepted-effects.json',inventory)
    return dict(native_POST_attempts=packet['transport']['posts'],inventory=inventory)

def verify_readback(folder,result,p4,rendered_content,*,readonly=False):
    if readonly:
        task=p4.uuid_text(result['task_id']); artifacts=[]
        for item in result.get('artifacts',[]):
            path=p4.artifact_path(folder,task,item['path']); raw=read_raw(path)
            artifacts.append(dict(item,text=raw.decode('utf8'),external_sha256=hashlib.sha256(raw).hexdigest()))
    else: artifacts=p4.read_artifacts(folder,result)
    require(len(artifacts)==1 and Path(artifacts[0]['path']).name=='research.md' and artifacts[0]['sha256']==artifacts[0]['external_sha256'],'Exact external research.md readback')
    require(artifacts[0]['text']==rendered_content,'Independent rendered byte readback mismatch')
    inventory=output_inventory(folder,p4)
    require(len(inventory)==1 and inventory[0]['path']==artifacts[0]['path'] and inventory[0]['sha256']==artifacts[0]['external_sha256'],'Unexpected output set')
    return artifacts

def output_inventory(folder,p4):
    budget=_OBSERVING.get()
    if budget is None: return p4.output_inventory(folder)
    records=[]
    for path in guarded_files(folder/'outputs',budget):
        require(len(records)<64,'Observed output count cap')
        raw=read_raw(path); require(len(raw)<=1048576,'Observed output size cap')
        records.append(dict(path=str(path),sha256=hashlib.sha256(raw).hexdigest(),bytes_hex=raw.hex()))
    return records

def guarded_files(root,budget,*,reserve_index=False):
    """Own filesystem walk: admission for each open, iteration and member stat."""
    root=Path(root).absolute(); files=[]; data_count=0; fixed_index=False
    if not budget.call('directory existence',root.exists): return files
    metadata=budget.call('directory root stat',root.lstat)
    require(stat.S_ISDIR(metadata.st_mode) and not getattr(metadata,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Directory root reparse/type')
    def walk(directory):
        nonlocal data_count,fixed_index
        budget.pre('directory open'); entries=os.scandir(directory)
        try:
            budget.post('directory open')
            while True:
                budget.pre('directory iteration')
                try: entry=next(entries)
                except StopIteration:
                    budget.post('directory iteration'); break
                budget.post('directory iteration')
                path=Path(entry.path).absolute(); require(path.is_relative_to(root),'Directory member escape')
                metadata=budget.call('directory member stat',entry.stat,follow_symlinks=False)
                require(not stat.S_ISLNK(metadata.st_mode) and not getattr(metadata,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Directory member reparse')
                if stat.S_ISDIR(metadata.st_mode): walk(path)
                elif stat.S_ISREG(metadata.st_mode):
                    if reserve_index and path.parent==root and path.name=='seal-index.json':
                        require(not fixed_index,'Duplicate fixed root index'); fixed_index=True
                    else:
                        require(data_count<256,'Closed directory data member cap'); data_count+=1
                    files.append(path)
                else: raise ValueError('Unknown directory member type')
        finally: entries.close()
    walk(root)
    if reserve_index: require(fixed_index,'Fixed root index missing')
    return files

def no_output_descendants(root,budget):
    """Inert effects: any child entry, including an empty directory, is an effect."""
    root=Path(root).absolute()
    def root_status():
        try: return root.lstat()
        except FileNotFoundError: return None
    metadata=budget.call('inert output root stat',root_status)
    if metadata is None: return True
    require(stat.S_ISDIR(metadata.st_mode) and not getattr(metadata,'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT,'Inert output root reparse/type')
    budget.pre('inert output directory open'); entries=os.scandir(root)
    try:
        budget.post('inert output directory open'); budget.pre('inert output directory iteration')
        try: next(entries)
        except StopIteration:
            budget.post('inert output directory iteration'); return True
        budget.post('inert output directory iteration'); return False
    finally: entries.close()

def validate_final_outputs(folder,result,accepted,p4):
    current=output_inventory(folder,p4)
    require(p4.inventory_map(current)==p4.inventory_map(accepted),'Closed final output drift')
    require(len(current)==1 and len(result.get('artifacts',[]))==1,'Closed exact output set')
    artifact=result['artifacts'][0]
    require(current[0]['path']==artifact['path'] and current[0]['sha256']==artifact['sha256'],'Closed output artifact binding')
    return current

def compare_pre_cleanup(accepted,observed,p4):
    require(p4.inventory_map(accepted)==p4.inventory_map(observed),'Observed pre-cleanup output drift')

def install_browser_fixture():
    """Exact old Browser search/GET fixture, without the old native send hook."""
    import ddgs
    import httpx
    sources={s['final_url']:s for s in corpus()['sources']}; original_dns=socket.getaddrinfo
    class Search:
        def text(self,query,max_results=5,**kwargs):
            return [{'title':'Retained official source '+str(i),'href':url,'body':'Controlled source discovery; read the full body.'} for i,url in enumerate(sources,1)][:max_results]
    def get(method,url,**kwargs):
        require(method=='GET' and str(url) in sources and kwargs['follow_redirects'] is False and kwargs['timeout']==5,'Unexpected fixture HTTP')
        source=sources[str(url)]
        return httpx.Response(200,content=source['body'].encode('utf8'),headers={'content-type':source['content_type']},request=httpx.Request(method,url))
    def dns(host,port,*args,**kwargs):
        if host in ('127.0.0.1','localhost','::1'): return original_dns(host,port,*args,**kwargs)
        if host=='raw.githubusercontent.com': return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',int(port or 443)))]
        raise OSError('Nonfixture public DNS forbidden')
    ddgs.DDGS=Search; httpx.request=get; socket.getaddrinfo=dns

def install_trusted_exports(folder):
    """Observe trusted inputs before composition; only bounded safe ledger output."""
    import threading
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    state=threading.local(); init=WorkLedger.__init__; freeze=WorkLedger._freeze_runtime_inputs; submit=WorkService.submit_work
    def observed_init(self):
        init(self)
        require(getattr(state,'ledger',None) is None,'One work ledger only'); state.ledger=self
    def observed_freeze(self,prompt,max_tokens):
        freeze(self,prompt,max_tokens)
        save_new(folder/'runtime-inputs.json',asdict(self._runtime_inputs))
    def observed_submit(self,*args,**kwargs):
        try:
            result=submit(self,*args,**kwargs)
            # Preserve product output before any export work that can fail.
            save_new(folder/'service-first-result.json',result)
            ledger=getattr(state,'ledger',None)
            require(ledger is not None,'Missing trusted ledger')
            raw=getattr(ledger,'_runtime_final',None); snapshot=ledger.issued_snapshot
            if type(raw) is bytes and raw and snapshot is not None:
                try: export_completed(folder,ledger,result)
                except Exception as exc:
                    save_new(folder/'trusted-export.failure.json',dict(complete=False,END=False,error_type=type(exc).__name__,native_POST_attempts=getattr(getattr(ledger,'_runtime_transport',None),'posts',None),actual_native_start_count=None))
                    raise
            else:
                transport=getattr(ledger,'_runtime_transport',None)
                save_new(folder/'trusted-export.json',dict(complete=False,END=False,native_POST_attempts=getattr(transport,'posts',None),actual_native_start_count=None,first_failure=bool(ledger.first_failure)))
            return result
        finally: state.ledger=None
    WorkLedger.__init__=observed_init; WorkLedger._freeze_runtime_inputs=observed_freeze; WorkService.submit_work=observed_submit

def run_case(authority_path:Path,ledger_path:Path)->dict:
    budget=entry_budget()
    context,p4=admit(authority_path,ledger_path,budget=budget)
    return execute_case(context,p4)

def seal_index(folder,budget,p4):
    files={}
    for path in guarded_files(folder,budget):
        budget.pre('seal member')
        p4.no_reparse(path)
        if path.is_file():
            require(len(files)<256 and path.stat().st_size<=CAP,'Seal index bound')
            files[str(path.relative_to(folder))]=budget.call('seal member hash',sha,path)
    budget.call('seal index close',save_new,folder/'seal-index.json',dict(run_id=budget.run_id,timing=budget.timing(),files=files))

class RootInvocation:
    """Prepared trusted ROOT invocation, never called by a product/inert child.

    Root creates this BEFORE writing concrete authority. parent_timing() supplies
    its same-clock native parent binding. call() is one-shot; it observes the
    returned closed package, then makes a nonrenewable timing adjudication. The
    child terminal itself can never provide this witness.
    """
    def __init__(self,*,clock=time.monotonic_ns):
        self.budget=Deadline(clock=clock); self.observer=TimingObservation(self.budget); self.called=False
    def parent_timing(self):
        module=self.budget.call('root pinned import',load_p4)
        return dict(self.budget.timing(),parent_identity=self.budget.call('root native identity',module.identity,os.getpid()))
    def call(self,entry,*args,**kwargs):
        require(not self.called,'Root invocation already consumed'); self.called=True
        token=_ENCLOSING.set(self.budget); result=None; digest=None; proofs={}; error=None; binding={}; observing=None
        try:
            result=entry(*args,**kwargs)
            self.budget.phase='seal'; observing=_OBSERVING.set(self.budget)
            require(isinstance(result,dict),'Returned closed package required')
            folder=Path(result['folder']); terminal=self.budget.call('root terminal read',load,folder/'terminal.json'); index=self.budget.call('root seal index read',load,folder/'seal-index.json')
            require(index['run_id']==self.budget.run_id and terminal['run_id']==self.budget.run_id,'Root observation run binding')
            require(index['timing']==self.budget.timing() and terminal['timing']==self.budget.timing(),'Root observation origin binding')
            required=({'attempt.json','admission.json','child-clearance.json','child-clearance.consumed.json','argv-roundtrip.json','native-argv.json','native-argv.raw','native-members.json','inert-exchange.json','listener.json','owned-tree.json','cleanup.json','protected-before.json','protected-after.json','boundary-before.json','boundary-after.json','terminal.json','server.stdout','server.stderr'} if terminal.get('kind')=='inert' else {'attempt.json','admission.json','child-clearance.json','child-clearance.consumed.json','argv.json','native-argv.json','native-argv.raw','native-members.json','effective-schedule.json','first-product.raw','product-result.json','service-first-result.json','trusted-export.json','trusted-runtime.raw','trusted-views.raw','trusted-replay.raw','trusted-collection.raw','runtime-inputs.json','accepted-effects.json','post-cleanup-effects.json','pre-cleanup-effects.json','external-artifacts.json','external-readback-attempts.json','owned-tree.json','cleanup.json','listener.json','boundary-before.json','boundary-after.json','terminal.json','server.stdout','server.stderr','cli.stdout','cli.stderr'})
            require(required<=set(index['files']),'Required closed execution evidence absent')
            observed_files={str(p.relative_to(folder)) for p in guarded_files(folder,self.budget,reserve_index=True)}
            require(observed_files==set(index['files'])|{'seal-index.json'},'Missing/extra sealed data')
            for name,expected in index['files'].items():
                raw=Path(name); require(not raw.is_absolute() and '..' not in raw.parts,'Seal relative member')
                require(self.budget.call('root closed member hash',sha,folder/raw)==expected,'Closed required data changed')
            digest=sha(folder/'terminal.json')
            proofs=validate_observed_package(folder,terminal,index,self.budget)
            binding=dict(kind=terminal.get('kind','actual'),folder=str(folder),seal_index_sha256=sha(folder/'seal-index.json'),member_hashes=dict(index['files']))
        except Exception as exc:
            error=type(exc).__name__; self.budget.failure=self.budget.failure or 'witness: '+str(exc)
        finally:
            if observing is not None: _OBSERVING.reset(observing)
            _ENCLOSING.reset(token)
        # Sampling occurs AFTER entry returned and after every required data hash
        # read closed. No child timestamp/mtime is used for the timing decision.
        witness=self.observer.finish(digest,proofs); witness['observation_error']=error; witness.update(binding)
        return dict(result=result,witness=witness)

def validate_observed_package(folder,terminal,index,budget):
    admitted=getattr(budget,'admitted',None); require(isinstance(admitted,dict),'Trusted admission proof absent')
    mode=admitted['mode']; canonical=V/'inert'/budget.run_id if mode=='inert' else V/'actual'/CASE
    require(folder==canonical and admitted['folder']==str(folder) and terminal.get('kind','actual')==mode,'Canonical observed mode/root')
    require(load(folder/'admission.json')==admitted and admitted['timing']==budget.timing(),'Observed admitted data mismatch')
    require(terminal.get('overall') in ('PENDING_ROOT_INDEPENDENT_REVIEW','READY_FOR_ROOT_TIMING_WITNESS') and not terminal.get('errors') and terminal.get('first_failure') is None,'Observed failed terminal')
    p4=budget.call('root pinned primitive import',load_p4)
    require(compare_operational_pins(admitted,budget)==admitted['pins'],'Observed operational pin drift')
    protected=admitted['baseline']['protected']; budget.call('root exact protected members',validate_protected_members,protected,p4)
    for name in ('boundary-before.json','boundary-after.json'):
        boundary=load(folder/name); require(boundary==dict(pins=admitted['pins'],protected=protected),'Substantive protected/pin boundary')
    native=load(folder/'native-members.json')
    require(native==getattr(budget,'native_members',None) and len(native.get('live_pids',[]))>=1 and len(native.get('members',[]))>=2,'Substantive native proof absent')
    members={m['identity']['pid']:m for m in native['members']}; root=native['launcher_identity']['pid']; listener=load(folder/'listener.json')
    require(listener==native['listener'] and listener['identity']['pid']!=root and members[listener['identity']['pid']]['parent']==root,'Observed native base listener relationship')
    require(set(map(int,native['snapshot']))==set(native['live_pids']),'Observed complete native row set')
    wire=read_raw(folder/'native-argv.raw'); proof=load(folder/'native-argv.json')
    require(proof['raw_sha256']==hashlib.sha256(wire).hexdigest() and proof['raw_hex']==wire.hex() and proof['records']==native['snapshot'],'Original native raw/record proof binding')
    rows=strict_json(wire.decode('ascii')); rows=[rows] if isinstance(rows,dict) else rows
    decoded={}
    for row in rows:
        row=dict(row); row['CommandLine']=base64.b64decode(row['CommandLineBase64'],validate=True).decode('utf-16-le')
        decoded[str(row['ProcessId'])]=row
    require(decoded==native['snapshot'],'Original native ASCII/UTF16 proof mismatch')
    for pid,row in native['snapshot'].items():
        member=members[int(pid)]; require(row['ParentProcessId']==member['parent'] and p4.argv_parse(row['CommandLine'])[1:]==native['argv'],'Observed native argv/parent')
    tree=load(folder/'owned-tree.json'); cleanup=load(folder/'cleanup.json')
    require(not tree.get('errors') and cleanup.get('status')=='PASS' and cleanup.get('port_closed') is True and not cleanup.get('errors'),'Substantive cleanup proof')
    expected={m['identity']['pid']:m['identity'] for m in tree['processes']+tree.get('auxiliary',[])}
    records=cleanup.get('processes',[])
    require(terminal['cleanup'].get('status')=='PASS' and terminal['cleanup'].get('port_definitively_closed') is True and terminal['cleanup'].get('logs_closed') is True and terminal['cleanup'].get('processes')==records,'Terminal/independent cleanup disagreement')
    require(expected and len(records)==len(expected) and {r['identity']['pid']:r['identity'] for r in records}==expected and all(r.get('absent') is True for r in records),'Exact native cleanup member set')
    owned=getattr(budget,'owned',None)
    require(owned is not None and {pid:item['identity'] for pid,item in owned.known.items()}=={m['identity']['pid']:m['identity'] for m in tree['processes']},'Trusted native ownership member binding')
    require(len(owned.logs)==(2 if mode=='inert' else 4) and all(stream.closed for stream in owned.logs),'Trusted closed log handles required')
    cleared=load(folder/'child-clearance.json'); consumed=load(folder/'child-clearance.consumed.json')
    require('child-clearance.ready' in index['files'] and read_raw(folder/'child-clearance.ready')==b'','Observed closed clearance publication')
    require(cleared['timing']==budget.timing() and cleared['mode']==mode and cleared['argv']==native['argv'] and consumed['clearance_sha256']==sha(folder/'child-clearance.json') and consumed['timing']==budget.timing() and any(m['identity']==consumed['identity'] for m in cleared['members']),'Observed one-use child clearance')
    require(consumed['identity']==listener['identity']==cleared['base_identity'] and cleared['launcher_identity']==native['launcher_identity'] and len(cleared['members'])==2 and cleared['attempt_sha256']==sha(folder/'attempt.json') and cleared['authority_sha256']==admitted['pins'][str(V/'inert-authority.json' if mode=='inert' else V/'controller-authority'/f'{CASE}.json')],'Observed intended child/authority binding')
    with PrivateIO(p4,budget) as io:
        require(not p4.process_snapshot(list(expected)),'Native owned process remains at observation')
        require(not p4.listener_owner(admitted['port']),'Listener remains at observation')
        probe=p4.socket.socket(); probe.settimeout(1)
        try: probe.connect_ex(('127.0.0.1',admitted['port']))
        finally: probe.close()
        require(io.port_closed,'Observed port closure unknown')
    if mode=='inert':
        validate_inert_exchange(load(folder/'inert-exchange.json'),getattr(budget,'inert_exchange',None),admitted,listener,budget)
        require(load(folder/'protected-before.json')==protected and load(folder/'protected-after.json')==protected,'Inert protected proof')
        roundtrip=load(folder/'argv-roundtrip.json'); require(roundtrip['question']==corpus()['query'] and native['argv']==inert_argv(folder,admitted['port']) and roundtrip['argv']==native['argv'][4:],'Observed original query/full argv roundtrip')
        require(no_output_descendants(folder/'outputs',budget),'Unexpected inert outputs')
    else:
        cli=load(folder/'product-result.json'); service=load(folder/'service-first-result.json'); reconcile_results(cli,service)
        require(cli.get('status')=='succeeded' and cli==load(folder/'first-product.raw'),'Observed first result mismatch')
        attempt=load(folder/'attempt.json'); argv=load(folder/'argv.json')
        require(all(cli[k]==attempt[k] for k in ('request_id','session_id')),'Observed CLI/attempt identity binding')
        context=dict(folder=folder,port=admitted['port'],request_id=attempt['request_id'],session_id=attempt['session_id'])
        server_args,cli_args=candidate_argv(context)
        require(argv['server']==server_args==native['argv'] and argv['cli']==cli_args and terminal['product_status']==cli['status'] and terminal['product_result_sha256']==sha(folder/'product-result.json') and terminal['service_first_result_sha256']==sha(folder/'service-first-result.json'),'Observed CLI/service/argv manifest binding')
        verify_exports(folder,cli,p4,readonly=True)
        accepted=load(folder/'accepted-effects.json'); compare_pre_cleanup(accepted,load(folder/'pre-cleanup-effects.json'),p4)
        final=validate_final_outputs(folder,cli,accepted,p4)
        require(final==load(folder/'post-cleanup-effects.json') and str(Path(cli['artifacts'][0]['path']).relative_to(folder)) in index['files'],'Required indexed task output')
    return dict(closed=True,cleanup=True,pins=True,protected=True,readback=True)

def inert_admit(*,child=False,budget=None):
    budget=budget or entry_budget()
    budget.call('inert source admission',check_inputs); p4=budget.call('inert pinned import',load_p4); path=p4.no_reparse(V/'inert-authority.json')
    authority=budget.call('inert authority read',load,path); validate_inert_documents(authority,dt.datetime.now(dt.timezone.utc))
    bind_parent(budget,authority,p4)
    budget.call('inert package admission',package_check,p4)
    require(authority.get('approval_sha256')==sha(V/'harness-approval.json'),'Inert independent approval binding')
    run_id=p4.uuid_text(authority['run_id']); folder=p4.no_reparse(V/'inert'/run_id)
    require(authority.get('folder')==str(folder) and type(authority.get('port')) is int and 1024<=authority['port']<=65535 and authority['port']!=11434,'Inert root/port')
    proof=load(p4.no_reparse(V/'inert-native-baseline.json'))
    require(authority.get('native_baseline_sha256')==sha(V/'inert-native-baseline.json'),'Inert native baseline binding')
    baseline=budget.call('inert native baseline',check_native_baseline,proof,p4)
    if child: require((folder/'attempt.json').exists(),'Claimed inert child required')
    else:
        with PrivateIO(p4,budget): require(not folder.exists() and not p4.listener_owner(authority['port']),'Exclusive inert folder/port required')
    require(run_id==budget.run_id,'Inert root run identity binding')
    admitted_record('inert',folder,authority['port'],authority,proof,budget)
    budget.post('inert admission'); return authority,folder,p4,baseline

def inert_argv(folder,port):
    return ['-B','-X','utf8',str(HERE/'adapter.py'),'--inert-child',str(folder),'--port',str(port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--question',corpus()['query']]

def inert_child(folder,args):
    budget=entry_budget(); authority,expected,p4,_=inert_admit(child=True,budget=budget)
    require(folder==expected and args==inert_argv(folder,authority['port'])[6:],'Exact original inert argv required')
    return inert_child_entry(dict(folder=folder,port=authority['port'],budget=budget,mode='inert'),p4,list(sys.orig_argv[1:]),sha(V/'inert-authority.json'))

def inert_child_entry(context,p4,native_argv,authority_sha256,*,constructor=None):
    require(context['mode']=='inert','Inert child mode required')
    folder=context['folder']; budget=context['budget']
    consume_clearance(context,p4,native_argv,authority_sha256)
    from http.server import BaseHTTPRequestHandler,HTTPServer
    save_new(folder/'argv-roundtrip.json',dict(question=native_argv[-1],argv=native_argv[4:],encoding='native Unicode argv to UTF8 JSON'))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            require(self.path=='/inert','Only inert endpoint')
            body=b'{"inert":true}'; self.send_response(200); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args): pass
    constructor=constructor or HTTPServer
    address=('127.0.0.1',context['port'])
    budget.pre('inert child listener startup')
    server=constructor(address,Handler); server.timeout=.1
    try:
        while not (folder/'stop').exists(): server.handle_request()
    finally: server.server_close()

def actual_child_entry(context,p4,native_argv,authority_sha256,*,dispatch=None):
    require(context['mode']=='actual','Actual child mode required')
    consume_clearance(context,p4,native_argv,authority_sha256)
    import runpy
    dispatch=dispatch or runpy.run_module
    previous=list(sys.argv)
    try:
        with candidate_import_path():
            install_browser_fixture(); install_trusted_exports(context['folder'])
            # Derive product flags from the same canonical full argv that was
            # consumed, never from parser leftovers.
            sys.argv=['src.brain.agent_server',*candidate_argv(context)[0][6:]]
            context['budget'].pre('actual child product startup')
            return dispatch('src.brain.agent_server',run_name='__main__')
    finally: sys.argv[:]=previous

def main():
    budget=entry_budget()
    parser=argparse.ArgumentParser(); parser.add_argument('--case',choices=[CASE]); parser.add_argument('--child-server',type=Path)
    parser.add_argument('--inert-child',type=Path)
    args,remaining=parser.parse_known_args()
    if args.inert_child:
        inert_child(args.inert_child,remaining); return 0
    if args.child_server:
        context,p4=admit(V/'controller-authority'/f'{CASE}.json',V/'controller-ledger.json',child=True,budget=budget)
        require(args.child_server==context['folder'],'Claimed first-case child required')
        actual_child_entry(context,p4,list(sys.orig_argv[1:]),sha(V/'controller-authority'/f'{CASE}.json'))
        return 0
    require(args.case==CASE and not remaining,'Explicit first case required')
    print(json.dumps(run_case(V/'controller-authority'/f'{CASE}.json',V/'controller-ledger.json'),ensure_ascii=False))
    return 2  # Standalone command has no trusted enclosing timing witness.

if __name__=='__main__': raise SystemExit(main())
