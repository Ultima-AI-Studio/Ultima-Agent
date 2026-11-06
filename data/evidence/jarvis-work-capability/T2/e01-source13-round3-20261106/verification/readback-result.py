"""Read the completed case and live identities without starting work or inference."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
CASE=ROOT/'actual/e01-round3'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def save(path,data):
    with path.open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')


terminal=load(CASE/'terminal.json');result=load(CASE/'product-result.json')
assert terminal['overall']=='PENDING_FACT_REVIEW' and terminal['errors']==[]
assert terminal['product_result_sha256']==sha(CASE/'product-result.json')
assert load(CASE/'cli.stdout')==result==load(CASE/'pre-cleanup-product-observed.json')
assert result['status']=='succeeded' and result['ok'] is True and len(result['artifacts'])==1
artifact=result['artifacts'][0];path=Path(artifact['path'])
assert path.resolve()==(CASE/'outputs'/result['task_id']/'summary.md').resolve()
assert path.is_file() and sha(path)==artifact['sha256']
external=load(CASE/'external-artifacts.json');effects=load(CASE/'pre-cleanup-effects.json')
assert len(external)==len(effects['outputs'])==1
assert external[0]['sha256']==external[0]['external_sha256']==effects['outputs'][0]['sha256']==sha(path)
assert external[0]['text']==path.read_text(encoding='utf-8')
assert bytes.fromhex(effects['outputs'][0]['bytes_hex'])==path.read_bytes()
events=[x for x in result['trace'] if x['type']=='inference_end']
writes=[x for x in result['trace'] if x['type']=='tool_call_end']
assert len(events)==2 and all(x['data']['model']=='qwen3-8b-uncensored' for x in events)
assert len(writes)==1 and writes[0]['data']['tool']=='ultima_work_file_write' and writes[0]['data']['success'] is True
assert writes[0]['data']['metadata']['content']==path.read_text(encoding='utf-8')
assert terminal['work_cli_count']==effects['cli_count']==1
save(ROOT/'verification/result-content-readback.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    producer='root',status='PASS_MECHANICAL_READBACK_PENDING_INDEPENDENT_FACTS',case='e01-round3',
    candidate=terminal['candidate'],task_id=result['task_id'],terminal_sha256=sha(CASE/'terminal.json'),
    product_result_sha256=sha(CASE/'product-result.json'),artifact_path=str(path),artifact_sha256=sha(path),
    artifact_bytes=path.stat().st_size,content=path.read_text(encoding='utf-8'),
    raw_cli_product_precleanup_equal=True,service_external_current_hash_equal=True,work_cli_count=1,
    completed_inference_events=len(events),completed_sdk_tool_events=len(writes),
    actual_native_start_count=None,generation_after_disconnect='unknown',facts='PENDING_ROOT_INDEPENDENT_REVIEW',
    additional_model_calls=0,audio_actions=0,next_execution_authorized=False))
sys.path.insert(0,str(ROOT/'code'))
from acceptance_backend import AcceptanceBackend
backend=AcceptanceBackend(ROOT)
post=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),producer='root',status='PENDING',
    actual_cases_started=0,model_inferences=0,audio_actions=0,UI_actions=0,errors=[])
try:
    proof=backend.inspect()
    post.update(protected=[dict(row,active=True,match=True) for row in proof['protected_processes']],
        native_version=proof['model']['version']['version'],model_name=proof['model']['model'],
        model_digest=proof['model']['digest'],native_listener_owner=proof['listener_pid'],
        protected_readonly_proof=proof)
    c=backend.controller;owned=[]
    for row in load(CASE/'cleanup.json')['processes']:
        original=row['identity']
        try:
            current=c.identity(original['pid'])
            owned.append(dict(identity=original,pid_currently_exists=True,
                original_identity_absent=(current!=original),current_identity=current))
        except OSError as exc:
            if getattr(exc,'winerror',None)!=87:raise
            owned.append(dict(identity=original,pid_currently_exists=False,original_identity_absent=True))
    post['owned']=owned
    port=load(CASE/'listener.json')['port'];post['isolated_port']=port
    post['isolated_port_closed']=not c.listener_owner(port)
    voice=subprocess.run([r'H:\UltimaAI\UltimaAgent\tools\venv-voice-next\Scripts\python.exe','-B','-X','utf8',
        r'H:\UltimaAI\UltimaAgent\src\voice-next\launch.py','--status'],capture_output=True,text=True,
        encoding='utf-8',creationflags=subprocess.CREATE_NO_WINDOW,timeout=30)
    assert voice.returncode==0
    raw=json.loads(voice.stdout)
    post['voice']={key:raw.get(key) for key in ('state','ready','fresh','worker_ready','instance_lock_held','pid','worker_pid','run_id')}
    baseline=load(ROOT/'inputs/protected-baseline.json')['voice_listener_status']
    assert post['voice']['state']=='ready' and all(post['voice'][key] is True for key in ('ready','fresh','worker_ready','instance_lock_held'))
    assert all(post['voice'][key]==baseline[key] for key in ('pid','worker_pid','run_id'))
    assert len(owned)==6 and all(row['original_identity_absent'] for row in owned) and post['isolated_port_closed']
    post['status']='PASS_POINT_IN_TIME_POSTCHECK'
except Exception as exc:
    post['status']='FAIL_POINT_IN_TIME_POSTCHECK';post['errors'].append({'type':type(exc).__name__,'error':str(exc)})
post['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat()
post['limitations']='Point-in-time only; no continuous/future availability or voice acoustic-function claim.'
save(ROOT/'verification/result-protected-readback.json',post)
print(json.dumps({'case':'e01-round3','artifact':str(path),'bytes':path.stat().st_size,
    'artifact_sha256':sha(path),'postcheck':post['status'],'protected':len(post.get('protected',[])),
    'owned':len(post.get('owned',[])),'errors':post['errors']},ensure_ascii=False))
sys.exit(0 if post['status']=='PASS_POINT_IN_TIME_POSTCHECK' else 1)
