"""Revision 3 original acceptance evidence controller. Root alone releases a case."""
from __future__ import annotations
import base64
import argparse, ctypes as C, datetime as dt, hashlib, json, os, socket, stat, subprocess, sys, time, uuid
from pathlib import Path
import urllib.request
P=Path(__file__).resolve().parent
P1=P.parent/'preparation'
if hashlib.sha256((P1/'acceptance_adapter.py').read_bytes()).hexdigest()!='d91ddf5e44a19d6143ee8657f1e0946617eb1c77197c399d017ace39cad02da4': raise RuntimeError('P1 changed')
sys.path.insert(0,str(P1))
import acceptance_adapter as old
ROOT,R,MODEL,DIGEST,ORDER,MODULE=old.ROOT,old.R,old.MODEL,old.DIGEST,old.ORDER,old.MODULE
sha,load,save,identity,protected,environment,terminate_owned=old.sha,old.load,old.save,old.identity,old.protected,old.environment,old.terminate_owned
no_reparse=old.no_reparse
MAX_ADMISSION=120
IDENTITY=('hwnd','control_hwnd','pid','process_created_filetime','title','class')

def require(ok,message):
    if not ok: raise ValueError(message)
def utc(): return dt.datetime.now(dt.timezone.utc)
def timestamp(value):
    result=dt.datetime.fromisoformat(value.replace('Z','+00:00'))
    require(result.tzinfo is not None,'Timezone required'); return result

def uuid_text(value):
    require(isinstance(value,str),'UUID string required')
    try: parsed=uuid.UUID(value)
    except (ValueError,AttributeError): raise ValueError('Canonical UUID required')
    require(str(parsed)==value and parsed.version==4,'Canonical UUID4 required')
    return value

def artifact_path(folder,task,value):
    uuid_text(task)
    require(isinstance(value,str) and Path(value).is_absolute(),'Absolute artifact path required')
    raw=Path(value); fixed=folder/'outputs'
    require('..' not in raw.parts and raw.parent==fixed/task and raw.is_relative_to(fixed),'Outside lexical task root')
    require(':' not in value[2:],'Alternate streams forbidden')
    raw=no_reparse(raw); root=no_reparse(fixed).resolve()
    resolved=raw.resolve()
    require(resolved.is_relative_to(root) and resolved.parent==root/task,'Artifact outside exact task root')
    return resolved

def source_check():
    current=old.source_check()
    for path,digest in load(P/'inputs.json')['files'].items(): require(sha(path)==digest,'Input drift '+path)
    return current

def validate_authority(case,folder,authority_path,ledger_path,*,active=False,now=None):
    require(not sys.flags.optimize,'Optimized Python forbidden')
    require(case in ORDER,'Only original cases')
    require(no_reparse(folder)==R/'actual'/case,'Exact fixed case root required')
    require(active or not folder.exists(),'Existing case forbidden')
    require(no_reparse(authority_path)==R/'controller-authority'/f'{case}.json','Canonical authority path required')
    require(no_reparse(ledger_path)==R/'controller-ledger.json','Canonical ledger path required')
    authority=load(authority_path); ledger=load(ledger_path); now=now or utc()
    require(authority.get('schema')==2 and ledger.get('schema')==2 and authority.get('issuer')=='root','Current root schema required')
    require(authority.get('case')==case and authority.get('folder')==str(folder),'Case binding mismatch')
    issued=timestamp(authority['issued_at']); expiry=timestamp(authority['expires_at'])
    require(issued<=now<expiry and 0<(expiry-issued).total_seconds()<=MAX_ADMISSION,'Expired/stale admission')
    require(authority.get('model')==MODEL and authority.get('digest')==DIGEST,'Model boundary mismatch')
    require(authority.get('preparation_manifest_sha256')==sha(P/'manifest.json'),'Preparation mismatch')
    package=load(P/'manifest.json')
    require(package.get('files',{}).get('controller.py')==sha(__file__),'Loaded runner/package mismatch')
    for name,digest in package['files'].items():
        require(Path(name).name==name,'Unsafe package entry')
        require(sha(no_reparse(P/name))==digest,'Preparation file drift')
    approval_path=no_reparse(R/'controller-preparation-approval.json'); approval=load(approval_path)
    review_path=no_reparse(R/'review-preparation-3/review.md')
    require(approval.get('schema')==2 and approval.get('overall')=='PASS' and approval.get('reviewer')=='root-independent','Independent preparation approval required')
    require(approval.get('preparation_manifest_sha256')==sha(P/'manifest.json') and approval.get('review_sha256')==sha(review_path),'Current review mismatch')
    require(authority.get('approval_sha256')==sha(approval_path),'Approval binding mismatch')
    require(authority.get('ledger_sha256')==sha(ledger_path),'Root ledger binding mismatch')
    index=ORDER.index(case)
    require(ledger.get('consumed')==list(ORDER[:index+1]) and ledger.get('released_case')==case,'Exact ordered preconsumption cap required')
    proof_path=no_reparse(R/'controller-native-preflight'/f'{case}.json'); proof=load(proof_path)
    require(authority.get('native_preflight_sha256')==sha(proof_path),'Native proof binding mismatch')
    age=(now-timestamp(proof['recorded_at'])).total_seconds()
    require(0<=age<=60 and proof.get('source21_sha256')==sha(R/'source21-before.json') and proof.get('head')=='244d2120abcd6b8d7744f74a05bd22de46a2d3a5','Stale source/native proof')
    require(proof.get('model')==MODEL and proof.get('digest')==DIGEST,'Preflight model mismatch')
    actual=R/'actual'; names={x.name for x in actual.iterdir()} if actual.exists() else set()
    require(names==set(ORDER[:index])|({case} if active else set()),'Unexpected/preexisting sibling state')
    reviews=authority.get('prior_reviews',[])
    require([x.get('case') for x in reviews]==list(ORDER[:index]),'Exact predecessor reviews required')
    for item in reviews:
        terminal_path=no_reparse(actual/item['case']/'terminal.json'); terminal=load(terminal_path)
        require(item.get('terminal_sha256')==sha(terminal_path) and terminal.get('case')==item['case'] and terminal.get('mechanical')=='PASS' and terminal.get('overall')=='PASS' and terminal.get('cleanup')=='PASS' and terminal.get('boundaries')=='PASS','Predecessor overall failure')
        review=no_reparse(actual/item['case']/'independent-review.json'); accepted=load(review)
        require(item.get('review_sha256')==sha(review) and accepted.get('terminal_sha256')==sha(terminal_path) and accepted.get('reviewer')=='root-independent','Predecessor review binding')
        require(all(accepted.get(k)=='PASS' for k in ('facts','mechanical','target','file','cleanup','boundaries')),'Predecessor independent acceptance required')
    return authority,ledger,proof

def get_json(url):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self,*args,**kwargs): raise ValueError('Redirect forbidden')
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
    with opener.open(url,timeout=2) as response: return json.load(response)

def native_proof(root_proof):
    require(os.environ.get('OLLAMA_HOST','http://localhost:11434') in ('http://localhost:11434','http://127.0.0.1:11434'),'Local model only')
    source_check(); protected()
    version=get_json('http://127.0.0.1:11434/api/version'); tags=get_json('http://127.0.0.1:11434/api/tags')
    path=Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama/models')/'manifests/registry.ollama.ai/library'/MODEL/'latest'
    manifest=no_reparse(path).read_bytes()
    old.metadata_valid({'ok':True,'model':MODEL,'agent':'native_react'},version,tags,manifest)
    require(root_proof.get('version')==version and root_proof.get('tags_sha256')==hashlib.sha256(json.dumps(tags,sort_keys=True).encode()).hexdigest() and root_proof.get('manifest_sha256')==hashlib.sha256(manifest).hexdigest(),'Fresh native proof differs from root binding')
    return {'recorded_at':utc().isoformat(),'version':version,'tags':tags,'manifest_sha256':hashlib.sha256(manifest).hexdigest(),'model':MODEL,'digest':DIGEST}

def argv_parse(text):
    from ctypes import wintypes as W
    shell=C.WinDLL('shell32'); kernel=C.WinDLL('kernel32')
    shell.CommandLineToArgvW.argtypes=[W.LPCWSTR,C.POINTER(C.c_int)]; shell.CommandLineToArgvW.restype=C.POINTER(W.LPWSTR)
    kernel.LocalFree.argtypes=[W.HLOCAL]
    count=C.c_int(); pointer=shell.CommandLineToArgvW(text,C.byref(count))
    if not pointer: raise OSError('CommandLineToArgvW')
    try: return [pointer[i] for i in range(count.value)]
    finally: kernel.LocalFree(C.cast(pointer,W.HLOCAL))

def process_snapshot(pids=None,proof=None):
    # Encode commandlines as UTF16LE base64 inside the child PowerShell process.
    # The wire JSON is ASCII; strict decoding never guesses GB2312/UTF8 or replaces.
    query='Get-CimInstance Win32_Process'
    if pids is not None:
        require(pids and all(type(pid) is int and pid>0 for pid in pids),'Exact PID scope required')
        query+=' -Filter "'+ ' OR '.join('ProcessId='+str(pid) for pid in pids)+'"'
    script=query+' | ForEach-Object { [pscustomobject]@{ProcessId=[int]$_.ProcessId;ParentProcessId=[int]$_.ParentProcessId;CommandLineBase64=[Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes([string]$_.CommandLine))} } | ConvertTo-Json -Compress'
    raw=subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',script],creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    records=json.loads(raw.decode('ascii',errors='strict') or '[]')
    if isinstance(records,dict): records=[records]
    snapshot={}
    for row in records:
        row=dict(row);row['CommandLine']=base64.b64decode(row['CommandLineBase64'],validate=True).decode('utf-16-le',errors='strict');snapshot[row['ProcessId']]=row
    if proof is not None:
        require(pids is not None,'Raw proof must be scoped to owned PIDs')
        Path(proof).with_suffix('.raw').write_bytes(raw)
        save(proof,{'transport':'ASCII JSON with base64 UTF16LE commandline','raw_sha256':hashlib.sha256(raw).hexdigest(),'raw_hex':raw.hex(),'records':snapshot})
    return snapshot


def process_times(proc):
    from ctypes import wintypes as W
    kernel=C.WinDLL('kernel32'); kernel.GetProcessTimes.argtypes=[W.HANDLE,*([C.POINTER(W.FILETIME)]*4)]
    values=[W.FILETIME() for _ in range(4)]
    if not kernel.GetProcessTimes(int(proc._handle),*[C.byref(x) for x in values]): raise OSError('Retained launcher times unavailable')
    return tuple(x.dwLowDateTime+(x.dwHighDateTime<<32) for x in values[:2])

def candidate_valid(key,row,root,argv,allowed_exes,exit_ticks):
    return (row['ParentProcessId']==root['pid'] and root['created_filetime']<=key['created_filetime'] and (not exit_ticks or key['created_filetime']<=exit_ticks) and key['exe'].lower() in allowed_exes and argv_parse(row['CommandLine'])[1:]==argv)

class Owned:
    def __init__(self,folder,env):
        self.folder,self.env=folder,env; self.launchers=[]; self.known={}; self.logs=[]; self.errors=[]; self.auxiliary={}; self.stale=[]
        self.allowed_exes={str(Path(sys.executable)).lower(),identity(os.getpid())['exe'].lower()}
        self.forbidden={x['pid'] for x in protected()}
    def discover(self):
        snapshot=process_snapshot()
        for item in self.launchers:
            proc=item['proc']; created,exited=process_times(proc)
            require(created==item['identity']['created_filetime'],'Launcher creation drift')
            for pid,row in snapshot.items():
                if row['ParentProcessId']!=proc.pid: continue
                key=identity(pid)
                # Console hosts have no case argv. Observation only: never terminate.
                console=str(Path(os.environ.get('SystemRoot','C:/Windows'))/'System32/conhost.exe').lower()
                if key['created_filetime']<created:
                    self.stale.append({'identity':key,'reason':'predates launcher'}); continue
                if key['exe'].lower()==console and (not exited or key['created_filetime']<=exited):
                    self.auxiliary[pid]={'identity':key,'parent':proc.pid,'argv':row['CommandLine'],'authority':'observe-only'}; continue
                # Ambiguous matching parent is never sufficient authority to stop.
                if not candidate_valid(key,row,item['identity'],item['argv'],self.allowed_exes,exited):
                    self.errors.append({'discovery':'ambiguous-child','pid':pid,'identity':key,'argv_matches':argv_parse(row['CommandLine'])[1:]==item['argv']}); continue
                require(pid not in self.forbidden,'Protected identity in tree')
                previous=self.known.get(pid)
                require(previous is None or previous['identity']==key,'Owned PID reuse')
                self.known[pid]={'identity':key,'role':item['role'],'argv':row['CommandLine'],'parent':proc.pid}
        # Inspect below validated interpreter children too. New nested identities
        # have no original launch authority: record and fail, never terminate.
        for parent_pid,parent in list(self.known.items()):
            if parent_pid not in snapshot: continue
            try: require(identity(parent_pid)==parent['identity'],'Known parent identity drift')
            except OSError: continue
            pending=[(parent_pid,parent['identity']['created_filetime'])]; visited=set()
            while pending:
                ancestor,created=pending.pop()
                if ancestor in visited: continue
                visited.add(ancestor)
                for pid,row in snapshot.items():
                    if row['ParentProcessId']!=ancestor or pid in self.known or pid in self.auxiliary: continue
                    key=identity(pid)
                    if key['created_filetime']<created: continue
                    self.errors.append({'discovery':'unknown-nested-descendant','identity':key,'parent':ancestor,'authority':'none'})
                    pending.append((pid,key['created_filetime']))
        save(self.folder/'owned-tree.json',{'processes':list(self.known.values()),'auxiliary':list(self.auxiliary.values()),'stale_rejected':self.stale,'errors':self.errors})
        require(not self.errors,'Owned discovery ambiguity')
        return snapshot
    def launch(self,argv,role):
        from src.brain.tests import work_context_acceptance as h
        out=open(self.folder/(role+'.stdout'),'w',encoding='utf-8'); err=open(self.folder/(role+'.stderr'),'w',encoding='utf-8'); self.logs.extend((out,err))
        proc=h.launch(argv,self.env,out,err); key=identity(proc.pid)
        require(key['pid'] not in self.forbidden and key['exe'].lower() in self.allowed_exes,'Unexpected launcher identity')
        item={'proc':proc,'identity':key,'argv':argv,'role':role}; self.launchers.append(item)
        self.known[proc.pid]={'identity':key,'role':role,'argv':argv,'parent':os.getpid()}
        self.discover(); return proc
    def flush(self):
        for stream in self.logs: stream.flush()
    def cleanup(self,port=None):
        records=[]
        try: self.discover()
        except Exception as exc: self.errors.append({'discovery_error':str(exc)})
        (self.folder/'stop').touch()
        for item in self.launchers:
            if item['role']=='fixture':
                try: item['proc'].wait(timeout=3)
                except subprocess.TimeoutExpired: pass
        roots={x['proc'].pid for x in self.launchers}
        for item in sorted(self.known.values(),key=lambda x:x['identity']['pid'] in roots):
            key=item['identity']; pid=key['pid']
            try:
                if pid in process_snapshot(): terminate_owned(key)
                absent=pid not in process_snapshot()
                require(absent,'Owned PID remains')
                records.append({'identity':key,'absent':True})
            except Exception as exc: self.errors.append({'cleanup':pid,'error':str(exc)}); records.append({'identity':key,'absent':False})
        for item in self.launchers:
            try: item['proc'].wait(timeout=2)
            except subprocess.TimeoutExpired: self.errors.append({'launcher_remains':item['proc'].pid})
        # Let console auxiliaries exit naturally; no parent-only termination.
        deadline=time.monotonic()+3
        while self.auxiliary and time.monotonic()<deadline:
            snapshot=process_snapshot()
            if not any(pid in snapshot for pid in self.auxiliary): break
            time.sleep(.05)
        snapshot=process_snapshot()
        for pid,item in self.auxiliary.items():
            if pid in snapshot: self.errors.append({'auxiliary_remains':item})
            else: records.append({'identity':item['identity'],'absent':True,'authority':'observe-only'})
        for stream in self.logs: stream.close()
        closed=True
        if port:
            probe=socket.socket(); probe.settimeout(1)
            try: closed=probe.connect_ex(('127.0.0.1',port))!=0
            finally: probe.close()
        result={'status':'PASS' if records and all(x['absent'] for x in records) and closed and not self.errors else 'FAIL','processes':records,'port_closed':closed,'errors':self.errors}
        save(self.folder/'cleanup.json',result); return result

def listener_owner(port):
    text=subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',f'@(Get-NetTCPConnection -State Listen -LocalPort {int(port)} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess) | ConvertTo-Json -Compress'],text=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=15).strip()
    value=json.loads(text or '[]'); return [value] if isinstance(value,int) else value

def assert_listener(owned,port,server_argv):
    owned.discover(); owners=set(listener_owner(port))
    require(len(owners)==1,'Unique listener required')
    pid=owners.pop(); item=owned.known.get(pid)
    require(item is not None and item['role']=='server' and identity(pid)==item['identity'],'Listener not owned server')
    argv=item['argv'] if isinstance(item['argv'],list) else argv_parse(item['argv'])[1:]
    require(argv==server_argv and str(owned.folder/'runtime') in argv and str(owned.folder/'outputs') in argv,'Listener case argv/root mismatch')
    proof={'port':port,'identity':item['identity'],'role':'server','argv':argv}; save(owned.folder/'listener.json',proof); return proof

def output_inventory(folder):
    root=no_reparse(folder/'outputs'); records=[]
    def walk(directory):
        for entry in os.scandir(directory):
            path=no_reparse(entry.path)
            require(path.resolve().is_relative_to(root.resolve()),'Inventory escape')
            require(len(records)<64,'Inventory bound exceeded')
            if entry.is_dir(follow_symlinks=False): walk(path)
            elif entry.is_file(follow_symlinks=False):
                require(path.stat().st_size<=1048576,'Output too large')
                raw=path.read_bytes(); records.append({'path':str(path.resolve()),'sha256':hashlib.sha256(raw).hexdigest(),'bytes_hex':raw.hex()})
            else: raise ValueError('Unknown output object')
    if root.exists(): walk(root)
    return records

def inventory_map(records):
    require(isinstance(records,list),'Output inventory unavailable')
    values={}
    for item in records:
        require(isinstance(item,dict) and all(isinstance(item.get(k),str) for k in ('path','bytes_hex','sha256')),'Incomplete inventory record')
        path=item['path'];require(path not in values,'Duplicate inventory path')
        raw=bytes.fromhex(item['bytes_hex']);require(hashlib.sha256(raw).hexdigest()==item['sha256'],'Inventory bytes/hash contradiction')
        values[path]={'sha256':item['sha256'],'bytes_hex':raw.hex()}
    return values

def reconcile_effects(expected,effects):
    require(expected is not None,'Accepted final state unavailable')
    required_unknown=('outputs_unknown','effects_unknown','logs_flush_unknown','fixture_owner_unknown')
    require(not any(k in effects for k in required_unknown) and not effects.get('product_result_conflict') and not (expected.get('cli_count',1)>0 and 'product_unknown' in effects),'Final effects unknown')
    require(expected['windows'] is None or 'windows_unknown' not in effects,'Required final window unknown')
    require(inventory_map(effects.get('outputs'))==inventory_map(expected['outputs']),'Final output set/bytes/hash changed')
    if expected['windows'] is not None:
        require(effects.get('windows')==expected['windows'],'Final owned window identity/text/selection/caret changed')
    return 'PASS'

def read_artifacts(folder,result):
    task=uuid_text(result.get('task_id')); artifacts=[]; attempts=[]
    for item in result.get('artifacts',[]):
        attempt={'claimed_artifact':item};attempts.append(attempt)
        try:
            path=artifact_path(folder,task,item.get('path')); raw=path.read_bytes()
            attempt.update(path=str(path),bytes_hex=raw.hex(),sha256=hashlib.sha256(raw).hexdigest())
            text=raw.decode('utf-8');artifacts.append(dict(item,text=text,external_sha256=attempt['sha256']))
        except Exception as exc:
            attempt.update(error=str(exc),error_type=type(exc).__name__);raise
        finally:
            save(folder/'external-readback-attempts.json',attempts)
            save(folder/'external-artifacts.json',artifacts)
    return artifacts


def ids(item,result):
    require(all(item.get(k)==result[k] for k in ('request_id','session_id','task_id')),'Run identity mismatch')
    uuid_text(item.get('call_id'))

def sdk_tool_proof(result,name,content):
    trace=result.get('trace',[])
    starts=[(i,x) for i,x in enumerate(trace) if x.get('type')=='tool_call_start' and x.get('data',{}).get('tool')==name]
    ends=[(i,x) for i,x in enumerate(trace) if x.get('type')=='tool_call_end' and x.get('data',{}).get('tool')==name]
    sdk=[x for x in result.get('tool_results',[]) if 'call_id' not in x and x.get('tool_name')==name]
    require(len(starts)==len(ends)==len(sdk)==1 and starts[0][0]<ends[0][0] and ends[0][1]['data'].get('success') is True and sdk[0].get('success') is True,'Completed SDK tool evidence missing')
    require(starts[0][1]['data'].get('arguments',{}).get('content')==content,'SDK arguments/ledger mismatch')
    return starts[0][1]['data']['arguments']

def mechanical(case,folder,result,artifacts,baseline,windows,inventory):
    require(result.get('status')=='succeeded' and result.get('request_id')==case and result.get('session_id')==case,'Product identity/status mismatch'); uuid_text(result.get('task_id'))
    expected='rewrite.md' if case.startswith('e03') else 'summary.md'
    require(len(artifacts)==1 and Path(artifacts[0]['path']).name==expected,'Exact output set required')
    artifact=artifacts[0]; ids(artifact,result)
    require(artifact.get('verified') is True and artifact['sha256']==artifact['external_sha256'],'Service/external hash mismatch')
    expected_inventory={artifact['path']:{'sha256':artifact['external_sha256'],'bytes_hex':artifact['text'].encode('utf-8').hex()}}
    require(inventory_map(inventory)==expected_inventory,'Unrelated/missing/contradictory output bytes/hash')
    records=[x for x in result.get('tool_results',[]) if 'call_id' in x]
    writes=[x for x in records if x.get('tool_name')=='ultima_work_file_write']
    require(len(writes)==1 and writes[0].get('success') is True,'One completed actual write required')
    write=writes[0]; ids(write,result)
    require(write['call_id']==artifact['call_id'] and write['path']==artifact['path'],'Write/artifact call mismatch')
    sdk_args=sdk_tool_proof(result,'ultima_work_file_write',write['content'])
    sdk_path=Path(sdk_args['path']); sdk_path=sdk_path if sdk_path.is_absolute() else folder/'outputs'/result['task_id']/sdk_path
    require(artifact_path(folder,result['task_id'],str(sdk_path))==Path(artifact['path']),'SDK write path mismatch')
    require(write['content'].replace('\r\n','\n')==artifact['text'].replace('\r\n','\n'),'Write content/readback mismatch')
    if case.startswith('e03'):
        require(len(baseline)==len(windows)==2,'Two owned windows required')
        capture=result['work_context']; uuid_text(capture.get('capture_id'))
        require(capture.get('available') is True and capture.get('source')=='win32.standard_edit','Current capture required')
        require(all(capture['window'][k]==baseline[0][k] for k in IDENTITY),'Capture target mismatch')
        require(capture['text_sha256']==hashlib.sha256(baseline[0]['text'].encode()).hexdigest(),'Capture text mismatch')
        timing=load(folder/'dispatch-baseline-timing.json'); final_timing=load(folder/'final-windows-timing.json')
        require(timestamp(timing['ended_at'])<=timestamp(capture['captured_at'])<=timestamp(final_timing['ended_at']),'Stale capture time')
        selection=capture['selection']; before=baseline[0]; raw=before['text'].encode('utf-16-le')
        require(selection['start_utf16']==before['start_utf16'] and selection['end_utf16']==before['end_utf16'] and 0<=selection['start_utf16']<selection['end_utf16']<=len(raw)//2,'Baseline selection mismatch')
        require(selection['text']==raw[2*selection['start_utf16']:2*selection['end_utf16']].decode('utf-16-le'),'Captured selection content mismatch')
        edits=result.get('context_results',[]); require(len(edits)==1,'One context result required'); edit=edits[0]; ids(edit,result)
        require(edit['before']==before,'Fresh before record mismatch')
        replaces=[x for x in records if x.get('tool_name')=='ultima_work_replace_selection' and x.get('event')!='mutation.send']
        sends=[x for x in records if x.get('event')=='mutation.send']
        require(len(replaces)==len(sends)==1 and replaces[0].get('success') is True,'One completed replace and one mutation send required')
        for item in (replaces[0],sends[0]): ids(item,result); require(item['call_id']==edit['call_id'],'Replace call mismatch')
        require(replaces[0]['result']['replacement_text']==edit['replacement_text'] and replaces[0]['result']['before']==before,'Replace evidence mismatch')
        require(sends[0].get('may_have_committed') is True,'Missing mutation intent witness')
        sdk_tool_proof(result,'ultima_work_replace_selection',edit['replacement_text'])
        replacement=edit['replacement_text']; expected_text=(raw[:2*before['start_utf16']]+replacement.encode('utf-16-le')+raw[2*before['end_utf16']:]).decode('utf-16-le')
        caret=before['start_utf16']+len(replacement.encode('utf-16-le'))//2
        for current,original in zip(windows,baseline): require(all(current[k]==original[k] for k in IDENTITY),'External target identity mismatch')
        require(windows[0]['text']==expected_text and windows[0]['start_utf16']==windows[0]['end_utf16']==caret,'External final text/caret mismatch')
        require(windows[1]['text']==baseline[1]['text'] and edit['after']==windows[0] and edit['expected_text']==expected_text,'Service/external state mismatch')
        require(artifact['path'] in edit['companion_paths'] and artifact['text'].replace('\r\n','\n')==replacement.replace('\r\n','\n'),'Exact companion mismatch')
    else: require(not any(x.get('event')=='mutation.send' or x.get('tool_name')=='ultima_work_replace_selection' for x in records),'Unexpected E01 mutation')
    return {'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}

class Case:
    def __init__(self,case,folder,env):
        self.case,self.folder=case,folder; self.owned=Owned(folder,env); self.port=None; self.fixture_ready=False; self.result=None; self.cli_count=0
    def observe(self,label):
        started=utc().isoformat()
        proc=self.owned.launch(['-B','-m',MODULE,'--observe-policy',str(self.folder/'fixture.json'),'--observe-result',str(self.folder/(label+'.json'))],label)
        require(proc.wait(timeout=15)==0,'Observer failed'); save(self.folder/(label+'-timing.json'),{'started_at':started,'ended_at':utc().isoformat()}); return load(self.folder/(label+'.json'))
    def command(self,index=0,select=True):
        from src.brain.tests import work_context_acceptance as h
        (self.folder/'command-done.json').unlink(missing_ok=True); save(self.folder/'command.json',{'index':index,'select':select}); h.wait_for(lambda:(self.folder/'command-done.json').exists(),10)
    def effects(self):
        evidence={'cli_count':self.cli_count,'native_start_count':None,'incomplete_inferences':None,'generation_after_disconnect':'unknown','attempted_at':utc().isoformat()}
        try: self.owned.flush()
        except Exception as exc: evidence['logs_flush_unknown']=str(exc)
        try:
            raw=(self.folder/'cli.stdout').read_text(encoding='utf-8'); evidence['raw_cli_preserved']='cli.stdout'
            observed=json.loads(raw); save(self.folder/'pre-cleanup-product-observed.json',observed)
            original=self.folder/'product-result.json'
            if original.exists():
                evidence['product_result_conflict']=load(original)!=observed
                self.result=load(original)
            else:
                self.result=observed;save(original,self.result)
        except Exception as exc: evidence['product_unknown']=str(exc)
        evidence['completed_inferences']=[x for x in (self.result or {}).get('trace',[]) if x.get('type')=='inference_end']
        try: evidence['outputs']=output_inventory(self.folder)
        except Exception as exc: evidence['outputs_unknown']=str(exc)
        if not self.fixture_ready and (self.folder/'fixture.json').exists():
            try:
                fixture=load(self.folder/'fixture.json'); owner=self.owned.known.get(fixture['pid'])
                self.fixture_ready=bool(owner and owner['role']=='fixture' and all(t['pid']==fixture['pid'] and t['process_created_filetime']==owner['identity']['created_filetime'] for t in fixture['targets']))
            except Exception as exc: evidence['fixture_owner_unknown']=str(exc)
        if self.fixture_ready:
            try: evidence['windows']=self.observe('pre-cleanup-windows')
            except Exception as exc: evidence['windows_unknown']=str(exc)
        else: evidence['windows_unknown']='No approved fixture was created'
        save(self.folder/'pre-cleanup-effects.json',evidence); return evidence
    def negative(self,baseline):
        from src.brain.work_context import WorkContextProvider,Win32Edit
        provider=WorkContextProvider(load(self.folder/'policy.json')); native=Win32Edit(); failures=[]; sends=[]
        before_files=output_inventory(self.folder)
        for scenario in ('focus','selection'):
            self.command(); capture=provider.capture_work_context(); require(capture['available'],'Negative capture unavailable')
            self.command(1 if scenario=='focus' else 0,scenario=='focus')
            current=self.observe('negative-'+scenario); focus=native.focused(); targets=load(self.folder/'fixture.json')['targets']; index=1 if scenario=='focus' else 0
            require(focus==(targets[index]['hwnd'],targets[index]['control_hwnd']),'Actual owned foreground change missing')
            require((current[0]['start_utf16'],current[0]['end_utf16'])!=(capture['selection']['start_utf16'],capture['selection']['end_utf16']) if scenario=='selection' else focus!=(targets[0]['hwnd'],targets[0]['control_hwnd']),'Actual negative change missing')
            rejected=False; error=None
            try: provider.replace_selection(capture,'SHOULD NEVER WRITE',before_send=lambda:sends.append(scenario))
            except ValueError as exc: rejected=True; error=str(exc)
            finally: provider.release(capture)
            after=self.observe('negative-'+scenario+'-after')
            require(rejected and not sends and [x['text'] for x in after]==[x['text'] for x in baseline] and output_inventory(self.folder)==before_files,'Negative refusal/mutation/text/file failure')
            failures.append({'scenario':scenario,'capture':capture,'changed_windows':current,'foreground':focus,'rejected':rejected,'error':error,'sends':list(sends),'texts_files_unchanged':True})
        self.accepted_effects={'outputs':before_files,'windows':after,'cli_count':0}
        save(self.folder/'negative-evidence.json',{'cases':failures,'mutation_sends':sends,'model_requests':0}); return {'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}

def execute(case,folder,authority_path,ledger_path):
    authority,ledger,root_proof=validate_authority(case,folder,authority_path,ledger_path)
    source_check(); before=protected(); native=native_proof(root_proof) # BEFORE fixture/UI, negative included
    folder.mkdir(parents=True,exist_ok=False)
    save(folder/'admission.json',{'authority':authority,'ledger':ledger,'native':native})
    sys.path.insert(0,str(ROOT)); context=Case(case,folder,environment(folder)); review=None; errors=[]; baseline=None; expected_effects=None
    try:
        from src.brain.tests import work_context_acceptance as h
        validate_authority(case,folder,authority_path,ledger_path,active=True)
        if case.startswith('e03'):
            context.owned.launch(['-B','-m',MODULE,'--fixture',str(folder)],'fixture'); h.wait_for(lambda:(folder/'fixture.json').exists(),20); context.owned.discover()
            fixture=load(folder/'fixture.json'); owner=context.owned.known.get(fixture['pid'])
            require(owner and owner['role']=='fixture' and all(t['pid']==fixture['pid'] and t['process_created_filetime']==owner['identity']['created_filetime'] for t in fixture['targets']),'Actual fixture owner mismatch')
            context.fixture_ready=True; baseline=context.observe('baseline')
            require(len(baseline)==2 and baseline[0]['text']==h.CASES['e03']['text'],'Frozen fixture mismatch')
        if case=='e03-negative':
            review=context.negative(baseline); expected_effects=context.accepted_effects
        else:
            sock=socket.socket(); sock.bind(('127.0.0.1',0)); context.port=sock.getsockname()[1]; sock.close()
            argv=['-B','-m','src.brain.agent_server','--port',str(context.port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--isolated']
            if case.startswith('e03'): argv+=['--work-target-policy',str(folder/'policy.json')]
            context.owned.launch(argv,'server')
            def ready():
                if not listener_owner(context.port): return False
                assert_listener(context.owned,context.port,argv)
                health=get_json(f'http://127.0.0.1:{context.port}/health')
                require(health.get('ok') is True and health.get('model')==MODEL and health.get('agent')=='native_react','Isolated health mismatch')
                return health
            save(folder/'isolated-health.json',h.wait_for(ready,30))
            if case.startswith('e03'): context.command(); baseline=context.observe('dispatch-baseline')
            validate_authority(case,folder,authority_path,ledger_path,active=True); save(folder/'native-dispatch.json',native_proof(root_proof)); assert_listener(context.owned,context.port,argv)
            query=h.CASES['e01']['request']+'\n'+'\n'.join(h.CASES['e01']['facts']); options=[]
            if case.startswith('e03'): query=old.E03_QUERY; options=['--current-window','--replace-selection']
            cli_args=['-B','-m','src.brain.cli','--work',*options,'--request-id',case,'--session-id',case,'--server-url',f'http://127.0.0.1:{context.port}','--json',query]
            save(folder/'argv.json',{'server':argv,'cli':cli_args,'max_turns':10,'work_max_tokens':2048,'CLI_timeout':300,'SDK_timeout':1800,'controller_wait':315,'overrides':[]})
            validate_authority(case,folder,authority_path,ledger_path,active=True)
            context.cli_count+=1; cli=context.owned.launch(cli_args,'cli'); old.wait_cli(cli,folder); context.owned.flush()
            context.result=load(folder/'cli.stdout'); save(folder/'product-result.json',context.result)
            require(cli.returncode==0,'Nonzero CLI exit; generation may continue')
            events=[x for x in context.result.get('trace',[]) if x.get('type')=='inference_end']; require(1<=len(events)<=10 and all(x.get('data',{}).get('model')==MODEL for x in events),'Completed inference proof missing')
            artifacts=read_artifacts(folder,context.result); windows=context.observe('final-windows') if context.fixture_ready else None
            observed_inventory=output_inventory(folder)
            save(folder/'mechanical-inputs.json',{'artifacts':artifacts,'baseline':baseline,'windows':windows,'outputs':observed_inventory})
            review=mechanical(case,folder,context.result,artifacts,baseline,windows,observed_inventory)
            expected_effects={'outputs':observed_inventory,'windows':windows,'cli_count':1}
            save(folder/'accepted-effects.json',expected_effects)
            save(folder/'mechanical-review.json',review)
    except Exception as exc: errors.append({'harness':str(exc),'type':type(exc).__name__})
    finally:
        try: effects=context.effects() # ALWAYS before target destruction/server termination
        except Exception as exc:
            effects={'effects_unknown':str(exc)}; save(folder/'pre-cleanup-effects.json',effects); errors.append({'effects':str(exc)})
        save(folder/'pre-cleanup-effects.json',effects)
        if review:
            try: reconcile_effects(expected_effects,effects)
            except Exception as exc: errors.append({'final_effects_consistency':str(exc)})
        try: save(folder/'native-after.json',native_proof(root_proof))
        except Exception as exc: errors.append({'native_boundary':str(exc)})
        try: cleanup=context.owned.cleanup(context.port)
        except Exception as exc:
            cleanup={'status':'FAIL','error':str(exc)}; save(folder/'cleanup.json',cleanup)
        boundary='FAIL'
        try:
            source_check(); after=protected(); require(after==before,'Protected identities changed'); boundary='PASS'; save(folder/'boundaries.json',{'status':'PASS','protected5':after})
        except Exception as exc: errors.append({'boundary':str(exc)})
        if 'outputs_unknown' in effects or context.fixture_ready and 'windows_unknown' in effects: errors.append({'failure_evidence':'Required effects unknown'})
        terminal={'schema':2,'case':case,'overall':'PASS' if review and not errors and cleanup['status']=='PASS' and boundary=='PASS' else 'FAIL','mechanical':(review or {}).get('mechanical','FAIL'),'facts':'PENDING_ROOT_INDEPENDENT_REVIEW','cleanup':cleanup['status'],'boundaries':boundary,'errors':errors,'product_result_sha256':sha(folder/'product-result.json') if (folder/'product-result.json').exists() else None,'effects_sha256':sha(folder/'pre-cleanup-effects.json'),'work_cli_count':context.cli_count,'actual_native_start_count':None}
        save(folder/'terminal.json',terminal)
    return terminal

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--case',required=True,choices=ORDER); args=parser.parse_args()
    terminal=execute(args.case,R/'actual'/args.case,R/'controller-authority'/f'{args.case}.json',R/'controller-ledger.json')
    print(json.dumps(terminal)); return 0 if terminal['overall']=='PASS' else 2
if __name__=='__main__': raise SystemExit(main())
