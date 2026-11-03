"""ROOT data materialization after a separately allocated live HELLO; no case invocation."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import time
import uuid

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/inert-revision2'
V=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261103-inert2')
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
HM='3d0b47c9102b969d75685cc07b65623a9764e51cfdeaaee687431d45ec6916c1'
def raw(p):return p.read_bytes()
def digest(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(raw(p))
def encode(d):return (json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode('utf8')
def save(p,b):
    with p.open('xb') as f:f.write(b);f.flush();os.fsync(f.fileno())
    assert raw(p)==b
gate=load(V/'inert-caller-code-gate.json');CM=gate['caller_manifest_sha256']
assert gate['spec']=='PASS' and gate['quality']=='APPROVED' and gate['open_findings']==[] and gate['execution_released'] is False
assert gate['candidate']==SOURCE and gate['harness_manifest_sha256']==HM
assert digest(raw(W/'inert-root-caller-manifest.json'))==CM
m=load(W/'inert-root-caller-manifest.json')
for n,h in m['files'].items():assert digest(raw(W/n))==h,n
for p,h in m['dependencies'].items():assert digest(raw(Path(p)))==h,p
approval=load(V/'harness-approval.json')
assert digest(raw(V/'harness-approval.json'))==gate['approval_sha256']
assert approval['caller_manifest_sha256']==CM and approval['manifest_sha256']==HM and approval['overall']=='PASS'
assert approval['caller_review_sha256']==gate['review_sha256'] and approval['caller_review_report_sha256']==gate['review_report_sha256']
allocation=load(V/'inert-root-launch-allocation.json')
assert allocation['candidate']==SOURCE and allocation['caller_manifest_sha256']==CM and allocation['harness_manifest_sha256']==HM
assert allocation['approval_sha256']==digest(raw(V/'harness-approval.json'))
assert allocation['consumed']==allocation['max_attempts']==1 and allocation['retry']==0
assert allocation['model_calls']==allocation['product_cli']==allocation['external']==0
release_id=allocation['release_id'];assert str(uuid.UUID(release_id))==release_id and uuid.UUID(release_id).version==4
hello=load(V/'inert-root-live-hello.json')
assert set(hello)=={'action','protocol','candidate','caller_manifest_sha256','entry'}
assert hello['action']=='hello' and hello['protocol']=='T4C-ALLOC-01' and hello['candidate']==SOURCE and hello['caller_manifest_sha256']==CM
entry=hello['entry'];assert set(entry)=={'pid','entry_nonce','origin_ns'}
assert type(entry['pid']) is int and entry['pid']>0 and entry['pid'] not in [12796,492,37880,32856,18068]
assert type(entry['origin_ns']) is int and 0<=time.monotonic_ns()-entry['origin_ns']<275000000000
assert str(uuid.UUID(entry['entry_nonce']))==entry['entry_nonce'] and uuid.UUID(entry['entry_nonce']).version==4
for n in ['inert-root-dispatch.json','inert-root-release.json','inert-root-release.consumed.json','inert-native-baseline.json','inert-authority.json','inert-root-result.json','inert-root-result.pending.json','inert']:assert not (V/n).exists(),n
template=load(W/'inert-root-release-template.json')
assert template['released'] is False and template['port']==18765 and template['candidate']==SOURCE
dispatch=dict(schema=1,kind='source10_inert_root_dispatch',issuer='root',consumed=1,max_attempts=1,retry=0,candidate=SOURCE,caller_manifest_sha256=CM,entry=entry,scope=template['scope'],model_policy=template['model_policy'],port=18765,run_scope='one-new-inert-root-invocation',release_id=release_id,protocol_ruling_sha256=template['protocol_ruling_sha256'])
dispatch_raw=encode(dispatch);now=dt.datetime.now(dt.timezone.utc)
release=dict(template,released=True,issued_at=now.isoformat(),expires_at=(now+dt.timedelta(seconds=120)).isoformat(),caller_manifest_sha256=CM,approval_sha256=digest(raw(V/'harness-approval.json')),caller_review_sha256=approval['caller_review_sha256'],caller_review_report_sha256=approval['caller_review_report_sha256'],entry=entry,release_id=release_id,dispatch_sha256=digest(dispatch_raw))
release_raw=encode(release)
# Pure data consumer validation only, in a separate namespace. Never main/run/P4/native.
source=raw(W/'root-inert-invocation.py');assert digest(source)==m['files']['root-inert-invocation.py']
contract={'__name__':'root_inert2_grant_pure_contract','__file__':str(W/'root-inert-invocation.py')}
exec(compile(source,str(W/'root-inert-invocation.py'),'exec'),contract)
contract['entry_binding']=lambda:entry
go=dict(action='go',dispatch_sha256=digest(dispatch_raw));contract['_GO']=go
contract['release_check'](release);contract['dispatch_check'](release,dispatch_raw)
save(V/'inert-root-dispatch.json',dispatch_raw);save(V/'inert-root-release.json',release_raw)
save(V/'inert-root-grant-close-receipt.json',encode(dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),kind='root_inert_grant_data_close_receipt',allocation_sha256=digest(raw(V/'inert-root-launch-allocation.json')),hello_sha256=digest(raw(V/'inert-root-live-hello.json')),dispatch_sha256=digest(dispatch_raw),release_sha256=digest(release_raw),dispatch_fsync_and_close_returned=True,release_fsync_and_close_returned=True,pure_reviewed_consumer_validation='PASS',scope=template['scope'],native_or_case_invoked=False)))
assert raw(V/'inert-root-dispatch.json')==dispatch_raw and raw(V/'inert-root-release.json')==release_raw
print(json.dumps(go))
