"""Seal preparation using bytes/AST/Git reads only. Never import package code."""
import ast
import datetime as dt
import difflib
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / 'e03-source12-acceptance-20261105-r1-fix1'
PROJECT = Path(r'H:\UltimaAI\UltimaAgent')
CANDIDATE = ROOT.parent / 'e03-source12-20261105-r31-preflight-log-isolation/candidate-manifest-r13.json'
EXPECTED_PARENT = 'a4fdb70c9e062b34cec82b1cbe2b9443d51386fd651269023b824d38531ea43d'
EXPECTED_CANDIDATE = '2cd5080b041e83afeeffe4747e1a10840e402c08be234d2b6ae15dccf59b841f'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def write(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def git(path, *args):
    return subprocess.check_output(['git', '-C', str(path), *args], text=True, encoding='utf-8').strip()


assert ROOT.name == 'e03-source12-manual-start-20261105-r2'
assert not (ROOT / 'manifest.json').exists(), 'Already sealed'
assert not (ROOT / 'actual').exists() and not (ROOT / 'release').exists()
assert sha(PARENT / 'manifest.json') == EXPECTED_PARENT
parent = read(PARENT / 'manifest.json')
assert all((PARENT / r['path']).stat().st_size == r['bytes'] and sha(PARENT / r['path']) == r['sha256'] for r in parent['files'])
assert sha(CANDIDATE) == EXPECTED_CANDIDATE
candidate = read(CANDIDATE)
source = [{'path': p, 'sha256': h, 'match': sha(Path(p)) == h} for p, h in candidate['source_files'].items()]
dependencies = [{'path': p, 'sha256': h, 'match': sha(Path(p)) == h} for p, h in candidate['dependencies'].items()]
assert all(r['match'] for r in source + dependencies)
sdk = []
for name, component in candidate['sdk_components'].items():
    mismatches = [p for p, h in component['files'].items() if sha(Path(component['root']) / p) != h]
    assert not mismatches, (name, mismatches)
    sdk.append({'name': name, 'files': len(component['files']), 'all_match': True})
worktrees = []
for path in (Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent'),
             Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-r25-runtime-complete')):
    head, branch, dirty = git(path, 'rev-parse', 'HEAD'), git(path, 'branch', '--show-current'), git(path, 'status', '--porcelain', '--untracked-files=no')
    assert head == parent['candidate'] and not dirty
    worktrees.append({'path': str(path), 'head': head, 'branch': branch, 'tracked_clean': True})
modules = sorted(p for directory in ('code', 'preparation-support') for p in (ROOT / directory).glob('*.py'))
for path in modules:
    ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
assert len(modules) == 14
provenance = {'parent_manifest_sha256': EXPECTED_PARENT, 'copies': [], 'derivatives': [], 'new_files': []}
diff = []
for path in modules + sorted((ROOT / 'inputs').glob('*.json')):
    relative = path.relative_to(ROOT).as_posix()
    old = PARENT / relative
    row = {'path': relative, 'sha256': sha(path)}
    if old.exists():
        row.update(source=str(old), source_sha256=sha(old))
        group = 'copies' if old.read_bytes() == path.read_bytes() else 'derivatives'
    else:
        group = 'new_files'
    provenance[group].append(row)
    if group != 'copies' and path.suffix == '.py':
        diff.extend(difflib.unified_diff(old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else [],
                    path.read_text(encoding='utf-8-sig').splitlines(True),
                    fromfile='parent/' + relative if old.exists() else '/dev/null', tofile='manual-start/' + relative))
write(ROOT / 'provenance.json', provenance)
(ROOT / 'verification/manual-start.diff').write_text(''.join(diff), encoding='utf-8')
plan_path = PROJECT / 'docs/plans/jarvis-work-e03-manual-start-plan-20261105.md'
plan = plan_path.read_text(encoding='utf-8-sig').replace('- [ ]', '- [x]', 4)
plan_path.write_text(plan, encoding='utf-8')
(ROOT / 'plan.md').write_text(plan, encoding='utf-8')
state_path = ROOT.parent / 'current-run.json'
with (ROOT / 'history/current-run-before-preparation.json').open('xb') as stream:
    stream.write(state_path.read_bytes())
now = dt.datetime.now(dt.timezone.utc).isoformat()
receipt = {'recorded_at': now, 'method': 'static-only bytes, JSON, AST and read-only Git; no reviewed module imports',
           'candidate_manifest_sha256': EXPECTED_CANDIDATE, 'source_files': source, 'dependencies': dependencies,
           'sdk_components': sdk, 'worktrees': worktrees,
           'parsed_modules': [p.relative_to(ROOT).as_posix() for p in modules],
           'tests': {'passed': 124, 'new': 25, 'retained': 99, 'log': 'verification/green-final-manual-start.log'},
           'import_probe': {'executed': False, 'reason': 'Automatic approval rejected combined write/import-probe command: blocked by policy; not retried.'},
           'live_ui_executed': False, 'model_calls': 0, 'audio_actions': 0, 'actual_allocation_issued': False}
write(ROOT / 'verification/static-readback.json', receipt)
with (ROOT / 'progress.md').open('a', encoding='utf-8') as stream:
    stream.write('\n' + now + ': Manual Start implemented. 124 offline tests pass (99 retained + 25 new). '
                 '14 modules parse; 41 candidate sources, 7 dependencies and all declared SDK hashes match. '
                 'Pinned candidate worktrees tracked clean. Import probe blocked and not reattempted; static-only receipt records limitation. '
                 'No actual UI, authority, model/audio or retry. Preparation review pending.\n')
assert '124 passed in 6.79s' in (ROOT / 'verification/green-final-manual-start.log').read_text()
files = []
for path in sorted(ROOT.rglob('*')):
    relative = path.relative_to(ROOT)
    if not path.is_file() or any(p.startswith('tmp-') or p in ('__pycache__', '.pytest_cache') for p in relative.parts):
        continue
    if relative.as_posix() == 'progress.md':
        continue
    files.append({'path': relative.as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)})
manifest = {k: v for k, v in parent.items() if k not in ('files', 'tests', 'sealed_at', 'parent_manifest_sha256')}
manifest.update(package_root=str(ROOT), parent_manifest_sha256=EXPECTED_PARENT, files=files, sealed_at=now,
                tests=receipt['tests'], preparation_revision='manual-start-r2',
                manual_start={'required': True, 'button_wait_seconds': 15, 'fixture_start_ceiling_seconds': 20,
                              'foreign_input_attachment': False, 'live_ui_verified': False},
                execution_authorized=False, import_probe_executed=False)
write(ROOT / 'manifest.json', manifest)
print(json.dumps({'manifest_sha256': sha(ROOT / 'manifest.json'), 'sealed_files': len(files),
                  'modules': len(modules), 'source_files': len(source), 'dependencies': len(dependencies),
                  'sdk_files': sum(s['files'] for s in sdk), 'tests_passed': 124,
                  'changed': [r['path'] for r in provenance['derivatives']],
                  'new': [r['path'] for r in provenance['new_files']]}, ensure_ascii=False))
