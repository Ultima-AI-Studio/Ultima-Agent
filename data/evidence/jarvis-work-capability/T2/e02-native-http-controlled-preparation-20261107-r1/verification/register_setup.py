"""Record the current preparation-only instruction and original work order."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];P=N.parent/'e02-native-http-diagnostics-20261107-r1'
R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
answer='为新候选准备受控入口和绑定；明确分配单例后，再取得真实请求回执，据此决定原生兼容修复。'
save(N/'inputs/direct-user-decision.json',dict(source='direct_user_message_in_current_chat',answer=answer,decision_id='user-message:sha256:'+hashlib.sha256(answer.encode()).hexdigest(),identifier_is_platform_message_id=False,scope='Prepare the controlled entry and bindings; real-case allocation remains a future explicit decision',actual_case_allocation=0,result_review_allocation=0,retry=0,model_calls=0,UI=False,audio=False,service_operations=False,plan_sha256=sha(N/'plan.md')))
save(N/'inputs/scope.json',dict(source='Current explicit preparation instruction',scope='Controlled entry and bindings for ee1bef6; offline verification and independent preparation review',actual_case_allocation=0,result_review_allocation=0,model_calls=0,UI=False,audio=False,service_operations=False))
save(N/'inputs/predecessor.json',dict(product_preparation_root=str(P),candidate='ee1bef61f04169c64978538dbc4ba799ef7be6c0',manifest_sha256=sha(P/'manifest.json'),review_sha256=sha(P/'review/independent-preparation-review.json'),publication_sha256=sha(P/'verification/publication-readback.json'),previous_actual_root=str(N.parent/'e02-unique-sections-20261107-r1'),previous_actual='be79869f-10e5-4c0d-96a9-144cd5967c12',previous_actual_result='FAIL_CONFIRMED',actual_credit=0))
(N/'inputs/unrelated-working-tree.json').write_bytes((P/'inputs/unrelated-working-tree.json').read_bytes())
save(N/'inputs/previous-current-run.json',json.loads((N.parent/'current-run.json').read_bytes()))
save(N/'inputs/DoR.json',dict(work_order='wo-ultimaagent-20261101-0021',stage='T2',checks=dict(explicit_preparation_source=True,goal_and_write_scope=True,acceptance_and_prohibitions=True,frozen_dependency_evidence=True,original_registration_continues=True),actual_cases=0,model_calls=0))
old=(P/'verification/register_progress.py').read_text('utf8')
old=old.replace('SOURCE22_E02_NATIVE_HTTP_','SOURCE23_E02_HTTP_CONTROLLED_').replace('jarvis-work-e02-native-http-diagnostics-plan-20261107.md','jarvis-work-e02-native-http-controlled-entry-plan-20261107.md').replace('2b42b3e19516154a26cbc895a3d9e69fabb07ab2','ee1bef61f04169c64978538dbc4ba799ef7be6c0').replace('Read-only native compatibility and evidence-proven minimal diagnostic repair; offline verification and necessary independent review','Controlled entry and binding preparation only; actual allocation requires a later explicit user decision').replace('E02 native HTTP ','E02 HTTP controlled entry ')
with (N/'verification/register_progress.py').open('x',encoding='utf8') as f:f.write(old)
print(json.dumps(dict(decision_sha256=sha(N/'inputs/direct-user-decision.json'),scope_sha256=sha(N/'inputs/scope.json'),plan_sha256=sha(N/'plan.md'),DoR='5/5 preparation only',actual_cases=0)))
