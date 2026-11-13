"""Owner-approved, bounded recovery of one lost T1 dispatch. No HTTP actions."""
from datetime import datetime, timezone
from contextlib import contextmanager
import getpass
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time
import uuid
from xml.sax.saxutils import escape

HERE=Path(__file__).resolve().parent
PROJECT=HERE.parents[1]
SHARED=PROJECT.parent/'_shared/queue'
ORDER='wo-s1-composite-window'
EXIT_EVIDENCE=('execution-exit.json','runtime-limit.json','dispatch-error.json')
PYTHON=PROJECT/'tools/python31313/python.exe'
sys.path.insert(0,str(PROJECT))
from tasks.queue_engine.dispatcher import DispatchLock, process_identity

def now():
    return datetime.now(timezone.utc).isoformat()

def read(path,default=None):
    try:
        value=json.loads(path.read_text(encoding='utf-8-sig'))
        return value if isinstance(value,dict) else default
    except FileNotFoundError:
        return default

def save(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
    temp.replace(path)

def decide(signal,state):
    def result(code,label):
        if code!='confirming' and code!='recover':
            state['streak']=0
        return dict(code=code,label=label)
    if signal['paused']:
        return result('paused','检测到暂停标记，不做恢复')
    if signal.get('in_scope') is False:
        return result('gate','运行已切换到本策略之外，不做恢复')
    if any(signal[k] for k in ['worker','adapter','runner']):
        return result('running','执行或监督身份有效，不重复派发')
    if signal['done'] or signal['final'] or signal.get('exit_evidence'):
        return result('gate','已有退出或交付证据，等待核对／独立审查')
    if not signal['identity_known']:
        return result('unknown','进程创建身份不足，停止自动动作')
    if signal['attempt_uncertain']:
        return result('uncertain','上次恢复启动结果未明，停止重复启动')
    if signal['attempts']>=2:
        return result('limit','已达2次恢复上限，等待人工检查')
    if signal['registered']!='executing':
        return result('gate','不属于缺回执的执行失联，不自动重跑')
    if state.get('run')!=signal['run']:
        state.update(run=signal['run'],streak=0)
    state['streak']=state.get('streak',0)+1
    if state['streak']<3:
        return result('confirming','连续失联确认 '+str(state['streak'])+'/3')
    return result('recover','三次确认失联，准备串行恢复')

def confirmation_due(previous,current_epoch):
    return previous is None or current_epoch-datetime.fromisoformat(previous.replace('Z','+00:00')).timestamp()>=30

@contextmanager
def supervisor_guard(folder):
    lock=DispatchLock(folder/'supervisor.lock')
    if not lock.acquire():
        yield False
        return
    try:
        yield True
    finally:
        lock.release()

def dispatch_module():
    spec=importlib.util.spec_from_file_location('recovery_dispatch',PROJECT/'scripts/dispatch-work-order.py')
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def session_live(session,pid_key='pid',identity_key='identity'):
    pid=session.get(pid_key)
    creation=session.get(identity_key)
    if type(pid) is not int or pid<=0 or not isinstance(creation,str) or not creation:
        return None
    return process_identity(pid)==creation

def schedule_runner(request, action=None, prefix='UltimaAgent-T1-Recovery-',time_limit='PT35M'):
    task=prefix+request.parent.name[-12:]
    action=action or HERE/'recovery_runner.py'
    xml=f'''<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"><RegistrationInfo><Description>Approved T1 recovery; one attempt, no triggers.</Description></RegistrationInfo><Principals><Principal id="Author"><UserId>{escape(getpass.getuser())}</UserId><LogonType>InteractiveToken</LogonType><RunLevel>LeastPrivilege</RunLevel></Principal></Principals><Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy><DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries><StopIfGoingOnBatteries>false</StopIfGoingOnBatteries><AllowHardTerminate>true</AllowHardTerminate><AllowStartOnDemand>true</AllowStartOnDemand><Enabled>true</Enabled><Hidden>true</Hidden><ExecutionTimeLimit>PT35M</ExecutionTimeLimit></Settings><Actions Context="Author"><Exec><Command>{escape(str(PYTHON.with_name('pythonw.exe')))}</Command><Arguments>-B -X utf8 &quot;{escape(str(action))}&quot; &quot;{escape(str(request))}&quot;</Arguments><WorkingDirectory>{escape(str(PROJECT))}</WorkingDirectory></Exec></Actions></Task>'''
    xml_path=request.parent/'task.xml'
    if time_limit not in {'PT35M','PT2H'}:raise ValueError('unapproved scheduler time limit')
    xml=xml.replace('<ExecutionTimeLimit>PT35M</ExecutionTimeLimit>','<ExecutionTimeLimit>'+time_limit+'</ExecutionTimeLimit>')
    xml_path.write_text(xml,encoding='utf-16')
    exe=str(Path(os.environ['SystemRoot'])/'System32/schtasks.exe')
    created=subprocess.run([exe,'/Create','/TN',task,'/XML',str(xml_path)],capture_output=True,timeout=15,creationflags=0x08000000)
    if created.returncode:
        raise RuntimeError('按需恢复任务启动失败，保留预约，禁止自动重复启动')
    try:
        started=subprocess.run([exe,'/Run','/TN',task],capture_output=True,timeout=15,creationflags=0x08000000)
        if started.returncode:
            raise RuntimeError('按需恢复任务启动失败，保留预约，禁止自动重复启动')
    finally:
        deleted=subprocess.run([exe,'/Delete','/TN',task,'/F'],capture_output=True,timeout=15,creationflags=0x08000000)
        if deleted.returncode and sys.exc_info()[0] is None:
            raise RuntimeError('一次性恢复任务自清扫失败')
    return task

class Supervisor:
    def __init__(self):
        self.folder=HERE/'recovery'
        self.state_path=self.folder/'state.json'
        self.last_monotonic=0

    def tick(self):
        policy=read(HERE/'recovery-policy.json',{})
        if policy.get('enabled') is not True:
            return
        if policy.get('order')!=ORDER or policy.get('max_attempts')!=2 or policy.get('interval_seconds')!=30:
            raise ValueError('恢复策略与批准范围不一致')
        self.folder.mkdir(exist_ok=True)
        with supervisor_guard(self.folder) as owned:
            if not owned:
                return
            state=read(self.state_path,{'attempts':[],'events':[]})
            if time.monotonic()-self.last_monotonic<30 or not confirmation_due(state.get('checked_at'),time.time()):
                return
            self.last_monotonic=time.monotonic()
            m=dispatch_module()
            text,row,_=m.registered(ORDER)
            match=re.search(r'\b('+ORDER+r'-\d{8}T\d+Z)\b',row.group(2))
            if not match:
                raise ValueError('本轮运行引用缺失')
            run=PROJECT/'tasks/queue/runs'/match.group(1)
            session=read(run/'session.json',{})
            worker=session_live(session)
            adapter=session_live(session,'adapter_pid','adapter_identity')
            attempts=state.get('attempts',[])
            runner_live=False
            uncertain=False
            in_scope=run.name==policy.get('initial_run')
            for attempt in attempts:
                owned=read(self.folder/attempt['id']/'runner.json',{})
                if owned.get('pid') and owned.get('identity') and session.get('parent_pid')==owned['pid'] and session.get('parent_identity')==owned['identity']:
                    in_scope=True
            if attempts:
                last=attempts[-1]
                runner=read(self.folder/last['id']/'runner.json',{})
                runner_live=session_live(runner) is True
                uncertain=last['old_run']==run.name and not (self.folder/last['id']/'result.json').is_file()
            signal=dict(run=run.name,registered=row.group(1),worker=worker,adapter=adapter,runner=runner_live,
                        in_scope=in_scope,
                        identity_known=worker is not None and adapter is not None,
                        paused=(PROJECT/'tasks/.pause-dispatch').exists() or (SHARED/'.pause-dispatch').exists(),
                        exit_evidence=any((run/name).exists() for name in EXIT_EVIDENCE),
                        done=(run/'done.json').exists(),final=(run/'final.json').exists(),attempts=len(attempts),attempt_uncertain=uncertain)
            decision=decide(signal,state)
            state.update(checked_at=now(),**decision)
            if decision['code']=='recover':
                self.recover(m,row,run,session,policy,state)
            save(self.state_path,state)

    def recover(self,m,row,run,session,policy,state):
        prompt=PROJECT/'tasks/queue/dispatch-wo-s1-composite-window-t1-20261024-prompt.txt'
        if hashlib.sha256(prompt.read_bytes()).hexdigest()!=policy.get('prompt_sha256'):
            state.update(code='gate',label='派发载荷已变化，停止自动恢复')
            return
        guard=subprocess.run([str(PYTHON),'-B','-X','utf8',str(PROJECT/'src/window/tests/verify_guardrails.py')],capture_output=True,timeout=30,creationflags=0x08000000)
        if guard.returncode:
            state.update(code='gate',label='冻结基线／版本门未通过，停止自动恢复')
            return
        with DispatchLock(SHARED/'.engineering-dispatch.lock'):
            text,current,_=m.registered(ORDER)
            if current.group(0)!=row.group(0):
                state.update(code='wait',label='登记已变化，下一轮重新核对',streak=0)
                return
            if any(session_live(session,a,b) is not False for a,b in [('pid','identity'),('adapter_pid','adapter_identity')]):
                state.update(code='wait',label='进程身份复核未确认消失，不恢复',streak=0)
                return
            if any((run/name).exists() for name in ['done.json','final.json',*EXIT_EVIDENCE]) or (PROJECT/'tasks/.pause-dispatch').exists() or (SHARED/'.pause-dispatch').exists():
                state.update(code='gate',label='已出现回执或暂停标记，停止恢复',streak=0)
                return
            roles=m.native.codex_processes()
            active=[r for r in roles if r['role']=='exec']
            if any(r['role']=='unknown' for r in roles) or len(active)>=3 or any(not r['project'] or Path(r['project']).resolve()==PROJECT for r in active):
                state.update(code='wait',label='执行容量或项目身份门未通过，等待',streak=0)
                return
            m.check_version_gates({'card_path':str(PROJECT/'tasks/cards/s1-window-dsl-schema/task.md')},PROJECT/'tasks')
            attempt_id=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:12]
            directory=self.folder/attempt_id
            directory.mkdir(exist_ok=False)
            observation=dict(at=now(),worker=session['pid'],worker_identity=session['identity'],
                             adapter=session['adapter_pid'],adapter_identity=session['adapter_identity'],
                             result='identities disappeared; exit code unknown; no completion receipt',
                             evidence={name:hashlib.sha256((run/name).read_bytes()).hexdigest() for name in ['session.json','out.jsonl','err.log'] if (run/name).is_file()})
            (run/('recovery-observation-'+attempt_id+'.json')).write_text(json.dumps(observation,indent=2),encoding='utf-8')
            request=dict(order=ORDER,phase='T1-only',old_run=run.name,prompt=str(prompt),prompt_sha256=policy['prompt_sha256'],attempt_id=attempt_id)
            save(directory/'request.json',request)
            (directory/'guardrails.json').write_bytes(guard.stdout)
            state.setdefault('attempts',[]).append(dict(id=attempt_id,old_run=run.name,at=now(),status='reserved'))
            state.update(code='reserved',label='恢复额度已预约，准备独立宿主串行续行',streak=0)
            save(self.state_path,state)  # durable before any launch
            m.state(ORDER,'blocked','自动监督三次确认失联；退出码未知、旧证据保留；恢复预约 '+attempt_id+'；'+run.name,run,
                    expected='executing',expected_run=run.name)
        task=schedule_runner(directory/'request.json')
        state['attempts'][-1].update(status='launch_requested',task=task)
        state.update(code='recovering',label='独立恢复任务已请求启动，等待真实进程与回执')
        state.setdefault('events',[]).append(dict(at=now(),label='第'+str(len(state['attempts']))+'次恢复：已保存旧证据并请求同单续行'))

    def loop(self):
        while True:
            try:
                self.tick()
            except Exception as exc:
                # Persist safe metadata only, never raw exception text or prompts.
                try:
                    self.record_error(exc)
                except Exception:
                    pass
            time.sleep(30)

    def record_error(self,exc):
        with supervisor_guard(self.folder) as owned:
            if not owned:
                return
            state=read(self.state_path,{'attempts':[],'events':[]})
            state.update(checked_at=now(),code='error',label='检查或恢复遇到 '+type(exc).__name__+'，保持安全等待')
            save(self.state_path,state)

def public_status():
    policy=read(HERE/'recovery-policy.json',{})
    state=read(HERE/'recovery/state.json',{})
    return dict(enabled=policy.get('enabled') is True,order=ORDER,interval_seconds=30,
                checked_at=state.get('checked_at'),code=state.get('code','disabled'),label=state.get('label','尚未启用自动恢复'),
                confirmations=state.get('streak',0),attempts=len(state.get('attempts',[])),max_attempts=2,
                events=[{'at':e.get('at'),'label':e.get('label')} for e in state.get('events',[])[-5:]])

def start():
    supervisor=Supervisor()
    threading.Thread(target=supervisor.loop,name='bounded-agent-recovery',daemon=True).start()
