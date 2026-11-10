"""Seal round2 preparation after offline checks, without issuing live authority."""
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
PARENT = ROOT.parent / 'e01-source13-round1-20261106'
TESTS = 252
LABEL = 'round2-final-green'


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
final = load(ROOT/'verification'/(LABEL+'.json'))
assert final['exit_code'] == 0 and final['source_unchanged'] is True
assert final['counts'] == {'tests':TESTS,'failures':0,'errors':0,'skipped':0}
guard = load(ROOT/'verification'/(LABEL+'-io-guard.json'))
assert guard['denied'] == guard['allowed'] == guard['open_owned_listeners'] == [] and guard['final_exit'] == 0
sys.path.insert(0,str(ROOT/'code'))
import acceptance_entry as entry
import source_candidate_guard as candidate_guard
source = candidate_guard.verify_current_candidate()
assert source['code_gate'] == 'PASS' and source['candidate'] == entry.HEAD
bindings = entry.predecessor_reviews(ROOT)
assert [x['case'] for x in bindings] == ['e03-round1','e03-round2','e03-round3','e03-negative','e01-round1']
runtime = load(ROOT/'inputs/candidate-runtime-manifest.json')
candidate = Path(runtime['candidate_root'])
assert git(candidate,'rev-parse','HEAD') == entry.HEAD
assert not git(candidate,'status','--porcelain','--untracked-files=no')
parent_seals = {}
for label in ('manifest.json','verification/result-evidence-manifest.json'):
    parent = load(PARENT/label)
    for row in parent['files']:
        path = PARENT/row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
    parent_seals[label] = {'sha256':sha(PARENT/label),'files':len(parent['files']),'unchanged':True}
pairs = []
for path in sorted((ROOT/'inputs').rglob('*')):
    if path.is_file() and 'prior-e01-round1' not in path.parts:
        original = PARENT/path.relative_to(ROOT)
        assert sha(path) == sha(original)
        pairs.append({'copy':str(path),'original':str(original),'sha256':sha(path)})
for name, original in [('terminal.json','actual/e01-round1/terminal.json'),
        ('review.json','review/independent-result-review.json'),('registration.json','verification/result-registration.json')]:
    path = ROOT/'inputs/prior-e01-round1'/name
    assert sha(path) == sha(PARENT/original)
    pairs.append({'copy':str(path),'original':str(PARENT/original),'sha256':sha(path)})
unchanged = ['code/acceptance_backend.py','code/controller.py','code/package_io.py',
             'code/fixture_adapter.py','code/fixture_input_origin.py','code/fixture_manual_start.py',
             'preparation-support/acceptance_adapter.py']
for name in unchanged:
    assert sha(ROOT/name) == sha(PARENT/name), name
for path in [*sorted((ROOT/'code').glob('*.py')), *sorted((ROOT/'preparation-support').glob('*.py'))]:
    ast.parse(path.read_text(encoding='utf-8-sig'))
parent_counts = Counter(x.get('classname') for x in ET.parse(PARENT/'verification/e01-final-green3.xml').iter('testcase'))
current_counts = Counter(x.get('classname') for x in ET.parse(ROOT/'verification'/(LABEL+'.xml')).iter('testcase'))
assert all(current_counts[name] >= count for name,count in parent_counts.items())
save(ROOT/'verification/test-scope-map.json', {
    'parent_archived_counts':dict(parent_counts),'current_fresh_counts':dict(current_counts),
    'parent_total':208,'current_total':TESTS,'excluded_parent_modules':[],
    'new_tests':44,'prerequisite_behavior_red':{'tests':38,'failures':38,'errors':0},
    'first_collection_syntax_error_retained':True,
    'conversion':'All 208 inherited checks retained. Positive scope/path changes to round2; exact ordered authority grows from E03 four credentials to five including E01 round1. E03 unit validator renamed without weakening its four-case assertions.',
    'new_coverage':'38 E01 round1 qualification cases; two old-round authority rejections; three unsealed dependency rejections and one coherent failed-review rejection before backend construction.',
    'limitation':'No live UI, server, CLI, model, audio or round2 acceptance case. Archived product485/8 results are source-bound history only.'})
diff = []
for path in sorted((ROOT/'code').glob('*.py')):
    old = PARENT/'code'/path.name
    before = old.read_text(encoding='utf-8-sig').splitlines(True) if old.exists() else []
    diff.extend(difflib.unified_diff(before,path.read_text(encoding='utf-8-sig').splitlines(True),
        fromfile='round1/code/'+path.name,tofile='round2/code/'+path.name))
(ROOT/'verification/parent-to-round2.diff').write_text(''.join(diff),encoding='utf-8')
save(ROOT/'verification/static-readback.json', {
    'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),'candidate_guard':source,
    'source_files':len(runtime['source_files']),'dependency_files':len(runtime['dependencies']),
    'sdk_files':sum(len(x['files']) for x in runtime['sdk_components'].values()),
    'candidate_tracked_clean':True,'input_original_pairs':pairs,'qualified_predecessors':bindings,
    'parent_seals':parent_seals,'unchanged_parent_runtime_files':unchanged,
    'offline_tests':TESTS,'model_calls':0,'actual_cases':0,'audio_actions':0,
    'authority_issued':False,'independent_preparation_review':'PENDING',
    'environment_claim':'Historical restored protected identities only; fresh native proof is required for any future admission.'})
ledger = ROOT/'progress.md'
ledger.write_text(ledger.read_text(encoding='utf-8')+
    '\nTask 1 complete: first collection syntax error retained, corrected test collection then38 behavioral RED failures, then38 GREEN. Eligible E01 round1 terminal/review/registration required after E03 chain.\n'
    'Task 2 complete: scope/root switched to round2; all five credentials bound; parent backend/controller/adapter unchanged.\n'
    'Task 3 complete:252 fresh offline checks PASS, no skips; guard allowed0/denied0/open0; all208 inherited semantics retained.\n'
    'Task 4 in progress: source bindings verified; package seal then one fresh independent preparation review.\n'
    'Task 5 pending: docs/mirror/local checkpoint; actual and result-review allocations remain0.\n',encoding='utf-8')
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
    prior_reviews=bindings,offline_tests=TESTS,
    files=[dict(path=p.relative_to(ROOT).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(files)])
save(ROOT/'manifest.json',manifest)
digest = entry.verify_package(ROOT)
save(ROOT/'verification/seal-readback.json',{'recorded_at':dt.datetime.now(dt.timezone.utc).isoformat(),
    'manifest_sha256':digest,'sealed_files':len(files),'verify_package':'PASS','actual_case_allocation':0,
    'result_review_allocation':0,'execution_authorized':False,'T2':'NOT_PASSED'})
print(json.dumps({'manifest_sha256':digest,'sealed_files':len(files),'offline_tests':TESTS,
                  'source_files':len(runtime['source_files']),'dependency_files':len(runtime['dependencies']),
                  'sdk_files':sum(len(x['files']) for x in runtime['sdk_components'].values()),
                  'actual':False,'authority':False}))
