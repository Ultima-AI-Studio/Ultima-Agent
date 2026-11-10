"""Register this authorized offline continuation without allocating live work."""
from pathlib import Path
import datetime as dt,hashlib,json,re,sys
R=Path('H:/UltimaAI/UltimaAgent');N=Path(__file__).resolve().parents[1]
label=sys.argv[1];status=sys.argv[2];summary=sys.argv[3]
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md')]
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
state.update(phase='SOURCE22_E02_NATIVE_HTTP_'+label.upper(),workflow_status=status,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),active_evidence=str(N),active_plan=str(R/'docs/plans/jarvis-work-e02-native-http-diagnostics-plan-20261107.md'),stage_queue_state='BLOCKED' if status=='blocked' else 'EXECUTING',e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Read-only native compatibility and evidence-proven minimal diagnostic repair; offline verification and necessary independent review',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),active_preparation=dict(root=str(N),candidate='2b42b3e19516154a26cbc895a3d9e69fabb07ab2',status=label.upper(),actual=False))
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo=before[str(paths[1])].decode('utf8');wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,wo,count=1);assert count==1
append='\n\n## 2026-11-07 E02 native HTTP '+label+'\n\n'+summary+'\n计划：docs/plans/jarvis-work-e02-native-http-diagnostics-plan-20261107.md；证据：'+str(N)+'；实际分配0。\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | '+('blocked' if status=='blocked' else 'executing')+' | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
receipt=N/'verification'/('registration-'+label+'.json');assert not receipt.exists()
snapshot=N/'verification'/('registration-'+label+'-before');snapshot.mkdir(exist_ok=False)
for i,p in enumerate(paths):assert p.read_bytes()==before[str(p)];(snapshot/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
receipt.write_text(json.dumps(dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),label=label,status=status,summary=summary,before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},actual_case_allocation=0,model_calls=0),ensure_ascii=False,indent=2),encoding='utf8')
print(receipt)
