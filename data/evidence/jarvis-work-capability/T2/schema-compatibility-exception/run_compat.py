import sys,json,importlib
from pathlib import Path
checkout=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
evidence=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/schema-compatibility-exception')
sys.path.insert(0,str(checkout))
sys.path.insert(0,str(checkout/'src/brain'))
from src.brain import agent_server
import agent_tools_ultima
import tasks.queue_engine
module=importlib.import_module('src.brain.tests.test_agent_tools_extend')
module.ROOT=evidence/'compat-sandbox'
(module.ROOT/'data').mkdir(parents=True,exist_ok=True)
unapproved={str(Path(p)).casefold() for p in ('H:/UltimaAI/UltimaAgent','H:/UltimaAI/UltimaAgent/src/brain','H:/UltimaAI/UltimaAgent/libs/base/openjarvis/src')}
sys.path[:]=[p for p in sys.path if str(Path(p)).casefold() not in unapproved]
paths={'server':agent_server.__file__,'agent_tools':agent_tools_ultima.__file__,'queue_engine':tasks.queue_engine.__file__,'test_module':module.__file__,'test_root':str(module.ROOT)}
assert all(Path(paths[k]).resolve().is_relative_to(checkout) for k in ('server','agent_tools','queue_engine','test_module')),paths
(evidence/'compat-loaded-paths.json').write_text(json.dumps(paths,indent=2),encoding='utf8')
import pytest
raise SystemExit(pytest.main(['src/brain/tests/test_agent_tools_extend.py','-q','-p','no:cacheprovider','--junitxml='+str(evidence/'compat.xml')]))


