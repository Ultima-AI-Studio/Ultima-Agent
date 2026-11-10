"""Named offline contracts; this runner cannot launch a product or native worker."""
from pathlib import Path
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET

CODE=Path(__file__).resolve().parent
ROOT=CODE.parent
PY=Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def save(path, value):
    with path.open('x',encoding='utf-8') as stream: json.dump(value,stream,ensure_ascii=False,indent=2)


def main():
    if len(sys.argv)<3 or sys.argv[1]!='--stage' or not re.fullmatch('[a-z0-9-]{1,60}',sys.argv[2]):
        raise ValueError('Named offline stage required')
    if Path(sys.executable).resolve()!=PY.resolve() or not sys.flags.isolated or not sys.flags.dont_write_bytecode or not sys.flags.utf8_mode or sys.flags.optimize:
        raise ValueError('Pinned isolated Python required')
    stage=ROOT/'offline'/sys.argv[2]; stage.mkdir(parents=True,exist_ok=False)
    (stage/'snapshot').mkdir()
    names=sys.argv[3:] or ['test_native_observation.py','test_controls.py','test_entry.py']
    allowed={'test_native_observation.py','test_controls.py','test_entry.py'}
    if any(name.split('::',1)[0] not in allowed for name in names): raise ValueError('Fixed test files only')
    source=json.loads((ROOT/'inputs/source-bindings.json').read_bytes())['files']
    before={row['path']:sha(Path(row['path'])) for row in source}
    if any(before[row['path']]!=row['sha256'] for row in source): raise ValueError('Frozen source drift')
    package={p.name:sha(p) for p in CODE.glob('*.py')}
    for name in package:(stage/'snapshot'/name).write_bytes((CODE/name).read_bytes())
    config=stage/'pytest.ini';config.write_text('[pytest]\n',encoding='utf-8')
    command=['-q',*names,'-c',str(config),'--noconftest','--confcutdir='+str(CODE),
             '--rootdir='+str(CODE),'--import-mode=importlib','--junitxml='+str(stage/'junit.xml'),
             '-o','cache_dir='+str(stage/'cache'),'--basetemp='+str(stage/'temp')]
    save(stage/'command.json',dict(interpreter=str(PY),argv=sys.argv,pytest=command,cwd=str(CODE)))
    denied=[]
    def guard(event,args):
        if (event.startswith(('socket.','subprocess.')) and event!='socket.gethostname') or event in ('os.system','os.startfile','os.startfile/2','os.posix_spawn','os.spawn'):
            denied.append(event);raise RuntimeError('Offline I/O denied: '+event)
    sys.addaudithook(guard)
    for key in tuple(os.environ):
        if key.startswith('PYTEST_'):os.environ.pop(key)
    os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
    sys.path.insert(0,str(CODE));os.chdir(CODE)
    import pytest
    inventory=[]
    class Inventory:
        def pytest_collection_finish(self,session):inventory.extend(item.nodeid for item in session.items)
    start=dt.datetime.now(dt.timezone.utc).isoformat()
    with (stage/'stdout.txt').open('w',encoding='utf-8') as out,(stage/'stderr.txt').open('w',encoding='utf-8') as err:
        with contextlib.redirect_stdout(out),contextlib.redirect_stderr(err):code=int(pytest.main(command,plugins=[Inventory()]))
    save(stage/'inventory.json',inventory)
    cases=ET.parse(stage/'junit.xml').findall('.//testcase')
    counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
                errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
    after={row['path']:sha(Path(row['path'])) for row in source}
    package_after={p.name:sha(p) for p in CODE.glob('*.py')}
    save(stage/'inputs-before.json',before);save(stage/'inputs-after.json',after)
    receipt=dict(scope='OFFLINE_SYNTHETIC_CONTRACTS_ONLY',started_at=start,finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
        exit_code=code,counts=counts,inventory_count=len(inventory),sources_unchanged=before==after,package_unchanged=package==package_after,
        package_before=package,package_after=package_after,denied_python_io=denied,OS_native_activity=None,
        original_profile_runs=0,model_calls=0,runtime_authority=False,
        raw_sha256={name:sha(stage/name) for name in ('command.json','stdout.txt','stderr.txt','junit.xml','inventory.json','pytest.ini')})
    save(stage/'receipt.json',receipt)
    print(json.dumps(dict(stage=str(stage),exit_code=code,counts=counts,sources_unchanged=before==after,package_unchanged=package==package_after,denied=denied)))
    return code if before==after and package==package_after and not denied else 2


if __name__=='__main__':raise SystemExit(main())
