"""Read and seal the one already-finished case. Never invokes entry or product."""
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import subprocess

R = Path(r'H:\UltimaAI\UltimaAgent')
N = R/'data/evidence/jarvis-work-capability/T2/e02-source13-child-admission-20261107-r1'
F = N/'actual/E02-controlled-1'
OUT = N/'review/result-inputs'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def save_new(p, value):
    with p.open('x', encoding='utf8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

def check_files(base, mapping):
    for name, digest in mapping.items():
        assert sha(base/Path(name)) == digest, name
    return len(mapping)

assert not OUT.exists(), 'Readonly closure already captured; do not overwrite'
assert sha(N/'manifest.json') == 'ae432a96ae7ede18da792d89dfe75fc3d3d7887e51761508aa03ce3f2e255353'
assert sha(N/'review/independent-preparation-review.json') == '32cded1fcfdb61b0706f93e7f63a984fb20ce8830e44fa161609c8b816042c76'
counts = {'preparation': check_files(N, load(N/'manifest.json')['files'])}
inputs = load(N/'inputs/input-manifest.json')
counts['bound_inputs'] = check_files(Path(), inputs['files'])
counts['foreign_working_tree'] = check_files(R, load(N/'inputs/unrelated-working-tree.json')['files'])
old = N.parent/'e02-source13-real-controlled-preparation-20261106'
assert sha(old/'manifest.json') == '9f7ffce882e07861fd83c043e85ffdaa586b37dfb1041135d12c688996388964'
assert sha(old/'review/independent-preparation-review.json') == '5dbb5c54eb38b5c8e4b04cb7e280cf7d5c9dd2e057dedeea20eac1999da4220f'
counts['preserved_preparation'] = check_files(old, load(old/'manifest.json')['files'])
counts['actual_seal'] = check_files(F, load(F/'seal-index.json')['files'])
prior=Path(load(N/'inputs/predecessor.json')['root'])
counts['preserved_prior_preparation']=check_files(prior,load(prior/'manifest.json')['files'])
counts['preserved_prior_result']=check_files(prior,load(prior/'review/result-inputs/result-manifest.json')['files'])
candidate = Path(inputs['candidate_root'])
assert subprocess.check_output(['git','-C',str(candidate),'rev-parse','HEAD'], text=True).strip() == inputs['candidate']
assert not subprocess.check_output(['git','-C',str(candidate),'status','--porcelain','--untracked-files=no'], text=True).strip()
terminal = load(F/'terminal.json')
root = load(N/'release/root-outcome.json')
receipt = load(N/'release/tool-execution-receipt.json')
assert root['status'] == terminal['overall'] == 'FAIL'
assert root['outcome']['result'] == terminal
assert receipt['invocations'] == 1 and receipt['retry'] == 0 and receipt['exit_code'] == 1
assert receipt['question_id'] == 'call_42e3d2dd124f406cb3ccebd14a9b1c0f'
assert terminal['work_cli_attempts'] == 1 and terminal['application_native_POST_attempts'] == 0
assert terminal['cleanup']['status'] == 'PASS' and not root['outcome']['witness']['eligible']
assert (F/'product-result.json').exists() and not list(F.glob('outputs/**/research.md'))
assert sha(F/'boundary-before.json') == sha(F/'boundary-after.json')

# Import the hash-bound definitions only. No run_once/run_case/Owned or product calls.
spec = importlib.util.spec_from_file_location('readonly_real_case_adapter', N/'harness/adapter.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
p4 = adapter.load_p4()
baseline = load(Path(inputs['protected_baseline_path']))
rows = baseline['protected5'] + baseline['protected_listener_pair']
expected = [{k: row[k] for k in ('pid','created_filetime','exe')} for row in rows]
known = load(F/'owned-tree.json')
known_rows = known['processes'] + known['auxiliary']
ambiguous_pids = sorted({e['pid'] for e in known['errors'] if 'pid' in e} |
                        {pid for e in known['errors'] for pid in e.get('dependent_pids',[])})
target_pids = sorted({row['pid'] for row in expected} |
                     {row['identity']['pid'] for row in known_rows} | set(ambiguous_pids))
observed_start = dt.datetime.now(dt.timezone.utc).isoformat()
snapshot = p4.process_snapshot(pids=target_pids)
protection = []
for row, identity in zip(rows, expected):
    native = p4.identity(identity['pid'])
    cim = snapshot.get(identity['pid'])
    command_hash = hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest() if cim else None
    protection.append(dict(role=row['role'], identity=native, native_identity_equal=native == identity,
                           cim_identity_equal=bool(cim and p4.snapshot_identity_matches(identity,cim)),
                           parent_equal=bool(cim and cim['ParentProcessId']==row['parent_pid']),
                           command_line_sha256=command_hash, command_equal=command_hash==row['command_line_sha256']))
remaining = []
for row in known_rows:
    key = row['identity']
    cim = snapshot.get(key['pid'])
    remaining.append(dict(original_identity=key, exact_pid_present=cim is not None,
                          original_identity_still_present=bool(cim and p4.snapshot_identity_matches(key,cim))))
ambiguous = []
for pid in ambiguous_pids:
    cim = snapshot.get(pid)
    item = dict(pid=pid, exact_pid_present=cim is not None, original_native_identity_available=False,
                retrospective_ownership_proven=False)
    if cim:
        item.update(observed_cim_created_filetime=cim['CreationFileTime'], observed_parent=cim['ParentProcessId'],
                    observed_command_sha256=hashlib.sha256(cim['CommandLine'].encode('utf-16le')).hexdigest())
        try:
            item['observed_native_identity'] = p4.identity(pid)
        except OSError as exc:
            item['native_error'] = str(exc)
    ambiguous.append(item)
listeners = {str(port): p4.listener_owner(port) for port in (18799,11434)}
protected_ok = all(all(row[k] for k in ('native_identity_equal','cim_identity_equal','parent_equal','command_equal')) for row in protection)
observation = dict(kind='READONLY_POST_CASE_OBSERVATION', observed_start_utc=observed_start,
    observed_end_utc=dt.datetime.now(dt.timezone.utc).isoformat(), case_run_id=terminal['run_id'],
    protected_count=len(protection), protected_all_equal=protected_ok, protected=protection,
    original_known_identities=remaining, ambiguous_ids=ambiguous, listeners=listeners,
    seven_protected_continuous_liveness_measured=False, retrospective_cleanup_upgrade=False,
    original_cleanup_status='PASS', new_termination_calls=0, new_product_calls=0, new_model_calls=0,
    network_requests=0, limits=['Point observations do not prove continuous liveness.',
    'Later point observations do not change the original terminal result.',
    'Application POST attempts are 0 in the trusted export; native inference totals and network-wide counts remain unmeasured.'])
OUT.mkdir(parents=True)
save_new(OUT/'readonly-closeout.json', observation)

product=load(F/'product-result.json')
assert product['status']=='failed' and product['error']=='Invalid native model metadata'
assert len(product['research_attempts'])==5 and all(row['success'] is True for row in product['research_attempts'])
assert [row['tool_name'] for row in product['research_attempts']]==['ultima_work_web_search']+['ultima_work_http_get']*4
assert load(F/'trusted-export.json')['native_POST_attempts']==0
metadata=load(N/'native-preflight/E02-controlled-1.json')
allowed={'name','model','modified_at','size','digest','details'}
extras=[dict(name=row.get('name'),unexpected_keys=sorted(set(row)-allowed),capabilities=row.get('capabilities')) for row in metadata['tags']['models'] if set(row)-allowed]
save_new(OUT/'metadata-shape-readback.json',dict(product_error=product['error'],
    source=str(candidate/'src/brain/work_research.py'),source_sha256=sha(candidate/'src/brain/work_research.py'),
    function='checked_native_identity',allowed_model_keys=sorted(allowed),saved_preflight_extra_fields=extras,
    root_preflight_sha256=sha(N/'native-preflight/E02-controlled-1.json'),
    metadata_origin='Root preflight GET response; exact product metadata GET body was not exported',
    finding='Saved preflight capabilities is rejected by the frozen product allowlist; sufficient static incompatibility, not an exact product-response byte attribution',
    research_preflight_search=1,research_preflight_GET=4,controlled_sources_available=4,
    application_native_POST_attempts=0,actual_native_start_count=None,
    new_network_requests=0,new_product_calls=0,new_tests=0))

verification = dict(kind='ONE_CASE_RESULT_BYTE_READBACK', candidate=inputs['candidate'],
    model=inputs['model'], model_digest=inputs['model_digest'], checks=counts,
    preparation_manifest_sha256=sha(N/'manifest.json'), preparation_review_sha256=sha(N/'review/independent-preparation-review.json'),
    original_terminal_sha256=sha(F/'terminal.json'), root_outcome_sha256=sha(N/'release/root-outcome.json'),
    actual_status='FAIL', cleanup_status='PASS', timing_eligible=False, work_cli_attempts=1,
    application_native_POST_attempts=0, actual_native_start_count=None, research_file_count=0,
    actual_case_allocation_remaining=0, result_review_allocation_remaining=1, acceptance_credit=0,
    readonly_observation_sha256=sha(OUT/'readonly-closeout.json'), protected_current_equal=protected_ok,
    E02='NOT_PASSED', T2='NOT_PASSED', additional_runtime_calls=0, additional_tests=0)
save_new(OUT/'byte-readback.json', verification)
files = {p for directory in ('release','controller-authority','native-preflight','actual','review/result-inputs')
         for p in (N/directory).rglob('*') if p.is_file()}
files |= {N/'controller-ledger.json', N/'manifest.json', N/'review/independent-preparation-review.json', N/'harness-approval.json'}
save_new(OUT/'result-manifest.json', dict(kind='IMMUTABLE_ONE_REAL_CASE_RESULT_INPUTS',
    preparation_manifest_sha256=sha(N/'manifest.json'), run_id=terminal['run_id'],
    user_question_id=receipt['question_id'], status='FAIL_PENDING_INDEPENDENT_CONFIRMATION',
    files={p.relative_to(N).as_posix(): sha(p) for p in sorted(files)},
    readonly_script_path=str(Path(__file__)), readonly_script_sha256=sha(Path(__file__)),
    no_acceptance_credit=True, retry=False))
print(json.dumps(dict(status='FAIL_RETAINED', manifest_sha256=sha(OUT/'result-manifest.json'),
    members=len(files), protected_equal=protected_ok, listeners=listeners,
    known_remaining=sum(x['original_identity_still_present'] for x in remaining),
    ambiguous_pid_present=sum(x['exact_pid_present'] for x in ambiguous), checks=counts)))
