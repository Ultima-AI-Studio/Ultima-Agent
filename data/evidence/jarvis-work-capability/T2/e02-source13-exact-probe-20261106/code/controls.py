"""Fixed root-owned admission and independent reader record adapters.

This is a trusted-code capability, not an adversarial Python/OS boundary.
No actual release or approval is shipped with this module.
"""
import importlib.util
from pathlib import Path
import hashlib
from copy import deepcopy
from datetime import datetime, timezone
import os
import re
import time
import uuid
from package_io import require,read,sha,digest,canonical,decode,load,safe_path,save_new

PY=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
BASE_MANIFEST=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-exact-probe-20261106\profile-preparation\manifest.json')
CANDIDATE='269aca511d88412dbb9c15d23911138469a37aa2'
MODEL_DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
SCOPE='ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE'
source=BASE_MANIFEST.parent/'profile.py'
if hashlib.sha256(source.read_bytes()).hexdigest()!='444081b115829e29d9203601091fac5303b0facb4f7b65ae0f9101b63400f29e':raise ValueError('Profile source drift')
spec=importlib.util.spec_from_file_location('source13_root_profile',source)
PROFILE=importlib.util.module_from_spec(spec);spec.loader.exec_module(PROFILE)

ROLES=['ollama','brain_primary','brain_runtime_child','voice_primary','voice_runtime_child',
       'voice_listener_primary','voice_listener_runtime_child']
IDENTITY_FIELDS={'pid','created_filetime','exe'}
PROTECTED_FIELDS=IDENTITY_FIELDS|{'parent_pid','command_line_sha256'}
MANIFEST_FIELDS={'schema','kind','runtime_released','candidate','model_digest','base_profile_manifest_path',
                 'base_profile_manifest_sha256','import_path','protected_baseline_path','files'}
RELEASE_FIELDS={'schema','kind','scope','run_id','entry_nonce','candidate','model_digest','root_manifest_sha256',
    'approval_sha256','preparation_review_sha256','issued_at','expires_at','max_submissions','retry',
    'actual_http_allowed','actual_11434_allowed','actual_inference_allowed','ssrf_dns_host','UI','audio'}
APPROVAL_FIELDS={'schema','kind','scope','approved','source','answer','recorded_at','profile_limit','result_review_limit',
    'actual_http_allowed','actual_11434_allowed','actual_inference_allowed','ssrf_dns_host','UI','audio'}
ALLOCATION_FIELDS={'schema','run_id','entry_nonce','origin_ns','root_native','root_manifest_sha256','release_sha256',
                   'consumed_at','consumed','max_submissions','retry'}
GRANT_FIELDS={'schema','run_id','entry_nonce','origin_ns','candidate','model_digest','root_manifest_sha256',
    'allocation_sha256','release_sha256','protected_before_sha256','worker_native','launcher_native',
    'worker_parent_pid','worker_argv_sha256','worker_executable','case_root','ssrf_backend','admitted_at_ns'}
EXIT_FIELDS={'identity','role','signaled','exit_code','observed_at_ns'}
OBSERVATION_FIELDS={'schema','run_id','entry_nonce','origin_ns','allocation_sha256','entry_grant_sha256','native_exit','hashes','progress_sha256'}
HASH_FILES={'first_result_sha256':'profile-first-result.json','closed_index_sha256':'closed-index.json',
            'expectations_sha256':'profile-observations.json','runtime_inputs_sha256':'runtime-inputs.json'}


def exact(value,fields,label):require(type(value) is dict and set(value)==fields,label+' closed schema')
def true_int(value):return type(value) is int and value>0
def is_sha(value):return type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None
def native_key(value):
    exact(value,IDENTITY_FIELDS,'Native identity')
    require(true_int(value['pid']) and true_int(value['created_filetime']) and type(value['exe']) is str
            and Path(value['exe']).is_absolute(),'Native identity fields')
    return value


def uuid4(value):
    require(type(value) is str and str(uuid.UUID(value))==value and uuid.UUID(value).version==4,'Canonical UUID4')
    return value


def timestamp(value):
    require(type(value) is str,'UTC timestamp required')
    result=datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None,'Timezone required')
    return result


def same(left,right):return canonical(left)==canonical(right)


def equal_pins(left,right):
    require(type(left) is dict and type(right) is dict and set(left)==set(right),'Closed derived pin mapping')
    left,right=dict(left),dict(right)
    for name in ('metadata','tags_bytes'):
        a,b=left.pop(name),right.pop(name)
        if name=='metadata':
            require(type(a) is dict and set(a)=={'tags','version'} and all(type(a[k]) is bytes and a[k]==b[k] for k in b),'Metadata pins changed')
        else:require(type(a) is bytes and a==b,'Tag bytes changed')
    require(same(left,right),'Derived pins changed')


class Context:
    def __init__(self,root,run_id,*,clock=time.monotonic_ns,utc=lambda:datetime.now(timezone.utc)):
        self.root=safe_path(root);self.run_id=uuid4(run_id);self.clock,self.utc=clock,utc
        self.run=self.root/'runs'/run_id
        self.control=self.run/'control';self.case=self.run/'worker'/'case';self.reader=self.run/'reader';self.process=self.run/'process'
        self.manifest_raw=read(self.root/'entry-manifest.json');self.manifest=decode(self.manifest_raw)
        self.manifest_sha=digest(self.manifest_raw)
        exact(self.manifest,MANIFEST_FIELDS,'Root manifest')
        m=self.manifest
        require(type(m['schema']) is int and m['schema']==1 and m['kind']=='SOURCE13_PROFILE_ROOT_PREPARATION'
                and m['runtime_released'] is False and m['candidate']==CANDIDATE and m['model_digest']==MODEL_DIGEST,'Root preparation scope')
        require(m['base_profile_manifest_path']==str(BASE_MANIFEST) and m['base_profile_manifest_sha256']==sha(BASE_MANIFEST),'Fixed base profile manifest')
        self.base=PROFILE.read_pins(BASE_MANIFEST)
        derived=[str(BASE_MANIFEST.parent),*self.base['import_path'][1:]]
        require(m['import_path']==derived and m['protected_baseline_path']==str(self.root/'inputs/protected-baseline.json'),'Explicit current root binding')
        require(type(m['files']) is dict and bool(m['files']) and str(BASE_MANIFEST) in m['files']
                and m['protected_baseline_path'] in m['files'],'Root input inventory')
        self._fresh_inputs()
        self.release_raw=read(self.root/'release/release.json');self.release=decode(self.release_raw)
        self.release_sha=digest(self.release_raw)
        self._release(False)

    def _fresh_inputs(self):
        require(read(self.root/'entry-manifest.json')==self.manifest_raw,'Root manifest drift')
        for name,expected in self.manifest['files'].items():
            require(type(name) is str and Path(name).is_absolute() and is_sha(expected) and sha(Path(name))==expected,'Root bound input drift')
        require(sha(BASE_MANIFEST)==self.manifest['base_profile_manifest_sha256'],'Base profile drift')

    def _release(self,fresh):
        self._fresh_inputs()
        require(read(self.root/'release/release.json')==self.release_raw,'Root release drift')
        r=self.release;exact(r,RELEASE_FIELDS,'Release')
        require(type(r['schema']) is int and r['schema']==1 and r['kind']=='SOURCE13_PROFILE_ROOT_RELEASE'
                and r['scope']==SCOPE and r['candidate']==CANDIDATE and r['model_digest']==MODEL_DIGEST,'Fixed release scope')
        require(uuid4(r['run_id'])==self.run_id and uuid4(r['entry_nonce'])!=self.run_id
                and r['root_manifest_sha256']==self.manifest_sha,'Release run/input binding')
        for name,value in dict(max_submissions=1,retry=0,actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,UI=0,audio=0).items():
            require(type(r[name]) is int and r[name]==value,'Release limits')
        require(r['ssrf_dns_host']=='raw.githubusercontent.com','Normal SSRF DNS scope must be explicit')
        issued,expires=timestamp(r['issued_at']),timestamp(r['expires_at'])
        require(0<(expires-issued).total_seconds()<=120,'Bounded release validity')
        if fresh:require(issued<=self.utc()<=expires,'Release expired or not yet valid')
        approval_path=self.root/'release/user-approval.json'
        require(sha(approval_path)==r['approval_sha256'],'User approval byte binding')
        a=load(approval_path);exact(a,APPROVAL_FIELDS,'User approval')
        require(type(a['schema']) is int and a['schema']==1 and a['kind']=='USER_EXPLICIT_APPROVAL' and a['scope']==SCOPE
                and a['approved'] is True and a['source']=='user_reply' and type(a['answer']) is str and bool(a['answer']),'Explicit user approval absent')
        timestamp(a['recorded_at'])
        for name,value in dict(profile_limit=1,result_review_limit=1,actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,UI=0,audio=0).items():
            require(type(a[name]) is int and a[name]==value,'User approval limits')
        require(a['ssrf_dns_host']==r['ssrf_dns_host'],'DNS not in explicit approval')
        review_path=self.root/'review/independent-preparation-review.json'
        require(sha(review_path)==r['preparation_review_sha256'],'Review byte binding')
        review=load(review_path)
        require(review.get('reviewer')=='root-independent' and review.get('scope')=='e02-source13-root-entry-preparation'
                and review.get('verdict')=='PASS' and review.get('manifest_sha256')==self.manifest_sha
                and review.get('runtime_authority') is False,'Independent preparation not passed')
        gate=load(self.root/'verification/code-preparation-gate.json')
        require(gate.get('verdict')=='PASS_PREPARATION_ONLY' and gate.get('manifest_sha256')==self.manifest_sha
                and gate.get('review_sha256')==sha(review_path) and gate.get('actual_authority') is False,'Root preparation disposition missing')
        return r

    def _time(self,origin,seconds,*,exclusive=False):
        now=self.clock();cutoff=origin+seconds*10**9
        require(true_int(origin) and type(now) is int and origin<=now and (now<cutoff if exclusive else now<=cutoff),'Original clock expired or invalid')
        return now

    def pins(self):
        self._fresh_inputs()
        pins=deepcopy(self.base);pins['import_path']=list(self.manifest['import_path'])
        pins['reader_root']=str(self.reader)
        pins['worker_evidence_roots']=[str(self.run/'worker'),str(self.control),str(self.process)]
        grant=self.control/'entry-grant.json'
        pins['ssrf_backend']=load(grant)['ssrf_backend'] if grant.exists() else None
        return pins

    def consume(self,root_native,origin):
        r=self._release(True);native_key(root_native);self._time(origin,275,exclusive=True)
        value=dict(schema=1,run_id=self.run_id,entry_nonce=r['entry_nonce'],origin_ns=origin,root_native=deepcopy(root_native),
            root_manifest_sha256=self.manifest_sha,release_sha256=self.release_sha,consumed_at=self.utc().isoformat(),
            consumed=1,max_submissions=1,retry=0)
        # Exclusive creation consumes permanently, even if write/flush later fails.
        return save_new(self.root/'release/consumed.json',value)

    def allocation(self):
        r=self._release(False);path=self.root/'release/consumed.json';raw=read(path);a=decode(raw)
        exact(a,ALLOCATION_FIELDS,'Allocation')
        require(type(a['schema']) is int and a['schema']==1 and a['run_id']==self.run_id and a['entry_nonce']==r['entry_nonce']
                and a['root_manifest_sha256']==self.manifest_sha and a['release_sha256']==self.release_sha,'Consumed allocation binding')
        for name,value in dict(consumed=1,max_submissions=1,retry=0).items():require(type(a[name]) is int and a[name]==value,'Consumed allocation limits')
        native_key(a['root_native']);require(true_int(a['origin_ns']),'Root original origin required')
        require(timestamp(r['issued_at'])<=timestamp(a['consumed_at'])<=timestamp(r['expires_at']),'Allocation outside release validity')
        return a,digest(raw)

    def protected(self,name,origin):
        data=load(self.control/name);exact(data,{'schema','observed_at_ns','identities'},'Protected observation')
        require(type(data['schema']) is int and data['schema']==1 and type(data['observed_at_ns']) is int
                and origin<=data['observed_at_ns']<=self.clock(),'Protected observation clock')
        baseline=load(Path(self.manifest['protected_baseline_path']))
        expected=baseline.get('protected5',[])+baseline.get('protected_listener_pair',[])
        require(type(baseline.get('protected_process_count')) is int and baseline['protected_process_count']==7
                and len(expected)==7 and [x.get('role') for x in expected]==ROLES,'Current seven protected roles required')
        rows=data['identities'];require(type(rows) is list and len(rows)==7,'Seven protected identities required')
        require(len({row.get('pid') for row in rows})==7,'Duplicate protected identity')
        observed={}
        for row in rows:
            exact(row,PROTECTED_FIELDS,'Protected member');native_key({k:row[k] for k in IDENTITY_FIELDS})
            require(true_int(row['parent_pid']) and is_sha(row['command_line_sha256']),'Protected parent/command binding')
            observed[row['pid']]=dict(row,exe=row['exe'].lower())
        wanted={row['pid']:{**{k:row[k] for k in PROTECTED_FIELDS},'exe':row['exe'].lower()} for row in expected}
        require(same(observed,wanted),'Protected native identity drift')
        return data

    def issue_worker(self,worker,launcher,parent_pid,argv_sha,ssrf_backend):
        self._release(True);a,allocation_sha=self.allocation();now=self._time(a['origin_ns'],275,exclusive=True)
        native_key(worker);native_key(launcher)
        require(true_int(parent_pid) and parent_pid in (a['root_native']['pid'],launcher['pid'])
                and launcher['created_filetime']<=worker['created_filetime'],'Owned launch relation required')
        protected=self.protected('protected-before.json',a['origin_ns'])
        protected_pids={x['pid'] for x in protected['identities']}
        require(worker['pid'] not in protected_pids and launcher['pid'] not in protected_pids,'Protected member cannot be worker')
        require(is_sha(argv_sha) and ssrf_backend in ('python','rust'),'Observed argv and normal backend required')
        require(self.case.is_dir() and not any(self.case.iterdir()),'Fresh empty worker case')
        value=dict(schema=1,run_id=self.run_id,entry_nonce=self.release['entry_nonce'],origin_ns=a['origin_ns'],candidate=CANDIDATE,
            model_digest=MODEL_DIGEST,root_manifest_sha256=self.manifest_sha,allocation_sha256=allocation_sha,release_sha256=self.release_sha,
            protected_before_sha256=sha(self.control/'protected-before.json'),worker_native=deepcopy(worker),launcher_native=deepcopy(launcher),
            worker_parent_pid=parent_pid,worker_argv_sha256=argv_sha,worker_executable=str(PY),case_root=str(self.case),ssrf_backend=ssrf_backend,
            admitted_at_ns=now)
        save_new(self.control/'entry-grant.json',value)
        return value

    def worker_grant(self,fresh=False):
        if fresh:self._release(True)
        a,allocation_sha=self.allocation();raw=read(self.control/'entry-grant.json');g=decode(raw)
        exact(g,GRANT_FIELDS,'Root worker grant')
        require(type(g['schema']) is int and g['schema']==1 and g['run_id']==self.run_id and g['entry_nonce']==a['entry_nonce']
                and g['origin_ns']==a['origin_ns'] and g['candidate']==CANDIDATE and g['model_digest']==MODEL_DIGEST
                and g['root_manifest_sha256']==self.manifest_sha and g['allocation_sha256']==allocation_sha
                and g['release_sha256']==self.release_sha,'Root grant binding')
        native_key(g['worker_native']);native_key(g['launcher_native'])
        require(g['worker_executable']==str(PY) and g['case_root']==str(self.case) and is_sha(g['worker_argv_sha256'])
                and g['ssrf_backend'] in ('python','rust'),'Worker role/pin binding')
        require(true_int(g['worker_parent_pid']) and g['worker_parent_pid'] in (a['root_native']['pid'],g['launcher_native']['pid'])
                and g['launcher_native']['created_filetime']<=g['worker_native']['created_filetime'],'Worker launch relation')
        require(type(g['admitted_at_ns']) is int and a['origin_ns']<=g['admitted_at_ns']<a['origin_ns']+275*10**9,'Original admission time')
        protected=self.protected('protected-before.json',a['origin_ns'])
        require(sha(self.control/'protected-before.json')==g['protected_before_sha256'],'Protected before bytes drift')
        require(g['worker_native']['pid'] not in {x['pid'] for x in protected['identities']},'Protected worker refused')
        return a,g,digest(raw)

    def closed_hashes(self):
        result={key:sha(self.case/name) for key,name in HASH_FILES.items()}
        result['protected_after_sha256']=sha(self.control/'protected-after.json')
        index=load(self.case/'closed-index.json');exact(index,{'format','files'},'Closed index')
        require(type(index['format']) is int and index['format']==1 and same(PROFILE.case_files(self.case),index['files']),'Closed worker inventory changed')
        return result

    def record_progress(self,label):
        require(label in ('work','cleanup'),'Fixed progress role')
        a,g,_=self.worker_grant()
        name='service-first-result.json' if label=='work' else 'profile-first-result.json'
        raw=read(self.case/name);require(type(decode(raw)) is dict,'Complete progress file required')
        now=self._time(a['origin_ns'],275 if label=='work' else 310,exclusive=label=='work')
        value=dict(schema=1,run_id=self.run_id,entry_nonce=a['entry_nonce'],origin_ns=a['origin_ns'],
                   label=label,observed_at_ns=now,sha256=digest(raw))
        save_new(self.control/(label+'-observation.json'),value)
        return value

    def progress(self):
        a,_,_=self.worker_grant();result={}
        for label,name,seconds in (('work','service-first-result.json',275),('cleanup','profile-first-result.json',310)):
            value=load(self.control/(label+'-observation.json'))
            exact(value,{'schema','run_id','entry_nonce','origin_ns','label','observed_at_ns','sha256'},'Independent progress')
            require(type(value['schema']) is int and value['schema']==1 and value['run_id']==self.run_id
                and value['entry_nonce']==a['entry_nonce'] and value['origin_ns']==a['origin_ns'] and value['label']==label,'Progress run/clock binding')
            now=value['observed_at_ns'];cutoff=a['origin_ns']+seconds*10**9
            require(type(now) is int and a['origin_ns']<=now<=self.clock() and (now<cutoff if label=='work' else now<=cutoff),
                'Independent progress outside original deadline')
            require(value['sha256']==sha(self.case/name),'Progress source bytes changed')
            result[label]=value
        require(result['work']['observed_at_ns']<=result['cleanup']['observed_at_ns'],'Independent progress order')
        return result

    def seal_worker(self,native_exit):
        a,g,grant_sha=self.worker_grant();self._time(a['origin_ns'],315)
        self.protected('protected-after.json',a['origin_ns'])
        self._exit(native_exit,g,a,require_success=False)
        progress_sha=save_new(self.control/'worker-progress.json',self.progress())
        value=dict(schema=1,run_id=self.run_id,entry_nonce=a['entry_nonce'],origin_ns=a['origin_ns'],allocation_sha256=sha(self.root/'release/consumed.json'),
            entry_grant_sha256=grant_sha,native_exit=deepcopy(native_exit),hashes=self.closed_hashes(),progress_sha256=progress_sha)
        save_new(self.control/'worker-observation.json',value)
        return value

    def _exit(self,value,g,a,*,require_success):
        exact(value,EXIT_FIELDS,'Root native exit')
        native_key(value['identity'])
        require(same(value['identity'],g['worker_native']) and value['role']=='worker' and value['signaled'] is True,'Independent worker exit identity/signal')
        require(type(value['exit_code']) is int and 0<=value['exit_code']<=0xffffffff and (not require_success or value['exit_code']==0),'Native worker did not exit successfully')
        require(type(value['observed_at_ns']) is int and g['admitted_at_ns']<=value['observed_at_ns']<=self.clock()
                and value['observed_at_ns']<=a['origin_ns']+315*10**9,'Native exit observation clock')

    def readback(self,folder,first):
        require(folder==self.case,'Fixed independent reader case')
        a,g,grant_sha=self.worker_grant();self._time(a['origin_ns'],315)
        observation_raw=read(self.control/'worker-observation.json');o=decode(observation_raw)
        exact(o,OBSERVATION_FIELDS,'Root worker observation')
        require(type(o['schema']) is int and o['schema']==1 and o['run_id']==self.run_id and o['entry_nonce']==a['entry_nonce']
                and o['origin_ns']==a['origin_ns'] and o['allocation_sha256']==sha(self.root/'release/consumed.json')
                and o['entry_grant_sha256']==grant_sha,'Root observed allocation/origin drift')
        self._exit(o['native_exit'],g,a,require_success=True)
        require(o['progress_sha256']==sha(self.control/'worker-progress.json')
                and same(load(self.control/'worker-progress.json'),self.progress()),'Independent progress drift')
        self.protected('protected-after.json',a['origin_ns'])
        hashes=self.closed_hashes();require(same(hashes,o['hashes']),'Root closed references drift')
        require(type(first) is dict and same(load(self.case/'profile-first-result.json'),first),'Untrusted first comparison mismatch')
        require(first.get('run_id')==self.run_id and first.get('entry_nonce')==a['entry_nonce']
                and type(first.get('worker_pid')) is int and first['worker_pid']==g['worker_native']['pid']
                and type(first.get('worker_creation_filetime')) is int and first['worker_creation_filetime']==g['worker_native']['created_filetime'],
                'Worker first identity differs from independent root')
        require(not any(k in first for k in ('python_exit_code','observed_at_ns','origin_ns')),'Worker supplied root observation fields')
        require(all(type(first.get(k)) is int for k in ('work_returned_ns','cleanup_closed_ns','sealed_ns')),'Worker typed comparison times')
        require(a['origin_ns']<=first['work_returned_ns']<=first['cleanup_closed_ns']<=first['sealed_ns']
                and first['work_returned_ns']<a['origin_ns']+275*10**9
                and first['cleanup_closed_ns']<=a['origin_ns']+310*10**9
                and first['sealed_ns']<=self.progress()['cleanup']['observed_at_ns']
                and first['sealed_ns']<=o['native_exit']['observed_at_ns'],'Worker comparison times differ from original independent clock')
        now=self._time(a['origin_ns'],315)
        require(read(self.control/'worker-observation.json')==observation_raw,'Observation changed during read')
        return dict(run_id=self.run_id,entry_nonce=a['entry_nonce'],worker_pid=g['worker_native']['pid'],
            worker_creation_filetime=g['worker_native']['created_filetime'],python_exit_code=o['native_exit']['exit_code'],observed_at_ns=now,**hashes)


class WorkerControls(PROFILE.RootControls):
    def __init__(self,context):self.context=context;self.used=False
    def admit(self,folder,pins):
        require(not self.used,'Worker admission already consumed');self.used=True
        ctx=self.context;a,g,grant_sha=ctx.worker_grant(fresh=True)
        ctx._time(a['origin_ns'],275,exclusive=True)
        require(folder==ctx.case and g['worker_native']['pid']==os.getpid(),'Actual worker role mismatch')
        equal_pins(pins,ctx.pins())
        origin=a['origin_ns']
        return dict(run_id=ctx.run_id,entry_nonce=a['entry_nonce'],worker_pid=g['worker_native']['pid'],
            worker_creation_filetime=g['worker_native']['created_filetime'],origin_ns=origin,
            work_deadline_ns=origin+275*10**9,cleanup_deadline_ns=origin+310*10**9,seal_deadline_ns=origin+315*10**9,
            case_root=str(ctx.case),worker_executable=str(PY),candidate=CANDIDATE,model_digest=MODEL_DIGEST,scope=SCOPE,
            consumed=1,max_submissions=1,retry=0,actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,
            ssrf_fail_open_present=False,ssrf_backend=g['ssrf_backend'],profile_manifest_sha256=pins['profile_manifest_sha256'],
            candidate_manifest_sha256=pins['candidate_manifest_sha256'],corpus_sha256=pins['corpus_sha256'],
            root_control_manifest_sha256=ctx.manifest_sha,allocation_sha256=sha(ctx.root/'release/consumed.json'),
            entry_grant_sha256=grant_sha,protected_before_sha256=g['protected_before_sha256'])


class ReaderControls(PROFILE.RootControls):
    def __init__(self,context):self.context=context;self.calls=0;self.previous=None;self.observations=[]
    def readback(self,folder,first):
        require(self.calls<2,'Only two independent readbacks');self.calls+=1
        result=self.context.readback(folder,first)
        if self.previous is not None:
            PROFILE.validate_readback(result,first,{},self.previous)
        self.previous=deepcopy(result);self.observations.append(deepcopy(result))
        return result
