"""Root controller: consume the recorded round3 allocation once, never retry."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
PYTHON = r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe'


def now():
    return dt.datetime.now(dt.timezone.utc)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x',encoding='utf-8') as f:
        json.dump(value,f,ensure_ascii=False,indent=2);f.write('\n')


def invoke(action, label):
    argv=[PYTHON,'-B','-X','utf8',str(ROOT/'code/acceptance_entry.py'),'--'+action]
    started=now();clock=time.monotonic()
    with (ROOT/'verification'/(label+'.stdout.log')).open('x',encoding='utf-8') as out, \
            (ROOT/'verification'/(label+'.stderr.log')).open('x',encoding='utf-8') as err:
        process=subprocess.run(argv,cwd=ROOT,stdout=out,stderr=err)
    receipt=dict(argv=argv,cwd=str(ROOT),started_at=started.isoformat(),finished_at=now().isoformat(),
                 elapsed_seconds=time.monotonic()-clock,exit_code=process.returncode,retry_authorized=False)
    save(ROOT/'verification'/(label+'-invocation.json'),receipt)
    return process.returncode


assert os.path.normcase(os.path.abspath(sys.executable))==os.path.normcase(PYTHON)
assert sys.dont_write_bytecode and not sys.flags.optimize
assert not (ROOT/'actual').exists() and not (ROOT/'release/authority.json').exists()
approval=load(ROOT/'user-approval.json');manifest=load(ROOT/'manifest.json')
assert approval['case']=='e01-round3' and approval['actual_case_allocation']==approval['independent_result_review_allocation']==1
assert approval['source']=='request_user_input_async/call_5790f6f4d5924325bead25c4bf764768/0'
assert approval['manifest_sha256']==sha(ROOT/'manifest.json')
assert approval['preparation_review_sha256']==sha(ROOT/'release/independent-review.json')
save(ROOT/'verification/actual-case-allocation.json',dict(recorded_at=now().isoformat(),case='e01-round3',
    allocation_consumed_for_single_attempt=True,user_approval_sha256=sha(ROOT/'user-approval.json'),
    case_cap=1,product_cli_cap=1,retry_authorized=False,result_review_remaining=1))
code=invoke('preflight','actual-preflight')
if code:
    save(ROOT/'verification/actual-case-completion.json',dict(recorded_at=now().isoformat(),case='e01-round3',
        outcome='PREFLIGHT_FAILED_NO_RETRY',exit_code=code,actual_created=(ROOT/'actual').exists(),retry_authorized=False))
    print(json.dumps({'stage':'preflight','exit_code':code,'retry':False}));sys.exit(code)
preflight=json.loads((ROOT/'verification/actual-preflight.stdout.log').read_text(encoding='utf-8'))
proof_path=ROOT/preflight['proof_path'];proof=load(proof_path)
assert proof_path.parent==ROOT/'release/preflight' and sha(proof_path)==preflight['proof_sha256']
issued=now();assert 0 <= (issued-dt.datetime.fromisoformat(proof['recorded_at'])).total_seconds() <= 60
authority=dict(schema=1,issuer='root',scope=manifest['scope'],case=manifest['case'],
    candidate=manifest['candidate'],candidate_manifest_sha256=manifest['candidate_manifest_sha256'],
    model=manifest['model'],digest=manifest['digest'],manifest_sha256=sha(ROOT/'manifest.json'),
    review_sha256=sha(ROOT/'release/independent-review.json'),proof_path=preflight['proof_path'],
    proof_sha256=preflight['proof_sha256'],case_cap=1,product_cli_cap=1,audio_actions=0,retry_authorized=False,
    acceptance_credit=False,prior_reviews=manifest['prior_reviews'],user_authorization=approval['source'],
    issued_at=issued.isoformat(),expires_at=(issued+dt.timedelta(seconds=120)).isoformat())
assert len(authority['prior_reviews'])==6
save(ROOT/'release/authority.json',authority)
save(ROOT/'verification/actual-entry-start.json',dict(recorded_at=now().isoformat(),case='e01-round3',
    authority_sha256=sha(ROOT/'release/authority.json'),proof_sha256=preflight['proof_sha256'],
    controller_pid=os.getpid(),automatic_retry=False))
code=invoke('run','actual-entry')
terminal=ROOT/'actual/e01-round3/terminal.json'
save(ROOT/'verification/actual-case-completion.json',dict(recorded_at=now().isoformat(),case='e01-round3',
    exit_code=code,terminal_present=terminal.is_file(),terminal_sha256=sha(terminal) if terminal.is_file() else None,
    actual_created=(ROOT/'actual').exists(),retry_authorized=False,actual_case_remaining=0,result_review_remaining=1))
result=load(terminal) if terminal.is_file() else {}
print(json.dumps({'case':'e01-round3','exit_code':code,'overall':result.get('overall'),
    'mechanical':result.get('mechanical'),'facts':result.get('facts'),'work_cli_count':result.get('work_cli_count'),
    'errors':result.get('errors'),'cleanup':result.get('cleanup',{}).get('status'),
    'audit':result.get('audit',{}).get('status'),'boundaries':result.get('boundaries',{}).get('status'),
    'terminal_sha256':sha(terminal) if terminal.is_file() else None},ensure_ascii=False))
sys.exit(code)
