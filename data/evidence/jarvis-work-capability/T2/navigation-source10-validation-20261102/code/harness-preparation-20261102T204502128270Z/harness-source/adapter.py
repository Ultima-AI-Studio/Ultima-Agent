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
from contextvars import ContextVar
from contextlib import contextmanager

HERE=Path(__file__).resolve().parent
V=HERE.parent
T=V.parent
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
P4=T/'e03-resume-20261102/preparation-r4/controller.py'
P1=P4.parent.parent/'preparation/acceptance_adapter.py'
MANIFEST_SHA='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
PREPARATION_SHA='0e8c2e273bc2a4c35d0fd01e4c0022955609cb4bcecc2ec1f47d3bf95cdd5418'
CANDIDATE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
MODEL='qwen3-8b-uncensored'
CASE='E02-controlled-1'
BUDGETS=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,outer_seconds=315,retry=0)
CORPUS=T/'source6-native-reference/controlled-corpus-inputs/corpus.json'
CAP=4*1024*1024
PY=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')
CLOCK_DOMAIN='monotonic_ns;same-host='+socket.gethostname()
_ENCLOSING=ContextVar('source10_root_enclosing',default=None)

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
        self.pre(label); result=function(*args,**kwargs); self.post(label); return result
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
                suffix=' | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
                snapshot=re.fullmatch(r'Get-CimInstance Win32_Process(?: -Filter "ProcessId=[1-9][0-9]*(?: OR ProcessId=[1-9][0-9]*)*")?'+re.escape(suffix),script)
                listener=re.fullmatch(r'@\(Get-NetTCPConnection -State Listen -LocalPort [0-9]+ -ErrorAction SilentlyContinue \| Select-Object -ExpandProperty OwningProcess\) \| ConvertTo-Json -Compress',script)
                require(snapshot or listener,'Only pinned P4 snapshot/listener I/O')
                requested=kwargs['timeout']; kwargs['timeout']=b.clip(requested,'P4 check_output')
                owner.events.append(dict(io='check_output',argv=argv,timeout=kwargs['timeout'],phase=b.phase))
                result=self.original.check_output(argv,**kwargs); b.post('P4 check_output'); return result
        class ClockIO(Delegate):
            def sleep(self,seconds):
                result=self.original.sleep(b.clip(seconds,'P4 sleep')); b.post('P4 sleep'); return result
        class Probe:
            def __init__(self,raw,allowance): self.raw=raw; self.allowance=allowance; self.closed=False
            def settimeout(self,seconds):
                # P4 sets timeout before its try/finally. Do not raise a budget
                # exception there; scope finally also owns closure of this probe.
                return self.raw.settimeout(min(seconds,self.allowance))
            def connect_ex(self,address):
                b.pre('cleanup port probe'); code=self.raw.connect_ex(address)
                owner.port_closed=(code in {errno.ECONNREFUSED,10061})
                owner.events.append(dict(io='port',code=code,definitive_refusal=owner.port_closed))
                try: b.post('cleanup port probe')
                except Exception: owner.port_closed=False; raise
                return code
            def close(self):
                try: return self.raw.close()
                finally: self.closed=True
        class SocketIO(Delegate):
            def socket(self,*args,**kwargs):
                allowance=b.clip(1,'cleanup socket allocation')
                raw=self.original.socket(*args,**kwargs)
                probe=Probe(raw,allowance); owner.probes.append(probe); return probe
        def terminate(key):
            b.pre('full original P1 termination',full_ns=10000000000)
            event=dict(io='terminate_owned',identity=key,entered=True,returned=False); owner.events.append(event)
            try:
                result=owner.saved['terminate_owned'](key); event['returned']=True
                b.post('original P1 termination'); return result
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
        finally:
            self.wrap_waits(owned)
            event['registered_launchers']=len(owned.launchers); event['known_identities']=len(owned.known)
    def cleanup(self,owned,port):
        self.budget.phase='cleanup'; self.budget.pre('cleanup entry'); self.wrap_waits(owned)
        try: result=owned.cleanup(port)
        except Exception as exc: result=dict(status='FAIL',error=type(exc).__name__,effects_unknown=True)
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

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()

def load(path):
    with Path(path).open('rb') as stream: raw=stream.read(CAP+1)
    require(len(raw)<=CAP,'Evidence byte cap')
    def pairs(items):
        result={}
        for key,value in items:
            require(key not in result,'Duplicate JSON field'); result[key]=value
        return result
    return json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs)

def save_new(path,value):
    raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False).encode('utf8')
    require(len(raw)<=CAP,'Evidence byte cap')
    with Path(path).open('xb') as stream: stream.write(raw)

def check_inputs():
    require(Path(sys.executable).resolve()==PY.resolve(),'Exact authorized interpreter required')
    require(not sys.flags.optimize and sys.flags.dont_write_bytecode and sys.flags.utf8_mode==1,'Python -B -X utf8 required')
    require(sha(V/'source10-candidate-manifest.json')==MANIFEST_SHA,'Source10 manifest drift')
    require(sha(V/'harness-preparation-authority.json')==PREPARATION_SHA,'Preparation authority drift')
    m=load(V/'source10-candidate-manifest.json'); prep=load(V/'harness-preparation-authority.json')
    require(m['candidate']==CANDIDATE and Path(m['candidate_root'])==C,'Candidate mismatch')
    require(prep['kind']=='source10_harness_preparation_only' and prep['candidate_manifest_sha256']==MANIFEST_SHA and prep['actual'] is False and prep['model_calls']==0,'Preparation fields')
    files=dict(m['source_files'],**m['sdk22'],**m['dependencies'])
    files[m['model']['policy_path']]=m['model']['policy_sha256']
    files[m['model']['local_manifest_path']]=m['model']['local_manifest_observed_sha256']
    for key in ('path','report_path'): files[m['code_gate'][key]]=m['code_gate']['sha256' if key=='path' else 'report_sha256']
    files[m['historical_source21_path']]=m['historical_source21_sha256']
    files[m['original_corpus_readback']]=m['original_corpus_readback_sha256']
    files[str(V/'harness-deadline-design/root-decision.json')]='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
    current={p:sha(p) for p in files}
    require(current==files,'Pinned source/SDK/dependency/model/policy drift')
    return current

def check_import_origins():
    from importlib.machinery import PathFinder
    manifest=load(V/'source10-candidate-manifest.json')
    for raw in manifest['sdk22']:
        path=Path(raw); site=next(p for p in path.parents if p.name=='site-packages')
        name='.'.join(path.relative_to(site).with_suffix('').parts)
        cached=sys.modules.get(name)
        if cached is not None: require(Path(getattr(cached,'__file__','')).resolve()==path.resolve(),'Import origin '+name)
        search=sys.path
        for index in range(1,len(name.split('.'))+1):
            prefix='.'.join(name.split('.')[:index]); spec=PathFinder.find_spec(prefix,search)
            require(spec is not None,'Missing pinned import '+prefix)
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
    require(sha(P4)=='8b8fb6fdf4868b3bb8cea61daaf402e5336f86167d0be84e04c455586d98706f','P4 drift')
    require(sha(P1)=='d91ddf5e44a19d6143ee8657f1e0946617eb1c77197c399d017ace39cad02da4','P1 drift')
    cached=sys.modules.get('acceptance_adapter')
    require(cached is None or Path(getattr(cached,'__file__','')).resolve()==P1.resolve(),'Unexpected cached acceptance_adapter')
    if cached is not None: require(getattr(cached,'__source10_verified_sha__',None)==sha(P1),'Unverified cached acceptance_adapter')
    spec=importlib.util.spec_from_file_location('source10_p4_definitions',P4)
    module=importlib.util.module_from_spec(spec); paths=list(sys.path)
    try: spec.loader.exec_module(module)
    finally: sys.path[:]=paths
    require(Path(module.old.__file__).resolve()==P1.resolve(),'P1 import origin')
    module.old.__source10_verified_sha__=sha(P1)
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
    require(len(identities)==5 and len({x['pid'] for x in identities})==5,'Protected exact five baseline')
    expected=p4.protected()  # Original legacy prerequisite returns CURRENT native identities.
    require({x['pid']:x for x in identities}=={x['pid']:x for x in expected},'Exact protected member binding')
    require(all(type(x['created_filetime']) is int and x['created_filetime']>0 and p4.identity(x['pid'])==x for x in identities),'Exact native identity drift')
    return identities

def package_check(p4):
    package=load(HERE/'manifest.json')
    require(set(package['files'])=={'adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md'},'Exact six-file package')
    for name,digest in package['files'].items(): require(sha(p4.no_reparse(HERE/name))==digest,'Harness drift')
    approval=load(p4.no_reparse(V/'harness-approval.json'))
    require(approval.get('reviewer')=='root-independent' and approval.get('overall')=='PASS' and approval.get('manifest_sha256')==sha(HERE/'manifest.json'),'Independent harness approval required')

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
    budget.call('package admission',package_check,p4)
    require(a.get('ledger_sha256')==sha(ledger_path) and a.get('approval_sha256')==sha(V/'harness-approval.json'),'Ledger/approval binding')
    proofpath=p4.no_reparse(V/'native-preflight'/f'{CASE}.json'); proof=budget.call('native proof read',load,proofpath)
    require(a.get('native_preflight_sha256')==sha(proofpath),'Native preflight binding'); budget.call('native admission baseline',check_native_baseline,proof,p4)
    m=load(V/'source10-candidate-manifest.json')
    local_manifest=budget.call('local model manifest read',Path(m['model']['local_manifest_path']).read_bytes)
    budget.call('local native metadata verification',p4.old.metadata_valid,dict(ok=True,model=MODEL,agent='native_react'),proof['version'],proof['tags'],local_manifest)
    folder=p4.no_reparse(V/'actual'/CASE)
    require(a.get('folder')==str(folder) and type(a.get('port')) is int and 1024<=a['port']<=65535 and a['port']!=11434,'Case root/port')
    if child: require((folder/'attempt.json').exists(),'Claimed child only')
    else:
        require(not folder.exists(),'First case already attempted')
        require(not (V/'actual').exists() or not list((V/'actual').iterdir()),'Unexpected sibling case')
        with PrivateIO(p4,budget): require(not p4.listener_owner(a['port']),'Port occupied')
    budget.post('case admission')
    return dict(folder=folder,port=a['port'],request_id=str(uuid.uuid4()),session_id=str(uuid.uuid4()),baseline=proof,authority=a,ledger=l,budget=budget),p4

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
    b=context['budget']; b.call('clearance original discovery',owned.discover)
    members=[]
    for item in owned.known.values():
        if item['role']!='server': continue
        actual=item['argv'] if isinstance(item['argv'],list) else p4.argv_parse(item['argv'])[1:]
        require(actual==argv and p4.identity(item['identity']['pid'])==item['identity'],'Registered child clearance identity/argv')
        members.append(dict(identity=item['identity'],role='server',parent=item['parent']))
    require(members,'No validated native child clearance')
    record=dict(mode=context['mode'],folder=str(context['folder']),timing=b.timing(),argv=argv,
        authority_sha256=authority_sha256,attempt_sha256=sha(context['folder']/'attempt.json'),members=members)
    b.call('one-shot clearance close',save_new,context['folder']/'child-clearance.json',record)

def consume_clearance(context,p4,argv,authority_sha256):
    b=context['budget']; folder=context['folder']
    expected=(inert_argv(folder,context['port']) if context['mode']=='inert' else candidate_argv(context)[0])
    require(argv==expected,'Exact full authorized child argv required')
    deadline=min(b.clock()+30000000000,b.cutoff_ns())
    while not (folder/'child-clearance.json').exists():
        b.pre('native child clearance wait')
        if b.clock()>=deadline: b.fail('Native child clearance missing')
        time.sleep(min(.01,(deadline-b.clock())/1000000000))
    record=b.call('native clearance read',load,p4.no_reparse(folder/'child-clearance.json'))
    require(record['mode']==context['mode'] and record['folder']==str(folder) and record['timing']==b.timing() and record['argv']==expected,'Child clearance binding')
    require(record['authority_sha256']==authority_sha256 and record['attempt_sha256']==sha(folder/'attempt.json'),'Child attempt/authority binding')
    own=p4.identity(os.getpid())
    require(any(m.get('role')=='server' and m.get('identity')==own for m in record['members']),'Child native identity not cleared')
    b.call('exclusive clearance consumption',save_new,folder/'child-clearance.consumed.json',dict(identity=own,clearance_sha256=sha(folder/'child-clearance.json'),argv=argv,timing=b.timing()))
    return own

def validate_native_members(owned,p4,snapshot,listener,argv):
    members={pid:item for pid,item in owned.known.items() if item['role']=='server'}
    launchers=[item for item in owned.launchers if item['role']=='server']
    require(len(launchers)==1 and len(members)>=2,'Native redirector/base members required')
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
    with PrivateIO(p4,budget) as io:
        try:
            before=budget.call('before pins',check_inputs); native_before=budget.call('before exact identities',check_native_baseline,context['baseline'],p4)
            budget.call('boundary before close',save_new,folder/'boundary-before.json',dict(pins=before,protected=native_before))
            env=budget.call('isolated environment',p4.environment,folder); env.pop('ULTIMA_CORPUS_WIRE_ROOT',None)
            sys.path.insert(0,str(C))
            server,cli=budget.call('candidate argv',candidate_argv,context)
            budget.call('argv close',save_new,folder/'argv.json',dict(server=server,cli=cli,budgets=BUDGETS,schedule=budget.timing()))
            owned=budget.call('Owned constructor',p4.Owned,folder,env); io.launch(owned,server,'server')
            ready_listener(p4,owned,context['port'],server,budget)
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
            errors.append(dict(harness=type(exc).__name__,message=str(exc))); budget.failure=budget.failure or type(exc).__name__
        finally:
            budget.phase='cleanup'
            if owned:
                try:
                    if (folder/'cli.stdout').exists() and product is None: product=budget.call('partial first product capture',capture_first,folder,owned,budget)
                except Exception as exc: errors.append(dict(first_raw=type(exc).__name__))
            try: inventory=budget.call('pre-cleanup effects',p4.output_inventory,folder)
            except Exception as exc: inventory={'effects_unknown':type(exc).__name__}; errors.append(dict(effects_unknown=type(exc).__name__))
            try: budget.call('effects close',save_new,folder/'pre-cleanup-effects.json',inventory)
            except Exception as exc: errors.append(dict(effects_receipt=type(exc).__name__))
            if owned:
                try: cleanup=io.cleanup(owned,context['port'])
                except Exception as exc: cleanup=dict(status='FAIL',error=type(exc).__name__)
            budget.phase='seal'
            try:
                require(budget.call('final pins',check_inputs)==before,'Input drift during run')
                final_protected=budget.call('final protected identities',lambda:[p4.identity(x['pid']) for x in native_before])
                require(final_protected==native_before,'Protected identity drift')
                budget.call('boundary after close',save_new,folder/'boundary-after.json',dict(pins=before,protected=final_protected))
            except Exception as exc: errors.append(dict(boundaries=type(exc).__name__))
            if budget.remaining_ns()<0: errors.append(dict(outer='315 seconds eligibility expired'))
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
                terminal['overall']='FAIL'; terminal['errors'].append(dict(seal=type(exc).__name__))
                # Late diagnostics never create a timely success or rewrite first data.
                if not (folder/'terminal.json').exists(): save_new(folder/'terminal.json',terminal)
    return terminal

def verify_exports(folder,result,p4):
    from src.brain.work_tools import WorkBinding,ResearchRuntimeInputs
    from src.brain.work_navigation import IssuedSnapshotV3,resolve_v3,render_v3
    from src.brain.work_research import ResearchCollection,verify_runtime_packet
    exported=load(folder/'trusted-export.json'); inputs=load(folder/'runtime-inputs.json')
    require(exported.get('complete') is True and exported.get('END') is True,'Missing complete packet or END')
    raw=base64.b64decode(exported['runtime_final'],validate=True)
    s=exported['issued_snapshot']; s['binding_key']=tuple(s['binding_key'])
    for key in ('views_json','replay_json'): s[key]=base64.b64decode(s[key],validate=True)
    snapshot=IssuedSnapshotV3(**s); inputs['binding_key']=tuple(inputs['binding_key']); runtime_inputs=ResearchRuntimeInputs(**inputs)
    binding=WorkBinding(Path(inputs['root']),*inputs['binding_key'])
    require(inputs['binding_key']==tuple(result[k] for k in ('request_id','session_id','task_id')),'Independent input binding mismatch')
    require(Path(inputs['root'])==folder/'outputs'/result['task_id'],'Independent root mismatch')
    collection=ResearchCollection(**exported['collection'])
    frozen=corpus()['sources']; actual_sources=json.loads(collection.catalogue_json)
    require([(s['final_url'],s['body'],s['decoded_body_sha256']) for s in actual_sources]==[(s['final_url'],s['body'],s['decoded_body_sha256']) for s in frozen],'Original four-source corpus mismatch')
    attempts=json.loads(collection.attempts_json)
    require(sum(x['tool_name']=='ultima_work_web_search' for x in attempts)==1 and sum(x['tool_name']=='ultima_work_http_get' for x in attempts)==4,'Original collection attempt caps')
    packet=verify_runtime_packet(binding,snapshot,collection,raw,require_ack=True,runtime_inputs=runtime_inputs)
    require(1<=packet['transport']['posts']<=8,'POST attempt bound')
    resolved,bindings=resolve_v3(packet['wires'][-2]['secured_envelope']['action_input'],snapshot,collection)
    rendered=render_v3(resolved,collection.catalogue_json,bindings=bindings)
    verify_readback(folder,result,p4,rendered.content)
    require(exported['ack_admitted'] is True,'Final ACK missing')
    return dict(native_POST_attempts=packet['transport']['posts'])

def verify_readback(folder,result,p4,rendered_content):
    artifacts=p4.read_artifacts(folder,result)
    require(len(artifacts)==1 and Path(artifacts[0]['path']).name=='research.md' and artifacts[0]['sha256']==artifacts[0]['external_sha256'],'Exact external research.md readback')
    require(artifacts[0]['text']==rendered_content,'Independent rendered byte readback mismatch')
    inventory=p4.output_inventory(folder)
    require(len(inventory)==1 and inventory[0]['path']==artifacts[0]['path'] and inventory[0]['sha256']==artifacts[0]['external_sha256'],'Unexpected output set')
    return artifacts

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
                require(len(raw)<=CAP,'Final packet export cap'); packet=json.loads(raw); ledger._scan_output(packet)
                s=asdict(snapshot)
                for key in ('views_json','replay_json'): s[key]=base64.b64encode(s[key]).decode('ascii')
                ends=[json.loads(e) for e in packet['events'] if json.loads(e).get('type')=='tool_call_end']
                writer_end=any(e.get('data',{}).get('tool')=='ultima_work_research_write' and e['data'].get('success') is True for e in ends)
                save_new(folder/'trusted-export.json',dict(complete=True,END=writer_end,native_POST_attempts=getattr(getattr(ledger,'_runtime_transport',None),'posts',None),runtime_final=base64.b64encode(raw).decode('ascii'),issued_snapshot=s,collection=asdict(ledger._collection),ack_admitted=result.get('status')=='succeeded'))
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
    for path in budget.call('seal listing',lambda:list(folder.rglob('*'))):
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
        token=_ENCLOSING.set(self.budget); result=None; digest=None; proofs={}; error=None
        try:
            result=entry(*args,**kwargs)
            require(isinstance(result,dict),'Returned closed package required')
            folder=Path(result['folder']); terminal=load(folder/'terminal.json'); index=load(folder/'seal-index.json')
            require(index['run_id']==self.budget.run_id and terminal['run_id']==self.budget.run_id,'Root observation run binding')
            require(index['timing']==self.budget.timing(),'Root observation origin binding')
            required=({'attempt.json','argv-roundtrip.json','native-argv.json','native-argv.raw','listener.json','owned-tree.json','cleanup.json','protected-before.json','protected-after.json','terminal.json','server.stdout','server.stderr'} if terminal.get('kind')=='inert' else {'attempt.json','argv.json','effective-schedule.json','first-product.raw','product-result.json','service-first-result.json','trusted-export.json','runtime-inputs.json','pre-cleanup-effects.json','external-artifacts.json','external-readback-attempts.json','owned-tree.json','cleanup.json','listener.json','boundary-before.json','boundary-after.json','terminal.json','server.stdout','server.stderr','cli.stdout','cli.stderr'})
            require(required<=set(index['files']),'Required closed execution evidence absent')
            observed_files={str(p.relative_to(folder)) for p in folder.rglob('*') if p.is_file()}
            require(observed_files==set(index['files'])|{'seal-index.json'},'Missing/extra sealed data')
            for name,expected in index['files'].items():
                raw=Path(name); require(not raw.is_absolute() and '..' not in raw.parts,'Seal relative member')
                require(sha(folder/raw)==expected,'Closed required data changed')
            digest=sha(folder/'terminal.json')
            clean=terminal.get('overall') in ('PENDING_ROOT_INDEPENDENT_REVIEW','READY_FOR_ROOT_TIMING_WITNESS')
            proofs=dict(closed=clean,cleanup=terminal['cleanup'].get('status')=='PASS' and terminal['cleanup'].get('port_definitively_closed') is True and terminal['cleanup'].get('logs_closed') is True,pins=not terminal['errors'],protected=not terminal['errors'],readback=clean)
        except Exception as exc: error=type(exc).__name__
        finally: _ENCLOSING.reset(token)
        # Sampling occurs AFTER entry returned and after every required data hash
        # read closed. No child timestamp/mtime is used for the timing decision.
        witness=self.observer.finish(digest,proofs); witness['observation_error']=error
        return dict(result=result,witness=witness)

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
    budget.post('inert admission'); return authority,folder,p4,baseline

def inert_argv(folder,port):
    return ['-B','-X','utf8',str(HERE/'adapter.py'),'--inert-child',str(folder),'--port',str(port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--question',corpus()['query']]

def inert_child(folder,args):
    budget=entry_budget(); authority,expected,_,_=inert_admit(child=True,budget=budget)
    require(folder==expected and args==inert_argv(folder,authority['port'])[6:],'Exact original inert argv required')
    from http.server import BaseHTTPRequestHandler,HTTPServer
    save_new(folder/'argv-roundtrip.json',dict(question=args[-1],argv=sys.argv[1:],encoding='native Unicode argv to UTF8 JSON'))
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            require(self.path=='/inert','Only inert endpoint')
            body=b'{"inert":true}'; self.send_response(200); self.send_header('Content-Length',str(len(body))); self.end_headers(); self.wfile.write(body)
        def log_message(self,*args): pass
    server=HTTPServer(('127.0.0.1',authority['port']),Handler); server.timeout=.1
    try:
        while not (folder/'stop').exists(): server.handle_request()
    finally: server.server_close()

def main():
    budget=entry_budget()
    parser=argparse.ArgumentParser(); parser.add_argument('--case',choices=[CASE]); parser.add_argument('--child-server',type=Path)
    parser.add_argument('--inert-child',type=Path)
    args,remaining=parser.parse_known_args()
    if args.inert_child:
        inert_child(args.inert_child,remaining); return 0
    if args.child_server:
        context,_=admit(V/'controller-authority'/f'{CASE}.json',V/'controller-ledger.json',child=True,budget=budget)
        require(args.child_server==context['folder'],'Claimed first-case child required')
        sys.path.insert(0,str(C)); install_browser_fixture(); install_trusted_exports(args.child_server)
        import runpy
        sys.argv=['src.brain.agent_server',*remaining]; runpy.run_module('src.brain.agent_server',run_name='__main__'); return 0
    require(args.case==CASE and not remaining,'Explicit first case required')
    print(json.dumps(run_case(V/'controller-authority'/f'{CASE}.json',V/'controller-ledger.json'),ensure_ascii=False))
    return 2  # Standalone command has no trusted enclosing timing witness.

if __name__=='__main__': raise SystemExit(main())
