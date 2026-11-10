"""Run one named offline stage; keep every result and immutable input snapshot."""
from pathlib import Path
import contextlib
import datetime as dt
import hashlib
import importlib.util
import json
import os
import sys
import xml.etree.ElementTree as ET

B = Path(__file__).resolve().parents[1]
PKG = B / 'profile-preparation'
PY = Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
CHOICES = {
    'binding-red': 'source13_admission_candidate or source13_adapter_bound_candidate or source13_adapter_has_no_legacy_entry',
    'binding-focused-green': 'source13_',
    'binding-inventory': None,
    'binding-full-green': None,
}


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def save(p, d):
    with p.open('x', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')


assert len(sys.argv) == 2 and sys.argv[1] in CHOICES
label = sys.argv[1]
assert Path(sys.executable).resolve() == PY.resolve()
assert sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.utf8_mode and not sys.flags.optimize
stage = B / 'code' / label
stage.mkdir(exist_ok=False)
(stage / 'snapshot').mkdir()
manifest = load(PKG / 'manifest.json')
names = [PKG / name for name in ('profile.py', 'test_profile.py', 'run_checks.py', 'README.md', 'manifest.json')]
names += [B / 'profile-adapter.py', Path(__file__), Path(__file__).with_name('offline_guards.py')]
for path in names:
    (stage / 'snapshot' / path.name).write_bytes(path.read_bytes())
before = {name: sha(Path(name)) for name in manifest['files']}
package_before = {str(path): sha(path) for path in names}
save(stage / 'dependencies-before.json', before)
config = stage / 'pytest.ini'
config.write_text('[pytest]\n', encoding='utf-8')
os.environ['PYTEST_DISABLE_PLUGIN_AUTOLOAD'] = '1'
os.chdir(PKG)
args = ['-q', 'test_profile.py', '-c', str(config), '--noconftest', '--confcutdir=' + str(PKG),
        '--rootdir=' + str(PKG), '--import-mode=importlib', '--junitxml=' + str(stage / 'junit.xml'),
        '-o', 'cache_dir=' + str(stage / 'cache'), '--basetemp=' + str(stage / 'temp')]
if CHOICES[label]: args += ['-k', CHOICES[label]]
if label == 'binding-inventory': args.append('--collect-only')
save(stage / 'command.json', dict(executable=sys.executable, python_flags=['-B', '-X', 'utf8', '-I'],
                                runner=str(Path(__file__).resolve()), args=args, cwd=str(PKG)))
spec = importlib.util.spec_from_file_location('binding_offline_guards', Path(__file__).with_name('offline_guards.py'))
guard = importlib.util.module_from_spec(spec); spec.loader.exec_module(guard)
import pytest
inventory = []


class Inventory:
    def pytest_collection_finish(self, session):
        inventory.extend(item.nodeid for item in session.items)


guard.install()
started = dt.datetime.now(dt.timezone.utc).isoformat()
with (stage / 'stdout.txt').open('w', encoding='utf-8') as out, (stage / 'stderr.txt').open('w', encoding='utf-8') as err:
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = int(pytest.main(args, plugins=[Inventory()]))
after = {name: sha(Path(name)) for name in manifest['files']}
package_after = {str(path): sha(path) for path in names}
save(stage / 'dependencies-after.json', after)
save(stage / 'inventory.json', inventory)
tree = ET.parse(stage / 'junit.xml')
cases = tree.findall('.//testcase')
counts = dict(tests=len(cases), failures=sum(case.find('failure') is not None for case in cases),
              errors=sum(case.find('error') is not None for case in cases),
              skipped=sum(case.find('skipped') is not None for case in cases))
io = guard.receipt()
final_code = code if before == after and package_before == package_after and not io['denied'] else 1
save(stage / 'receipt.json', dict(scope='OFFLINE_SYNTHETIC_CONTRACTS_ONLY', stage=label,
    started_at=started, finished_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    pytest_exit_code=code, exit_code=final_code, counts=counts, inventory_count=len(inventory),
    dependencies_count=len(before), dependencies_unchanged=before == after, package_unchanged=package_before == package_after,
    package_before=package_before, package_after=package_after, io_guard=io,
    product_cli_runs=0, original_profile_runs=0, model_calls=0, runtime_released=False,
    raw_sha256={name: sha(stage / name) for name in ('stdout.txt', 'stderr.txt', 'junit.xml', 'inventory.json', 'command.json')}))
print(json.dumps(dict(stage=label, counts=counts, inventory_count=len(inventory), exit_code=final_code,
                     dependency_drift=before != after, denied=io['denied'])))
raise SystemExit(final_code)
