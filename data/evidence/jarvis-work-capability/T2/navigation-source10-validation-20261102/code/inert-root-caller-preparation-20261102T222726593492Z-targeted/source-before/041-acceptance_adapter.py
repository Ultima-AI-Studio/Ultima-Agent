"""One root-released original acceptance case; no release is included in preparation.
Only the CLI submits work. No research, retry, budget override or model replacement.
"""
from __future__ import annotations
import argparse, ctypes as C, hashlib, json, os, socket, stat, subprocess, sys, time
from pathlib import Path
import urllib.request
ROOT=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
R=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102')
PREP=R/'preparation'
MODEL='qwen3-8b-uncensored'
DIGEST='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
ORDER=('e03-round1','e03-round2','e03-round3','e03-negative','e01-round1','e01-round2','e01-round3')
MODULE='src.brain.tests.work_context_acceptance'
E03_QUERY='将当前选区整理为三条要点，替换该选区，并保存相同改写到rewrite.md。保留所有原事实，不新增事实。'
CLI_TIMEOUT=315  # unchanged product HTTP client deadline 300 + bounded receipt margin

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def load(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def save(path,value): Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
def no_reparse(path):
    p=Path(path).absolute()
    if '..' in p.parts: raise ValueError('Traversal forbidden')
    for q in (p,*p.parents):
        if q.exists() and (q.is_symlink() or getattr(q.lstat(),'st_file_attributes',0)&stat.FILE_ATTRIBUTE_REPARSE_POINT):
            raise ValueError('Reparse path forbidden')
    return p

def source_check():
    expected=load(R/'source21-before.json')
    current={k:sha(ROOT/k) for k in expected}
    if current!=expected: raise ValueError('Frozen source21 drift')
    if subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()!='244d2120abcd6b8d7744f74a05bd22de46a2d3a5':
        raise ValueError('HEAD drift')
    before=load(PREP/'preservation-before.json')
    for key,digest in before['old_files'].items():
        if sha(R/key)!=digest: raise ValueError('Old evidence drift: '+key)
    for path,digest in load(PREP/'sdk-sources.json')['sha256'].items():
        if sha(path)!=digest: raise ValueError('SDK drift')
    return current

def validate_release(case,folder,authority,ledger):
    if sys.flags.optimize: raise ValueError('Optimized Python forbidden')
    if case not in ORDER: raise ValueError('Only seven original cases permitted')
    folder=no_reparse(folder)
    if folder!=R/'actual'/case or folder.exists(): raise ValueError('Exclusive new case path required')
    if authority.get('schema')!=1 or authority.get('issuer')!='root' or authority.get('case')!=case:
        raise ValueError('Root single-case authority required')
    if authority.get('runner_sha256')!=sha(__file__) or authority.get('source21_sha256')!=sha(R/'source21-before.json'):
        raise ValueError('Release package mismatch')
    if authority.get('model')!=MODEL or authority.get('digest')!=DIGEST or authority.get('folder')!=str(folder):
        raise ValueError('Release model/path mismatch')
    index=ORDER.index(case)
    if ledger.get('consumed')!=list(ORDER[:index+1]) or ledger.get('released_case')!=case:
        raise ValueError('Root ledger must preconsume exact ordered case; total positive cap six')
    if authority.get('ledger_sha256')!=hashlib.sha256(json.dumps(ledger,sort_keys=True).encode()).hexdigest():
        raise ValueError('Release ledger mismatch')
    prior=authority.get('prior_reviews',[])
    if [x.get('case') for x in prior]!=list(ORDER[:index]): raise ValueError('Prior independent reviews required')
    for item in prior:
        if item.get('reviewer')!='root-independent' or any(item.get(k)!='PASS' for k in ('mechanical','facts','target','file','cleanup')):
            raise ValueError('Prior case not independently accepted')
        path=no_reparse(R/'actual'/item['case']/'receipt.json')
        if sha(path)!=item.get('receipt_sha256') or load(path).get('status')!='succeeded': raise ValueError('Prior receipt mismatch')
    return folder

def metadata_valid(health,version,tags,manifest):
    if health.get('ok') is not True or health.get('model')!=MODEL or health.get('agent')!='native_react': raise ValueError('Isolated health/model mismatch')
    if version.get('version')!='0.32.15': raise ValueError('Daemon version drift')
    matches=[m for m in tags.get('models',[]) if m.get('name') in (MODEL,MODEL+':latest')]
    if len(matches)!=1 or matches[0].get('digest')!=DIGEST or hashlib.sha256(manifest).hexdigest()!=DIGEST:
        raise ValueError('Native tag/manifest mismatch')
    if matches[0].get('details',{}).get('parameter_size')!='8.2B': raise ValueError('8B proof missing')

def identity(pid):
    # Read creation time + actual executable from one process handle, no task killing.
    from ctypes import wintypes as W
    k=C.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]; k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.GetProcessTimes.argtypes=[W.HANDLE,*([C.POINTER(W.FILETIME)]*4)]
    k.QueryFullProcessImageNameW.argtypes=[W.HANDLE,W.DWORD,W.LPWSTR,C.POINTER(W.DWORD)]
    h=k.OpenProcess(0x1000,False,pid)
    if not h: raise OSError('Cannot prove process identity '+str(pid))
    try:
        times=[W.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(h,*[C.byref(x) for x in times]): raise OSError('GetProcessTimes')
        size=W.DWORD(32768); buf=C.create_unicode_buffer(size.value)
        if not k.QueryFullProcessImageNameW(h,0,buf,C.byref(size)): raise OSError('QueryFullProcessImageName')
        return {'pid':pid,'created_filetime':times[0].dwLowDateTime+(times[0].dwHighDateTime<<32),'exe':buf.value}
    finally: k.CloseHandle(h)

def process_snapshot():
    # Read-only CIM. All-process data stays transient; persist only own descendants.
    text=subprocess.check_output(['powershell.exe','-NoProfile','-NonInteractive','-Command',
        'Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,CommandLine | ConvertTo-Json -Compress'],text=True,encoding='utf-8',errors='replace',creationflags=subprocess.CREATE_NO_WINDOW,timeout=15)
    value=json.loads(text)
    return {x['ProcessId']:x for x in value}

def terminate_owned(key):
    from ctypes import wintypes as W
    if identity(key['pid'])!=key: raise ValueError('Owned cleanup identity mismatch')
    k=C.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD]; k.OpenProcess.restype=W.HANDLE
    k.CloseHandle.argtypes=[W.HANDLE]
    k.TerminateProcess.argtypes=[W.HANDLE,W.UINT]
    k.WaitForSingleObject.argtypes=[W.HANDLE,W.DWORD]
    handle=k.OpenProcess(0x00100001,False,key['pid'])
    if not handle: raise OSError('Cannot open exact owned process')
    try:
        # Recheck after opening handle; termination targets that retained handle.
        if identity(key['pid'])!=key: raise ValueError('Owned cleanup identity changed')
        if not k.TerminateProcess(handle,1): raise OSError('TerminateProcess failed')
        if k.WaitForSingleObject(handle,10000)!=0: raise TimeoutError('Owned process exit not proved')
    finally: k.CloseHandle(handle)


def protected():
    import datetime
    result=[]
    for expected in load(R/'runtime-before.json')['protected5']:
        actual=identity(expected['pid'])
        dt=datetime.datetime.fromisoformat(expected['created_utc'].replace('Z','+00:00'))
        expected_ticks=int((dt-datetime.datetime(1601,1,1,tzinfo=datetime.timezone.utc)).total_seconds()*10000000)
        if actual['exe'].lower()!=expected['exe'].lower() or abs(actual['created_filetime']-expected_ticks)>20:
            raise ValueError('Protected identity drift')
        result.append(actual)
    return result

def environment(folder):
    env=dict(os.environ,NO_PROXY='localhost,127.0.0.1,::1',PYTHONIOENCODING='utf-8',PYTHONDONTWRITEBYTECODE='1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1')
    for key in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME'):
        directory=folder/'owned-env'/key; directory.mkdir(parents=True)
        env[key]=str(directory)
    if os.environ.get('OLLAMA_HOST','http://localhost:11434') not in ('http://localhost:11434','http://127.0.0.1:11434'):
        raise ValueError('Nonlocal model host forbidden')
    for key in ('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy'):
        env.pop(key,None)
    env['PYTHONPATH']=str(ROOT)
    return env

def external_validate(case,result,artifacts,windows=None,baseline=None):
    if result.get('status')!='succeeded' or not artifacts or not all(x['verified'] for x in artifacts): raise ValueError('Product or external file failure')
    expected='rewrite.md' if case.startswith('e03') else 'summary.md'
    files=[x for x in artifacts if Path(x['path']).name==expected]
    if len(files)!=1: raise ValueError('Expected exact output missing/ambiguous')
    # Human root review still owns factual meaning/no additions. Literal checks are evidence only.
    if case.startswith('e03'):
        edits=result.get('context_results',[])
        if len(edits)!=1 or not windows or not baseline: raise ValueError('Missing external target proof')
        edit=edits[0]; original=edit['before']; actual=windows[0]
        raw=original['text'].encode('utf-16-le')
        replacement=edit['replacement_text']
        expected_text=(raw[:2*original['start_utf16']]+replacement.encode('utf-16-le')+raw[2*original['end_utf16']:]).decode('utf-16-le')
        if original['text']!=baseline[0]['text']: raise ValueError('Captured source drift')
        for a,b in zip(windows,baseline):
            for field in ('hwnd','control_hwnd','pid','process_created_filetime','title','class'):
                if a[field]!=b[field]: raise ValueError('Owned target identity drift')
        for key in ('hwnd','control_hwnd','pid','process_created_filetime','title','class'):
            if actual[key]!=baseline[0][key] or original[key]!=baseline[0][key]: raise ValueError('Target identity mismatch')
        if actual['text']!=expected_text or windows[1]['text']!=baseline[1]['text']: raise ValueError('Window outside replacement changed')
        if files[0]['text'].replace('\r\n','\n')!=replacement.replace('\r\n','\n'): raise ValueError('Companion exact replacement mismatch')
    return {'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW','file_sha256':files[0]['sha256']}

def wait_cli(cli,folder):
    try: return cli.wait(timeout=CLI_TIMEOUT)
    except subprocess.TimeoutExpired:
        save(folder/'timeout.json',{'timeout_seconds':CLI_TIMEOUT,'work_cli_count':1,'retry':False,'logs_preserved':True,'sdk_inference_count':None})
        raise


def execute(case,folder,authority,ledger):
    folder=validate_release(case,folder,authority,ledger)
    if os.environ.get('OLLAMA_HOST','http://localhost:11434') not in ('http://localhost:11434','http://127.0.0.1:11434'): raise ValueError('Nonlocal model host forbidden')
    before_source=source_check(); before_process=protected()
    folder.mkdir(parents=True,exist_ok=False)
    save(folder/'authority.json',authority); save(folder/'ledger.json',ledger)
    save(folder/'boundary-before.json',{'source21':before_source,'protected5':before_process})
    env=environment(folder)
    sys.path.insert(0,str(ROOT))
    from src.brain.tests import work_context_acceptance as h
    children=[]; logs=[]; result={}; cleanup=[]; owned={}; port=None
    def refresh_owned():
        snapshot=process_snapshot()
        for item in children:
            proc=item['process']; root_key=item['identity']
            if proc.poll() is not None: continue
            if identity(proc.pid)!=root_key: raise ValueError('Launcher identity drift')
            pending=[proc.pid]
            while pending:
                pid=pending.pop()
                row=snapshot.get(pid)
                if row is None: continue
                try: key=identity(pid)
                except OSError:
                    if pid not in process_snapshot(): continue
                    raise
                if pid in {x['pid'] for x in before_process}: raise ValueError('Protected process in owned tree')
                owned[pid]={'identity':key,'ppid':row['ParentProcessId'],'argv':row['CommandLine'],'label':item['label']}
                pending.extend(x['ProcessId'] for x in snapshot.values() if x['ParentProcessId']==pid)
        save(folder/'owned-tree.json',list(owned.values()))
    def launch(argv,label):
        out=open(folder/(label+'.stdout'),'w',encoding='utf-8'); err=open(folder/(label+'.stderr'),'w',encoding='utf-8'); logs.extend([out,err])
        proc=h.launch(argv,env,out,err)
        record={'process':proc,'identity':identity(proc.pid),'label':label}
        children.append(record)
        owned[proc.pid]={'identity':record['identity'],'ppid':os.getpid(),'argv':argv,'label':label}
        refresh_owned()
        save(folder/'owned-processes.json',[{k:v for k,v in x.items() if k!='process'} for x in children])
        return proc
    def observe(name):
        proc=launch(['-B','-m',MODULE,'--observe-policy',str(folder/'fixture.json'),'--observe-result',str(folder/name)],name)
        if proc.wait(timeout=15): raise ValueError('External observer failed')
        return load(folder/name)
    def command(index=0,select=True):
        (folder/'command-done.json').unlink(missing_ok=True)
        save(folder/'command.json',{'index':index,'select':select})
        h.wait_for(lambda:(folder/'command-done.json').exists(),10)
    try:
        if case.startswith('e03'):
            fixture=launch(['-B','-m',MODULE,'--fixture',str(folder)],'fixture')
            h.wait_for(lambda:(folder/'fixture.json').exists(),20)
            fixture_data=load(folder/'fixture.json')
            refresh_owned()
            actual_fixture=owned.get(fixture_data['pid'])
            if not actual_fixture or actual_fixture['label']!='fixture' or any(t['pid']!=fixture_data['pid'] or t['process_created_filetime']!=actual_fixture['identity']['created_filetime'] for t in fixture_data['targets']): raise ValueError('Fixture ownership mismatch')
            baseline=observe('external-before.json')
            if baseline[0]['text']!=h.CASES['e03']['text'] or len(baseline)!=2: raise ValueError('Original fixture mismatch')
        if case=='e03-negative':
            from src.brain.work_context import WorkContextProvider
            provider=WorkContextProvider(load(folder/'policy.json')); sends=[]; failures=[]
            for scenario in ('focus','selection'):
                command(); capture=provider.capture_work_context()
                if not capture['available']: raise ValueError('Negative capture unavailable')
                command(1 if scenario=='focus' else 0,scenario=='focus')
                try:
                    provider.replace_selection(capture,'SHOULD NEVER WRITE',before_send=lambda:sends.append(scenario))
                    failures.append({'scenario':scenario,'rejected':False})
                except ValueError as exc: failures.append({'scenario':scenario,'rejected':True,'error':str(exc)})
                finally: provider.release(capture)
            after=observe('external-after.json')
            unchanged=[o['text'] for o in baseline]==[o['text'] for o in after]
            passed=not sends and unchanged and len(failures)==2 and all(x['rejected'] for x in failures)
            result={'status':'succeeded' if passed else 'failed','case':case,'cases':failures,'sends':sends,'all_window_text_unchanged':unchanged,'work_cli_count':0,'sdk_inference_end_count':0}
            save(folder/'negative-receipt.json',result); save(folder/'receipt.json',result)
            return result
        sock=socket.socket(); sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]; sock.close()
        server_args=['-B','-m','src.brain.agent_server','--port',str(port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--isolated']
        if case.startswith('e03'): server_args+=['--work-target-policy',str(folder/'policy.json')]
        server=launch(server_args,'server')
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*args,**kwargs): raise ValueError('Metadata redirect forbidden')
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}),NoRedirect())
        def get(url):
            with opener.open(url,timeout=2) as response: return json.load(response)
        def healthy():
            if server.poll() is not None: raise ValueError('Owned server exited')
            try: return get(f'http://127.0.0.1:{port}/health')
            except OSError: return None
        health=h.wait_for(healthy,30)
        refresh_owned()
        save(folder/'config-source-proof.json',load(PREP/'sdk-sources.json'))
        version=get('http://127.0.0.1:11434/api/version'); tags=get('http://127.0.0.1:11434/api/tags')
        manifest_path=Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama/models')/'manifests/registry.ollama.ai/library'/MODEL/'latest'
        manifest=manifest_path.read_bytes()
        save(folder/'metadata-get-only.json',{'health':health,'version':version,'tags':tags,'manifest_path':str(manifest_path),'manifest_sha256':hashlib.sha256(manifest).hexdigest(),'manifest':json.loads(manifest)})
        metadata_valid(health,version,tags,manifest)
        source_check(); protected()
        query=h.CASES['e01']['request']+'\n'+'\n'.join(h.CASES['e01']['facts']); options=[]
        if case.startswith('e03'):
            command(); query=E03_QUERY; options=['--current-window','--replace-selection']
        cli_args=['-B','-m','src.brain.cli','--work',*options,'--request-id',case,'--session-id',case,'--server-url',f'http://127.0.0.1:{port}','--json',query]
        save(folder/'argv.json',{'server':server_args,'cli':cli_args,'max_tokens_override':None,'max_turns_override':None,'work_cli_cap':1,'cli_timeout':CLI_TIMEOUT})
        cli=launch(cli_args,'cli')
        time.sleep(.1)
        refresh_owned()
        code=wait_cli(cli,folder)
        for f in logs: f.flush()
        result=load(folder/'cli.stdout')
        inferences=[x for x in result.get('trace',[]) if x.get('type')=='inference_end']
        if not inferences or len(inferences)>10 or any(x.get('data',{}).get('model')!=MODEL for x in inferences): raise ValueError('Missing/mismatched SDK inference proof')
        save(folder/'receipt.json',dict(result,cli_exit=code,case=case,work_cli_count=1,sdk_inference_end_count=sum(x.get('type')=='inference_end' for x in result.get('trace',[])),sdk_inference_start_count=None,native_post_count=None,incomplete_inference_count=None,model_proof='metadata-get-only.json'))
        if result.get('request_id')!=case or result.get('session_id')!=case: raise ValueError('Result identity mismatch')
        for a in result.get('artifacts',[]):
            path=no_reparse(a['path'])
            if path.parent!=folder/'outputs'/result['task_id']: raise ValueError('External artifact escaped exact task root')
        artifacts=h.external_readback(result,folder)
        windows=observe('external-windows.json') if case.startswith('e03') else None
        save(folder/'mechanical-review.json',external_validate(case,result,artifacts,windows,baseline if case.startswith('e03') else None))
        if code: raise ValueError('CLI nonzero exit')
        return result
    except Exception as exc:
        save(folder/'harness-error.json',{'error':str(exc),'type':type(exc).__name__,'result':result,'retry':False})
        raise
    finally:
        (folder/'stop').touch()
        try: refresh_owned()
        except Exception as exc: save(folder/'cleanup-refresh-error.json',{'error':str(exc)})
        fixture_launchers=[x['process'] for x in children if x['label']=='fixture']
        for p in fixture_launchers:
            try: p.wait(timeout=3)
            except subprocess.TimeoutExpired: pass
        # Descendants first. Every terminate checks exact PID+creation+exe again.
        roots={x['process'].pid for x in children}
        sequence=sorted(owned.values(),key=lambda x:x['identity']['pid'] in roots)
        for item in sequence:
            key=item['identity']; pid=key['pid']
            try:
                if pid not in process_snapshot():
                    cleanup.append({'identity':key,'absent':True}); continue
                terminate_owned(key)
                cleanup.append({'identity':key,'terminated':True,'absent':pid not in process_snapshot()})
            except Exception as exc: cleanup.append({'identity':key,'cleanup_error':str(exc),'absent':False})
        for item in children:
            try: item['process'].wait(timeout=2)
            except subprocess.TimeoutExpired: pass
        if port:
            probe=socket.socket(); probe.settimeout(1)
            try: save(folder/'port-cleanup.json',{'port':port,'closed':probe.connect_ex(('127.0.0.1',port))!=0})
            finally: probe.close()
        for f in logs: f.close()
        save(folder/'cleanup.json',cleanup)
        try:
            save(folder/'boundary-after.json',{'source21':source_check(),'protected5':protected(),'matches_before':protected()==before_process})
        except Exception as exc: save(folder/'boundary-error.json',{'error':str(exc)})

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case',required=True,choices=ORDER)
    parser.add_argument('--folder',required=True,type=Path)
    parser.add_argument('--authority',required=True,type=Path)
    parser.add_argument('--ledger',required=True,type=Path)
    args=parser.parse_args()
    authority=load(no_reparse(args.authority)); ledger=load(no_reparse(args.ledger))
    result=execute(args.case,args.folder,authority,ledger)
    print(json.dumps({'case':args.case,'status':result.get('status'),'facts':'PENDING_ROOT_REVIEW'}))
    return 0 if result.get('status')=='succeeded' else 2
if __name__=='__main__': raise SystemExit(main())
