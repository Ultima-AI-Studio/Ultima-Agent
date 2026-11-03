"""ROOT code-only caller gate; no native allocation or runtime invocation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101';W2=W/'inert-revision2'
H=Path('H:/UltimaAI/UltimaAgent');T=H/'data/evidence/jarvis-work-capability/T2';V=T/'navigation-source10-validation-20261103-inert2'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0';HM='3d0b47c9102b969d75685cc07b65623a9764e51cfdeaaee687431d45ec6916c1'
MODEL=dict(alias='qwen3-8b-uncensored',digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',only_current8b=True)
def read(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,d):
    raw=(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
    assert p.read_bytes()==raw
def append(p,text):
    with p.open('ab') as f:f.write(('\n'+text+'\n').encode('utf8'))
def git(*args):
    p=subprocess.run(['git','-C',str(C),*args],capture_output=True);assert p.returncode==0,p.stderr[:1000];return p.stdout.decode().strip()
assert git('rev-parse','HEAD')==SOURCE and not git('diff','--name-only') and not git('diff','--cached','--name-only')
review=V/'inert-root-caller-review-1/verdict.json';human=review.with_name('review.md');d=read(review)
proofpath=V/'code/root-inert2-caller-before-review.json';proof=read(proofpath)
CM=sha(W2/'inert-root-caller-manifest.json');m=read(W2/'inert-root-caller-manifest.json')
assert d['candidate']==SOURCE and d['caller_manifest_sha256']==CM==proof['manifest_sha256']
assert d['spec']==d['spec_verdict']=='PASS' and d['quality']==d['quality_verdict']=='APPROVED' and d['findings']==[]
assert d['execution_released'] is False and d['T2']=='NOT_PASSED'
assert set(d['held_closed'])=={f'RC-{i:02}' for i in range(1,10)}
assert human.read_bytes()==(W/'task-4-inert2-caller-review-report.md').read_bytes()
assert proof['all_prior84_ids_retained'] and proof['final_tests']>=84
for p,h in read(W/'task-4-inert2-caller-review-inputs.json')['inputs'].items():assert sha(Path(p))==h,p
for p,h in m['dependencies'].items():assert sha(Path(p))==h,p
for n,h in m['files'].items():assert sha(W2/n)==h,n
assert sha(V/'harness/manifest.json')==HM
hg=read(V/'harness-code-gate.json');assert sha(V/'harness-code-gate.json')=='72808f725f14d3026f3f21048af78ea41767ff4a699d90b33f5d139ca26c8755'
assert hg['review_sha256']=='d5f25d002bb82590fca1f7582357bac6e588936ecd895a464213e9803603acc3' and hg['open_findings']==[]
for n in ['harness-approval.json','inert-root-launch-allocation.json','inert-root-live-hello.json','inert-root-dispatch.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert-root-result.pending.json','inert','actual']:assert not (V/n).exists(),n
approval=V/'harness-approval.json'
new(approval,dict(schema=1,reviewer='root-independent',overall='PASS',candidate=SOURCE,manifest_sha256=HM,candidate_manifest_sha256='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50',review_sha256=hg['review_sha256'],review_report_sha256=hg['report_sha256'],caller_manifest_sha256=CM,caller_review_sha256=sha(review),caller_review_report_sha256=sha(human),caller_spec='PASS',caller_quality='APPROVED',model_policy=MODEL,scope='REVIEWED_HARNESS_AND_CONCRETE_CALLER_CODE_ONLY',execution_released=False,T2='NOT_PASSED'))
gate=V/'inert-caller-code-gate.json'
new(gate,dict(schema_version=1,utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=SOURCE,caller_manifest_sha256=CM,harness_manifest_sha256=HM,spec='PASS',quality='APPROVED',review=str(review),review_sha256=sha(review),review_report_sha256=sha(human),closed_findings=[f'RC-{i:02}' for i in range(1,10)],open_findings=[],tests=proof['final_tests'],prior84_retained=True,pin_count=proof['pin_count'],root_readback_sha256=sha(proofpath),scope='CONCRETE_ENCLOSING_CALLER_CODE_PREPARATION_ONLY',approval_sha256=sha(approval),runtime_not_yet_qualified=['native identity','listener ownership','physical cleanup','timely closed real package','actual root readback'],execution_released=False,inert=False,profile=False,model=False,actual=False,T2='NOT_PASSED'))
p=T/'current-run.json';s=read(p)
assert s['source10_inert_actual_result']=='PERMANENT_FAIL' and s['source10_inert_remaining_launches']==0
s.update(phase='E02_NAVIGATION_SOURCE10_INERT2_CODE_READY_NOT_ALLOCATED',active_implementation_agent=None,active_review_agent=None,source10_inert2_caller_manifest_sha256=CM,source10_inert2_caller_review_sha256=sha(review),source10_inert2_caller_review_report_sha256=sha(human),source10_inert2_caller_tests=proof['final_tests'],source10_inert2_caller_status='SPEC_PASS_QUALITY_APPROVED_CODE_ONLY',source10_inert2_caller_code_gate_sha256=sha(gate),source10_inert2_harness_approval_sha256=sha(approval),source10_inert2_allocation_released=False)
p.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note=f'T4-PORT-REV2 Task2 complete CODE ONLY: caller{CM},review{sha(review)},{proof["final_tests"]}tests/all84held/9closuresheld; fresh dual approval{sha(approval)} scopeCODEONLY/executionfalse. Native2allocation remainsUNISSUED; oldactual1PERMANENTFAIL1/1closed and unknownmockEND preserved; model0/profile/actual/T3unreleased.'
for p in [W/'progress.md',W/'resume-current.md',H/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']:append(p,note)
print(json.dumps(dict(caller_manifest_sha256=CM,gate_sha256=sha(gate),approval_sha256=sha(approval),tests=proof['final_tests'],runtime_released=False)))
