"""Bind the frozen JSON-string candidate; copy only preparation source, never grants."""
from pathlib import Path
import ast, hashlib, json, re, subprocess

N = Path(__file__).resolve().parents[1]
OLD = N.parent / 'e02-source-coverage-controlled-preparation-20261107-r1'
BASE = N.parent / 'e02-native-pattern-json-20261107-r1'
P = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
HEAD = '6d758d9c3961f156a062e349ec4a949e2ee7a9a9'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def save(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)
def write(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f: f.write(value)
def replace(text, before, after):
    assert before in text, before
    return text.replace(before, after)

review = load(N / 'review/independent-plan-review.json')
assert review['reviewer'] == 'root-independent' and review['verdict'] == 'PASS_PLAN_ONLY'
assert review['actual_run_authorized'] is False and review['plan_sha256'] == sha(N / 'plan.md')
assert sha(N / 'plan.md') == '54e4409782b2d7bb2d3dc5f4ac398cecb29c3adc325cb508f9a195463534a25e'
git = lambda *args: subprocess.check_output(['git', '-C', str(C), *args], text=True, creationflags=subprocess.CREATE_NO_WINDOW).strip()
assert git('rev-parse', 'HEAD') == git('rev-parse', 'ultimaagent-e02-json-string-candidate-20261107') == HEAD
assert not git('status', '--porcelain')

groups = {'harness': ('adapter.py', 'test_adapter.py', 'run_checks.py', 'headless_proof.py', 'README.md', 'manifest.json'),
          'code': ('entry.py', 'bindings.py'),
          'tests': ('test_bindings.py', 'test_entry.py', 'test_live_boundary.py', 'test_plumbing_replay.py'),
          'verification': ('offline_pytest.py', 'run_binding_checks.py', 'run_entry_checks.py', 'run_boundary_checks.py',
                           'prepare_review.py', 'read_runtime.py', 'verify_preservation.py', 'verify_preparation.py',
                           'run_preparation_checks.py')}
copied = {}
for folder, names in groups.items():
    for name in names:
        source, target = OLD / folder / name, N / folder / name
        assert not target.exists()
        data = source.read_bytes()
        if target.suffix == '.py':
            data = data.decode('utf8').replace('jarvis-e02-source-coverage', 'jarvis-e02-json-string-projection').encode('utf8')
        with target.open('xb') as f: f.write(data)
        copied[str(source)] = sha(source)

old = load(OLD / 'inputs/input-manifest.json')
sources = {str(C / Path(path).relative_to(P)): sha(C / Path(path).relative_to(P)) for path in old['source_files']}
sources.update(load(BASE / 'verification/candidate-freeze.json')['source_sha256'])
expected = load(BASE / 'inputs/current-inputs.json')['files']
assert len(sources) == 74
assert all(Path(path).is_relative_to(C) and sha(Path(path)) == digest == expected[path] for path, digest in sources.items())
runtime = load(OLD / 'inputs/candidate-runtime-manifest.json')
runtime.update(candidate=HEAD, candidate_root=str(C), branch='codex/jarvis-e02-json-string-projection', source_files=sources,
               scope='Frozen JSON-string sampler repair; current entry preparation only', code_gate='FROZEN_N16_PASS_PREPARATION_ONLY',
               final_code_tests=781, final_code_test_scope='N16 frozen prior product775 plus reference6; not rerun in N17',
               source_revision=HEAD, actual_cases=0, actual_release=False, acceptance_credit=False)
save(N / 'inputs/candidate-runtime-manifest.json', runtime)
files = {p: h for p, h in old['files'].items() if not Path(p).is_relative_to(P) and p != str(OLD / 'inputs/candidate-runtime-manifest.json')}
files.update(sources)
for p in (N / 'inputs/candidate-runtime-manifest.json', BASE / 'manifest.json',
          BASE / 'review/independent-preparation-review.json', BASE / 'verification/publication-readback.json'):
    files[str(p)] = sha(p)
save(N / 'inputs/input-manifest.json', dict(old, candidate=HEAD, candidate_root=str(C), source_files=sources, files=files))

def constants(path, values):
    text, previous = path.read_text('utf8'), {}
    for key, value in values.items():
        match = re.search(r"(?m)^" + key + r"='([^']*)'", text)
        assert match, key
        previous[key] = match[1]
        text, count = re.subn(r"(?m)^" + key + r"='[^']*'", key + '=' + repr(value), text)
        assert count == 1
    path.write_text(text, encoding='utf8', newline='\n')
    return previous

constants(N / 'code/bindings.py', dict(CANDIDATE=HEAD, CANDIDATE_MANIFEST_SHA=sha(N / 'inputs/candidate-runtime-manifest.json')))
previous = constants(N / 'harness/adapter.py', dict(CANDIDATE=HEAD, MANIFEST_SHA=sha(N / 'inputs/input-manifest.json'),
                     BINDINGS_SHA=sha(N / 'code/bindings.py'), PREPARATION_SHA=sha(N / 'inputs/scope.json')))
constants(N / 'code/entry.py', dict(CANDIDATE=HEAD, DIRECT_USER_DECISION_SHA=sha(N / 'inputs/direct-user-decision.json')))
for p in (N / 'harness/test_adapter.py', N / 'tests/test_live_boundary.py'):
    text = p.read_text('utf8').replace(previous['CANDIDATE'], HEAD).replace(previous['MANIFEST_SHA'], sha(N / 'inputs/input-manifest.json'))
    p.write_text(text, encoding='utf8', newline='\n')
(N / 'harness/README.md').write_text('# Frozen C14 JSON-string controlled-entry preparation\n\nProduct ' + HEAD +
    '; current 8B and original budgets/corpus/cleanup unchanged.\nNo actual grant, model call or acceptance credit is allocated.\n'
    'Only path/candidate/input digest constants are rebound from N15.\nCurrent sampler/strict contracts are jointly verified through SDK MockTransport and trusted exports.\n', encoding='utf8', newline='\n')

p = N / 'verification/verify_preservation.py'
text = p.read_text('utf8').replace("e02-source-coverage-budget-20261107-r1", BASE.name)
text = replace(text, 'ultimaagent-e02-source-coverage-candidate-20261107', 'ultimaagent-e02-json-string-candidate-20261107')
p.write_text(text, encoding='utf8', newline='\n')
p = N / 'verification/verify_preparation.py'
text = p.read_text('utf8').replace('e02-native-http-controlled-preparation-20261107-r1', OLD.name)
text = text.replace('e02-source-coverage-budget-20261107-r1', BASE.name).replace(previous['CANDIDATE'], HEAD)
start, end = text.index('    red_runs=[]\n'), text.index('    preservation=')
text = text[:start] + '    # Frozen product already has preserved RED/GREEN; this turn only rebinds and verifies.\n' + text[end:]
text = replace(text, 'red_runs=red_runs,red_failures=1,', 'red_runs=[],red_failures=0,product_sources_changed=False,')
text = replace(text, 'product_baseline_tests=746', 'product_baseline_tests=781')
p.write_text(text, encoding='utf8', newline='\n')
p = N / 'verification/run_preparation_checks.py'
text = replace(p.read_text('utf8'), "('bindings','verification/run_binding_checks.py','green')",
    "('failure-export-green','harness/run_checks.py','failure-export-green'),\n      ('bindings','verification/run_binding_checks.py','green')")
p.write_text(text, encoding='utf8', newline='\n')

for name in ('harness/adapter.py', 'code/bindings.py', 'code/entry.py'):
    functions = lambda p: {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(p.read_bytes()).body
                          if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))}
    assert functions(N / name) == functions(OLD / name), name
save(N / 'inputs/candidate-transition.json', dict(base=old['candidate'], candidate=HEAD, old_root=str(P), new_root=str(C),
    current_sources=len(sources), protected_baseline_sha256=files[old['protected_baseline_path']],
    changed_existing_sources=[str(Path(p).relative_to(C)) for p, h in sources.items()
                              if (P / Path(p).relative_to(C)).exists() and sha(P / Path(p).relative_to(C)) != h],
    changed_product_sources_this_turn=[], model_or_budget_changed=False, shared_P4_P1_changed=False, old_credit_transferred=False))
save(N / 'verification/source-copy.json', dict(source_files=copied, actual_artifacts_copied=False, actual_allocation=0))
ledger = N.parents[4] / '.superpowers/sdd/jarvis-work-e02-json-string-controlled-entry-plan-20261107/progress.md'
ledger.parent.mkdir(parents=True, exist_ok=True)
write(ledger, '# SDD ledger — plan: H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-json-string-controlled-entry-plan-20261107.md\n\n'
    '- Task 1: IN_PROGRESS; plan PASS, 74 sources rebound, core function/class AST unchanged.\n'
    '- Task 2: PENDING; fresh offline checks, whole-package review, local publication.\n'
    '- Pre-flight: Task 2 consumes Task 1 final source/hash bindings; freeze test bytes before running all shards.\n'
    '- Ruling: use native Windows ledger and preserve evidence; no shell installation or workspace deletion.\n'
    '- Ruling: no new product behavior and no fabricated RED; frozen N16 RED/GREEN retained, new observer integration checks run against frozen product.\n'
    '- Actual/result-review allocation 0; user single-case gate remains mandatory.\n')
print(json.dumps(dict(candidate=HEAD, sources=len(sources), inputs=len(files), actual_allocation=0)))
