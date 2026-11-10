"""Prepared one-case root entry. No default runtime allocation."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import os
import stat
import sys
N=Path(__file__).resolve().parents[1]
CANDIDATE='900b944165c0175b91492e3fe5b31d96aabdcd5c'
MODEL='qwen3-8b-uncensored'
DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
KIND='SOURCE13_CURRENT8B_REAL_CONTROLLED_ONE_CASE'

PY=N.parents[4]/'tools/venv-openjarvis/Scripts/python.exe'
CAP=4*1024*1024

def require(ok,message):
    if not ok:raise ValueError(message)

def no_reparse(path):
    path=Path(path)
    require(path.is_absolute() and path==path.resolve(),'Canonical absolute path required')
    for member in (path,*path.parents):
        if member.exists():
            info=member.lstat()
            require(not stat.S_ISLNK(info.st_mode) and not getattr(info,'st_file_attributes',0)&0x400,'Reparse path refused')
    return path

def sha(path):return hashlib.sha256(no_reparse(path).read_bytes()).hexdigest()

def strict_json(raw):
    require(len(raw)<=CAP,'Bounded JSON required')
    def pairs(values):
        result={}
        for key,value in values:
            require(key not in result,'Duplicate JSON member');result[key]=value
        return result
    def nonfinite(value):raise ValueError('Nonfinite JSON')
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=nonfinite)

def load(path):
    with no_reparse(path).open('rb') as stream:return strict_json(stream.read(CAP+1))

def save_new(path,value):
    no_reparse(path)
    raw=json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False).encode('utf8')
    require(len(raw)<=CAP,'Bounded receipt required')
    with path.open('xb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())

def read_ready(root):
    require(type(root) is type(N) and root==N and root==root.resolve(),'Fixed prepared root required')
    manifest=load(root/'manifest.json')
    require(manifest.get('kind')=='SOURCE13_REAL_CONTROLLED_PREPARATION'
            and manifest.get('candidate')==CANDIDATE and manifest.get('model')==MODEL
            and manifest.get('model_digest')==DIGEST and manifest.get('actual_released') is False,'Current preparation binding')
    files=manifest.get('files')
    require(type(files) is dict and {'code/entry.py','code/bindings.py','harness/adapter.py','harness/manifest.json','inputs/input-manifest.json','execution-proposal.md'}<=set(files),'Complete preparation source set required')
    for name,digest in files.items():
        relative=Path(name)
        require(type(name) is str and not relative.is_absolute() and not relative.drive and '..' not in relative.parts
                and (root/relative).resolve().is_relative_to(root),'Relative preparation member required')
        require(type(digest) is str and sha(root/relative)==digest,'Preparation source drift')
    manifest_sha=sha(root/'manifest.json')
    review_path=root/'review/independent-preparation-review.json';review=load(review_path)
    require(review.get('reviewer')=='root-independent' and review.get('verdict')=='PASS_PREPARATION_ONLY'
            and review.get('manifest_sha256')==manifest_sha and review.get('actual_run_authorized') is False,'Independent preparation PASS required')
    review_sha=sha(review_path)
    approval=load(root/'harness-approval.json')
    require(approval==dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(root/'harness/manifest.json'),
            review_sha256=review_sha,preparation_manifest_sha256=manifest_sha),'Harness review binding required')
    return dict(manifest_sha256=manifest_sha,review_sha256=review_sha,harness_approval_sha256=sha(root/'harness-approval.json'))

def read_release(root,package,now):
    grant=load(root/'release/user-allocation.json')
    fields='schema kind source question_id answer candidate model model_digest manifest_sha256 review_sha256 case actual_case_allocation result_review_allocation retry issued_at expires_at'.split()
    require(type(grant) is dict and set(grant)==set(fields),'Closed user allocation fields required')
    require(type(grant['schema']) is int and grant['schema']==1 and grant['kind']==KIND and grant['source']=='user_explicit','Explicit real-case user allocation required')
    require(type(grant['question_id']) is str and grant['question_id'].startswith('call_')
            and grant['question_id']!='call_e9e5dd014d9b43f4b529f09bd2487d52'
            and type(grant['answer']) is str and bool(grant['answer'].strip()),'Fresh user decision required; zero-inference grant is spent')
    require(grant['candidate']==CANDIDATE and grant['model']==MODEL and grant['model_digest']==DIGEST,'Fixed current8B candidate required')
    require(all(grant[key]==package[key] for key in ('manifest_sha256','review_sha256')),'Allocation preparation binding')
    require(grant['case']=='E02-controlled-1' and all(type(grant[key]) is int and grant[key]==value for key,value in
            (('actual_case_allocation',1),('result_review_allocation',1),('retry',0))),'One case, one review, zero retries')
    issued=dt.datetime.fromisoformat(grant['issued_at']);expires=dt.datetime.fromisoformat(grant['expires_at'])
    require(issued.tzinfo is not None and expires.tzinfo is not None and issued<=now<expires
            and 0<(expires-issued).total_seconds()<=120,'Fresh bounded allocation required')
    return grant

def native_metadata(adapter,budget,path):
    """Two fixed loopback GETs only; no proxy, redirects or inference here."""
    import http.client
    require(path in ('/api/version','/api/tags'),'Fixed native metadata route')
    connection=http.client.HTTPConnection('127.0.0.1',11434,timeout=budget.clip(5,'metadata connect'))
    try:
        budget.call('metadata GET request',connection.request,'GET',path)
        response=budget.call('metadata GET response',connection.getresponse)
        require(response.status==200,'Native metadata status')
        raw=budget.call('bounded native metadata body',response.read,32769)
        require(len(raw)<=32768,'Native metadata size cap')
        value=strict_json(raw);require(type(value) is dict,'Native metadata object required')
        return value
    finally:connection.close()

def run_released(root,grant,package):
    require(Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
            and sys.flags.utf8_mode==1 and not sys.flags.optimize,'Fixed isolated interpreter required')
    source=root/'harness/adapter.py'
    spec=importlib.util.spec_from_file_location('source13_actual_harness',source)
    adapter=importlib.util.module_from_spec(spec);spec.loader.exec_module(adapter)
    invocation=adapter.RootInvocation();budget=invocation.budget
    # The original root clock begins before every authority/preflight operation.
    budget.call('full current input verification',adapter.check_inputs)
    parent=invocation.parent_timing();p4=budget.call('pinned identity helper',adapter.load_p4)
    with adapter.PrivateIO(p4,budget):
        protected=budget.call('current protected native identities',p4.protected)
        budget.call('current protected parent and command identities',adapter.validate_protected_members,protected,p4)
        expected_ollama=p4.old.protected_entries(adapter.load(adapter.PROTECTED_BASELINE))[0]['pid']
        require(budget.call('protected Ollama listener identity',p4.listener_owner,11434)==[expected_ollama],'Ollama listener identity drift')
    version=native_metadata(adapter,budget,'/api/version');tags=native_metadata(adapter,budget,'/api/tags')
    proof=dict(candidate=CANDIDATE,precision='FILETIME100ns',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=protected,version=version,tags=tags)
    inputs=adapter.bindings.load_inputs(adapter.INPUTS_PATH)
    budget.call('fixed native metadata validation',p4.old.metadata_valid,dict(ok=True,model=MODEL,agent='native_react'),version,tags,Path(inputs['model_manifest_path']).read_bytes())
    for name in ('controller-authority','native-preflight'):budget.call('fresh '+name,(root/name).mkdir,exist_ok=False)
    ledger_path=root/'controller-ledger.json';proof_path=root/'native-preflight/E02-controlled-1.json'
    budget.call('one preconsumed ledger',save_new,ledger_path,dict(schema=11,released_case='E02-controlled-1',consumed=['E02-controlled-1'],attempts=1,retry=0))
    budget.call('fresh native baseline',save_new,proof_path,proof)
    issued=dt.datetime.now(dt.timezone.utc)
    authority=dict(schema=11,kind='source10_execution',issuer='root',actual=True,case=adapter.CASE,candidate=CANDIDATE,
        candidate_manifest_sha256=adapter.MANIFEST_SHA,model=MODEL,native_precision='FILETIME100ns',
        issued_at=issued.isoformat(),expires_at=(issued+dt.timedelta(seconds=120)).isoformat(),budgets=adapter.BUDGETS,
        schedule=dict(work_seconds=275,cleanup_seconds=310,outer_seconds=315,ruling_sha256='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'),
        parent_timing=parent,ledger_sha256=sha(ledger_path),approval_sha256=package['harness_approval_sha256'],native_preflight_sha256=sha(proof_path),
        folder=str(root/'actual/E02-controlled-1'),port=18799)
    authority_path=root/'controller-authority/E02-controlled-1.json'
    budget.call('same-clock root authority',save_new,authority_path,authority)
    outcome=invocation.call(adapter.run_case,authority_path,ledger_path)
    terminal=outcome.get('result') or {}
    eligible=outcome['witness'].get('eligible') is True and terminal.get('overall')=='PENDING_ROOT_INDEPENDENT_REVIEW'
    return dict(status='PENDING_ROOT_INDEPENDENT_REVIEW' if eligible else 'FAIL',outcome=outcome,
                candidate=CANDIDATE,model=MODEL,model_digest=DIGEST,actual_case_allocation_remaining=0,
                result_review_allocation_remaining=1,acceptance_credit=0,next_case=False,retry=False)

def run_once(root):
    package=read_ready(root)
    grant=read_release(root,package,dt.datetime.now(dt.timezone.utc))
    save_new(root/'release/consumed.json',dict(allocation_sha256=sha(root/'release/user-allocation.json'),
        package=package,case='E02-controlled-1',consumed_at=dt.datetime.now(dt.timezone.utc).isoformat(),retry=0))
    try:
        require(read_ready(root)==package and load(root/'release/user-allocation.json')==grant,'Post-consumption input drift')
        result=run_released(root,grant,package)
    except BaseException as exc:
        result=dict(status='FAIL',error=type(exc).__name__+': '+str(exc),actual_case_allocation_remaining=0,
                    result_review_allocation_remaining=1,acceptance_credit=0,next_case=False,retry=False)
    save_new(root/'release/root-outcome.json',result)
    return result

if __name__=='__main__':
    require(not sys.argv[1:],'Fixed entry accepts no overrides')
    result=run_once(N)
    print(json.dumps(dict(status=result['status'],candidate=CANDIDATE,acceptance_credit=0,output=str(N/'release/root-outcome.json'))))
    raise SystemExit(0 if result['status']=='PENDING_ROOT_INDEPENDENT_REVIEW' else 1)
