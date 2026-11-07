"""Seal the first outcome and observe current identities; never retry the case."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];A=N/'actual/E02-controlled-1';D=N/'review/result-inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,p):
    s=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
e=module('result_seal_entry',N/'code/entry.py');a=module('result_seal_adapter',N/'harness/adapter.py')
package=e.read_ready(N);a.check_inputs();outcome=load(N/'release/root-outcome.json');terminal=load(A/'terminal.json')
assert load(N/'release/tool-execution-receipt.json')['invocations']==1
for name,h in load(A/'seal-index.json')['files'].items():assert sha(A/name)==h,name
for p,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==h,p
old=N.parent/'e02-failure-state-20261107-r1'
for name in ('manifest.json','review/result-inputs/result-manifest.json'):
    for p,h in load(old/name)['files'].items():assert sha(old/p)==h,p
for p,h in load(old/'inputs/input-manifest.json')['source_files'].items():assert sha(Path(p))==h,p
D.mkdir(exist_ok=False);start=dt.datetime.now(dt.timezone.utc).isoformat();p4=a.load_p4();b=a.Deadline()
with a.PrivateIO(p4,b):
    protected=p4.protected();a.validate_protected_members(protected,p4)
    listener=p4.listener_owner(18799);assert not listener
    owned=[row['identity'] for row in load(A/'cleanup.json')['processes']]
    snapshot=p4.process_snapshot(pids=[row['pid'] for row in owned])
    owned_after=[dict(identity=row,absent_at_observation=row['pid'] not in snapshot,matching_identity_present=(row['pid'] in snapshot and p4.snapshot_identity_matches(row,snapshot[row['pid']]))) for row in owned]
    assert all(not x['matching_identity_present'] for x in owned_after)
save(D/'readonly-closeout.json',dict(kind='READONLY_POST_CASE_OBSERVATION',observed_start_utc=start,observed_end_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    case_run_id=terminal['run_id'],protected_count=len(protected),protected_all_equal=True,protected=protected,owned_after=owned_after,
    isolated_port_owners=listener,original_cleanup_status=terminal['cleanup']['status'],retrospective_cleanup_upgrade=False,continuous_liveness_measured=False,
    actual_calls=0,model_calls=0,service_operations=0))
members=set()
for folder in ('actual','release','controller-authority','native-preflight'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file())
members.update(N/name for name in ('controller-ledger.json','harness-approval.json','review/independent-preparation-review.json',
    'verification/final-ready-readback.json','verification/ready-mirror-readback.json','verification/runtime-readiness.json',
    'verification/seal_result.py','review/result-inputs/readonly-closeout.json'))
manifest=dict(kind='IMMUTABLE_ONE_REAL_CASE_RESULT_INPUTS',preparation_manifest_sha256=sha(N/'manifest.json'),run_id=terminal['run_id'],
    user_question_id=load(N/'release/user-allocation.json')['question_id'],status='FAIL_PENDING_INDEPENDENT_CONFIRMATION' if outcome['status']=='FAIL' else 'PENDING_ROOT_INDEPENDENT_REVIEW',
    files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)})
save(D/'result-manifest.json',manifest)
for p,h in manifest['files'].items():assert sha(N/p)==h
product=load(A/'product-result.json');tools=product['tool_results']
result=dict(verdict='PASS_RESULT_BYTES_NOT_ACCEPTANCE',run_id=terminal['run_id'],result_manifest_sha256=sha(D/'result-manifest.json'),
    result_members=len(members),preparation_members=len(load(N/'manifest.json')['files']),candidate=e.CANDIDATE,original_status=outcome['status'],
    product_status=product['status'],product_error=product.get('error'),counts={name:sum(1 for x in tools if x.get('tool_name')==name and x.get('success')) for name in ('ultima_work_web_search','ultima_work_http_get','ultima_work_research_inspect','ultima_work_research_write')},
    research_files=len(list(A.rglob('research.md'))),native_POST_attempts=terminal.get('application_native_POST_attempts'),actual_native_start_count=None,
    root_witness_eligible=outcome['outcome']['witness']['eligible'],cleanup=terminal['cleanup']['status'],protected_after=True,old_evidence_unchanged=True,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=1,E02='NOT_PASSED',T2='NOT_PASSED')
diagnostic=A/'trusted-failure-diagnostic.raw'
export=A/'trusted-failure-diagnostic.export.json'
if export.exists():
    result['failure_diagnostic_export']=load(export)
if diagnostic.exists():
    raw=diagnostic.read_bytes();packet=json.loads(raw)
    assert 0<len(raw)<=16384 and load(export)['sha256']==sha(diagnostic)
    assert packet['complete'] is False and packet['acceptance_credit']==0
    result['failure_diagnostic']=dict(sha256=sha(diagnostic),bytes=len(raw),branch=packet['branch'],pages=len(packet['pages']),
        final_answer_preserved=packet['final_answer'] is not None,eligible_source_ids=packet['eligible_source_ids'],
        budget=packet['budget'],write_confirmed=packet['write_confirmed'],ack_confirmed=packet['ack_confirmed'],acceptance_credit=0)
save(D/'byte-readback.json',result);print(json.dumps(result))
