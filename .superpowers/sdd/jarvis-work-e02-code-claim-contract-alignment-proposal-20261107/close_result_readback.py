"""Seal the already completed one-case result without invoking entry or product."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-code-claim-schema-20261107-r1'
F=N/'actual/E02-controlled-1';OUT=N/'review/result-inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def verify(base,files):
    for name,digest in files.items():assert sha(base/name)==digest,name
    return len(files)
assert not OUT.exists()
checkpoint=load(N/'verification/ready-checkpoint.json')
assert sha(N/'manifest.json')==checkpoint['manifest_sha256']
assert sha(N/'review/independent-preparation-review.json')==checkpoint['review_sha256']
counts=dict(preparation=verify(N,load(N/'manifest.json')['files']),bound_inputs=verify(Path(),load(N/'inputs/input-manifest.json')['files']),
    foreign_files=verify(R,load(N/'inputs/unrelated-working-tree.json')['files']))
prior=Path(load(N/'inputs/predecessor.json')['root'])
counts['prior_preparation']=verify(prior,load(prior/'manifest.json')['files'])
counts['prior_result']=verify(prior,load(prior/'review/result-inputs/result-manifest.json')['files'])
inputs=load(N/'inputs/input-manifest.json');C=Path(inputs['candidate_root'])
assert subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip()==inputs['candidate']
assert not subprocess.check_output(['git','-C',str(C),'status','--porcelain'],text=True).strip()
receipt=load(N/'release/tool-execution-receipt.json');root=load(N/'release/root-outcome.json')
assert receipt['invocations']==1 and receipt['retry']==0 and receipt['question_id']=='call_99e734b15417466b92af3e8e85fdc3ea'
terminal=load(F/'terminal.json') if (F/'terminal.json').exists() else None
if terminal:
    assert root['outcome']['result']==terminal
    counts['actual_seal']=verify(F,load(F/'seal-index.json')['files'])
product=load(F/'product-result.json') if (F/'product-result.json').exists() else None
export=load(F/'trusted-export.json') if (F/'trusted-export.json').exists() else None
known=load(F/'owned-tree.json') if (F/'owned-tree.json').exists() else dict(processes=[],auxiliary=[],errors=[])
known_rows=known['processes']+known['auxiliary']
ambiguous_pids=sorted({e['pid'] for e in known['errors'] if 'pid' in e}|{pid for e in known['errors'] for pid in e.get('dependent_pids',[])})
spec=importlib.util.spec_from_file_location('metadata_result_readonly_adapter',N/'harness/adapter.py')
a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a);p4=a.load_p4()
baseline=load(Path(inputs['protected_baseline_path']));rows=baseline['protected5']+baseline['protected_listener_pair']
expected=[{k:row[k] for k in ('pid','created_filetime','exe')} for row in rows]
target_pids=sorted({key['pid'] for key in expected}|{row['identity']['pid'] for row in known_rows}|set(ambiguous_pids))
started=dt.datetime.now(dt.timezone.utc).isoformat();snapshot=p4.process_snapshot(pids=target_pids)
protection=[]
for row,key in zip(rows,expected):
    cim=snapshot.get(key['pid'])
    try:native=p4.identity(key['pid']);error=None
    except OSError as exc:native=None;error=type(exc).__name__+': '+str(exc)
    command_hash=hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest() if cim else None
    protection.append(dict(role=row['role'],identity=native,native_error=error,native_identity_equal=native==key,
        cim_identity_equal=bool(cim and p4.snapshot_identity_matches(key,cim)),parent_equal=bool(cim and cim['ParentProcessId']==row['parent_pid']),command_line_sha256=command_hash,command_equal=command_hash==row['command_line_sha256']))
remaining=[]
for row in known_rows:
    key=row['identity'];cim=snapshot.get(key['pid'])
    remaining.append(dict(original_identity=key,exact_pid_present=cim is not None,original_identity_still_present=bool(cim and p4.snapshot_identity_matches(key,cim))))
ambiguous=[]
for pid in ambiguous_pids:
    cim=snapshot.get(pid);v=dict(pid=pid,exact_pid_present=cim is not None,retrospective_ownership_proven=False)
    if cim:v.update(observed_cim_created_filetime=cim['CreationFileTime'],observed_parent=cim['ParentProcessId'],observed_command_sha256=hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest())
    ambiguous.append(v)
listeners={str(port):p4.listener_owner(port) for port in (18799,11434)}
protected_ok=all(all(row[k] for k in ('native_identity_equal','cim_identity_equal','parent_equal','command_equal')) for row in protection)
OUT.mkdir(parents=True)
status=terminal['overall'] if terminal else root['status']
run_id=terminal['run_id'] if terminal else None
save(OUT/'readonly-closeout.json',dict(kind='READONLY_POST_CASE_OBSERVATION',observed_start_utc=started,observed_end_utc=dt.datetime.now(dt.timezone.utc).isoformat(),case_run_id=run_id,
    protected_count=len(protection),protected_all_equal=protected_ok,protected=protection,original_known_identities=remaining,ambiguous_ids=ambiguous,listeners=listeners,
    seven_protected_continuous_liveness_measured=False,retrospective_cleanup_upgrade=False,original_cleanup_status=terminal.get('cleanup',{}).get('status') if terminal else None,
    new_termination_calls=0,new_product_calls=0,new_model_calls=0,network_requests=0,limits=['Point observations do not prove continuous liveness.','Later observations do not upgrade the original terminal.','Global native inference counts and OS packets remain unmeasured.']))
artifacts=[]
for p in sorted(F.glob('outputs/**/research.md')):artifacts.append(dict(path=str(p),bytes=p.stat().st_size,sha256=sha(p)))
attempts=product.get('research_attempts',[]) if product else []
summary=dict(kind='ONE_CASE_RESULT_BYTE_READBACK',candidate=inputs['candidate'],model=inputs['model'],model_digest=inputs['model_digest'],checks=counts,
    preparation_manifest_sha256=sha(N/'manifest.json'),preparation_review_sha256=sha(N/'review/independent-preparation-review.json'),
    run_id=run_id,actual_status=status,cleanup_status=terminal.get('cleanup',{}).get('status') if terminal else None,
    work_cli_attempts=terminal.get('work_cli_attempts') if terminal else None,application_native_POST_attempts=terminal.get('application_native_POST_attempts') if terminal else None,
    actual_native_start_count=terminal.get('actual_native_start_count') if terminal else None,root_witness_eligible=root.get('outcome',{}).get('witness',{}).get('eligible'),
    product_status=product.get('status') if product else None,product_error=product.get('error') if product else None,
    research_failure=product.get('research_failure') if product else None,
    controlled_search_success=sum(row['tool_name']=='ultima_work_web_search' and row['success'] is True for row in attempts),
    controlled_GET_success=sum(row['tool_name']=='ultima_work_http_get' and row['success'] is True for row in attempts),
    available_sources=len(product.get('available_sources',[])) if product else None,artifacts=artifacts,
    trusted_export_complete=export.get('complete') if export else None,outer_elapsed_seconds=receipt['outer_elapsed_seconds'],
    protected_current_equal=protected_ok,known_original_identities_remaining=sum(row['original_identity_still_present'] for row in remaining),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=1,acceptance_credit=0,E02='NOT_PASSED',T2='NOT_PASSED',additional_tests=0,additional_runtime_calls=0)
save(OUT/'byte-readback.json',summary)
files={p for directory in ('release','controller-authority','native-preflight','actual','review/result-inputs') for p in (N/directory).rglob('*') if p.is_file()}
files|={p for p in (N/'controller-ledger.json',N/'manifest.json',N/'review/independent-preparation-review.json',N/'harness-approval.json') if p.is_file()}
save(OUT/'result-manifest.json',dict(kind='IMMUTABLE_ONE_REAL_CASE_RESULT_INPUTS',preparation_manifest_sha256=sha(N/'manifest.json'),run_id=run_id,user_question_id=receipt['question_id'],
    status=status+'_PENDING_INDEPENDENT_CONFIRMATION',files={p.relative_to(N).as_posix():sha(p) for p in sorted(files)},readonly_script_path=str(Path(__file__)),readonly_script_sha256=sha(Path(__file__)),no_acceptance_credit=True,retry=False))
print(json.dumps(dict(status=status,product_status=summary['product_status'],product_error=summary['product_error'],manifest_sha256=sha(OUT/'result-manifest.json'),members=len(files),protected_equal=protected_ok,listeners=listeners,known_remaining=summary['known_original_identities_remaining'])))
