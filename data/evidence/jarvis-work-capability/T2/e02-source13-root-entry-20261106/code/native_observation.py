"""Observe a verified Owned member through one retained, readonly Windows handle."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import ast
import errno
import hashlib
import importlib.util
import os
import re
import socket
import sys
import time
import uuid
from package_io import load,save_new,sha

LEGACY=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261103-inert2\harness\adapter.py')
LEGACY_SHA='27100afd246c9fb58579ed0389412731b4f029f1c5073ecce9e0cdd8b89d09ed'
HELPER=LEGACY.parents[2]/'e01-source13-round3-20261106'


def deadline_io():
    raw=LEGACY.read_bytes();require(hashlib.sha256(raw).hexdigest()==LEGACY_SHA,'Pinned deadline/IO source drift')
    tree=ast.parse(raw);nodes=[node for node in tree.body if isinstance(node,ast.ClassDef) and node.name in ('Deadline','PrivateIO')]
    require([node.name for node in nodes]==['Deadline','PrivateIO'],'Pinned private class inventory')
    changed=0
    for node in ast.walk(nodes[1]):
        if isinstance(node,ast.Constant) and isinstance(node.value,str) and node.value.startswith(' | ForEach-Object { [pscustomobject]@{ProcessId='):
            require('CreationFileTime' not in node.value and node.value.count('CommandLineBase64=')==1,'Pinned snapshot suffix')
            node.value=node.value.replace('CommandLineBase64=','CreationFileTime=[Int64]$_.CreationDate.ToFileTimeUtc();CommandLineBase64=')
            changed+=1
    require(changed==1,'Exactly one explicit CIM compatibility extension')
    ns=dict(require=require,time=time,uuid=uuid,re=re,errno=errno,CLOCK_DOMAIN='monotonic_ns;same-host='+socket.gethostname())
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(LEGACY),'exec'),ns)
    return ns['Deadline'],ns['PrivateIO']


def cleanup_no_listener(io,owned):
    # Profile client closure retains its original 310 cutoff. Enclosing process
    # teardown and reader observation share the original 315 seal cutoff.
    b=io.budget;b.phase='seal';b.pre('zero-listener enclosing cleanup');io.wrap_waits(owned)
    try:result=dict(owned.cleanup(None))
    except Exception as exc:result=dict(status='FAIL',error_type=type(exc).__name__,effects_unknown=True)
    result.update(logs_closed=all(stream.closed for stream in owned.logs),
        unregistered_launch_possible=any(not item['registered'] for item in io.launch_attempts),
        port_probe='NOT_APPLICABLE_NO_LISTENER')
    if not result['logs_closed'] or result['unregistered_launch_possible'] or b.remaining_ns()<0 or b.failure:
        result['status']='FAIL';result['effects_unknown']=True
    return result


def cleanup_reservation(owned,additional=0):
    """Conservative admission reserve for the unchanged, registered Owned tree.

    Per helper source: discovery, two snapshots/member, final snapshot, protected
    proof; each may take15s. Preserve full10s termination/member and2s launcher
    waits. Console observation can start one15s query before its3s window closes.
    Five seconds are held for fixed local reopens/sealing (still deadline checked).
    Unexpected discovery failures remain failures, never a cleanup guarantee.
    """
    require(additional in (0,2),'Only a fixed new role pair may be reserved')
    members=len(owned.known) if owned is not None else 0
    launchers=len(owned.launchers) if owned is not None else 0
    auxiliary=bool(owned is not None and owned.auxiliary)
    members+=additional;launchers+=int(bool(additional))
    reserve=15*(2*members+3)+10*members+2*launchers+(18 if auxiliary else 0)+5
    # Startup and qualification each use the existing snapshot helper: three
    # bounded calls before waiting. Their time cannot consume the cleanup reserve.
    return reserve+(45 if additional else 0)


class NativeBackend:
    """Fixed wiring to the accepted Owned helper, with no new termination method."""
    def __init__(self,context,origin):
        from entry import clean_environment
        self.context,self.origin=context,origin;self.owned=None;self.observers={};self.arguments={};self.io=None
        context._release(True);context._time(origin,275,exclusive=True)
        require('OPENJARVIS_SSRF_FAIL_OPEN' not in {k.upper() for k in os.environ},'SSRF override is not normal configuration')
        self.environment=clean_environment(dict(os.environ))
        paths=[Path(__file__).parent/name for name in ('entry.py','controls.py','native_observation.py','package_io.py')]
        paths += [HELPER/'code'/name for name in ('controller.py','source_candidate_guard.py','fixture_adapter.py',
            'fixture_manual_start.py','fixture_input_origin.py','acceptance_backend.py')]
        paths += [HELPER/'preparation-support/acceptance_adapter.py',LEGACY]
        for path in paths:self.pinned(path)
        previous=list(sys.path)
        try:
            sys.path.insert(0,str(HELPER/'code'))
            self.controller=self.module(HELPER/'code/controller.py','source13_root_owned_controller')
        finally:sys.path[:]=previous
        c=self.controller
        for name,relative in (('acceptance_adapter','preparation-support/acceptance_adapter.py'),
            ('source_candidate_guard','code/source_candidate_guard.py'),('fixture_adapter','code/fixture_adapter.py'),
            ('fixture_manual_start','code/fixture_manual_start.py'),('fixture_input_origin','code/fixture_input_origin.py')):
            require(name in sys.modules and Path(sys.modules[name].__file__).resolve()==(HELPER/relative).resolve(),'Fixed helper import origin')
        c.old.PROTECTED_BASELINE=Path(context.manifest['protected_baseline_path'])
        self.baseline=load(c.old.PROTECTED_BASELINE)
        Deadline,PrivateIO=deadline_io();self.budget=Deadline(clock=context.clock);self.budget.run_id=context.run_id
        self.budget.adopt_parent(dict(run_id=context.run_id,origin_ns=origin,clock_domain=self.budget.timing()['clock_domain']))
        self.api=WindowsReadAPI(c);self.io=PrivateIO(c,self.budget);self.io.__enter__()

    def pinned(self,path):
        require(str(path) in self.context.manifest['files'] and sha(path)==self.context.manifest['files'][str(path)],'Unbound root helper input')

    def module(self,path,name):
        self.pinned(path);spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

    def root_identity(self):return self.budget.call('root native identity',self.controller.identity,os.getpid())

    def require_cleanup_room(self,additional=0):
        reserve=cleanup_reservation(self.owned,additional)
        require(self.budget.remaining_ns('seal')>reserve*10**9,'Original allowance reserved for Owned cleanup')

    def protected(self):
        path=HELPER/'code/acceptance_backend.py';self.pinned(path)
        tree=ast.parse(path.read_bytes());cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='AcceptanceBackend')
        method=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='_protected')
        ns=dict(require=require,hashlib=hashlib)
        exec(compile(ast.Module(body=[method],type_ignores=[]),str(path),'exec'),ns)
        return self.budget.call('seven protected native identities',ns['_protected'],self)

    def normal_backend(self):
        pins=self.context.base
        paths=[Path(name) for name in pins['files'] if Path(name).name=='_rust_bridge.py' and Path(name).parent.name=='openjarvis']
        require(len(paths)==1,'Pinned normal SSRF bridge')
        path=paths[0];require(sha(path)==pins['files'][str(path)],'Normal SSRF bridge drift')
        spec=importlib.util.spec_from_file_location('source13_normal_rust_bridge',path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        require(type(module.RUST_AVAILABLE) is bool,'Normal SSRF backend unknown')
        if module.RUST_AVAILABLE:
            rust=module.get_rust_module()
            for value in (rust,rust.openjarvis_rust):
                source=str(Path(value.__file__).resolve())
                require(source in pins['files'] and sha(Path(source))==pins['files'][source],'Normal Rust import origin drift')
            require(str(Path(rust.openjarvis_rust.__file__).resolve())==str(Path(pins['rust_extension_origin']).resolve()),'Normal Rust extension drift')
        self.budget.post('normal backend observation')
        return 'rust' if module.RUST_AVAILABLE else 'python'

    def start(self,role):
        require(role in ('worker','reader') and role not in self.arguments,'One launch per fixed role')
        self.budget.phase='work' if role=='worker' else 'seal'
        if self.owned is None:self.owned=self.controller.Owned(self.context.process,self.environment)
        argv=['-I','-B','-X','utf8',str(self.context.root/'code/entry.py'),'--role',role,'--run-id',self.context.run_id]
        self.arguments[role]=argv
        previous=list(sys.path)
        try:
            sys.path.insert(0,str(self.controller.ROOT))
            self.io.launch(self.owned,argv,role)
        finally:sys.path[:]=previous

    def qualify(self,role,hello):
        require(role in ('worker','reader') and role not in self.observers,'One retained observation per role')
        self.context._time(self.origin,275 if role=='worker' else 315,exclusive=True)
        self.owned.discover();pid=hello['pid'];item=self.owned.known.get(pid)
        require(item is not None and item.get('role')==role and pid not in self.owned.forbidden,'HELLO not a registered Owned role')
        launchers=[item for item in self.owned.launchers if item['role']==role]
        require(len(launchers)==1,'Exactly one retained launcher')
        launcher=launchers[0]['identity'];key=item['identity']
        snapshot=self.controller.process_snapshot(pids=[pid],proof=self.context.process/(role+'-argv.json'))
        row=snapshot.get(pid)
        require(row is not None and self.controller.snapshot_identity_matches(key,row),'Native role creation differs from CIM')
        parent=os.getpid() if pid==launcher['pid'] else launcher['pid']
        require(row['ParentProcessId']==item['parent']==parent and launcher['created_filetime']<=key['created_filetime']
            and self.controller.argv_parse(row['CommandLine'])[1:]==self.arguments[role],'Native parent/complete argv mismatch')
        observer=RetainedExit(self.owned,key,role,api=self.api,clock=self.context.clock)
        self.observers[role]=observer
        return dict(identity=deepcopy(key),launcher=deepcopy(launcher),parent_pid=parent,
            argv_sha256=hashlib.sha256(row['CommandLine'].encode('utf-16le')).hexdigest())

    def poll(self,role):
        # Admission/work/cleanup are independently checked against their own
        # original cutoffs by the root progress records. Waiting cannot renew
        # the invocation or accidentally truncate its already allowed seal time.
        self.budget.phase='seal'
        return self.observers[role].poll(self.origin,self.origin+315*10**9)

    def pause(self):
        time.sleep(self.budget.clip(.05,'root polling'));self.budget.post('root polling')

    def cleanup(self):
        if self.owned is None:
            return dict(status='PASS',logs_closed=True,unregistered_launch_possible=False,processes=[],port_probe='NOT_APPLICABLE_NO_LAUNCH')
        return cleanup_no_listener(self.io,self.owned)

    def close(self):
        try:
            for observer in self.observers.values():observer.close()
        finally:
            if self.io is not None:self.io.__exit__(None,None,None);self.io=None


def require(value, message):
    if not value: raise ValueError(message)


class WindowsReadAPI:
    """Existing native identity/times helpers and CPython's handle observation calls."""
    def __init__(self, controller):
        import _winapi
        self.api = _winapi
        self.controller = controller

    def identity(self, pid): return self.controller.identity(pid)
    def open(self, pid): return self.api.OpenProcess(0x00100000 | 0x1000, False, pid)
    def times(self, handle): return self.controller.process_times(SimpleNamespace(_handle=handle))
    def signaled(self, handle):
        result = self.api.WaitForSingleObject(handle, 0)
        require(result in (self.api.WAIT_OBJECT_0, self.api.WAIT_TIMEOUT), 'Native wait observation failed')
        return result == self.api.WAIT_OBJECT_0
    def exit_code(self, handle): return self.api.GetExitCodeProcess(handle)
    def close(self, handle): self.api.CloseHandle(handle)


class RetainedExit:
    def __init__(self, owned, key, role, *, api, clock):
        require(type(key) is dict and set(key)=={'pid','created_filetime','exe'}, 'Closed native identity required')
        require(all(type(key[name]) is int and key[name]>0 for name in ('pid','created_filetime'))
                and type(key['exe']) is str and Path(key['exe']).is_absolute(), 'Native identity types')
        require(role in ('worker','reader') and key['pid'] not in owned.forbidden, 'Protected or wrong role')
        member = owned.known.get(key['pid'])
        require(type(member) is dict and member.get('identity')==key and member.get('role')==role,
                'Exact Owned member required before handle acquisition')
        self.key, self.role, self.api, self.clock = deepcopy(key), role, api, clock
        self.handle = None
        require(api.identity(key['pid'])==self.key, 'Native identity changed before open')
        handle = api.open(key['pid'])
        require(type(handle) is int and handle>0, 'Readonly native handle unavailable')
        self.handle = handle
        try:
            created, _ = api.times(handle)
            require(type(created) is int and created==self.key['created_filetime'], 'Retained handle creation mismatch')
            require(api.identity(key['pid'])==self.key, 'PID reused during handle acquisition')
        except BaseException:
            self.close()
            raise

    def _time(self, origin, cutoff):
        require(type(origin) is int and type(cutoff) is int and 0<origin<=cutoff, 'Original bounded clock required')
        now = self.clock()
        require(type(now) is int and origin<=now<=cutoff, 'Native observation outside original deadline')
        return now

    def poll(self, origin, cutoff):
        require(self.handle is not None, 'Retained handle closed')
        self._time(origin, cutoff)
        signaled = self.api.signaled(self.handle)
        require(type(signaled) is bool, 'Unknown native signal observation')
        if not signaled:
            self._time(origin, cutoff)
            return None
        code = self.api.exit_code(self.handle)
        require(type(code) is int and 0<=code<=0xffffffff, 'Unknown native exit code')
        observed = self._time(origin, cutoff)
        return dict(identity=deepcopy(self.key),role=self.role,signaled=True,exit_code=code,observed_at_ns=observed)

    def close(self):
        handle, self.handle = self.handle, None
        if handle is not None: self.api.close(handle)

    def __enter__(self): return self
    def __exit__(self, *exc): self.close()
