"""Read-only exact-identity postcheck and immutable failed-result inventory."""
from pathlib import Path
import ast,base64,ctypes as C,datetime as dt,hashlib,json,subprocess
E=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf-8') as stream:json.dump(v,stream,ensure_ascii=False,indent=2)
def require(ok,message):
    if not ok:raise ValueError(message)
entry=load(E/'entry-manifest.json');helper=E.parent/'e01-source13-round3-20261106'
for path,names in ((helper/'preparation-support/acceptance_adapter.py',{'process_api_error','identity'}),
                   (helper/'code/controller.py',{'process_snapshot','snapshot_identity_matches'})):
    assert sha(path)==entry['files'][str(path)]
    nodes=[n for n in ast.parse(path.read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'))
release=load(E/'release/release.json');run=E/'runs'/release['run_id'];terminal=load(run/'control/terminal.json')
assert terminal['status']=='FAIL' and terminal['mechanical']=='FAIL' and terminal['acceptance_credit'] is False
assert terminal==load(E/'execution/root.stdout') and load(E/'execution/root-exit.json')['exit_code']==1
assert load(E/'release/consumed.json')['consumed']==1
baseline=load(E/'inputs/protected-baseline.json');expected=baseline['protected5']+baseline['protected_listener_pair']
owned=[row['identity'] for row in terminal['cleanup']['processes']]+[load(E/'release/consumed.json')['root_native']]
proof=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),status='PENDING',protected=[],owned=[],errors=[],
    limitations='Point-in-time native identity observations; no continuous liveness, acoustic or OS-wide packet claim.')
try:
    rows=process_snapshot(pids=[x['pid'] for x in expected+owned])
    for want in expected:
        key=identity(want['pid']);row=rows.get(want['pid']);assert row is not None
        value=dict(key,parent_pid=row['ParentProcessId'],command_line_sha256=hashlib.sha256(row['CommandLine'].encode('utf-16le')).hexdigest())
        assert all(value[k]==want[k] for k in value) and snapshot_identity_matches(key,row),want['role']
        proof['protected'].append(dict(role=want['role'],**value,match=True))
    for key in owned:
        item=dict(identity=key,pid_in_CIM=key['pid'] in rows)
        try:
            live=identity(key['pid']);item.update(current_identity=live,original_identity_absent=live!=key)
        except OSError as exc:
            assert exc.winerror==87 and key['pid'] not in rows
            item.update(native_error=87,original_identity_absent=True)
        assert item['original_identity_absent'];proof['owned'].append(item)
    assert terminal['cleanup']['status']=='PASS' and terminal['cleanup']['logs_closed'] is True
    assert terminal['observed_at_ns']-terminal['origin_ns']<=315*10**9
    for path,digest in entry['files'].items():assert sha(Path(path))==digest,path
    proof['status']='PASS_POINT_IN_TIME_POSTCHECK'
except Exception as exc:proof.update(status='FAIL_POSTCHECK',errors=[dict(type=type(exc).__name__,message=str(exc))])
save(E/'execution/postcheck.json',proof)
assert proof['status']=='PASS_POINT_IN_TIME_POSTCHECK'
stderr=(run/'process/worker.stderr').read_text(encoding='utf-8')
assert 'socket.gethostname()' in stderr and "ValueError: Unexpected audited operation" in stderr
assert not (run/'worker/case/service-first-result.json').exists() and not (run/'worker/case/profile-first-result.json').exists()
assert not (run/'control/reader-go.json').exists() and not list(run.rglob('research.md'))
summary=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),run_id=release['run_id'],execution='FAIL',
    root_entry_invocations=1,profile_invocations=1,reader_invocations=0,retry=0,
    root_elapsed_seconds=(terminal['observed_at_ns']-terminal['origin_ns'])/10**9,
    error_surface=terminal['error'],root_cause='Ollama eager Client initialization calls platform.machine -> platform.uname -> socket.gethostname; WorkerAudit rejects all socket.* except scoped getaddrinfo.',
    failure_stage='private_scope entry / own_ollama_types, before run_profile body and real SDK research submission',
    inference_reached=False,SDK_research_submission_reached=False,research_artifact_produced=False,
    counters_basis='Failure traceback and reviewed control flow; no structured profile-first result produced.',
    actual_model_calls_observed=0,native_network_packets=None,native_DNS_calls=None,
    cleanup=terminal['cleanup']['status'],protected_match_count=len(proof['protected']),owned_plus_root_absent=len(proof['owned']),
    preparation_verdict_unchanged='PASS_PREPARATION_ONLY',E02='NOT_PASSED',T2='NOT_PASSED',
    remaining_root_invocations=0,remaining_result_reviews=1,independent_result_review='PENDING',next_runtime_authority=False)
save(E/'execution/root-result-readback.json',summary)
members={p for folder in (run,E/'release',E/'execution') for p in folder.rglob('*') if p.is_file()}
members.update({E/'entry-manifest.json',E/'manifest.json',E/'review/independent-preparation-review.json',
    E/'verification/code-preparation-gate.json',Path(__file__),E/'verification/profile-once-preflight.py',E/'verification/execute-profile-once.py'})
manifest=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),scope='ONE_AUTHORIZED_PROFILE_FAILED_RESULT',
    run_id=release['run_id'],execution='FAIL',runtime_authority=False,
    files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)])
save(E/'execution/result-manifest.json',manifest)
print(json.dumps(dict(run_id=release['run_id'],execution='FAIL',elapsed=summary['root_elapsed_seconds'],
    postcheck=proof['status'],protected=7,owned_plus_root_absent=4,result_files=len(members),
    result_manifest_sha256=sha(E/'execution/result-manifest.json'),reader_started=False,delivery=False,retry=False)))
