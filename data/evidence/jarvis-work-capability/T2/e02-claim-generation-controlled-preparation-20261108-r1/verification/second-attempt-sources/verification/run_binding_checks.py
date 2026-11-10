"""One isolated standard-library test child; each stage is exclusive."""
from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parents[1];PY=N.parents[4]/'tools/venv-openjarvis/Scripts/python.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)==3 and sys.argv[1]=='--child':
    import importlib.util,unittest
    stage=Path(sys.argv[2]);denied=[]
    def audit(event,args):
        if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.startfile','os.posix_spawn','os.spawn'):
            denied.append(event);raise RuntimeError('Offline input tests forbid network/process operations')
    sys.addaudithook(audit)
    spec=importlib.util.spec_from_file_location('test_bindings',N/'tests/test_bindings.py')
    test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test))
    data=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),denied=denied,success=result.wasSuccessful())
    with (stage/'test-result.json').open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
    raise SystemExit(0 if result.wasSuccessful() and not denied else 1)
assert len(sys.argv)==2 and sys.argv[1] in ('recovery-green','red','red-bound','green')
assert Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
stage=N/'offline'/('bindings-'+sys.argv[1]);stage.mkdir(parents=True,exist_ok=False)
sources=[N/'code/bindings.py',N/'tests/test_bindings.py',Path(__file__),N/'inputs/input-manifest.json']
before={str(p):sha(p) for p in sources};(stage/'snapshot').mkdir()
for p in sources:(stage/'snapshot'/p.name).write_bytes(p.read_bytes())
env=dict(os.environ)
for key in list(env):
    if key.upper().endswith('_PROXY') or key.upper().startswith(('OLLAMA_','OPENJARVIS_','PYTHON')):env.pop(key)
argv=[str(PY),'-I','-B','-X','utf8',str(Path(__file__)),'--child',str(stage)]
started=dt.datetime.now(dt.timezone.utc).isoformat()
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
    proc=subprocess.run(argv,cwd=str(stage),env=env,stdout=out,stderr=err,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
after={str(p):sha(p) for p in sources};result=json.loads((stage/'test-result.json').read_bytes())
receipt=dict(started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),argv=argv,exit_code=proc.returncode,
    sources=before,sources_unchanged=after==before,result=result,actual_product_runs=0,model_calls=0)
with (stage/'receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,indent=2)
print(json.dumps(dict(stage=stage.name,**result,exit_code=proc.returncode,sources_unchanged=after==before)))
raise SystemExit(proc.returncode)
