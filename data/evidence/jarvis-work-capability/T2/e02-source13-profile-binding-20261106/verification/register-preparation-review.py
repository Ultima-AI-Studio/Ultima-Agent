"""Register the existing sealed offline review; does not import or execute profile code."""
from pathlib import Path
import datetime as dt
import hashlib
import json

B = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo')
MANIFEST_SHA = 'ec15aa82ee9ef72ff366c33eb997307e8151a97957eaa6d3f8544dc555424382'
REVIEW_SHA = '94eb752925b1f1644d1ab91f5762a9d8e3a2daba3d7f3a5b0fca1b22a84d40ce'
TAG = 'ultimaagent-t2-e02-source13-binding-prep-20261106'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save_new(path, data):
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


manifest_path = B/'manifest.json'
assert sha(manifest_path) == MANIFEST_SHA
manifest = load(manifest_path)
assert len(manifest['files']) == 129
for row in manifest['files']:
    path = B/row['path']
    assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)
review_path = B/'review/independent-preparation-review.json'
assert sha(review_path) == REVIEW_SHA
review = load(review_path)
assert review['reviewer'] == 'root-independent' and review['verdict'] == 'PASS'
assert review['manifest_sha256'] == MANIFEST_SHA and review['findings'] == []
assert review['actual_authority'] is review['runtime_authority'] is review['model_authority'] is False
receipt = load(B/'code/binding-full-green2/receipt.json')
assert receipt['counts'] == dict(tests=557, failures=0, errors=0, skipped=0)
assert receipt['exit_code'] == 0 and receipt['package_unchanged'] and receipt['dependencies_unchanged']
assert receipt['io_guard']['denied'] == []
for name, digest in receipt['raw_sha256'].items():
    assert sha(B/'code/binding-full-green2'/name) == digest, name
allocation = load(B/'review/allocation.json')
assert allocation['allocated'] == allocation['dispatch_reserved'] == 1 and allocation['remaining'] == 0
now = dt.datetime.now(dt.timezone.utc).isoformat()
dispositions = [
    'Accepted limitation. Concrete controls and native worker/reader entry remain the next separate offline preparation task; no successful default or runtime grant.',
    'Accepted limitation. An actual profile run and native timing proof need a separately reviewed entry and fresh user case/result-review grant; synthetic contracts carry no integration credit.',
    'Accepted limitation. Fixed run_checks.py has not run. Current 557 results are explicitly attributed to run-stage.py; a fixed runner receipt will be prepared before actual entry release.',
    'Accepted limitation. No OS-wide inactivity claim; native activity remains unknown and Python audit records only its observed requests.',
    'Accepted limitation. E02, T2, later stages and Owner gates remain NOT_PASSED; E01/E03 accepted fixed-corpus records are retained separately.',
    'Accepted trust boundary. Reused private module is trusted code pinned by bytes; not protection against hostile arbitrary Python.',
    'Accepted scope. Commit only explicit owned files; record and preserve unrelated dirty bytes and concurrent commits.',
    'Accepted limitation. Old NOT_READY and six repair rounds remain historical failures; no universal correctness or reset of old budgets.'
]
assert len(review['declined_to_judge']) == len(dispositions)
disposition = dict(recorded_at=now, controller='root', scope='E02_SOURCE13_OFFLINE_BINDING_PREPARATION',
    manifest_sha256=MANIFEST_SHA, review_path=str(review_path), review_sha256=REVIEW_SHA,
    independent_verdict='PASS', root_disposition='ACCEPT_PREPARATION_ONLY', unresolved_blocking_findings=[],
    limitations=[dict(**item, root_disposition=text) for item, text in zip(review['declined_to_judge'], dispositions)],
    recommendations=review['recommendations'], code_fix_passes_after_review=0,
    actual_authority=False, model_authority=False, runtime_authority=False, result_review_allocation=0,
    E01='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', E02='NOT_PASSED', T2='NOT_PASSED')
save_new(B/'verification/root-review-disposition.json', disposition)
save_new(B/'verification/code-preparation-gate.json', dict(recorded_at=now,
    verdict='PASS_PREPARATION_ONLY', manifest_sha256=MANIFEST_SHA, sealed_files=129, bound_inputs=1461,
    final_named_runner_tests=557, original_test_ids=540, added_test_ids=17,
    final_named_runner_receipt_sha256=sha(B/'code/binding-full-green2/receipt.json'),
    independent_review_sha256=REVIEW_SHA, root_disposition_sha256=sha(B/'verification/root-review-disposition.json'),
    fixed_runner_runs=0, original_profile_runs=0, model_calls=0, actual_case_allocation=0,
    original_six_repair_rounds_preserved=True, old_budget_reopened=False,
    actual_authority=False, E02='NOT_PASSED', T2='NOT_PASSED'))

report_path = REPO/'docs/reports/jarvis-work-t2-e02-source13-profile-binding-preparation-20261106.md'
pending_report = report_path.read_bytes()
with (B/'verification/report-before-review-disposition.md').open('xb') as stream:
    stream.write(pending_report)
report = pending_report.decode('utf-8')
report = report.replace('独立准备审查进行中，E02/T2及后续门未通过。', '独立准备审查PASS，root已接受其离线准备结论；E02/T2及后续门未通过。')
report = report.replace('下一步需在准备审查结论基础上准备外层入口', '下一步按独审列明的边界准备外层入口')
old_paragraph = '用户持续推进授权覆盖本轮有界离线准备；内联实施及一次整包准备独审，不包含新的实际用例或结果复核。当前reviewer为/root/review_e02_source13_profile_binding；报告返回后由root处置，不以“测试通过”预填独审、运行、E02或T2通过。'
assert old_paragraph in report
report = report.replace(old_paragraph,
    '用户持续推进授权覆盖本轮有界离线准备；内联实施及一次整包准备独审，不包含新的实际用例或结果复核。独立reviewer /root/review_e02_source13_profile_binding返回PASS，无阻断发现；报告SHA-256 '+REVIEW_SHA+'。root逐项接受8项未裁定范围，记录于verification/root-review-disposition.json，准备门见verification/code-preparation-gate.json。审查核对129封存文件和1461输入均无漂移；确认原109个顶层AST语句、540旧标识以及全部失败保留。\n\n'
    '独审未裁定具体RootControls和worker/reader启动、实际SDK/profile/模型及原生时限、原固定run_checks.py执行、OS/native全局活动、E02/T2/Owner及真实研究质量、恶意Python隔离、无关工作区文件和所有环境下的算法正确性。root没有将这些项目登记为通过。下一步先完成外层入口的具体设计和必要适配；独立事实复核与新的实际运行均仍需新分配。')
report = report.replace('ultimaagent-t2-e02-source13-binding-review-20261106', TAG)
report_path.write_text(report.replace('\r\n','\n'), encoding='utf-8', newline='\n')

state_path = B.parent/'current-run.json'
before_state = state_path.read_bytes()
with (B/'verification/current-run-before-review-disposition.json').open('xb') as stream:
    stream.write(before_state)
state = json.loads(before_state)
assert state['phase'] == 'SOURCE13_E02_PROFILE_BINDING_PENDING_PREPARATION_REVIEW'
assert state['e01_current_candidate_positive_passed'] == 3
state.update(updated_utc=now, phase='SOURCE13_E02_BINDING_PREPARATION_PASS_ROOT_ENTRY_PENDING',
    active_preparation_root=str(B), active_review_agent=None,
    preparation_status='PASS_PREPARATION_ONLY', preparation_review='PASS', preparation_test_count=557,
    preparation_test_scope='Named isolated run-stage.py contracts; original540 plus17; fixed runner not executed',
    preparation_review_path=str(review_path), preparation_review_sha256=REVIEW_SHA,
    e02_preparation_review='PASS', e02_preparation_review_path=str(review_path),
    e02_preparation_review_sha256=REVIEW_SHA,
    e02_preparation_root_disposition=str(B/'verification/root-review-disposition.json'),
    e02_preparation_root_disposition_sha256=sha(B/'verification/root-review-disposition.json'),
    e02_preparation_checkpoint_tag=TAG, e02_preparation_checkpoint_receipt=str(B/'verification/preparation-local-checkpoint.json'),
    e02='NOT_PASSED', e02_execution_released=False, live_gate_released=False, next_stage_released=False)
state['next_action_scope'] = dict(scope='e02-source13-root-entry-design-and-offline-preparation',
    binding_preparation_package=str(B), binding_preparation_verdict='PASS_PREPARATION_ONLY',
    actual_case_allocation=0, actual_result_review_allocation=0, authority_issued=False,
    old_repair_budget_reopened=False, model='qwen3-8b-uncensored', audio_actions=0,
    next_step='Prepare concrete outer RootControls entry, original clock/exit observation and seven protected identities; no actual SDK/profile/model execution.')
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2)+'\n', encoding='utf-8', newline='\n')

status = '当前269aca5与当前8B的E01固定3/3、E03三正例及负例已PASS；E02当前绑定557项离线检查及129文件独立准备审查PASS，root已处置全部未裁定项。外层Root执行入口待准备，实际/模型/运行authority均0；E02/T2及后续门未过，旧失败及六轮历史保留。'
appendix = '\n## 2026-11-06 E02当前绑定独立准备审查PASS\n\n'+status+'\n\n独审SHA '+REVIEW_SHA+'；准备manifest '+MANIFEST_SHA+'。结论仅限离线绑定准备，8项未裁定范围逐项记录于data/evidence/jarvis-work-capability/T2/e02-source13-profile-binding-20261106/verification/root-review-disposition.json。原固定runner尚未执行，未据557项模拟检查登记实际profile或研究能力通过；下一步先准备具体外层入口。报告：docs/reports/jarvis-work-t2-e02-source13-profile-binding-preparation-20261106.md。\n'
order = REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
lines = order.read_text(encoding='utf-8').splitlines()
assert sum(line.startswith('- 状态：') for line in lines) == 1
lines = ['- 状态：'+status if line.startswith('- 状态：') else line for line in lines]
order.write_text('\n'.join(lines).rstrip()+'\n'+appendix, encoding='utf-8', newline='\n')
stage = REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
stage.write_text(stage.read_text(encoding='utf-8').rstrip()+'\n'+appendix, encoding='utf-8', newline='\n')
queue = Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
rows = queue.read_text(encoding='utf-8').splitlines()
prefix = '| UltimaAgent | wo-ultimaagent-20261101-0021 |'
assert sum(line.startswith(prefix) for line in rows) == 1
rows = [prefix+' executing | '+status+' |' if line.startswith(prefix) else line for line in rows]
queue.write_text('\n'.join(rows)+'\n', encoding='utf-8', newline='\n')
progress_path = REPO/'.superpowers/sdd/jarvis-work-e02-source13-profile-binding-plan-20261106/progress.md'
with progress_path.open('a', encoding='utf-8', newline='\n') as stream:
    stream.write('\nTask 2: independent preparation review PASS, no blocking findings; root accepted all8 unjudged scopes. No new code fix or repeated tests. Preparation complete, local checkpoint pending; actual/model/result-review allocations0.\n')
with (B/'verification/progress-after-review.md').open('xb') as stream:
    stream.write(progress_path.read_bytes())
mirrors=[]
for source in (report_path, REPO/'docs/plans/jarvis-work-e02-source13-profile-binding-plan-20261106.md'):
    target=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    target.write_bytes(source.read_bytes())
    assert sha(source)==sha(target)
    mirrors.append(dict(source=str(source), mirror=str(target), bytes=source.stat().st_size, sha256=sha(source)))
save_new(B/'verification/reviewed-document-mirror-readback.json', dict(recorded_at=now, mirrors=mirrors))
assert sha(manifest_path) == MANIFEST_SHA and sha(review_path) == REVIEW_SHA
print(json.dumps(dict(verdict='PASS_PREPARATION_ONLY', review_sha256=REVIEW_SHA, mirror_files=len(mirrors), E02='NOT_PASSED', actual_authority=False)))
