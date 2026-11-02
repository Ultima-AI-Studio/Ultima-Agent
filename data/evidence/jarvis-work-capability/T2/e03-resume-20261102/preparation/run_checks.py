"""Offline proof driver; invokes existing pytest files unchanged with owned env."""
import contextlib, hashlib, importlib, json, os, socket, sys
from pathlib import Path
ROOT=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
P=Path(__file__).resolve().parent
sys.path[:0]=[str(ROOT),str(P)]
os.chdir(ROOT)
for key in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME'):
    directory=P/'test-env'/key; directory.mkdir(parents=True,exist_ok=True); os.environ[key]=str(directory)
os.environ.update(PYTHONDONTWRITEBYTECODE='1',NO_PROXY='localhost,127.0.0.1,::1',HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONPATH=str(ROOT)+os.pathsep+str(P))
network_events=[]
def audit(event,args):
    if event=='socket.connect':
        address=args[1]
        if not isinstance(address,tuple) or address[0] not in ('localhost','127.0.0.1','::1') or address[1] in (8756,11434):
            raise RuntimeError('Preparation forbids production or external socket: '+str(address))
        network_events.append({'event':event,'address':address})
sys.addaudithook(audit)
import pytest
mode=sys.argv[1]
files=['src/brain/tests/test_work_context.py','src/brain/tests/test_work_delivery.py'] if mode=='covering' else [str(P/'test_acceptance_adapter.py')]
args=[*files,'-q','-p','no:cacheprovider','--basetemp',str(P/(mode+'-basetemp')),'--junitxml',str(P/(mode+'.xml'))]
with (P/(mode+'.log')).open('w',encoding='utf-8') as f,contextlib.redirect_stdout(f),contextlib.redirect_stderr(f):
    code=pytest.main(args)
modules={}
for name,module in list(sys.modules.items()):
    path=getattr(module,'__file__',None)
    if path and (name.startswith('src.brain') or name.startswith('openjarvis')) and Path(path).is_file():
        modules[name]={'path':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
for name,item in modules.items():
    if name.startswith('src.brain') and not Path(item['path']).is_relative_to(ROOT): raise RuntimeError('Wrong product checkout '+name)
(P/(mode+'-receipt.json')).write_text(json.dumps({'argv':[sys.executable,'-B','-X','utf8','-m','pytest',*args],'driver_argv':sys.argv,'exit_code':int(code),'environment_overrides':{k:os.environ[k] for k in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME','XDG_CONFIG_HOME','XDG_DATA_HOME','NO_PROXY','PYTHONPATH','HF_HUB_OFFLINE','TRANSFORMERS_OFFLINE')},'loaded_modules':modules,'allowed_local_test_connections':network_events,'production_and_external_connections':'blocked by socket.connect audit hook'},indent=2),encoding='utf-8')
print(json.dumps({'mode':mode,'exit_code':int(code),'module_count':len(modules),'allowed_test_connections':len(network_events)}))
raise SystemExit(code)
