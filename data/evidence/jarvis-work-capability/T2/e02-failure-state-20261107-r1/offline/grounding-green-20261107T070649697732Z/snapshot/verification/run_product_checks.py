"""Guarded offline product regression with immutable source and output receipts."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
PY=R/'tools/venv-openjarvis/Scripts/python.exe'
GROUPS={'failure-red':['test_work_failure_diagnostics.py'],'failure-green':['test_work_failure_diagnostics.py'],'grounding-red':['test_work_grounding_context.py'],'grounding-green':['test_work_grounding_context.py'],'metadata-red':['test_native_metadata_compat.py'], 'metadata-green':['test_native_metadata_compat.py'],
    'claim-red':['test_work_code_claim_schema.py'], 'claim-green':['test_work_code_claim_schema.py'],
    'grammar':[str(N/'verification/grammar_checks.py')],
    'reference-red':['test_work_source_reference_schema.py'], 'reference-green':['test_work_source_reference_schema.py'],
    'target-red':['test_work_fixed_target_schema.py'], 'target-green':['test_work_fixed_target_schema.py'],
    'diagnostics-red':['test_work_write_diagnostics.py'], 'diagnostics-green':['test_work_write_diagnostics.py'],
    'research':['test_work_research.py'],
    'research-a':['test_work_research.py'], 'research-b':['test_work_research.py'],
    'navigation':['test_work_navigation.py','test_work_navigation_sdk.py'],
    'transport':['test_work_navigation_transport.py'],
    'delivery':['test_work_delivery.py','test_work_context.py']}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert len(sys.argv)==2 and sys.argv[1] in GROUPS
assert Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
group=sys.argv[1];run=N/'offline'/(group+'-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
run.mkdir(exist_ok=False);(run/'snapshot').mkdir()
paths=[*C.glob('src/brain/*.py'),*C.glob('src/brain/tests/test_work*.py'),C/'src/brain/tests/test_native_metadata_compat.py',C/'src/brain/tests/fixtures/native_metadata_0_32_15.json',N/'verification/product_pytest.py',Path(__file__)]
paths += [N/'verification/grammar_checks.py', *sorted((N/'verification/upstream').glob('*'))]
before={str(p):sha(p) for p in paths}
for p in paths:
    dst=run/'snapshot'/(p.relative_to(C) if p.is_relative_to(C) else p.relative_to(N))
    dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(p.read_bytes())
env={k:v for k,v in os.environ.items() if not k.upper().endswith('_PROXY') and not k.upper().startswith(('OLLAMA_','OPENJARVIS_','PYTHON','PYTEST','ULTIMA_ADAPTER_'))}
env.update(PYTHONDONTWRITEBYTECODE='1',PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONIOENCODING='utf-8',TEMP=str(run),TMP=str(run),OPENJARVIS_HOME=str(run/'owned-env/openjarvis'),HF_HOME=str(run/'owned-env/hf'),XDG_CACHE_HOME=str(run/'owned-env/cache'))
targets=[str(C/'src/brain/tests'/name) for name in GROUPS[group]]
if group in ('research-a','research-b'):
    names=[n.name for n in ast.parse(Path(targets[0]).read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')]
    selected=names[:len(names)//2] if group=='research-a' else names[len(names)//2:]
    targets=[targets[0]+'::'+name for name in selected]
argv=[str(PY),'-I','-B','-X','utf8',str(N/'verification/product_pytest.py'),*targets,'-vv','-p','no:cacheprovider','--basetemp='+str(run/'temp'),'--junitxml='+str(run/'junit.xml')]
if group=='delivery':
    argv+=['-k','not test_http_work_legacy_and_cli and not test_reparse_rejected']
started=dt.datetime.now(dt.timezone.utc).isoformat()
try:r=subprocess.run(argv,cwd=run,env=env,capture_output=True,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
except subprocess.TimeoutExpired as exc:r=subprocess.CompletedProcess(argv,124,exc.stdout or b'',(exc.stderr or b'')+b'\nOFFLINE 90 SECOND TIMEOUT\n')
(run/'stdout.log').write_bytes(r.stdout);(run/'stderr.log').write_bytes(r.stderr)
unchanged=before=={str(p):sha(p) for p in paths}
save(run/'receipt.json',dict(group=group,argv=argv,exit_code=r.returncode,source_sha256=before,sources_unchanged=unchanged,started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),actual=False,model_calls=0,product_launches=0))
print(r.stdout.decode('utf8','replace')[-2600:]);print(r.stderr.decode('utf8','replace')[-1000:]);print('RECEIPT '+str(run/'receipt.json'))
raise SystemExit(r.returncode if unchanged else 2)
