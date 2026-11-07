"""Update only this original order; retain the previous state as evidence."""
from pathlib import Path
import datetime as dt, hashlib, json, re, sys
R=Path('H:/UltimaAI/UltimaAgent'); N=Path(__file__).resolve().parents[1]
label=sys.argv[1]; status=sys.argv[2]; summary=sys.argv[3]
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',
       R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
       R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
       Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={str(p):p.read_bytes() for p in paths}
state=json.loads(before[str(paths[0])]); state.update(
    phase='SOURCE20_E02_FAILURE_STATE_'+label.upper(),workflow_status=status,
    active_evidence=str(N),active_plan=str(R/'docs/plans/jarvis-work-e02-failure-state-and-handoff-plan-20261107.md'),
    stage_queue_state='BLOCKED' if status=='blocked' else 'EXECUTING',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    next_action_scope=dict(authorized=True,source='User: 先补齐失败时的最终分支和选页诊断，再针对证据修复“读取到交付”的衔接。',
       scope='Diagnose once, then only an evidence-based repair in a separate candidate and one conditional verification; independent preparation and result review for each, no retry',
       actual_case_allocation=1,result_review_allocation=1,conditional_on_preparation_PASS=True))
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo=before[str(paths[1])].decode('utf8'); wo,n=re.subn(r'(?m)^- 状态：.*$', '- 状态：'+summary,wo,count=1); assert n==1
append='\n\n## 2026-11-07 E02 failure-state '+label+'\n\n'+summary+'\n'
texts[str(paths[1])]=wo+append
texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue=before[str(paths[3])].decode('utf8'); queue,n=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | '+('blocked' if status=='blocked' else 'executing')+' | '+summary+' |',queue); assert n==1
texts[str(paths[3])]=queue
receipt=N/'verification'/('registration-'+label+'.json'); assert not receipt.exists()
for p in paths: assert p.read_bytes()==before[str(p)]
for p in paths:p.write_text(texts[str(p)],encoding='utf8')
receipt.write_text(json.dumps(dict(at=dt.datetime.now(dt.timezone.utc).isoformat(),label=label,status=status,summary=summary,
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}),ensure_ascii=False,indent=2),encoding='utf8')
print(receipt)
