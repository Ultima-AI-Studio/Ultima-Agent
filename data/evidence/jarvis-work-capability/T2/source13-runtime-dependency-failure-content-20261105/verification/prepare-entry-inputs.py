"""Prepare a new case package, without issuing or consuming live authority."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

BASE = Path(r'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2')
OLD = BASE / 'e03-source12-input-guidance-20261105-r3'
FIX = BASE / 'source13-runtime-dependency-failure-content-20261105'
NEW = BASE / 'e03-source13-runtime-fix-20261105-r1'
ROOT = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
load = lambda p: json.loads(Path(p).read_text(encoding='utf8'))


def save(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf8')


assert not NEW.exists()
assert sha(OLD / 'manifest.json') == '0195699e7fe521d9aaa5da8ec01bedb53533cdc3a2364ea42496f142f6d07352'
parent = load(OLD / 'manifest.json')
for directory in ('code', 'inputs', 'preparation-support', 'verification', 'history'):
    (NEW / directory).mkdir(parents=True)
copies = []
for item in parent['files']:
    relative = item['path']
    if relative.split('/')[0] not in ('code', 'preparation-support', 'inputs'):
        continue
    source, target = OLD / relative, NEW / relative
    assert source.stat().st_size == item['bytes'] and sha(source) == item['sha256']
    target.write_bytes(source.read_bytes())
    copies.append({'path': relative, 'parent_sha256': item['sha256']})
for name in ('manifest.json', 'independent-preparation-review.json', 'independent-result-review.json'):
    (NEW / 'history' / ('r3-' + name)).write_bytes((OLD / name).read_bytes())
fix = load(FIX / 'candidate-manifest.json')
old_manifest = load(fix['parent_manifest_path'])
sources = {**fix['source_files'], **load(FIX / 'verification/original-gates/supplemental-inputs.json')['source_files']}
assert all(sha(p) == value for p, value in sources.items())
corpus = ROOT / 'src/brain/tests/fixtures/work_capability/acceptance-cases.json'
old_corpus = Path(old_manifest['candidate_root']) / corpus.relative_to(ROOT)
assert corpus.read_bytes() == old_corpus.read_bytes()
save(NEW / 'inputs/corpus-readback.json', {'candidate': fix['candidate'], 'original_path': str(old_corpus),
     'candidate_path': str(corpus), 'sha256': sha(corpus), 'unchanged': True,
     'recorded_at': datetime.now(timezone.utc).isoformat()})
gate = FIX / 'code-verdict.json'
report = Path(load(gate)['report_path'])
full = FIX / 'verification/original-gates/covering-isolated/receipt.json'
compat = FIX / 'verification/original-gates/compat/receipt.json'
protected = FIX / 'verification/original-gates-protected-readback.json'
manifest = dict(schema_version=1, scope='source13 E03 round1 candidate with restored runtime dependency and truthful failure content',
    candidate=fix['candidate'], candidate_root=str(ROOT), branch=fix['branch'], source_files=sources,
    dependencies=fix['dependencies'], sdk_components=fix['sdk_components'], model=fix['model'],
    code_gate={'path': str(gate), 'sha256': sha(gate), 'report_path': str(report), 'report_sha256': sha(report)},
    final_code_tests={'covering':485, 'compat':8, 'full_receipt':str(full), 'full_sha256':sha(full),
                      'compat_receipt':str(compat), 'compat_sha256':sha(compat)},
    original_corpus_readback=str(NEW/'inputs/corpus-readback.json'),
    original_corpus_readback_sha256=sha(NEW/'inputs/corpus-readback.json'),
    last_protected_readback=str(protected), last_protected_readback_sha256=sha(protected),
    historical_source21_path=old_manifest['historical_source21_path'],
    historical_source21_sha256=old_manifest['historical_source21_sha256'],
    code_review_manifest_path=str(FIX/'candidate-manifest.json'), code_review_manifest_sha256=sha(FIX/'candidate-manifest.json'),
    parent_case_manifest_sha256=sha(OLD/'manifest.json'), source_revision=13,
    actual_cases=0, actual_release=False, acceptance_credit=False)
candidate_path = NEW / 'inputs/candidate-runtime-manifest.json'
save(candidate_path, manifest)
bindings = {
    'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-r25-runtime-complete': ROOT.as_posix(),
    'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-source12-20261105-r31-preflight-log-isolation/candidate-manifest-r13.json': candidate_path.as_posix(),
    '2cd5080b041e83afeeffe4747e1a10840e402c08be234d2b6ae15dccf59b841f': sha(candidate_path),
    '7975e477665c02820fa235b73d203718bd33b2c9': fix['candidate'],
    'codex/jarvis-work-navigation-v3-source12-r25-runtime': fix['branch'],
}
for relative in ('code/source_candidate_guard.py', 'code/acceptance_entry.py', 'preparation-support/acceptance_adapter.py'):
    path = NEW / relative
    content = path.read_text(encoding='utf8')
    for old, new in bindings.items():
        content = content.replace(old, new)
    if relative == 'code/source_candidate_guard.py':
        content = content.replace('fixed source12 focus-handoff candidate', 'fixed source13 dependency/content candidate')
        content = content.replace('tests.get("covering") == 479', 'tests.get("covering") == 485')
        content = content.replace('"source10 covering receipt", 479', '"source10 covering receipt", 485')
    if relative == 'code/acceptance_entry.py':
        content = content.replace("'inputs/protected-baseline.json'}", "'inputs/protected-baseline.json', 'inputs/candidate-runtime-manifest.json'}")
    path.write_text(content, encoding='utf8')
controller = NEW / 'code/controller.py'
content = controller.read_text(encoding='utf8')
assert content.count('641a77d4d48ccfaf9659766f29283abea878c3b3ce7ebfd4831cca8b34c751cc') == 1
controller.write_text(content.replace('641a77d4d48ccfaf9659766f29283abea878c3b3ce7ebfd4831cca8b34c751cc',
                                      sha(NEW/'preparation-support/acceptance_adapter.py')), encoding='utf8')
(NEW / '.gitignore').write_text('verification/tmp-*/\nverification/env-*/\n__pycache__/\n.pytest_cache/\n', encoding='utf8')
save(NEW / 'provenance.json', {'recorded_at':datetime.now(timezone.utc).isoformat(),
    'parent_root':str(OLD), 'parent_manifest_sha256':sha(OLD/'manifest.json'), 'copied_files':copies,
    'candidate':fix['candidate'], 'candidate_runtime_manifest_sha256':sha(candidate_path),
    'source_fix_manifest_sha256':sha(FIX/'candidate-manifest.json'),
    'case_cap_proposed':1, 'new_authority_issued':False, 'actual_cases':0,
    'binding_changes':bindings,
    'constraints':'Original fixture, manual Start, deadlines, cleanup and factual review gates retained; no old authority copied'})
print(json.dumps({'package_root':str(NEW), 'candidate_manifest_sha256':sha(candidate_path), 'source_files':len(sources)}))
