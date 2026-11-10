"""Issue one fresh diagnostic allocation and invoke the reviewed entry exactly once."""
from pathlib import Path
import datetime as dt
import importlib.util
import json
import subprocess
import time

N=Path(__file__).resolve().parents[1]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
spec=importlib.util.spec_from_file_location('diagnostic_one_case_entry',N/'code/entry.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
package=e.read_ready(N)
publication=e.load(N/'verification/final-ready-readback.json')
assert publication['verdict']=='PASS_LOCAL_PREPARATION_PUBLICATION' and publication['package']==package
assert not (N/'release').exists() and not (N/'actual').exists()
decision=e.load(N/'inputs/direct-user-decision.json')
assert decision['maximum_case_allocations']['diagnostic']==1 and decision['retry_per_case']==0
(N/'release').mkdir(exist_ok=False)
issued=dt.datetime.now(dt.timezone.utc)
grant=dict(schema=1,kind=e.KIND,source='user_explicit',question_id=decision['decision_id'],answer=decision['answer'],
    candidate=e.CANDIDATE,model=e.MODEL,model_digest=e.DIGEST,manifest_sha256=package['manifest_sha256'],review_sha256=package['review_sha256'],
    case='E02-controlled-1',actual_case_allocation=1,result_review_allocation=1,retry=0,
    issued_at=issued.isoformat(),expires_at=(issued+dt.timedelta(seconds=120)).isoformat())
e.save_new(N/'release/user-allocation.json',grant)
e.save_new(N/'release/purpose.json',dict(purpose='diagnostic',candidate=e.CANDIDATE,allocation_sha256=e.sha(N/'release/user-allocation.json'),
    post_repair_verification=False,maximum_invocations=1,retry=0))
argv=[str(e.PY),'-I','-B','-X','utf8',str(N/'code/entry.py')]
start=dt.datetime.now(dt.timezone.utc);clock=time.monotonic();exit_code=None
try:
    with (N/'release/entry.stdout.log').open('xb') as out,(N/'release/entry.stderr.log').open('xb') as err:
        completed=subprocess.run(argv,cwd=C,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW)
        exit_code=completed.returncode
finally:
    receipt=dict(entry='code/entry.py',argv=argv,started_utc=start.isoformat(),finished_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        outer_elapsed_seconds=time.monotonic()-clock,exit_code=exit_code,invocations=1,retry=0,question_id=decision['decision_id'])
    e.save_new(N/'release/tool-execution-receipt.json',receipt)
print(json.dumps(receipt))
raise SystemExit(exit_code if exit_code is not None else 1)
