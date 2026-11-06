"""Rebind the existing operational wrappers to this user's new one-case grant."""
from pathlib import Path
import ast,datetime as dt,hashlib,json
T=Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2')
B=T/'e02-source13-cold-import-20261106';Q=T/'e02-source13-exact-probe-20261106'
OLD='call_c6b188dbc9514611ad330bb3b8829619'
NEW='call_e9e5dd014d9b43f4b529f09bd2487d52'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert not (Q/'release').exists() and not (Q/'runs').exists() and not (Q/'execution').exists()
c=load(Q/'verification/preparation-checkpoint.json')
assert c['main']['commit']=='e44f3b0d117c278935c4641def7657195fe24fda'
assert c['mirror']['commit']=='2c27ae9d58161ad842b64ecd4f3e9df73f111a7a'
assert c['review_sha256']==sha(Q/'review/independent-preparation-review.json')
assert load(Q/'review/independent-preparation-review.json')['verdict']=='PASS'
for row in load(Q/'manifest.json')['files']:assert sha(Q/row['path'])==row['sha256']
bindings=[]
for name in ('profile-once-preflight.py','execute-profile-once.py','profile-once-postcheck.py'):
    src=B/'verification'/name;raw=src.read_text('utf-8');changed=raw
    if name!='profile-once-postcheck.py':
        assert raw.count(OLD)==1;changed=raw.replace(OLD,NEW)
    else:
        assert raw.count('ONE_AUTHORIZED_COLD_IMPORT_PROFILE_RESULT')==1
        changed=raw.replace('ONE_AUTHORIZED_COLD_IMPORT_PROFILE_RESULT','ONE_AUTHORIZED_EXACT_PROBE_PROFILE_RESULT')
    ast.parse(changed)
    target=Q/'verification'/name
    with target.open('x',encoding='utf-8') as f:f.write(changed)
    bindings.append(dict(source=str(src),source_sha256=sha(src),target=str(target),target_sha256=sha(target),
        only_change='result scope label' if name=='profile-once-postcheck.py' else 'new explicit question id'))
(Q/'execution').mkdir()
save(Q/'execution/operational-helper-bindings.json',dict(bindings=bindings,entry_source_changed=False))
save(Q/'execution/scope-approval.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),source='user_reply',
    question_id=NEW,answer='授权一例接线验证及独立结果复核（推荐）',scope='ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE',
    actual_profile_limit=1,root_entry_limit=1,result_review_limit=1,retry=0,inference=0,HTTP=0,port11434=0,
    DNS_host='raw.githubusercontent.com',UI=0,audio=0,services=0,
    local_ipv6_probe='Exact pinned urllib3 initialization, one AF_INET6/SOCK_STREAM/protocol0 socket, bind (::1,0), close',
    entry_manifest_sha256=sha(Q/'entry-manifest.json'),package_manifest_sha256=sha(Q/'manifest.json'),
    independent_review_sha256=sha(Q/'review/independent-preparation-review.json'),
    proposal_sha256=sha(Q/'execution-proposal.md'),preparation_commit=c['main']['commit']))
print(json.dumps(dict(scope='NEW_USER_SINGLE_CASE',source=NEW,helpers=len(bindings),actual_runs=0,release_issued=False)))
