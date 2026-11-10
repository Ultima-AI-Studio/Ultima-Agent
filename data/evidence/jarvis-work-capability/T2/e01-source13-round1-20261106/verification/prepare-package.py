"""Seal the bounded E01 preparation only after final offline checks pass."""
from pathlib import Path
import ast
from collections import Counter
import datetime as dt
import difflib
import hashlib
import json
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PARENT = ROOT.parent / 'e03-source13-negative-20261106'
REPO = Path(r'H:\UltimaAI\UltimaAgent')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, data):
    assert not path.exists(), str(path)
    path.write_bytes((json.dumps(data, ensure_ascii=False, indent=2)+'\n').encode('utf-8'))


def git(path, *args):
    return subprocess.check_output(['git','-C',str(path),*args], text=True, encoding='utf-8').strip()


assert not (ROOT/'manifest.json').exists()
assert not (ROOT/'actual').exists() and not (ROOT/'release').exists()
final = load(ROOT/'verification/e01-final-green3.json')
assert final['exit_code'] == 0 and final['source_unchanged'] is True
assert final['counts'] == {'tests':208,'failures':0,'errors':0,'skipped':0}
guard_receipt = load(ROOT/'verification/e01-final-green3-io-guard.json')
assert guard_receipt['denied'] == guard_receipt['allowed'] == guard_receipt['open_owned_listeners'] == []
assert guard_receipt['final_exit'] == 0
sys.path.insert(0,str(ROOT/'code'))
import acceptance_entry as entry
import source_candidate_guard as candidate_guard
source = candidate_guard.verify_current_candidate()
assert source['code_gate'] == 'PASS' and source['candidate'] == entry.HEAD
bindings = entry.predecessor_reviews(ROOT)
assert len(bindings) == 4
runtime = load(ROOT/'inputs/candidate-runtime-manifest.json')
candidate = Path(runtime['candidate_root'])
assert git(candidate,'rev-parse','HEAD') == entry.HEAD
assert not git(candidate,'status','--porcelain','--untracked-files=no')
for label in ('manifest.json','verification/result-evidence-manifest.json'):
    for row in load(PARENT/label)['files']:
        path = PARENT/row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
pairs = []
for path in (ROOT/'inputs').rglob('*'):
    if path.is_file() and 'prior-negative' not in path.parts:
        original = PARENT/path.relative_to(ROOT)
        assert sha(path) == sha(original)
        pairs.append({'copy':str(path),'original':str(original),'sha256':sha(path)})
for name, original in [('terminal.json','actual/e03-negative/terminal.json'),
        ('review.json','independent-result-review.json'),('registration.json','verification/result-registration.json'),
        ('result-manifest.json','verification/result-evidence-manifest.json'),
        ('negative-evidence.json','actual/e03-negative/negative-evidence.json')]:
    path = ROOT/'inputs/prior-negative'/name
    assert sha(path) == sha(PARENT/original)
    pairs.append({'copy':str(path),'original':str(PARENT/original),'sha256':sha(path)})
assert sha(ROOT/'code/controller.py') == sha(PARENT/'code/controller.py')
assert sha(ROOT/'preparation-support/acceptance_adapter.py') == sha(PARENT/'preparation-support/acceptance_adapter.py')
for path in [*sorted((ROOT/'code').glob('*.py')), *sorted((ROOT/'preparation-support').glob('*.py'))]:
    ast.parse(path.read_text(encoding='utf-8-sig'))
parent_counts = Counter(x.get('classname') for x in ET.parse(PARENT/'verification/negative-final-green.xml').iter('testcase'))
current_counts = Counter(x.get('classname') for x in ET.parse(ROOT/'verification/e01-final-green3.xml').iter('testcase'))
save(ROOT/'verification/test-scope-map.json', {
    'parent_archived_counts':dict(parent_counts), 'current_fresh_counts':dict(current_counts),
    'current_total':208, 'parent_total':255,
    'excluded_parent_modules':load(ROOT/'verification/workspace-setup.json')['excluded_parent_test_modules'],
    'conversion':'Common admission/predecessor tests retain their purpose; valid positive path now expects E01, four prior E03 results and one CLI. New backend tests exercise real Case/file validators with fake native/process boundaries.',
    'limitation':'No UI, server, CLI, model, audio or E01 acceptance case was run; old product485/8 reports are source-bound history only.'})
diff = []
for path in sorted((ROOT/'code').glob('*.py')):
    old = PARENT/'code'/path.name
    before = old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else []
    diff.extend(difflib.unified_diff(before,path.read_text(encoding='utf-8-sig').splitlines(True),
        fromfile='parent/code/'+path.name,tofile='e01/code/'+path.name))
(ROOT/'verification/parent-to-e01.diff').write_text(''.join(diff),encoding='utf-8')
save(ROOT/'verification/static-readback.json', {
    'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'candidate_guard':source,
    'source_files':len(runtime['source_files']),'dependency_files':len(runtime['dependencies']),
    'sdk_files':sum(len(x['files']) for x in runtime['sdk_components'].values()),
    'candidate_tracked_clean':True,'input_original_pairs':pairs,'qualified_E03':bindings,
    'parent_141_sealed_files_unchanged':True,'unchanged_controller_and_adapter':True,
    'offline_tests':208,'model_calls':0,'actual_cases':0,'audio_actions':0,
    'authority_issued':False,'independent_preparation_review':'PENDING',
    'environment_claim':'Historical restored protected identities only. No claim of continuous availability; actual admission will require fresh proof.'})
ledger = ROOT/'progress.md'
ledger.write_text(ledger.read_text(encoding='utf-8')+
    '\nTask 1: complete — four E03 credentials checked before native construction; original 34 RED failures then34 PASS.\n'
    'Task 2: complete — no fixture/window action, existing server/CLI/file validators;14 path tests passed before added end-to-end guards.\n'
    'Task 3: complete — fresh208/208 offline suite, no skips; socket/process guard allowed0/denied0/open0. All prior failures retained. The final inherited assertion was changed from three predecessors to the exact four-case E03 chain.\n'
    'Task 4: in progress — seal and one fresh-context whole-package independent preparation review.\n'
    'Task 5: pending — no E01 authority, preflight, actual case, model or audio.\n',encoding='utf-8')
files = {ROOT/'plan.md',ROOT/'progress.md',ROOT/'review-brief.md'}
files.update(p for d in ('code','inputs','preparation-support') for p in (ROOT/d).rglob('*') if p.is_file())
files.update(p for p in (ROOT/'verification').iterdir() if p.is_file())
assert all(p.is_file() for p in files)
manifest = dict(schema=1,scope=entry.SCOPE,case=entry.CASE,package_root=str(ROOT),candidate=entry.HEAD,
    candidate_manifest_sha256=entry.CANDIDATE_MANIFEST,python_executable=str(entry.PYTHON),
    model=entry.MODEL,digest=entry.DIGEST,case_cap=1,product_cli_cap=1,audio_actions=0,
    retry_authorized=False,fixture_required=False,proof_max_age_seconds=60,admission_max_seconds=120,
    product_timeouts={'CLI':300,'SDK':1800,'controller_wait':315},
    execution_authorized=False,acceptance_credit_granted=False,actual_case_allocation=0,result_review_allocation=0,
    parent_manifest_sha256=sha(PARENT/'manifest.json'),
    parent_result_registration_sha256=sha(PARENT/'verification/result-registration.json'),
    prior_reviews=bindings,offline_tests=208,
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)])
save(ROOT/'manifest.json',manifest)
digest = entry.verify_package(ROOT)
save(ROOT/'verification/seal-readback.json',{'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'manifest_sha256':digest,'sealed_files':len(files),'verify_package':'PASS','actual_case_allocation':0,
    'result_review_allocation':0,'execution_authorized':False,'T2':'NOT_PASSED'})
print(json.dumps({'manifest_sha256':digest,'sealed_files':len(files),'offline_tests':208,
                  'source_files':len(runtime['source_files']),'dependency_files':len(runtime['dependencies']),
                  'sdk_files':sum(len(x['files']) for x in runtime['sdk_components'].values()),
                  'actual':False,'authority':False}))
