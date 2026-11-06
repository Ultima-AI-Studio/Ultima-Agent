"""Derive the real research harness; retain original implementation and tests."""
from pathlib import Path
import ast,difflib,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent;H=N/'harness';OLD=T/'navigation-source10-validation-20261103-inert2/harness'
E01=T/'e01-source13-round3-20261106';Q=T/'e02-source13-exact-probe-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def replace_function(text,name,body):
    node=next(n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef) and n.name==name)
    lines=text.splitlines(True);return ''.join(lines[:node.lineno-1])+body.rstrip()+'\n'+''.join(lines[node.end_lineno:])
assert not (N/'inputs/harness-adaptation.json').exists()
for row in load(N/'inputs/harness-copy.json'):assert sha(H/row['name'])==row['sha256']
source=(H/'adapter.py').read_text('utf-8')
replacements={
    "C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')":"C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')",
    "P4=T/'e03-resume-20261102/preparation-r4/controller.py'":"P4=T/'e01-source13-round3-20261106/code/controller.py'",
    "P1=P4.parent.parent/'preparation/acceptance_adapter.py'":"P1=P4.parent.parent/'preparation-support/acceptance_adapter.py'",
    '118ba152b007c30d358c8bc44c51aabe8ae820f0':'269aca511d88412dbb9c15d23911138469a37aa2',
    'cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50':sha(N/'inputs/input-manifest.json'),
    'f3dcea80f720f903cc98ce77d1f8b9461ca4ad9b4e87e9d9d8c8b89262ae118a':sha(N/'inputs/scope.json'),
    '8b8fb6fdf4868b3bb8cea61daaf402e5336f86167d0be84e04c455586d98706f':sha(E01/'code/controller.py'),
    'd91ddf5e44a19d6143ee8657f1e0946617eb1c77197c399d017ace39cad02da4':sha(E01/'preparation-support/acceptance_adapter.py'),
}
for old,new in replacements.items():assert old in source,old;source=source.replace(old,new)
extra=f'''
INPUTS_PATH=V/'inputs/input-manifest.json'
BINDINGS_PATH=V/'code/bindings.py'
BINDINGS_SHA={sha(N/'code/bindings.py')!r}
PROTECTED_BASELINE=T/'e02-source13-exact-probe-20261106/inputs/protected-baseline.json'
SDK_SOURCES={tuple(load(OLD.parent/'source10-candidate-manifest.json')['sdk22'])!r}
if hashlib.sha256(BINDINGS_PATH.read_bytes()).hexdigest()!=BINDINGS_SHA:raise ValueError('Binding source drift')
_binding_spec=importlib.util.spec_from_file_location('source13_real_input_bindings',BINDINGS_PATH)
bindings=importlib.util.module_from_spec(_binding_spec);_binding_spec.loader.exec_module(bindings)
'''
source=source.replace("_OBSERVING=ContextVar('source10_root_observing',default=None)","_OBSERVING=ContextVar('source10_root_observing',default=None)\n"+extra)
source=replace_function(source,'check_inputs','''def check_inputs():
    require(Path(sys.executable).resolve()==PY.resolve(),'Exact authorized interpreter required')
    require(not sys.flags.optimize and sys.flags.dont_write_bytecode and sys.flags.utf8_mode==1,'Python -B -X utf8 required')
    require(sha(INPUTS_PATH)==MANIFEST_SHA and sha(BINDINGS_PATH)==BINDINGS_SHA,'Source13 input/source drift')
    require(sha(V/'inputs/scope.json')==PREPARATION_SHA,'Offline preparation scope drift')
    fixed=bindings.load_inputs(INPUTS_PATH)
    return dict(fixed['files'],**{str(INPUTS_PATH):MANIFEST_SHA,str(BINDINGS_PATH):BINDINGS_SHA,str(V/'inputs/scope.json'):PREPARATION_SHA})
''')
source=source.replace("    manifest=load(V/'source10-candidate-manifest.json')\n    for raw in manifest['sdk22']:","    for raw in SDK_SOURCES:")
source=source.replace("    try: spec.loader.exec_module(module)\n    finally: sys.path[:]=paths", "    try:\n        sys.path.insert(0,str(P4.parent))\n        spec.loader.exec_module(module)\n    finally: sys.path[:]=paths")
source=source.replace("    module.old.__source10_verified_sha__=sha(P1)\n    return module", "    module.old.__source10_verified_sha__=sha(P1)\n    module.old.PROTECTED_BASELINE=PROTECTED_BASELINE\n    return module")
source=replace_function(source,'validate_protected_members','''def validate_protected_members(identities,p4):
    require(type(identities) is list and len(identities)==7 and len({x['pid'] for x in identities})==7,'Exact protected member inventory: seven required')
    baseline=load(PROTECTED_BASELINE)
    rows=baseline.get('protected5',[])+baseline.get('protected_listener_pair',[])
    require(baseline.get('protected_process_count')==7 and len(rows)==7,'Seven accepted protected baseline rows')
    expected=[{k:row[k] for k in ('pid','created_filetime','exe')} for row in rows]
    require({x['pid']:x for x in identities}=={x['pid']:x for x in expected},'Exact protected member binding')
    require({x['pid']:x for x in p4.protected()}=={x['pid']:x for x in expected},'Protected live inventory drift')
    require(all(type(x['created_filetime']) is int and x['created_filetime']>0 and p4.identity(x['pid'])==x for x in identities),'Exact native identity drift')
    snapshot=p4.process_snapshot(pids=sorted(x['pid'] for x in identities))
    for row,key in zip(rows,expected):
        current=snapshot.get(row['pid'])
        require(current is not None and current['ParentProcessId']==row['parent_pid'],'Protected parent drift')
        require(p4.snapshot_identity_matches(key,current),'Protected CIM identity drift')
        require(hashlib.sha256(current['CommandLine'].encode('utf-16le')).hexdigest()==row['command_line_sha256'],'Protected command drift')
    return identities
''')
source=source.replace("P1.parent.parent/'runtime-before.json'","PROTECTED_BASELINE")
source=source.replace("    m=load(V/'source10-candidate-manifest.json')","    m=bindings.load_inputs(INPUTS_PATH)")
source=source.replace("Path(m['model']['local_manifest_path'])","Path(m['model_manifest_path'])")
ast.parse(source);(H/'adapter.py').write_text(source,encoding='utf-8')
test=(H/'test_adapter.py').read_text('utf-8')
for old,new in replacements.items():
    if old in test:test=test.replace(old,new)
(H/'test_adapter.py').write_text(test,encoding='utf-8')
runner=(H/'run_checks.py').read_text('utf-8')
runner=replace_function(runner,'snapshot','''def snapshot():
    import importlib.util
    spec=importlib.util.spec_from_file_location('source13_snapshot_adapter',HERE/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    files=module.check_inputs()
    for path,digest_value in FROZEN_FILES.items():
        if digest(path)!=digest_value:raise ValueError('Historical synthetic fixture drift')
        files[path]=digest_value
    return files
''')
runner=runner.replace("[str(PY), '-B', '-X', 'utf8', '-m', 'pytest'", "[str(PY), '-I', '-B', '-X', 'utf8', '-m', 'pytest'")
runner=runner.replace('result = subprocess.run(argv,cwd=run,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)',
    'result = subprocess.run(argv,cwd=run,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)')
(H/'run_checks.py').write_text(runner,encoding='utf-8')
(H/'README.md').write_text('''# Current source13 real controlled E02 harness — preparation only

Derived from the original source10 actual research harness. Product269aca5 and current community8B only. Keep original question, four-source corpus, product CLI/server, native SDK transport, RootInvocation and275/310/315 deadlines. Changes bind current inputs and current E01 helper plus all7protected identities with native/parent/command checks. The original browser search/GET fixture remains; model responses are never supplied by this harness. No execution release exists. Old case/historical failures remain intact. Original test function identities are retained; fixtures will be reconciled with current bindings, and all RED outputs preserved. Source13 binding adaptation is incomplete until offline full regression, export replay, root entry and independent preparation PASS.
''',encoding='utf-8')
manifest=dict(schema=13,kind='source13_real_controlled_harness_preparation_only',candidate='269aca511d88412dbb9c15d23911138469a37aa2',
    candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'),runtime_authority=False,
    files={name:sha(H/name) for name in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md')})
with (H/'manifest.json').open('x',encoding='utf-8') as f:json.dump(manifest,f,indent=2)
old_names=[n.name for n in ast.parse((OLD/'test_adapter.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
new_names=[n.name for n in ast.parse(test).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
assert old_names==new_names and len(new_names)==71
with (N/'inputs/harness-adaptation.json').open('x',encoding='utf-8') as f:json.dump(dict(old_test_function_ids=old_names,current_test_function_ids=new_names,
    replacements=replacements,actual_product_runs=0,model_calls=0,scope='Bindings/accepted helpers/protected inventory only; offline preparation incomplete'),f,indent=2)
diff=''.join(difflib.unified_diff((OLD/'adapter.py').read_text('utf-8').splitlines(True),source.splitlines(True),fromfile=str(OLD/'adapter.py'),tofile=str(H/'adapter.py')))
(N/'verification/harness-binding.diff').write_text(diff,encoding='utf-8')
print(json.dumps(dict(adapted=True,old_test_function_ids_retained=len(new_names),runtime_authority=False)))
