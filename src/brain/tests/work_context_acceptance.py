"""Opt-in real acceptance harness. Only owns its fixture/server subprocesses.

No canned inference, save logic or model replacement. Product requests go via CLI.
"""
from __future__ import annotations
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request

ROOT=Path(__file__).resolve().parents[3]
MODULE='src.brain.tests.work_context_acceptance'
CASES=json.loads((Path(__file__).parent/'fixtures/work_capability/acceptance-cases.json').read_text(encoding='utf-8'))


def save(path,value):
    Path(path).write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')


def wait_for(predicate,seconds=30):
    deadline=time.monotonic()+seconds
    while time.monotonic()<deadline:
        value=predicate()
        if value: return value
        time.sleep(.1)
    raise TimeoutError('Acceptance prerequisite timed out')


def fixture(folder):
    from src.brain.work_context import Win32Edit
    native=Win32Edit(); u=native.u
    u.CreateWindowExW.restype=W.HWND
    u.CreateWindowExW.argtypes=[W.DWORD,W.LPCWSTR,W.LPCWSTR,W.DWORD,C.c_int,C.c_int,C.c_int,C.c_int,W.HWND,W.HMENU,W.HINSTANCE,C.c_void_p]
    for name in ('SetForegroundWindow','SetFocus','ShowWindow','DestroyWindow'):
        getattr(u,name).argtypes=[W.HWND]+([C.c_int] if name=='ShowWindow' else [])
    u.SetFocus.restype=W.HWND
    u.PeekMessageW.argtypes=[C.POINTER(W.MSG),W.HWND,W.UINT,W.UINT,W.UINT]
    u.TranslateMessage.argtypes=[C.POINTER(W.MSG)]
    u.DispatchMessageW.argtypes=[C.POINTER(W.MSG)]; u.DispatchMessageW.restype=C.c_ssize_t
    u.AttachThreadInput.argtypes=[W.DWORD,W.DWORD,W.BOOL]; u.AttachThreadInput.restype=W.BOOL
    native.k.GetCurrentThreadId.restype=W.DWORD; native.k.GetCurrentThreadId.argtypes=[]
    targets=[]
    for index,title in enumerate((CASES['e03']['window_title'],CASES['e03']['window_title']+' Other')):
        h=u.CreateWindowExW(0,'STATIC',title,0x10CF0000,150+index*80,150+index*80,700,250,None,None,None,None)
        text=CASES['e03']['text'] if index==0 else 'UNRELATED OWNED FIXTURE — DO NOT CHANGE'
        ch=u.CreateWindowExW(0,'EDIT',text,0x508100C4,10,10,660,180,h,None,None,None)
        if not h or not ch: raise OSError('Fixture window creation failed')
        targets.append(dict(hwnd=int(h),control_hwnd=int(ch),pid=os.getpid(),process_created_filetime=native.created(os.getpid()),title=title,**{'class':'Edit'},allowed_operations=['capture','replace_selection'],max_age_seconds=300))
    def activate(index=0,select=True):
        t=targets[index]
        native.identity(t,foreground=False)
        own_thread=native.k.GetCurrentThreadId()
        foreground=u.GetForegroundWindow()
        other_thread=u.GetWindowThreadProcessId(foreground,None)
        attached=False
        record={'own_thread':own_thread,'foreground_thread':other_thread,'target':t['hwnd']}
        try:
            if other_thread and other_thread!=own_thread:
                attached=bool(u.AttachThreadInput(own_thread,other_thread,True))
                record['attach_return']=attached
            u.ShowWindow(t['hwnd'],5)
            record['set_foreground_return']=bool(u.SetForegroundWindow(t['hwnd']))
            u.SetFocus(t['control_hwnd'])
        finally:
            if attached: record['detach_return']=bool(u.AttachThreadInput(own_thread,other_thread,False))
            with (folder/'activation.jsonl').open('a',encoding='utf-8') as log: log.write(json.dumps(record)+'\n')
        native.send(t['control_hwnd'],0x00B1,0,-1 if select else 1)
    activate()
    save(folder/'fixture.json',{'targets':targets,'pid':os.getpid()})
    save(folder/'policy.json',{'version':1,'targets':[targets[0]]})
    msg=W.MSG()
    try:
        while not (folder/'stop').exists():
            while u.PeekMessageW(C.byref(msg),None,0,0,1):
                u.TranslateMessage(C.byref(msg)); u.DispatchMessageW(C.byref(msg))
            command=folder/'command.json'
            if command.exists():
                data=json.loads(command.read_text(encoding='utf-8')); command.unlink()
                activate(data.get('index',0),data.get('select',True))
                save(folder/'command-done.json',data)
            time.sleep(.01)
    finally:
        for t in targets: u.DestroyWindow(t['hwnd'])


def observe(policy,result_path):
    from src.brain.work_context import Win32Edit
    n=Win32Edit()
    data=json.loads(Path(policy).read_text(encoding='utf-8'))
    observations=[n.observe(t,foreground=False) for t in data['targets']]
    save(result_path,observations)


def external_readback(result,folder):
    readbacks=[]
    for index,a in enumerate(result.get('artifacts',[])):
        raw=Path(a['path']).read_bytes()
        (folder/f'external-{index}.raw').write_bytes(raw)
        readbacks.append(dict(path=a['path'],sha256=hashlib.sha256(raw).hexdigest(),verified=hashlib.sha256(raw).hexdigest()==a['sha256'],text=raw.decode('utf-8')))
    save(folder/'external-artifacts.json',readbacks)
    return readbacks


def launch(argv,env,stdout,stderr):
    return subprocess.Popen([sys.executable,*argv],cwd=ROOT,env=env,stdout=stdout,stderr=stderr,creationflags=subprocess.CREATE_NO_WINDOW)


def round_case(case,folder):
    folder.mkdir(parents=True,exist_ok=False)
    task_files=['work_context.py','work_tools.py','work_service.py','work_verifier.py','environment.py','exec/channel.py','browser/channel.py','agent_server.py','agent_client.py','cli.py','tests/test_work_context.py','tests/test_work_delivery.py','tests/work_context_acceptance.py']
    manifest={name:hashlib.sha256((ROOT/'src/brain'/name).read_bytes()).hexdigest() for name in task_files}
    commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    save(folder/'candidate.json',dict(commit=commit,source_sha256=manifest,spec_sha256=hashlib.sha256((ROOT/'docs/specs/jarvis-work-capability-contract-20261101.md').read_bytes()).hexdigest(),cases_sha256=hashlib.sha256((Path(__file__).parent/'fixtures/work_capability/acceptance-cases.json').read_bytes()).hexdigest()))
    env=dict(os.environ,NO_PROXY='localhost,127.0.0.1',PYTHONIOENCODING='utf-8')
    children=[]; logs=[]; result={}
    try:
        if case in ('e03','e03-negative'):
            out=open(folder/'fixture.stdout','w',encoding='utf-8'); err=open(folder/'fixture.stderr','w',encoding='utf-8'); logs+=[out,err]
            proc=launch(['-m',MODULE,'--fixture',str(folder)],env,out,err); children.append(proc)
            wait_for(lambda:(folder/'fixture.json').exists())
        if case=='e03-negative':
            from src.brain.work_context import WorkContextProvider
            provider=WorkContextProvider(json.loads((folder/'policy.json').read_text(encoding='utf-8')))
            def command(index,select=True):
                (folder/'command-done.json').unlink(missing_ok=True)
                save(folder/'command.json',dict(index=index,select=select))
                wait_for(lambda:(folder/'command-done.json').exists())
            def read(name):
                done=subprocess.run([sys.executable,'-m',MODULE,'--observe-policy',str(folder/'fixture.json'),'--observe-result',str(folder/name)],env=env,cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
                if done.returncode: raise RuntimeError(done.stderr.decode('utf-8','replace'))
                return json.loads((folder/name).read_text(encoding='utf-8'))
            command(0)
            before=read('external-before.json')
            failures=[]; sends=[]
            for scenario in ('focus','selection'):
                command(0)
                capture=provider.capture_work_context()
                if not capture['available']: raise ValueError('Negative fixture capture unavailable')
                command(1 if scenario=='focus' else 0,scenario=='focus')
                try:
                    provider.replace_selection(capture,'SHOULD NEVER WRITE',before_send=lambda:sends.append(scenario))
                    failures.append(dict(scenario=scenario,rejected=False))
                except ValueError as exc: failures.append(dict(scenario=scenario,rejected=True,error=str(exc)))
                finally: provider.release(capture)
            after=read('external-after.json')
            unchanged=[o['text'] for o in before]==[o['text'] for o in after]
            passed=not sends and unchanged and all(x['rejected'] for x in failures)
            save(folder/'negative-receipt.json',dict(proof='real owned native windows',cases=failures,sends=sends,all_window_text_unchanged=unchanged,passed=passed))
            return dict(case=case,status='succeeded' if passed else 'failed',external_verified=unchanged,folder=str(folder))
        sock=socket.socket(); sock.bind(('127.0.0.1',0)); port=sock.getsockname()[1]; sock.close()
        server_args=['-m','src.brain.agent_server','--port',str(port),'--runtime-root',str(folder/'runtime'),'--work-output-root',str(folder/'outputs'),'--isolated']
        if case=='e03': server_args+=['--work-target-policy',str(folder/'policy.json')]
        if case=='e02': server_args+=['--work-research']
        out=open(folder/'server.stdout','w',encoding='utf-8'); err=open(folder/'server.stderr','w',encoding='utf-8'); logs+=[out,err]
        server=launch(server_args,env,out,err); children.append(server)
        opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
        def healthy():
            if server.poll() is not None: raise RuntimeError('Candidate server exited')
            try:
                with opener.open(f'http://127.0.0.1:{port}/health',timeout=1) as r: return json.load(r).get('ok')
            except OSError: return False
        wait_for(healthy)
        if case=='e03':
            # Fixture itself sets foreground/focus; launching hidden CLI does not steal it.
            save(folder/'command.json',{'index':0,'select':True})
            wait_for(lambda:(folder/'command-done.json').exists())
        query=CASES['e01']['request']+'\n'+'\n'.join(CASES['e01']['facts'])
        options=[]
        if case=='e03':
            options=['--current-window','--replace-selection']
            query='将当前选区整理为三条要点，替换该选区，并保存相同改写到rewrite.md。保留所有原事实，不新增事实。'
        if case=='e02':
            options=['--research']
            pinned='https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/'
            sdk_source='https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py'
            query='查询'+CASES['e02']['topic']+'。实际搜索Jarvis.ceo akshayaggarwal99 jarvis-ai-assistant，再GET读取以下三个官方固定版本架构来源：'+', '.join(pinned+x for x in ('README.md','src/core/agent-manager.ts','src/agents/unified-agent.ts'))+'。另GET现有OpenJarvis底座官方源码：'+sdk_source+'。仅依据这四个实际抓取正文整理中文文档，每条架构事实旁引用匹配的完整URL，保存为research.md。搜索片段只供发现，不收录同名人物或无关产品。重点区分两个项目的架构，不把两者当同一系统；来源无法证实的接入方式请明确留为建议，不伪称已实现。'
        cli_args=['-m','src.brain.cli','--work',*options,'--request-id',folder.name,'--session-id',folder.name,'--server-url',f'http://127.0.0.1:{port}','--json',query]
        save(folder/'argv.json',dict(server=server_args,cli=cli_args,owned_pids=[p.pid for p in children],environment_overrides={'NO_PROXY':env['NO_PROXY'],'PYTHONIOENCODING':'utf-8'}))
        out=open(folder/'cli.stdout','w',encoding='utf-8'); err=open(folder/'cli.stderr','w',encoding='utf-8'); logs+=[out,err]
        cli=launch(cli_args,env,out,err); children.append(cli)
        code=cli.wait(timeout=900); out.flush(); err.flush()
        result=json.loads((folder/'cli.stdout').read_text(encoding='utf-8'))
        save(folder/'receipt.json',dict(result,cli_exit=code,case=case,model='qwen3-8b-uncensored',agent='native_react',proof='live'))
        with (folder/'trace.jsonl').open('w',encoding='utf-8') as f:
            for record in result.get('trace',[])+result.get('tool_results',[]): f.write(json.dumps(record,ensure_ascii=False)+'\n')
        artifacts=external_readback(result,folder)
        save(folder/'sources.json',result.get('sources',[]))
        if result.get('sources'):
            from src.brain.browser.channel import BrowserChannel
            reads=[]
            for source in result['sources']:
                fetched=BrowserChannel().fetch_public(source['final_url'])
                reads.append(dict(fetched,matches_product_hash=fetched['decoded_body_sha256']==source['decoded_body_sha256']))
            save(folder/'external-sources.json',reads)
        if case=='e03':
            obs=subprocess.run([sys.executable,'-m',MODULE,'--observe-policy',str(folder/'fixture.json'),'--observe-result',str(folder/'external-windows.json')],env=env,cwd=ROOT,capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            save(folder/'observer-process.json',dict(exit_code=obs.returncode,stderr=obs.stderr.decode('utf-8','replace')))
        return dict(case=case,status=result.get('status'),cli_exit=code,external_verified=bool(artifacts) and all(x['verified'] for x in artifacts),folder=str(folder))
    except Exception as exc:
        save(folder/'harness-error.json',dict(error=str(exc),case=case,result=result))
        return dict(case=case,status='harness_error',error=str(exc),folder=str(folder))
    finally:
        save(folder/'candidate-after.json',{'source_unchanged':all(hashlib.sha256((ROOT/'src/brain'/name).read_bytes()).hexdigest()==sha for name,sha in manifest.items())})
        if case in ('e03','e03-negative'): (folder/'stop').touch()
        cleanup=[]
        for p in reversed(children):
            if p.poll() is None:
                if case in ('e03','e03-negative') and p==children[0]:
                    try: p.wait(timeout=3)
                    except subprocess.TimeoutExpired: p.terminate()
                else: p.terminate()
                p.wait(timeout=10)
            cleanup.append(dict(pid=p.pid,exit_code=p.returncode,absent=p.poll() is not None))
        for f in logs: f.close()
        save(folder/'cleanup.json',cleanup)


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--fixture',type=Path)
    parser.add_argument('--observe-policy',type=Path)
    parser.add_argument('--observe-result',type=Path)
    parser.add_argument('--run-root',type=Path)
    parser.add_argument('--case',choices=['e01','e02','e03','e03-negative'])
    parser.add_argument('--rounds',type=int,default=3)
    a=parser.parse_args()
    if a.fixture: return fixture(a.fixture)
    if a.observe_policy: return observe(a.observe_policy,a.observe_result)
    if not a.run_root or not a.case: parser.error('--run-root and --case required')
    a.run_root.mkdir(parents=True,exist_ok=True)
    results=[]
    for i in range(1,a.rounds+1):
        result=round_case(a.case,a.run_root/f'{a.case}-round-{i}')
        results.append(result)
        print(json.dumps(result,ensure_ascii=False),flush=True)
    save(a.run_root/f'{a.case}-group.json',results)
    return 0 if all(r['status']=='succeeded' and r['external_verified'] for r in results) else 2


if __name__=='__main__':
    raise SystemExit(main())
