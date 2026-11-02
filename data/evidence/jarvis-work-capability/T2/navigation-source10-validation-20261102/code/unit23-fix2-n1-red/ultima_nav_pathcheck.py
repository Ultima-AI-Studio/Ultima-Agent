import json,os,sys
from pathlib import Path
def pytest_sessionfinish(session, exitstatus):
    root=Path(os.environ['ULTIMA_NAV_TEST_RECEIPT_ROOT'])
    candidate=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent').resolve()
    sdk=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages').resolve()
    paths={n:str(Path(m.__file__).resolve()) for n,m in tuple(sys.modules.items()) if getattr(m,'__file__',None) and (n.startswith('src.brain.') or n.startswith('openjarvis.') or n in ('agent_server','agent_tools_ultima','work_tools','work_research','work_service','tasks.queue_engine'))}
    bad={n:p for n,p in paths.items() if not Path(p).is_relative_to(sdk if n.startswith('openjarvis.') else candidate)}
    (root/'loaded-paths.json').write_text(json.dumps({'modules':paths,'unexpected':bad,'sys_path':sys.path},indent=2),encoding='utf-8')
    if bad: session.exitstatus=1
