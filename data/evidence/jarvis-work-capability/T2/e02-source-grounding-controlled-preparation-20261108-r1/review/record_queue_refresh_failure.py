"""Preserve a failed aggregate refresh without changing another work order."""
from pathlib import Path
import datetime as dt
import hashlib
import json

N = Path(__file__).resolve().parents[1]
Q = Path('H:/UltimaAI/_shared/queue')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

assert sha(Q/'queue-status-gen.py')=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
assert sha(N/'manifest.json')=='f019de1da34ca272a48172493ad857b228d449d0e4bd817c1f8bfd9bba8d1eec'
manifest=json.loads((N/'manifest.json').read_bytes())
for name,h in manifest['files'].items():assert sha(N/name)==h,name
index=(Q/'global-queue-index.md').read_bytes()
section=index.decode('utf-8-sig').split('<!-- queue-items:start -->',1)[1].split('<!-- queue-items:end -->',1)[0]
rows=[tuple(c.strip() for c in line.strip('|').split('|')) for line in section.splitlines() if line.startswith('| Ultima')]
states={'frozen','pending','executing','audit','blocked','cancelled'}
assert all(len(r)==4 for r in rows)
invalid=[dict(project=r[0],id=r[1],state=r[2],reason=r[3]) for r in rows if r[2] not in states]
assert [(r['project'],r['id'],r['state']) for r in invalid]==[('UltimaAgent','wo-ultimaagent-20261108-0026','completed')]
assert len({r[:2] for r in rows})==len(rows)
own=[r for r in rows if r[:2]==('UltimaAgent','wo-ultimaagent-20261101-0021')]
assert len(own)==1 and own[0][2]=='blocked'
status=(Q/'queue-status.json').read_bytes();old=json.loads(status)
with (N/'verification/queue-status-after.json').open('xb') as f:f.write(status)
receipt=dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    status='FAILED_AGGREGATE_REFRESH_OUT_OF_SCOPE_REGISTER_STATE',
    generator_sha256=sha(Q/'queue-status-gen.py'),exit_code=1,
    observed_failure="ValueError: Duplicate work order or invalid state: ('UltimaAgent', 'wo-ultimaagent-20261108-0026')",
    failure_provenance='Observed refresh_queue.py tool execution failed before its receipt creation; this is a later read-only reconciliation, not a fabricated successful generator receipt.',
    invalid_rows=invalid,duplicate_rows=0,own_registration=list(own[0]),
    registrations_unchanged_by_reconciliation=True,aggregate_regenerated=False,
    snapshot_sha256=hashlib.sha256(status).hexdigest(),snapshot_updated_at=old['updated_at'],
    snapshot_is_fresh=False,observed_global_sha256=hashlib.sha256(index).hexdigest(),
    ruling='Retain canonical own registration as blocked awaiting allocation. Do not convert another order completed to frozen or weaken generator validation. Preserve stale aggregate snapshot explicitly as historical; local candidate/report publication may continue without representing the aggregate as refreshed. No queue generator retry.',
    actual_cases=0,model_calls=0,product_checks_changed=False,entry_checks_changed=False)
save(N/'verification/queue-refresh.json',receipt)
p=N.parent/'current-run.json';before=p.read_bytes();state=json.loads(before)
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
with (N/'review/current-run-before-queue-reconciliation.json').open('xb') as f:f.write(before)
state['queue_status_refresh']=dict(status=receipt['status'],receipt=str(N/'verification/queue-refresh.json'),
    canonical_own_registration_updated=True,aggregate_regenerated=False,snapshot_is_fresh=False,
    invalid_other_order='wo-ultimaagent-20261108-0026',invalid_state='completed')
p.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
save(N/'review/queue-refresh-reconciliation.json',dict(
    manifest_sha256=sha(N/'manifest.json'),queue_refresh_sha256=sha(N/'verification/queue-refresh.json'),
    current_run_before_sha256=hashlib.sha256(before).hexdigest(),current_run_after_sha256=sha(p),
    preserved_candidate=manifest['candidate'],scope='metadata-only-record-failure-no-foreign-row-mutation',
    actual_cases=0,model_calls=0,aggregate_regenerated=False))
assert (Q/'global-queue-index.md').read_bytes()==index and (Q/'queue-status.json').read_bytes()==status
print(json.dumps(dict(status=receipt['status'],canonical_own_registration='blocked',aggregate_regenerated=False)))
