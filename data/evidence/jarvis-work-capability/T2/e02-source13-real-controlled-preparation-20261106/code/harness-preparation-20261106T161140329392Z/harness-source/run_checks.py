"""Fixed-interpreter isolated deterministic units; writes only new receipts."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

HERE = Path(__file__).resolve().parent
V = HERE.parent
PY = Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')

def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()

FROZEN_FIXTURE = Path('H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0')
FROZEN_FILES = {'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\accepted-effects.json': 'b18842f04d71e0a5126dfba9067cae2bb5a4418c1250247dc44f955ad01c2b56', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\audit.db': '00d17ada6802a5251b5f2bd0bc07f647f421ca18f70315bad4a7ddfbd94bb996', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\external-artifacts.json': '147adc38e79767c967750214bb1d37e0d24a1db3a360920c75ea274e7870975d', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\external-readback-attempts.json': 'ea94c4d37a3a543c668eee1b370f494ab0612f450182c815eb8b5219fd479dc1', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\outputs\\e0a1433f-f9a6-4148-a25e-d908898ec846\\research.md': 'd02d4922394a206a6dcbaf4c4ec1d814d557e0a93f46757e84e5d93cc56e6f53', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\runtime-inputs.json': 'd46a24a07a2d92fb02108e586ca514f6b47d146084b8b1682549614f6bf1c911', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\service-first-result.json': '887334f2e147e813a0f55e59cdd52406ca5dc2c2b73f2cdf820d2ffe50cf4267', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\trusted-collection.raw': 'c5ec8c993bae1f54e2b950ba101daa7f31894cd06a4a3f4f57912b09164b7c64', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\trusted-export.json': 'a19afa70e6c580b1f9b0976fb2922cdd85080f1d50b2cd693195c478f1d72b95', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\trusted-replay.raw': '2d3c01c37de1ab46f9ca8ab181785af4bb1dc1d8b31823fb58d012617f5cf3a6', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\trusted-runtime.raw': '5224d589d1908e6c9981f9b15b2eeb7c8ce3d344a5304c0b573553a453682106', 'H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0\\trusted-views.raw': '97b624903d6ed8db00226c05a9c88aecafe6dc3504ed93426a71e5f0379bbb24'}

def snapshot():
    import importlib.util
    spec=importlib.util.spec_from_file_location('source13_snapshot_adapter',HERE/'adapter.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    files=module.check_inputs()
    for path,digest_value in FROZEN_FILES.items():
        if digest(path)!=digest_value:raise ValueError('Historical synthetic fixture drift')
        files[path]=digest_value
    return files

def main():
    if sys.argv[1:] != ['adapter'] or Path(sys.executable).resolve() != PY.resolve() or not sys.flags.dont_write_bytecode or sys.flags.utf8_mode != 1:
        raise ValueError('Fixed H Python -B -X utf8 and adapter required')
    before = snapshot()
    for path in HERE.glob('*.py'): ast.parse(path.read_text('utf8'),filename=str(path))
    run = V/'code'/('harness-preparation-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir(parents=True, exist_ok=False)
    (run/'harness').mkdir()
    (run/'harness-source').mkdir()
    names={'adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json'}
    if {p.name for p in HERE.iterdir() if p.is_file()}!=names: raise ValueError('Exact six harness files required')
    harness_before={}
    for name in sorted(names):
        raw=(HERE/name).read_bytes(); (run/'harness-source'/name).write_bytes(raw)
        harness_before[name]=hashlib.sha256(raw).hexdigest()
    (run/'source-before.json').write_text(json.dumps(before,indent=2),encoding='utf8')
    guard=V/'verification/offline_pytest.py'
    guard_before=digest(guard)
    (run/'harness-source/offline_pytest.py').write_bytes(guard.read_bytes())
    argv = [str(PY), '-I', '-B', '-X', 'utf8', str(guard), str(HERE/'test_adapter.py'), '-q', '-p', 'no:cacheprovider', '--basetemp='+str(run/'temp'), '--junitxml='+str(run/'harness/adapter.xml')]
    env = {key:value for key,value in os.environ.items() if not key.upper().endswith('_PROXY') and not key.upper().startswith(('OLLAMA_','OPENJARVIS_','PYTHON','PYTEST','ULTIMA_ADAPTER_'))}
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', TEMP=str(run), TMP=str(run),OPENJARVIS_HOME=str(run/'owned-env/openjarvis'),HF_HOME=str(run/'owned-env/hf'),XDG_CACHE_HOME=str(run/'owned-env/cache'))
    result = subprocess.run(argv,cwd=run,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90,creationflags=subprocess.CREATE_NO_WINDOW)
    (run/'stdout.log').write_bytes(result.stdout)
    (run/'stderr.log').write_bytes(result.stderr)
    after_error=None
    try: after = snapshot()
    except Exception as exc: after={'snapshot_error':str(exc)}; after_error=type(exc).__name__
    (run/'source-after.json').write_text(json.dumps(after,indent=2),encoding='utf8')
    harness_after={name:digest(HERE/name) if (HERE/name).is_file() else None for name in sorted(names)}
    members_after={p.name for p in HERE.iterdir() if p.is_file()}
    unchanged=harness_before==harness_after and members_after==names and digest(guard)==guard_before
    exit_code=result.returncode if unchanged and before==after and after_error is None else 2
    receipt = dict(argv=argv,cwd=str(run),exit_code=exit_code,pytest_exit_code=result.returncode,snapshot_after_error=after_error,inputs_unchanged=before==after,harness_before=harness_before,harness_after=harness_after,harness_members_after=sorted(members_after),harness_unchanged=unchanged,controlled_environment={key:env[key] for key in ('PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING','PYTEST_DISABLE_PLUGIN_AUTOLOAD','TEMP','TMP','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME')},kind='mocked-boundary-unit-only',inert=False,actual=False,model_calls=0,product_launches=0,T2='NOT_PASSED',files=harness_after)
    (run/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(result.stdout.decode('utf8'),end='')
    print(result.stderr.decode('utf8'),end='',file=sys.stderr)
    print('RECEIPT '+str(run/'receipt.json'))
    return exit_code

if __name__ == '__main__':
    raise SystemExit(main())
