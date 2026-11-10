"""Issue this user's exact single-case release and invoke the reviewed entry once."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,sys,uuid
E=Path(__file__).resolve().parents[1];repo=E.parents[4];PY=repo/'tools/venv-openjarvis/Scripts/python.exe'
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as stream:json.dump(v,stream,ensure_ascii=False,indent=2)
def replace(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
assert not (E/'release').exists() and not (E/'runs').exists() and not (E/'execution/root-invocation.json').exists()
scope=load(E/'execution/scope-approval.json');preflight=load(E/'execution/preflight-v2.json')
assert scope['question_id']=='call_c6b188dbc9514611ad330bb3b8829619' and scope['root_entry_limit']==scope['actual_profile_limit']==1
assert preflight['status']=='PASS_POINT_IN_TIME_PREFLIGHT' and len(preflight['protected'])==7
entry=load(E/'entry-manifest.json');review=load(E/'review/independent-preparation-review.json');gate=load(E/'verification/code-preparation-gate.json')
assert sha(E/'entry-manifest.json')==scope['entry_manifest_sha256']==review['manifest_sha256']==gate['manifest_sha256']
assert sha(E/'review/independent-preparation-review.json')==gate['review_sha256']==scope['independent_review_sha256']
assert review['verdict']=='PASS' and gate['verdict']=='PASS_PREPARATION_ONLY' and gate['actual_authority'] is False
for name,digest in entry['files'].items():assert sha(Path(name))==digest,name
assert 'OPENJARVIS_SSRF_FAIL_OPEN' not in {k.upper() for k in os.environ}
run_id=str(uuid.uuid4());nonce=str(uuid.uuid4())
statepath=E.parent/'current-run.json';state=load(statepath)
state.update(phase='SOURCE13_E02_ZERO_INFERENCE_PROFILE_USER_ALLOCATED',active_review_agent=None,e02_execution_released=True,
    e02_zero_inference_run_id=run_id,next_work='One root entry invocation then one readonly independent result review; no retry')
state['next_action_scope']=dict(scope=scope['scope'],approved=True,approval_question_id=scope['question_id'],
    actual_case_allocation=1,actual_result_review_allocation=1,authority_issued=True,retry=0,model_calls=0,audio_actions=0)
replace(statepath,state)
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');lines=registry.read_bytes().decode().splitlines(keepends=True);matched=0
for index,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[index]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | E01固定3/3、E03三正一负PASS；E02已授权一次原资料零推理接线验证及一次独立结果复核，当前8B配置不推理、原截止与七保护身份保持，失败不重试；研究/T2未过。 |'+('\r\n' if line.endswith('\r\n') else '\n');matched+=1
assert matched==1;registry.write_bytes(''.join(lines).encode())
q=subprocess.run([str(PY),'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
for name,body in (('queue-before.stdout',q.stdout),('queue-before.stderr',q.stderr)):
    with (E/'execution'/name).open('xb') as stream:stream.write(body)
assert q.returncode==0
release_dir=E/'release';release_dir.mkdir(exist_ok=False);now=dt.datetime.now(dt.timezone.utc)
approval=dict(schema=1,kind='USER_EXPLICIT_APPROVAL',scope=scope['scope'],approved=True,source='user_reply',answer=scope['answer'],
    recorded_at=scope['recorded_at'],profile_limit=1,result_review_limit=1,actual_http_allowed=0,actual_11434_allowed=0,
    actual_inference_allowed=0,ssrf_dns_host='raw.githubusercontent.com',UI=0,audio=0)
save(release_dir/'user-approval.json',approval)
release=dict(schema=1,kind='SOURCE13_PROFILE_ROOT_RELEASE',scope=scope['scope'],run_id=run_id,entry_nonce=nonce,
    candidate=entry['candidate'],model_digest=entry['model_digest'],root_manifest_sha256=sha(E/'entry-manifest.json'),
    approval_sha256=sha(release_dir/'user-approval.json'),preparation_review_sha256=sha(E/'review/independent-preparation-review.json'),
    issued_at=now.isoformat(),expires_at=(now+dt.timedelta(seconds=120)).isoformat(),max_submissions=1,retry=0,
    actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,ssrf_dns_host='raw.githubusercontent.com',UI=0,audio=0)
save(release_dir/'release.json',release)
argv=[str(PY),'-I','-B','-X','utf8',str(E/'code/entry.py')]
save(E/'execution/root-invocation.json',dict(run_id=run_id,argv=argv,recorded_at=now.isoformat(),max_attempts=1,retry=0,
    attempt_consumed=True,release_sha256=sha(release_dir/'release.json'),scope_approval_sha256=sha(E/'execution/scope-approval.json')))
with (E/'execution/root.stdout').open('xb') as out,(E/'execution/root.stderr').open('xb') as err:
    proc=subprocess.Popen(argv,cwd=str(repo),stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
    save(E/'execution/root-launch.json',dict(run_id=run_id,launcher_pid=proc.pid,started_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        observation='Popen launcher only; reviewed entry records native root/worker identities separately'))
    print(json.dumps(dict(state='STARTED_ONE_ROOT_ENTRY',run_id=run_id,launcher_pid=proc.pid)),flush=True)
    code=proc.wait()
save(E/'execution/root-exit.json',dict(run_id=run_id,launcher_pid=proc.pid,exit_code=code,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    stdout_sha256=sha(E/'execution/root.stdout'),stderr_sha256=sha(E/'execution/root.stderr'),retry=False))
print(json.dumps(dict(state='ROOT_EXITED',run_id=run_id,exit_code=code,terminal=str(E/'runs'/run_id/'control/terminal.json'))),flush=True)
raise SystemExit(code)
