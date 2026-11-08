"""Use this session's explicit one-case answer and invoke the frozen entry once."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess,time
N=Path(__file__).resolve().parents[1]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
QUESTION_ID='call_c910dd9e4819410492607baac9ed63bf'
ANSWER='明确分配一例当前 8B 研究及一次独立结果复核（推荐）'
MANIFEST='c36908a9a99f290889cb420613a93d70611386ace39765e8b970f55f5ea1f16a'
REVIEW='112435823a9ab087ede87457026e0a78d11659e39a1cff22a2b14dafa767af5d'
spec=importlib.util.spec_from_file_location('allocated_current_http_entry',N/'code/entry.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
package=e.read_ready(N)
assert package['manifest_sha256']==MANIFEST and package['review_sha256']==REVIEW
publication=e.load(N/'verification/publication-readback.json')
assert publication['verdict']=='PASS_LOCAL_PUBLICATION_READBACK' and publication['manifest_sha256']==MANIFEST and publication['review_sha256']==REVIEW
assert publication['heads']['project']=='13699f8d7b523b420cd5c67f0a992e5e581a0125'
assert publication['heads']['candidate']==e.CANDIDATE=='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
assert not any((N/name).exists() for name in ('release','actual','controller-authority','native-preflight'))
decision=e.load(N/'verification/allocated-user-decision.json')
assert decision['question_id']==QUESTION_ID and decision['answer']==ANSWER
assert decision['manifest_sha256']==MANIFEST and decision['review_sha256']==REVIEW
assert all(type(decision[k]) is int and decision[k]==v for k,v in (('actual_case_allocation',1),('result_review_allocation',1),('retry',0)))
# Preparation deliberately deferred live checks; the unchanged entry performs all fresh
# identity/listener/native metadata checks inside its original clock after exclusive consumption.
assert e.load(N/'verification/actual-admission-readback.json')['verdict']=='PASS_CURRENT_IMMUTABLE_PREPARATION_AND_INPUTS'
(N/'release').mkdir(exist_ok=False)
issued=dt.datetime.now(dt.timezone.utc)
grant=dict(schema=1,kind=e.KIND,source='user_explicit',question_id=QUESTION_ID,answer=ANSWER,
    candidate=e.CANDIDATE,model=e.MODEL,model_digest=e.DIGEST,manifest_sha256=MANIFEST,review_sha256=REVIEW,
    case='E02-controlled-1',actual_case_allocation=1,result_review_allocation=1,retry=0,
    issued_at=issued.isoformat(),expires_at=(issued+dt.timedelta(seconds=120)).isoformat())
e.save_new(N/'release/user-allocation.json',grant)
e.save_new(N/'release/purpose.json',dict(purpose='claim_generation_one_case',candidate=e.CANDIDATE,
    allocation_sha256=e.sha(N/'release/user-allocation.json'),user_decision_sha256=e.sha(N/'verification/allocated-user-decision.json'),
    launcher_sha256=e.sha(Path(__file__)),maximum_invocations=1,retry=0))
argv=[str(e.PY),'-I','-B','-X','utf8',str(N/'code/entry.py')]
start=dt.datetime.now(dt.timezone.utc);clock=time.monotonic();exit_code=None
try:
    with (N/'release/entry.stdout.log').open('xb') as out,(N/'release/entry.stderr.log').open('xb') as err:
        completed=subprocess.run(argv,cwd=C,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        exit_code=completed.returncode
finally:
    receipt=dict(entry='code/entry.py',argv=argv,started_utc=start.isoformat(),finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        outer_elapsed_seconds=time.monotonic()-clock,exit_code=exit_code,invocations=1,retry=0,question_id=QUESTION_ID)
    e.save_new(N/'release/tool-execution-receipt.json',receipt)
print(json.dumps(receipt))
raise SystemExit(exit_code if exit_code is not None else 1)
