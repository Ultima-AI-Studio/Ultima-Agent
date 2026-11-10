"""Classify the observed other-order worker without stopping or hiding it."""
from pathlib import Path
import ast,hashlib,json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
p=N/'inputs/worker-observation.json';raw=p.read_bytes();worker=json.loads(raw)
assert worker['count']==1 and worker['workers'][0]['ProcessId']==20896
with (N/'inputs/worker-observation-initial.json').open('xb') as f:f.write(raw)
worker.update(this_order_worker_count=0,foreign_worker_count=1,
    identity_readback=dict(pid=20896,parent_pid=26900,created='2026-11-08T12:58:42.717716+08:00',executable='C:/Users/Administrator/AppData/Local/Programs/OpenAI/Codex/bin/codex.exe',other_order='wo-ultimaagent-20261108-0026-20261108',mentions_this_order=False,mentions_candidate=False),
    ruling='Root is sole implementer of order0021 in isolated frozen candidate; other-order worker is observed and preserved. Do not claim global zero or stop unrelated work.',worker_operations=0)
p.write_text(json.dumps(worker,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
plan=R/'docs/plans/jarvis-work-e02-source-grounding-controlled-entry-plan-20261108.md'
s=plan.read_text('utf8')+'\nWorker-scope ruling before independent plan review: one live codex exec PID20896 belongs to order0026 and does not mention order0021 or the candidate. Preserve it; report total1/this-order0 honestly. Admission checks only prohibit duplicate implementers of this order. Root uses the frozen isolated candidate and exact publication paths; no other-order process or source is modified. Original broad count0 copy stopped registration before mutation; the saved plan/state copies are reused only if their bytes still match.\n'
plan.write_text(s,encoding='utf8',newline='\n');(N/'plan.md').write_bytes(plan.read_bytes())
p=N/'verification/register.py';s=p.read_text('utf8')
s=s.replace("with b.open('xb') as f:f.write(a.read_bytes())", "if b.exists():assert b.read_bytes()==a.read_bytes(),str(b)\n    else:\n        with b.open('xb') as f:f.write(a.read_bytes())")
s=s.replace("assert worker['count']==0","assert worker['count']==worker['foreign_worker_count']==1 and worker['this_order_worker_count']==0")
s=s.replace("actual_codex_exec_workers_observed=worker['count'],reasoning_effort", "actual_codex_exec_workers_observed=worker['count'],this_order_workers=0,foreign_workers_preserved=1,reasoning_effort")
ast.parse(s);p.write_text(s,encoding='utf8',newline='\n')
with (N/'inputs/worker-scope-ruling.json').open('x',encoding='utf8') as f:json.dump(dict(initial_sha256=hashlib.sha256(raw).hexdigest(),current_observation_sha256=hashlib.sha256((N/'inputs/worker-observation.json').read_bytes()).hexdigest(),scope='No duplicate implementer of this work order; foreign order preserved',actual_cases=0),f,indent=2)
print('total1/this-order0/foreign1 recorded; no process operated')
