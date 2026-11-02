"""Only activated for exact-command deterministic pytest subprocess."""
import atexit,hashlib,json,os,sys
from pathlib import Path
if os.environ.get('WORK_ACCEPTANCE_PREP_TEST')=='covering-exact':
    p=Path(__file__).resolve().parent; events=[]
    def audit(event,args):
        if event=='socket.connect':
            addr=args[1]
            if not isinstance(addr,tuple) or addr[0] not in ('127.0.0.1','localhost','::1') or addr[1] in (11434,8756): raise RuntimeError('Preparation forbids production/external socket')
            events.append(addr)
    sys.addaudithook(audit)
    @atexit.register
    def receipt():
        modules={}
        root=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
        for name,module in list(sys.modules.items()):
            path=getattr(module,'__file__',None)
            if path and (name.startswith('src.brain') or name.startswith('openjarvis')) and Path(path).is_file():
                modules[name]={'path':str(Path(path).resolve()),'sha256':hashlib.sha256(Path(path).read_bytes()).hexdigest()}
        bad=[n for n,x in modules.items() if n.startswith('src.brain') and not Path(x['path']).is_relative_to(root)]
        (p/'covering-exact-imports.json').write_text(json.dumps({'modules':modules,'wrong_checkout':bad,'permitted_local_test_connections':events,'production_and_external':'socket.connect blocked'},indent=2),encoding='utf-8')
