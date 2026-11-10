from pathlib import Path
import datetime as dt,hashlib,json,os,subprocess,sys
N=Path(__file__).resolve().parents[1];PY=N.parents[4]/'tools/venv-openjarvis/Scripts/python.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
if len(sys.argv)==3 and sys.argv[1]=='--child':
    import importlib.util,unittest
    stage=Path(sys.argv[2]);denied=[]
    def audit(event,args):
        if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.startfile','os.posix_spawn','os.spawn'):
            denied.append(event);raise RuntimeError('Offline boundary test forbids actual network or process operations')
    sys.addaudithook(audit)
    spec=importlib.util.spec_from_file_location('test_entry',N/'tests/test_entry.py')
    test=importlib.util.module_from_spec(spec);spec.loader.exec_module(test)
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test))
    data=dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),denied=denied,success=result.wasSuccessful())
    with (stage/'test-result.json').open('x',encoding='utf-8') as f:json.dump(data,f,indent=2)
    raise SystemExit(0 if result.wasSuccessful() and not denied else 1)
assert len(sys.argv)==2 and sys.argv[1] in ('red','green','final','review-red','review-green')
assert Path(sys.executable).resolve()==PY.resolve() and sys.flags.isolated and sys.flags.dont_write_bytecode
stage=N/'offline'/('entry-'+sys.argv[1]);stage.mkdir(parents=True,exist_ok=False);(stage/'snapshot').mkdir()
sources=[N/'code/entry.py',N/'tests/test_entry.py',Path(__file__)]
before={str(p):sha(p) for p in sources}
for p in sources:(stage/'snapshot'/p.name).write_bytes(p.read_bytes())
env={k:v for k,v in os.environ.items() if not k.upper().endswith('_PROXY') and not k.upper().startswith(('OLLAMA_','OPENJARVIS_','PYTHON'))}
argv=[str(PY),'-I','-B','-X','utf8',str(Path(__file__)),'--child',str(stage)]
started=dt.datetime.now(dt.timezone.utc).isoformat()
with (stage/'stdout.log').open('xb') as out,(stage/'stderr.log').open('xb') as err:
    proc=subprocess.run(argv,cwd=str(stage),env=env,stdout=out,stderr=err,timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
result=json.loads((stage/'test-result.json').read_bytes());unchanged=before=={str(p):sha(p) for p in sources}
with (stage/'receipt.json').open('x',encoding='utf-8') as f:json.dump(dict(started_at=started,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    argv=argv,exit_code=proc.returncode,sources=before,sources_unchanged=unchanged,result=result,actual_product_runs=0,model_calls=0),f,indent=2)
print(json.dumps(dict(stage=stage.name,**result,exit_code=proc.returncode,sources_unchanged=unchanged)))
raise SystemExit(proc.returncode)
