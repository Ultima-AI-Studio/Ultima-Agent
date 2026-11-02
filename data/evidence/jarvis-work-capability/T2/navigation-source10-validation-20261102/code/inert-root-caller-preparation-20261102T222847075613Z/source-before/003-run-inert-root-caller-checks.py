"""Fixed-interpreter preparation units and immutable source readback receipts."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import os
import subprocess
import sys

W = Path(__file__).resolve().parent
V = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102')
PY = Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')
NAMES = ('root-inert-invocation.py', 'test_root_inert_invocation.py', 'inert-root-release-template.json', 'inert-root-caller-manifest.json', 'run-inert-root-caller-checks.py')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def write(path, value):
    with path.open('x', encoding='utf8') as stream:
        json.dump(value, stream, indent=2)


def snapshot(run, stage):
    manifest = json.loads((W/'inert-root-caller-manifest.json').read_text('utf8'))
    expected = dict(manifest['dependencies'])
    expected.update({str(W/name): value for name, value in manifest['files'].items()})
    paths = set(expected) | {str(W/'inert-root-caller-manifest.json')}
    copies = run/('source-'+stage); copies.mkdir()
    actual = {}
    inventory = {}
    for index, name in enumerate(sorted(paths)):
        path = Path(name)
        raw = path.read_bytes()
        actual[name] = digest(raw)
        copy = copies/(str(index).zfill(3)+'-'+path.name)
        copy.write_bytes(raw)
        inventory[name] = dict(copy=str(copy), sha256=digest(raw), bytes=len(raw))
    write(run/('source-'+stage+'.json'), actual)
    write(run/('copies-'+stage+'.json'), inventory)
    mismatches = {p: dict(expected=h, actual=actual[p]) for p, h in expected.items() if actual[p] != h}
    return actual, mismatches


def main():
    if sys.argv[1:] or Path(sys.executable).resolve() != PY.resolve() or not sys.flags.dont_write_bytecode or sys.flags.utf8_mode != 1:
        raise ValueError('Fixed H Python -B -X utf8; no arguments')
    run = V/'code'/('inert-root-caller-preparation-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    run.mkdir(parents=True, exist_ok=False)
    before, drift_before = snapshot(run, 'before')
    for name in NAMES:
        if name.endswith('.py'):
            ast.parse((W/name).read_text('utf8'), filename=str(W/name))
    argv = [str(PY), '-B', '-X', 'utf8', '-m', 'pytest', str(W/'test_root_inert_invocation.py'), '-q', '-p', 'no:cacheprovider', '--basetemp='+str(run/'temp'), '--junitxml='+str(run/'junit.xml')]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', PYTHONIOENCODING='utf-8', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
               TEMP=str(run), TMP=str(run), OPENJARVIS_HOME=str(run/'owned-env/openjarvis'), HF_HOME=str(run/'owned-env/hf'), XDG_CACHE_HOME=str(run/'owned-env/cache'))
    code = None; error = None
    try:
        if drift_before:
            raise ValueError('Pinned source drift before tests')
        result = subprocess.run(argv, cwd=run, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=90)
        (run/'stdout.log').write_bytes(result.stdout); (run/'stderr.log').write_bytes(result.stderr)
        code = result.returncode
        print(result.stdout.decode('utf8'), end='')
        print(result.stderr.decode('utf8'), end='', file=sys.stderr)
    except Exception as exc:
        error = dict(type=type(exc).__name__, message=str(exc))
    after, drift_after = snapshot(run, 'after')
    unchanged = before == after and not drift_before and not drift_after
    exit_code = 0 if code == 0 and unchanged and error is None else 2
    write(run/'receipt.json', dict(argv=argv, cwd=str(run), exit_code=exit_code, pytest_exit_code=code,
          setup_error=error, inputs_unchanged=unchanged, drift_before=drift_before, drift_after=drift_after,
          source_before=str(run/'source-before.json'), source_after=str(run/'source-after.json'),
          source_count=len(before), candidate_input_count=64, harness_files=6, caller_files=5,
          junit=str(run/'junit.xml'), stdout=str(run/'stdout.log'), stderr=str(run/'stderr.log'),
          controlled_environment={k:env[k] for k in ('PYTHONDONTWRITEBYTECODE','PYTHONIOENCODING','PYTEST_DISABLE_PLUGIN_AUTOLOAD','TEMP','TMP','OPENJARVIS_HOME','HF_HOME','XDG_CACHE_HOME')},
          kind='pure-mocked-caller-preparation-only', actual=False, inert=False, model_calls=0, product_launches=0, T2='NOT_PASSED'))
    print('RECEIPT '+str(run/'receipt.json'))
    return exit_code


if __name__ == '__main__':
    raise SystemExit(main())
