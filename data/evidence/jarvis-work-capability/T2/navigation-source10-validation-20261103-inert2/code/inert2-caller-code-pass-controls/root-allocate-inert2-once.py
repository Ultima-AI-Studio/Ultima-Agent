"""ROOT allocation data ONLY. Executing this consumes one new submission; never launches."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import uuid

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101';W2=W/'inert-revision2'
H=Path('H:/UltimaAI/UltimaAgent');T=H/'data/evidence/jarvis-work-capability/T2';OLD=T/'navigation-source10-validation-20261102';V=T/'navigation-source10-validation-20261103-inert2'
PY=H/'tools/venv-openjarvis/Scripts/python.exe';SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(repo,*args):
    p=subprocess.run(['git','-C',str(repo),*args],capture_output=True);assert p.returncode==0,p.stderr[:1000];return p.stdout.decode().strip()
def new(p,data):
    raw=(json.dumps(data,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==raw
assert git(C,'rev-parse','HEAD')==SOURCE and not git(C,'diff','--name-only') and not git(C,'diff','--cached','--name-only')
assert git(H,'rev-parse','HEAD')=='0a31d84169ba8e151ec2f9a2c6fea958804daa5b'
state=read(T/'current-run.json');assert state['source10_inert_actual_result']=='PERMANENT_FAIL' and state['source10_inert_remaining_launches']==0
assert state['source10_inert2_allocation_released'] is False
assert sha(OLD/'inert-actual1-root-readback.json')=='f37eb5d7ea954a899105d1efc4a358f382614b56cfa03fc4a671e4f93cbd4d7a'
gate=read(V/'inert-caller-code-gate.json');approval=read(V/'harness-approval.json')
assert gate['candidate']==SOURCE and gate['spec']=='PASS' and gate['quality']=='APPROVED' and gate['open_findings']==[] and gate['execution_released'] is False
assert gate['approval_sha256']==sha(V/'harness-approval.json') and approval['overall']=='PASS' and approval['execution_released'] is False
CM=sha(W2/'inert-root-caller-manifest.json');assert CM==gate['caller_manifest_sha256']==approval['caller_manifest_sha256']
m=read(W2/'inert-root-caller-manifest.json')
for p,h in m['dependencies'].items():assert sha(Path(p))==h,p
for n,h in m['files'].items():assert sha(W2/n)==h,n
assert sha(V/'harness/manifest.json')==gate['harness_manifest_sha256']=='3d0b47c9102b969d75685cc07b65623a9764e51cfdeaaee687431d45ec6916c1'
for n in ['inert-root-launch-allocation.json','inert-root-live-hello.json','inert-root-dispatch.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert-root-result.pending.json','inert','actual']:assert not (V/n).exists(),n
release_id=str(uuid.uuid4());argv=[str(PY),'-B','-X','utf8',str(W2/'root-inert-invocation.py')]
allocation=dict(schema=1,issuer='root',kind='source10_one_inert_launch_allocation',issued_at=dt.datetime.now(dt.timezone.utc).isoformat(),original_order='wo-ultimaagent-20261101-0021',candidate=SOURCE,caller_manifest_sha256=CM,harness_manifest_sha256=gate['harness_manifest_sha256'],approval_sha256=sha(V/'harness-approval.json'),consumed=1,max_attempts=1,retry=0,release_id=release_id,argv=argv,cwd=str(C),tty=True,actual_launch_confirmed=None,model_calls=0,product_cli=0,external=0,UI=0,audio=0,mic=0,port=18765,actual=False,profile=False,T2='NOT_PASSED',revision='inert2',prior_failed_allocation_preserved=True,prior_failed_allocation_sha256=sha(OLD/'inert-root-launch-allocation.json'),semantics='Changed reviewed code; ONE new ROOT submission preconsumed; oldactual1 remainsPERMANENTFAIL. Same liveHELLO/closeddispatch/go only,no replacement/retry/model/profile/actual/T3 grant.',outer_exit_propagation='PowerShell immediately exits with native LASTEXITCODE after the single Python child')
target=V/'inert-root-launch-allocation.json';new(target,allocation)
state.update(phase='E02_NAVIGATION_SOURCE10_INERT2_ONE_ROOT_ALLOCATION_RELEASED',source10_inert2_allocation_released=True,source10_inert2_release_id=release_id,source10_inert2_launch_submissions_consumed=1,source10_inert2_max_launch_submissions=1,source10_inert2_remaining_submissions=0,source10_inert2_retry=0,source10_inert2_launch_confirmed=False,source10_inert2_model_calls=0)
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note=f'ROOT separately RELEASED ONE changed-code INERT2 ONLY allocation{release_id}; fsync+CLOSE preconsumed1/1/retry0 before CLI, allocationSHA{sha(target)}. Next fixedH Python-B-Xutf8 W2/root-inert-invocation.py CWD C TTYTRUE, explicit outer exit nativeLASTEXITCODE. Capture HELLO, close freshROOTdispatch/release with prepared root-issue-inert2-runtime-data.py, send GO ONCE same session. No relaunch/reissue/model/profile/actual/T3. Oldactual1 remainsPERMANENTFAIL1/1/0remaining; product/KWS/protected5 untouched.'
for p in [W/'progress.md',W/'resume-current.md',H/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']:
    with p.open('a',encoding='utf8') as f:f.write('\n'+note+'\n')
print(json.dumps(dict(release_id=release_id,allocation_sha256=sha(target),argv=argv,consumed=1,max_attempts=1,model_calls=0,launch_not_yet_confirmed=True)))
