"""Read-only preparation for the explicitly authorized single profile invocation."""
from pathlib import Path
import ast,base64,ctypes as C,datetime as dt,hashlib,json,os,re,subprocess
E=Path(__file__).resolve().parents[1];repo=E.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8') as stream:json.dump(v,stream,ensure_ascii=False,indent=2)
def require(ok,message):
    if not ok:raise ValueError(message)
assert sha(E/'entry-manifest.json')=='8b63f148aa43f923b85ac5fa97a40a358e4eff5ab85e7adb2dde8f29951e542f'
assert sha(E/'manifest.json')=='22fec32700802661d9d238a76a616efe4292bd6504b3fc723e48984048cfe591'
for row in load(E/'manifest.json')['files']:assert sha(E/row['path'])==row['sha256'],row['path']
entry=load(E/'entry-manifest.json')
for name,digest in entry['files'].items():assert sha(Path(name))==digest,name
base=load(Path(entry['base_profile_manifest_path']))
for name,digest in base['files'].items():assert sha(Path(name))==digest,name
assert not (E/'release').exists() and not (E/'runs').exists()
work=E/'execution';assert load(work/'scope-approval.json')['question_id']=='call_e2d3b965cd22479087e7a5b013e77e65'
# Extract the unchanged read-only native helpers; no termination/controller module execution.
helper=E.parent/'e01-source13-round3-20261106'
ns=globals()
for path,names in ((helper/'preparation-support/acceptance_adapter.py',{'process_api_error','identity'}),
                   (helper/'code/controller.py',{'process_snapshot','snapshot_identity_matches'})):
    assert sha(path)==entry['files'][str(path)]
    tree=ast.parse(path.read_bytes());nodes=[node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name in names]
    assert len(nodes)==len(names)
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(path),'exec'),ns)
baseline=load(E/'inputs/protected-baseline.json');expected=baseline['protected5']+baseline['protected_listener_pair']
proof=dict(started_at=dt.datetime.now(dt.timezone.utc).isoformat(),status='PENDING',errors=[],protected=[],
    model_calls=0,profile_runs=0,UI=0,audio=0,services=0,source_bindings=len(entry['files']),base_bindings=len(base['files']))
try:
    rows=process_snapshot(pids=[x['pid'] for x in expected])
    for want in expected:
        key=identity(want['pid']);row=rows.get(want['pid']);assert row is not None
        value=dict(key,parent_pid=row['ParentProcessId'],command_line_sha256=hashlib.sha256(row['CommandLine'].encode('utf-16le')).hexdigest())
        assert all(value[k]==want[k] for k in value),want['role']
        assert snapshot_identity_matches(key,row),want['role']+' existing CIM precision rule'
        proof['protected'].append(dict(role=want['role'],**value,match=True))
    allrows=process_snapshot();executors=[];same_entry=[]
    for row in allrows.values():
        cmd=row['CommandLine'];lower=cmd.lower()
        if re.search(r'(?:^|[\\/])codex(?:\.exe)?"?\s+exec(?:\s|$)',cmd,re.I):
            executors.append(dict(pid=row['ProcessId'],parent_pid=row['ParentProcessId'],created_filetime=row['CreationFileTime'],
                command_line_sha256=hashlib.sha256(cmd.encode('utf-16le')).hexdigest()))
        if str(E/'code/entry.py').lower() in lower:same_entry.append(row['ProcessId'])
    assert not same_entry,'Existing same-entry process'
    assert len(executors)<3,'Global external execution limit already full'
    proof.update(status='PASS_POINT_IN_TIME_PREFLIGHT',external_codex_exec_count=len(executors),external_executors=executors,
        same_entry_processes=same_entry,inventory_basis='read-only CIM, actual codex exec rather than app-server/exec-server; no commandline plaintext persisted')
except Exception as exc:proof.update(status='FAIL_PREFLIGHT',errors=[dict(type=type(exc).__name__,message=str(exc))])
proof['finished_at']=dt.datetime.now(dt.timezone.utc).isoformat();save(work/'preflight-v2.json',proof)
print(json.dumps(dict(status=proof['status'],protected=len(proof['protected']),external_exec=proof.get('external_codex_exec_count'),errors=proof['errors'])))
raise SystemExit(0 if proof['status']=='PASS_POINT_IN_TIME_PREFLIGHT' else 1)
