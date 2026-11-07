"""Seal the first completed outcome and observe identities, without any retry."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
A=N/'actual/E02-controlled-1';D=N/'review/result-inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
e=module('current_result_seal_entry',N/'code/entry.py');a=module('current_result_seal_adapter',N/'harness/adapter.py')
package=e.read_ready(N);a.check_inputs()
receipt=load(N/'release/tool-execution-receipt.json');outcome=load(N/'release/root-outcome.json')
assert receipt['invocations']==1 and receipt['retry']==0 and receipt['question_id']=='call_7ea1218e1bc347188fc72c160c50097a'
assert load(N/'release/consumed.json')['retry']==0
terminal=load(A/'terminal.json') if (A/'terminal.json').exists() else None
product=load(A/'product-result.json') if (A/'product-result.json').exists() else None
seal_index=load(A/'seal-index.json') if (A/'seal-index.json').exists() else None
if seal_index:
    for name,digest in seal_index['files'].items():assert sha(A/name)==digest,name
preservation=module('current_result_preservation',N/'verification/verify_preservation.py').verify()
D.mkdir(exist_ok=False)
save(D/'preservation-readback.json',preservation)
start=dt.datetime.now(dt.timezone.utc).isoformat();p4=a.load_p4();b=a.Deadline()
with a.PrivateIO(p4,b):
    protected=p4.protected();a.validate_protected_members(protected,p4)
    listener=p4.listener_owner(18799)
    cleanup=load(A/'cleanup.json') if (A/'cleanup.json').exists() else None
    owned=[row['identity'] for row in cleanup['processes']] if cleanup else []
    snapshot=p4.process_snapshot(pids=[row['pid'] for row in owned]) if owned else {}
    owned_after=[dict(identity=row,absent_at_observation=row['pid'] not in snapshot,
        matching_identity_present=(row['pid'] in snapshot and p4.snapshot_identity_matches(row,snapshot[row['pid']]))) for row in owned]
save(D/'readonly-closeout.json',dict(kind='READONLY_POST_CASE_OBSERVATION',observed_start_utc=start,
    observed_end_utc=dt.datetime.now(dt.timezone.utc).isoformat(),case_run_id=terminal.get('run_id') if terminal else None,
    protected_count=len(protected),protected_all_equal=True,protected=protected,owned_after=owned_after,
    isolated_port_owners=listener,original_cleanup_status=terminal.get('cleanup',{}).get('status') if terminal else None,
    retrospective_cleanup_upgrade=False,continuous_liveness_measured=False,actual_calls=0,model_calls=0,service_operations=0))
tools=product.get('tool_results',[]) if product else []
summary=dict(verdict='PASS_RESULT_BYTES_NOT_ACCEPTANCE',candidate=e.CANDIDATE,run_id=terminal.get('run_id') if terminal else None,
    original_status=outcome['status'],root_error=outcome.get('error'),product_status=product.get('status') if product else None,
    product_error=product.get('error') if product else None,entry_invocations=1,retry=0,
    counts={name:sum(x.get('tool_name')==name and x.get('success') is True for x in tools) for name in
        ('ultima_work_web_search','ultima_work_http_get','ultima_work_research_inspect','ultima_work_research_write')},
    research_files=len(list(A.rglob('research.md'))) if A.exists() else 0,
    application_native_POST_attempts=terminal.get('application_native_POST_attempts') if terminal else None,
    completed_native_posts=None,actual_native_start_count=None,
    root_witness_eligible=outcome.get('outcome',{}).get('witness',{}).get('eligible',False),
    cleanup=terminal.get('cleanup',{}).get('status') if terminal else None,protected_after=True,
    owned_identities_absent=all(not r['matching_identity_present'] for r in owned_after),isolated_port_free=not listener,
    outer_elapsed_seconds=receipt['outer_elapsed_seconds'],preparation_manifest_sha256=sha(N/'manifest.json'),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=1,acceptance_credit=0,E02='NOT_PASSED',T2='NOT_PASSED')
diagnostic=A/'trusted-failure-diagnostic.raw';export=A/'trusted-failure-diagnostic.export.json'
if export.exists():summary['failure_diagnostic_export']=load(export)
if diagnostic.exists():
    raw=diagnostic.read_bytes();packet=json.loads(raw)
    assert 0<len(raw)<=16384 and load(export)['status']=='SAVED' and load(export)['sha256']==sha(diagnostic)
    assert packet['kind']=='research_failure_diagnostic_v3' and packet['complete'] is False and packet['acceptance_credit']==0
    assert product['research_diagnostic']['sha256']==sha(diagnostic)
    with a.candidate_import_path():
        from src.brain.work_research_diagnostics import validate_failure_diagnostic
        validate_failure_diagnostic(packet)
    summary['failure_diagnostic']=dict(sha256=sha(diagnostic),bytes=len(raw),kind=packet['kind'],branch=packet['branch'],
        pages=len(packet['pages']),confirmed_pages=sum(p['confirmed'] is True for p in packet['pages']),
        visible_pages=sum(p['visible'] is True for p in packet['pages']),final_answer_preserved=packet['final_answer'] is not None,
        eligible_source_ids=packet['eligible_source_ids'],budget=packet['budget'],last_http=packet['last_http'],
        write_confirmed=packet['write_confirmed'],ack_confirmed=packet['ack_confirmed'],acceptance_credit=0)
    summary['completed_native_posts']=packet['budget']['completed_posts']
save(D/'byte-readback.json',summary)
members=set()
for folder in ('actual','release','controller-authority','native-preflight'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file())
for name in ('controller-ledger.json','harness-approval.json','review/independent-preparation-review.json',
    'verification/allocated-user-decision.json','verification/allocation-registration.json','verification/run_allocated_case.py',
    'verification/register_allocation.py','verification/observe_before_case.py','verification/runtime-before-allocated-case.json',
    'verification/publication-readback.json','verification/ready-readback.json','verification/seal_allocated_result.py',
    'review/result-inputs/readonly-closeout.json','review/result-inputs/preservation-readback.json','review/result-inputs/byte-readback.json'):
    if (N/name).exists():members.add(N/name)
manifest=dict(kind='IMMUTABLE_ONE_REAL_CASE_RESULT_INPUTS',candidate=e.CANDIDATE,preparation_manifest_sha256=sha(N/'manifest.json'),
    run_id=summary['run_id'],user_question_id=receipt['question_id'],actual_invocations=1,result_review_allocation=1,
    status='FAIL_PENDING_INDEPENDENT_CONFIRMATION' if outcome['status']=='FAIL' else 'PENDING_ROOT_INDEPENDENT_REVIEW',
    files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)})
save(D/'result-manifest.json',manifest)
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
print(json.dumps(dict(summary=summary,result_members=len(members),result_manifest_sha256=sha(D/'result-manifest.json')),ensure_ascii=False))
