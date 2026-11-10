"""Allocate only the already granted one readonly review of sealed results."""
from pathlib import Path
import datetime as dt,hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-code-claim-schema-20261107-r1'
def load(p):return json.loads(p.read_bytes())
scope=load(N/'inputs/granted-scope.json');p=N/'review/result-inputs/result-manifest.json';m=load(p)
assert scope['question_id']=='call_99e734b15417466b92af3e8e85fdc3ea' and scope['result_review_allocation']==1
assert load(N/'release/tool-execution-receipt.json')['invocations']==1
value=dict(kind='ONE_READONLY_CODE_CLAIM_RESULT_REVIEW',question_id=scope['question_id'],answer=scope['answer'],
    result_manifest_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),run_id=m['run_id'],
    reviewer='/root/review_e02_code_claim_result',allocated=1,consumed=1,remaining=0,new_actual_case=0,tests=0,retry=0,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
with (N/'review/result-review-allocation.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
s=load(N.parent/'current-run.json');s.update(active_review_agent=value['reviewer'],workflow_status='independent_result_review',actual_case_allocation_remaining=0,result_review_allocation_remaining=0)
(N.parent/'current-run.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps(value))
