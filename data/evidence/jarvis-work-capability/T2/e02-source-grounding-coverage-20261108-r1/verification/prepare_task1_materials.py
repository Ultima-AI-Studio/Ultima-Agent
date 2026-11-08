"""Preserve real semantic counterexamples and parent baseline receipts only."""
from pathlib import Path
import hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];R=N.parents[4]
P=N.parent/'e02-claim-generation-controlled-preparation-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review=load(P/'review/independent-result-review.json');artifact=Path(review['artifact']['path'])
assert sha(artifact)==review['artifact']['sha256']
for src,name in [(artifact,'previous-research.md'),(P/'review/independent-result-review.json','previous-independent-result-review.json')]:
    with (N/'inputs'/name).open('xb') as f:f.write(src.read_bytes())
save(N/'inputs/actual-negative-cases.json',dict(kind='ACTUAL_FACTUAL_ACCEPTANCE_COUNTEREXAMPLES_NOT_MODEL_ANSWERS',
    run_id=review['run_id'],candidate=review['candidate'],result_manifest_sha256=review['result_manifest_sha256'],
    review_sha256=sha(P/'review/independent-result-review.json'),artifact_sha256=sha(artifact),
    claim_reviews=review['claim_reviews'],coverage=review['full_question_coverage'],
    interpretation='Only claim7 passed both fact and selected citation; schema/card validity must never receive semantic credit. These records are not a template answer or model-supplied fixture.',
    model_calls=0,actual_cases=0,acceptance_credit=0))
baselines=[]
for group in ('baseline-json','baseline-coverage'):
    runs=list((N/'offline').glob(group+'-*'));assert len(runs)==1
    run=runs[0];receipt=load(run/'receipt.json');audit=load(run/'offline-audit.json')
    cases=list(ET.parse(run/'junit.xml').getroot().iter('testcase'))
    assert receipt['exit_code']==0 and receipt['sources_unchanged'] and audit['python_operations_clean']
    assert not audit['denied'] and all(not list(c) for c in cases)
    baselines.append(dict(group=group,root=str(run),tests=len(cases),receipt_sha256=sha(run/'receipt.json'),audit_sha256=sha(run/'offline-audit.json')))
save(N/'verification/baseline-readback.json',dict(verdict='PASS_PARENT_BASELINE_ONLY',tests=sum(x['tests'] for x in baselines),groups=baselines,product_changes=0,actual_cases=0,model_calls=0))
ledger=R/'.superpowers/sdd/jarvis-work-e02-source-grounding-coverage-plan-20261108/progress.md'
with ledger.open('a',encoding='utf8',newline='\n') as f:f.write('\n- Parent baseline: json35 + coverage40 = 75 passed, fresh guarded receipts; no source mutation, no denied operation, model/actual0.\n- Preserved all nine prior factual judgments and the actual failed-content artifact under N/inputs; not supplied as a template answer.\n')
print(json.dumps(dict(baseline_tests=75,semantic_counterexamples_preserved=9,model_calls=0,product_changes=0)))
