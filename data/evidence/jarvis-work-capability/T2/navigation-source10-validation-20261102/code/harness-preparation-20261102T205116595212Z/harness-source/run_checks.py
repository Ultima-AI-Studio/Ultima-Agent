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

def snapshot():
    m = json.loads((V/'source10-candidate-manifest.json').read_text('utf8'))
    files = dict(m['source_files'], **m['sdk22'], **m['dependencies'])
    files[m['model']['policy_path']] = m['model']['policy_sha256']
    files[m['model']['local_manifest_path']] = m['model']['local_manifest_observed_sha256']
    files[str(V/'harness-preparation-authority.json')] = '0e8c2e273bc2a4c35d0fd01e4c0022955609cb4bcecc2ec1f47d3bf95cdd5418'
    files[str(V/'source10-candidate-manifest.json')] = 'cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
    files[str(V/'harness-deadline-design/root-decision.json')]='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
    report=Path(m['candidate_root'])/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-4-navigation-adapter-report.md'
    if hashlib.sha256(report.read_bytes()[:13665]).hexdigest()!='47246ba87216f07d696a7bb2b1bb38d525fa7c99eb83a72e694552090dc3c2c1': raise ValueError('Original author report prefix drift')
    actual = {p: digest(p) for p in files}
    if actual != files:
        raise ValueError('Pinned preparation input drift')
    return actual

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
    argv = [str(PY), '-B', '-X', 'utf8', '-m', 'pytest', str(HERE/'test_adapter.py'), '-q', '-p', 'no:cacheprovider', '--basetemp='+str(run/'temp'), '--junitxml='+str(run/'harness/adapter.xml')]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1', TEMP=str(run), TMP=str(run),OPENJARVIS_HOME=str(run/'owned-env/openjarvis'),HF_HOME=str(run/'owned-env/hf'),XDG_CACHE_HOME=str(run/'owned-env/cache'))
    result = subprocess.run(argv,cwd=run,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=90)
    (run/'stdout.log').write_bytes(result.stdout)
    (run/'stderr.log').write_bytes(result.stderr)
    after_error=None
    try: after = snapshot()
    except Exception as exc: after={'snapshot_error':str(exc)}; after_error=type(exc).__name__
    (run/'source-after.json').write_text(json.dumps(after,indent=2),encoding='utf8')
    harness_after={name:digest(HERE/name) if (HERE/name).is_file() else None for name in sorted(names)}
    members_after={p.name for p in HERE.iterdir() if p.is_file()}
    unchanged=harness_before==harness_after and members_after==names
    exit_code=result.returncode if unchanged and before==after and after_error is None else 2
    receipt = dict(argv=argv,cwd=str(run),exit_code=exit_code,pytest_exit_code=result.returncode,snapshot_after_error=after_error,inputs_unchanged=before==after,harness_before=harness_before,harness_after=harness_after,harness_members_after=sorted(members_after),harness_unchanged=unchanged,controlled_environment={key:env[key] for key in ('PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING','PYTEST_DISABLE_PLUGIN_AUTOLOAD','TEMP','TMP')},kind='mocked-boundary-unit-only',inert=False,actual=False,model_calls=0,product_launches=0,T2='NOT_PASSED',files=harness_after)
    (run/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf8')
    print(result.stdout.decode('utf8'),end='')
    print(result.stderr.decode('utf8'),end='',file=sys.stderr)
    print('RECEIPT '+str(run/'receipt.json'))
    return exit_code

if __name__ == '__main__':
    raise SystemExit(main())
