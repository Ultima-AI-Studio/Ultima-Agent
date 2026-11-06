"""Fixed offline contracts only. This module has no runtime/profile entry."""
from __future__ import annotations
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
EVIDENCE_ROOT=HERE.parent/'code'
PY=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')


def sha(raw): return hashlib.sha256(raw).hexdigest()


def save(path,value):
    with path.open('xb') as stream:
        stream.write(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False).encode('utf8'))


def load_profile():
    spec=importlib.util.spec_from_file_location('profile_contract_definitions',HERE/'profile.py')
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def fingerprints(names): return {str(name):sha(Path(name).read_bytes()) for name in names}


def main(argv: list[str]) -> int:
    if argv!=['--contracts']:
        print('Only --contracts is supported. No runtime entry exists.')
        return 2
    stage=EVIDENCE_ROOT/('profile-preparation-contracts-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')+'-'+uuid.uuid4().hex[:8])
    stage.mkdir(parents=True,exist_ok=False); (stage/'snapshot').mkdir()
    receipt=dict(kind='full_fixed_contracts',qualification='OFFLINE_SYNTHETIC_CONTRACTS_ONLY',runtime_released=False,
        original_profile_runs=0,expected_count=None,actual_count=None,pytest_exit_code=None,exit_code=1,error_type=None)
    code=1
    try:
        if Path(sys.executable).resolve()!=PY.resolve() or not sys.flags.isolated or not sys.flags.dont_write_bytecode or not sys.flags.utf8_mode or sys.flags.optimize:
            raise ValueError('Fixed interpreter required')
        profile=load_profile(); pins=profile.read_pins(HERE/'manifest.json')
        expected=pins['test_ids']
        if (type(expected) is not list or not expected or len(set(expected))!=len(expected)
                or any(type(node) is not str or not node.startswith('test_profile.py::test_') for node in expected)):
            raise ValueError('Fixed test allowlist required')
        receipt['expected_count']=len(expected)
        names=[HERE/name for name in ('profile.py','test_profile.py','run_checks.py','manifest.json','README.md')]
        package_before=fingerprints(names); dependencies_before=fingerprints(pins['files'])
        for path in names: (stage/'snapshot'/path.name).write_bytes(path.read_bytes())
        save(stage/'dependencies-before.json',dependencies_before); save(stage/'package-before.json',package_before)
        config=stage/'pytest.ini'; config.write_text('[pytest]\n',encoding='utf8')
        command=[str(PY),'-B','-X','utf8','-I','-m','pytest','-q','test_profile.py',
            '-c',str(config),'--noconftest','--confcutdir='+str(HERE),'--rootdir='+str(HERE),'--import-mode=importlib',
            '--junitxml='+str(stage/'junit.xml'),'-o','cache_dir='+str(stage/'cache'),'--basetemp='+str(stage/'temp')]
        receipt['command']=command; receipt['interpreter']=str(PY)
        receipt['versions']={name:importlib.metadata.version(name) for name in ('pytest','httpx','openjarvis')}
        receipt['python']=sys.version
        (stage/'command.txt').write_text(subprocess.list2cmdline(command),encoding='utf8')
        env={key:value for key,value in os.environ.items() if not key.upper().startswith(('PYTHON','PYTEST_'))}
        env['PYTEST_DISABLE_PLUGIN_AUTOLOAD']='1'
        child=subprocess.run(command,cwd=HERE,env=env,capture_output=True)
        (stage/'stdout.txt').write_bytes(child.stdout); (stage/'stderr.txt').write_bytes(child.stderr)
        receipt['pytest_exit_code']=child.returncode
        dependencies_after=fingerprints(pins['files']); package_after=fingerprints(names)
        save(stage/'dependencies-after.json',dependencies_after); save(stage/'package-after.json',package_after)
        receipt['dependencies_count']=len(dependencies_before)
        receipt['dependencies_unchanged']=dependencies_before==dependencies_after
        receipt['package_unchanged']=package_before==package_after
        tree=ET.parse(stage/'junit.xml'); cases=tree.findall('.//testcase')
        actual=[]; failed=False
        for case in cases:
            if case.get('classname')!='test_profile': failed=True
            actual.append('test_profile.py::'+case.get('name',''))
            if any(case.find(kind) is not None for kind in ('failure','error','skipped')): failed=True
        receipt['actual_count']=len(actual)
        receipt['actual_test_ids']=actual
        receipt['allowlist_exact']=len(actual)==len(expected) and len(set(actual))==len(actual) and set(actual)==set(expected)
        eligible=child.returncode==0 and not failed and receipt['allowlist_exact'] and receipt['dependencies_unchanged'] and receipt['package_unchanged']
        receipt['raw_sha256']={name:sha((stage/name).read_bytes()) for name in ('command.txt','stdout.txt','stderr.txt','junit.xml','pytest.ini')}
        code=0 if eligible else 1
    except Exception as exc:
        code=1
        receipt['error_type']=type(exc).__name__[:80]
    receipt['exit_code']=code
    save(stage/'receipt.json',receipt)
    print(str(stage))
    return code


if __name__=='__main__':
    raise SystemExit(main(sys.argv[1:]))
