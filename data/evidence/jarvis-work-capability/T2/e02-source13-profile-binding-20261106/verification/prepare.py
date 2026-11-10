"""Create a new evidence-only binding baseline; never rewrite the old package."""
from pathlib import Path
import datetime as dt
import hashlib
import json

B = Path(__file__).resolve().parents[1]
T2 = B.parent
OLD = T2 / 'navigation-source10-validation-20261103-inert2'
PKG = B / 'profile-preparation'
CURRENT = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
OLD_ROOT = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent')
RUNTIME = T2 / 'e01-source13-round3-20261106/inputs/candidate-runtime-manifest.json'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def save(p, d):
    with p.open('x', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')


assert not PKG.exists()
assert sha(OLD / 'profile-preparation/manifest.json') == '06bb89c1955225fb37d31832ed9844c41200dc74dd57a15098ae7d6c7dad8dfb'
assert sha(RUNTIME) == '957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3'
for directory in (PKG, B / 'inputs', B / 'history', B / 'review', B / 'code'):
    directory.mkdir(parents=True, exist_ok=False)
old = load(OLD / 'profile-preparation/manifest.json')
history = []
for name in ('profile.py', 'test_profile.py', 'run_checks.py', 'README.md', 'manifest.json'):
    path = OLD / 'profile-preparation' / name
    if name != 'manifest.json': assert sha(path) == old['members'][name]
    (B / 'history' / name).write_bytes(path.read_bytes())
    history.append(dict(path=str(path), sha256=sha(path), bytes=path.stat().st_size))
for name in ('profile.py', 'test_profile.py', 'run_checks.py', 'README.md'):
    (PKG / name).write_bytes((B / 'history' / name).read_bytes())
(B / 'profile-adapter.py').write_bytes((OLD / 'harness/adapter.py').read_bytes())
(B / 'inputs/candidate-runtime-manifest.json').write_bytes(RUNTIME.read_bytes())
prior_paths = [T2 / 'e01-source13-round3-20261106/verification/result-registration.json',
               T2 / 'e03-source13-negative-20261106/verification/result-registration.json']
for index, path in enumerate(prior_paths):
    (B / 'inputs' / ('e01-registration.json' if index == 0 else 'e03-registration.json')).write_bytes(path.read_bytes())
runtime = load(RUNTIME)
assert runtime['candidate'] == '269aca511d88412dbb9c15d23911138469a37aa2'
files = {}
for name, digest in old['files'].items():
    path = Path(name)
    try: relative = path.relative_to(OLD_ROOT)
    except ValueError: relative = None
    if relative is not None and relative.parts[0] == 'src':
        path = CURRENT / relative; digest = sha(path)
    assert sha(path) == digest, str(path)
    files[str(path)] = digest
for group in ('source_files', 'dependencies'):
    for name, digest in runtime[group].items():
        assert sha(Path(name)) == digest, name
        files[name] = digest
for component in runtime['sdk_components'].values():
    for name, digest in component['files'].items():
        path = Path(component['root']) / name
        assert sha(path) == digest, str(path)
        files[str(path)] = digest
for path in (RUNTIME, B / 'inputs/candidate-runtime-manifest.json', *prior_paths,
             B / 'profile-adapter.py', B / 'inputs/e01-registration.json', B / 'inputs/e03-registration.json'):
    files[str(path)] = sha(path)
new = dict(old)
new.update(files=files, candidate_root=str(CURRENT), package_root=str(PKG), adapter=str(B / 'profile-adapter.py'),
           candidate_manifest_sha256=sha(RUNTIME), runtime_released=False,
           qualification='SOURCE13_BINDING_BASELINE_NOT_REVIEWED',
           control_implementation='SEPARATE_ROOT_TASK_NOT_INCLUDED',
           source13_binding=dict(parent_manifest_sha256=sha(OLD / 'profile-preparation/manifest.json'),
                                 historical_repairs=6, old_repair_sequence_reopened=False,
                                 actual_profile_runs=0, model_calls=0, root_entry_implemented=False))
new['members'] = {name: sha(PKG / name) for name in old['members']}
save(PKG / 'manifest.json', new)
save(B / 'history/baseline.json', dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    originals=history, old_manifest_sha256=sha(OLD / 'profile-preparation/manifest.json'),
    current_runtime_sha256=sha(RUNTIME), old_repair_sequence_reopened=False,
    previous_goal_turn='PROGRESS_E01_ROUND3_ACTUAL_AND_INDEPENDENT_REVIEW_REGISTERED',
    actual_or_model_authority=False))
save(B / 'inputs/preparation-scope.json', dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    controller='root', work_order='wo-ultimaagent-20261101-0021', scope='SOURCE13_PROFILE_BINDING_OFFLINE_ONLY',
    basis='User continuous-goal authorization and published E02 reentry plan; inline implementation.',
    candidate=runtime['candidate'], implementation_passes=1, new_diff_review_fix_passes=1,
    old_profile_algorithm_changes_allowed=False, historical_repairs=6, old_budget_reset=False,
    actual_case_cap=0, model_calls=0, profile_runs=0, UI_audio=0, service_operations=0,
    root_entry_implemented=False, independent_preparation_review_required=True))
print(json.dumps(dict(baseline=str(PKG), pinned_files=len(files), historical_tests=len(old['test_ids']),
                     product_calls=0, new_tests=0)))
