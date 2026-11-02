"""One isolated pytest invocation with exact command, paths and immutable logs."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

CANDIDATE = Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
PYTHON = 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe'
ROOT = Path(__file__).resolve().parent

stage, *tests = sys.argv[1:]
if not stage or Path(stage).name != stage or not tests:
    raise SystemExit('stage and explicit test paths are required')
folder = ROOT / stage
folder.mkdir(exist_ok=False)
env = os.environ.copy()
for key in ('TEMP', 'TMP', 'TMPDIR', 'OPENJARVIS_HOME', 'XDG_CACHE_HOME', 'HF_HOME', 'TORCH_HOME', 'MPLCONFIGDIR', 'NUMBA_CACHE_DIR'):
    target = folder / 'env' / key
    target.mkdir(parents=True)
    env[key] = str(target)
env.update(HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1', PYTHONDONTWRITEBYTECODE='1', NO_PROXY='localhost,127.0.0.1,::1')
env['PYTHONPATH'] = os.pathsep.join((str(CANDIDATE), str(CANDIDATE / 'src/brain'), str(folder)))
env['ULTIMA_NAV_TEST_RECEIPT_ROOT'] = str(folder)
plugin = '''import json,os,sys
from pathlib import Path
def pytest_sessionfinish(session, exitstatus):
    root=Path(os.environ['ULTIMA_NAV_TEST_RECEIPT_ROOT'])
    candidate=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent').resolve()
    sdk=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages').resolve()
    paths={n:str(Path(m.__file__).resolve()) for n,m in tuple(sys.modules.items()) if getattr(m,'__file__',None) and (n.startswith('src.brain.') or n.startswith('openjarvis.') or n in ('agent_server','agent_tools_ultima','work_tools','work_research','work_service','tasks.queue_engine'))}
    bad={n:p for n,p in paths.items() if not Path(p).is_relative_to(sdk if n.startswith('openjarvis.') else candidate)}
    (root/'loaded-paths.json').write_text(json.dumps({'modules':paths,'unexpected':bad,'sys_path':sys.path},indent=2),encoding='utf-8')
    if bad: session.exitstatus=1
'''
(folder / 'ultima_nav_pathcheck.py').write_text(plugin, encoding='utf-8')
cmd = [PYTHON, '-B', '-X', 'utf8', '-m', 'pytest', *tests, '-q', '-p', 'no:cacheprovider', '-p', 'ultima_nav_pathcheck', '--basetemp=' + str(folder / 'temp'), '--junitxml=' + str(folder / 'junit.xml')]
# Pin every baseline authority path plus allowed candidate/test path before the run.
t2 = ROOT.parents[1]
baseline_paths = json.loads((t2 / 'e02-interface-reassessment-20261102/source21-before.json').read_bytes())
allowed = json.loads((ROOT.parent / 'root-code-only-authority.json').read_bytes())['allowlist']
input_names = sorted(set(x.replace(chr(92), '/') for x in baseline_paths) | set(allowed) | set(x.split('::')[0] for x in tests))
def input_hashes(copy_to=None):
    result = {}
    for rel in input_names:
        path = CANDIDATE / rel
        if not path.is_file():
            result[rel] = None
            continue
        raw = path.read_bytes()
        result[rel] = hashlib.sha256(raw).hexdigest()
        if copy_to is not None:
            target = copy_to / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(raw)
    return result
before_sources = input_hashes(folder / 'source-inputs')
metadata = {'stage': stage, 'cwd': str(CANDIDATE), 'argv': cmd, 'env': {k: env[k] for k in ('TEMP','TMP','TMPDIR','OPENJARVIS_HOME','XDG_CACHE_HOME','HF_HOME','TORCH_HOME','MPLCONFIGDIR','NUMBA_CACHE_DIR','HF_HUB_OFFLINE','HF_HUB_DISABLE_TELEMETRY','PYTHONDONTWRITEBYTECODE','NO_PROXY','PYTHONPATH')}, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'runner_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
metadata['source_inputs_before'] = before_sources
(folder / 'invocation.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
with (folder / 'stdout.log').open('wb') as out, (folder / 'stderr.log').open('wb') as err:
    proc = subprocess.run(cmd, cwd=CANDIDATE, env=env, stdout=out, stderr=err)
after_sources = input_hashes()
source_unchanged = before_sources == after_sources
metadata.update(exit_code=proc.returncode if source_unchanged else 1, pytest_exit_code=proc.returncode, source_inputs_after=after_sources, source_unchanged=source_unchanged, finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
junit = folder / 'junit.xml'
if junit.exists():
    cases = ET.parse(junit).getroot().findall('.//testcase')
    metadata['counts'] = {'tests':len(cases), 'failures':sum(x.find('failure') is not None for x in cases), 'errors':sum(x.find('error') is not None for x in cases), 'skipped':sum(x.find('skipped') is not None for x in cases)}
metadata['files'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in folder.iterdir() if p.is_file()}
(folder / 'receipt.json').write_text(json.dumps(metadata, indent=2), encoding='utf-8')
print(json.dumps({'stage':stage,'exit_code':metadata['exit_code'],'counts':metadata.get('counts'),'receipt':str(folder/'receipt.json')},ensure_ascii=False))
print((folder / 'stdout.log').read_text(encoding='utf-8', errors='replace')[-3000:])
print((folder / 'stderr.log').read_text(encoding='utf-8', errors='replace')[-1000:])
raise SystemExit(metadata['exit_code'])
