"""Start/status/stop only the new voice listener; no legacy process termination."""
from pathlib import Path
import argparse,json,os,socket,subprocess,sys,time,urllib.request,uuid,shutil
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock
DATA=ROOT/'data/voice-next'
FLAGS=getattr(subprocess,'CREATE_NO_WINDOW',0)|getattr(subprocess,'DETACHED_PROCESS',0)

def locked():
    lock=DispatchLock(DATA/'service.lock')
    acquired=lock.acquire()
    if acquired:lock.release()
    return not acquired

def read_status():
    try:result=json.loads((DATA/'status.json').read_text(encoding='utf-8'))
    except (ValueError,OSError):return {}
    result['fresh']=time.time()-result.get('updated_epoch',0)<6
    result['instance_lock_held']=locked()
    return result

def legacy_listeners():
    command = "Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^python(w)?\\.exe$' -and $_.CommandLine -match 'voice-listen-daemon\\.py|kws_listener\\.py' } | Select-Object ProcessId,CreationDate | ConvertTo-Json -Compress"
    completed=subprocess.run([shutil.which('pwsh.exe') or 'pwsh.exe','-NoProfile','-NonInteractive','-Command',command],capture_output=True,text=True,encoding='utf-8',timeout=15,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    if completed.returncode:raise RuntimeError('Cannot verify legacy listener process state')
    return json.loads(completed.stdout) if completed.stdout.strip() else []

def ensure_agent():
    opener=urllib.request.build_opener(urllib.request.ProxyHandler({}))
    def health():
        try:
            with opener.open('http://127.0.0.1:8756/health',timeout=2) as response:return bool(json.load(response).get('ok'))
        except Exception:return False
    if health():return {'healthy':True,'started':False}
    try:
        with socket.create_connection(('127.0.0.1',8756),timeout=1):return {'healthy':False,'started':False,'error':'Port occupied by unhealthy service'}
    except OSError:pass
    with (DATA/'agent.stdout.log').open('ab',buffering=0) as out,(DATA/'agent.stderr.log').open('ab',buffering=0) as err:
        proc=subprocess.Popen([str(ROOT/'tools/venv-openjarvis/Scripts/python.exe'),'-X','utf8',str(ROOT/'src/brain/agent_server.py')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=FLAGS)
    for _ in range(60):
        if health():return {'healthy':True,'started':True,'launcher_pid':proc.pid}
        if proc.poll() is not None:return {'healthy':False,'started':True,'launcher_pid':proc.pid,'exit_code':proc.returncode}
        time.sleep(.2)
    return {'healthy':False,'started':True,'launcher_pid':proc.pid,'error':'Health timeout; process left intact'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--status',action='store_true');parser.add_argument('--stop',action='store_true')
    parser.add_argument('--wait',type=float,default=90)
    args=parser.parse_args();DATA.mkdir(parents=True,exist_ok=True)
    if args.status:
        print(json.dumps(read_status(),ensure_ascii=True));return 0
    if args.stop:
        status=read_status()
        if not status.get('instance_lock_held') or not status.get('run_id'):
            print(json.dumps({'stopped':False,'error':'No active owned listener'}));return 1
        (DATA/'stop.request.json').write_text(json.dumps({'run_id':status['run_id']}),encoding='utf-8')
        print(json.dumps({'requested_stop':True,'run_id':status['run_id']}));return 0
    if locked():
        expected=read_status().get('run_id')
    else:
        old=legacy_listeners()
        if old:
            print(json.dumps({'ready':False,'error':'Legacy listener still running; no process was stopped','legacy':old},ensure_ascii=True));return 1
        agent=ensure_agent();expected=uuid.uuid4().hex
        environment=dict(os.environ);environment['ULTIMA_VOICE_NEXT_RUN_ID']=expected
        environment['PYTHONUNBUFFERED']='1';environment['PYTHONIOENCODING']='utf-8'
        with (DATA/'service.stdout.log').open('ab',buffering=0) as out,(DATA/'service.stderr.log').open('ab',buffering=0) as err:
            proc=subprocess.Popen([str(ROOT/'tools/venv-voice-next/Scripts/python.exe'),'-X','utf8',str(Path(__file__).with_name('live.py'))],cwd=ROOT,env=environment,stdin=subprocess.DEVNULL,stdout=out,stderr=err,creationflags=FLAGS)
        (DATA/'launch.json').write_text(json.dumps({'run_id':expected,'launcher_pid':proc.pid,'created_epoch':time.time(),'agent':agent},indent=2),encoding='utf-8')
    deadline=time.monotonic()+args.wait
    while time.monotonic()<deadline:
        status=read_status()
        if status.get('run_id')==expected:
            if status.get('state') in ('error','stopped'):
                print(json.dumps(status,ensure_ascii=True));return 1
            if status.get('ready') and status.get('fresh') and status.get('instance_lock_held') and status.get('callbacks',0)>0 and status.get('live_model_packets',0)>0:
                print(json.dumps(status,ensure_ascii=True));return 0
        time.sleep(.2)
    print(json.dumps({'ready':False,'error':'Listener startup timeout','status':read_status()},ensure_ascii=True));return 1

if __name__=='__main__':raise SystemExit(main())
