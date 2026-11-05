"""One-time receipt-derived status correction; no process or case execution."""
import datetime as dt
import hashlib
import json
from pathlib import Path

BASE = Path(r'H:\UltimaAI\UltimaAgent')
T2 = BASE / 'data/evidence/jarvis-work-capability/T2'
ROOT = T2 / 'e03-fixture-input-origin-20261105'
R31 = T2 / 'e03-source12-20261105-r31-preflight-log-isolation'
WORK = BASE / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
STAGE = BASE / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
QUEUE = Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
CURRENT = T2 / 'current-run.json'
STORE = BASE / 'tasks/tasks.json'
REPORT = BASE / 'docs/reports/jarvis-work-t2-e03-r31-diagnosis-20261105.md'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def load(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

def new(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)

receipt_path = ROOT / 'verification/r31-readback.json'
assert digest(receipt_path.read_bytes()) == '91ecd3d49f6416e6722457a52a5c3f02df4ed54e2a9f6adf6b4f2ba7c5f166df'
readback = load(receipt_path)
assert readback['terminal']['overall'] == 'FAIL'
counts = readback['derived_counts']
assert counts['reviewed_positive_cases'] == counts['reviewed_negative_cases'] == 0
for row in readback['same_candidate_case_receipts']:
    assert digest(Path(row['path']).read_bytes()) == row['terminal_sha256']
    assert row['candidate'] == readback['candidate']
    assert row['overall'] == row['mechanical'] == 'FAIL'
store_raw = STORE.read_bytes()
assert next(item for item in load(STORE) if item['task_id'] == 'wo-ultimaagent-20261101-0021-t2')['state'] == 'BLOCKED'
old = {path: path.read_bytes() for path in (CURRENT, WORK, STAGE, QUEUE)}
snapshots = {CURRENT: 'current-run-before.json', WORK: 'work-order-before.md',
             STAGE: 't2-stage-before.md', QUEUE: 'global-queue-before.md'}
now = dt.datetime.now(dt.timezone.utc).isoformat()
old_gate_path = T2 / 'e03-resume-20261102/e03-gate-pass.json'
old_gate = load(old_gate_path)
assert old_gate['candidate'] != readback['candidate']
authority_path = R31 / 'controller-authority/e03-round2.json'
authority = load(authority_path)
assert authority['candidate'] == readback['candidate']
auth = load(R31 / 'authorization.json')
ledger = load(R31 / 'controller-ledger.json')
assert auth['case_cap'] == 1 and auth['retry_authorized'] is False
assert ledger['consumed'] == ['e03-round2']

current = dict(
    schema=2, original_order='wo-ultimaagent-20261101-0021',
    stage_task='wo-ultimaagent-20261101-0021-t2', updated_utc=now,
    phase='E03_CURRENT_CANDIDATE_NOT_PASSED_FIXTURE_DIAGNOSTIC_PREPARATION',
    candidate=readback['candidate'], stage_queue_state='BLOCKED', workflow_status='blocked',
    goal_status='active', model=readback['model']['alias'], model_digest=readback['model']['digest'],
    model14_approved=False, model14_executed=False, otherweights_or_larger_allowed=False,
    source_implementation_released=False, live_gate_released=False, next_stage_released=False,
    active_report=str(REPORT), active_preparation_root=str(ROOT), active_review_agent=None,
    preparation_status='OFFLINE_READY_FOR_INDEPENDENT_REVIEW',
    preparation_review='NOT_RUN', preparation_test_count=36,
    preparation_test_scope='focused offline fixture-origin and controller audit validation only',
    e03_overall='NOT_PASSED_CURRENT_CANDIDATE', e03_positive_passed=counts['reviewed_positive_cases'],
    e03_positive_required=3, e03_negative_passed=bool(counts['reviewed_negative_cases']),
    e03_actual_work_cli_submissions=counts['work_cli_submissions'],
    e03_observed_completed_inferences=None, e03_gate=None,
    e03_current_case='e03-round2', e03_current_case_scope='consumed R31 recovery diagnostic; no acceptance credit',
    e03_current_authority=str(authority_path), e03_current_authority_sha256=digest(authority_path.read_bytes()),
    e03_current_terminal=str(R31 / 'actual/e03-round2/terminal.json'),
    e03_current_terminal_sha256=readback['source_hashes']['actual/e03-round2/terminal.json'],
    e03_current_review=None, e03_current_review_sha256=None,
    e03_current_case_overall='FAIL', e03_current_case_work_cli_count=0,
    e03_current_case_product_result_sha256=None, e03_execution_released=False,
    e03_workflow_step='FIXTURE_DIAGNOSIS_PREPARATION_NO_LIVE_ALLOCATION',
    e03_next_acceptance_case='e03-round1',
    e03_count_scope='top-level e03-source12*/actual/* candidate-bound original receipts; excludes copied history',
    e03_counts_receipt=str(receipt_path), e03_counts_receipt_sha256=digest(receipt_path.read_bytes()),
    e03_same_candidate_counts=counts,
    current_case_budget=dict(case_cap=1, consumed=['e03-round2'], retry_authorized=False,
                             remaining=0, acceptance_credit=False, new_allocation_issued=False),
    input_source='UNCONFIRMED', user_context='Unable to confirm whether typing at the event time',
    new_live_cases_this_preparation=0, new_model_calls_this_preparation=0,
    e01='PENDING_SAME_CANDIDATE_REGRESSION_AFTER_E03', e02='NOT_PASSED_HISTORY_RETAINED',
    t2='NOT_PASSED', t3_t5_released=False, owner_gate='NOT_PASSED',
    next_work='Independent read-only review of observation patch and evidence-credit correction; '
              'then separately prepare/review a newly authorized bounded fixture-only diagnostic. '
              'Formal acceptance starts at current-candidate E03 round1, then rounds2/3 and negative, E01, E02.',
    historical_current_run=dict(path=str(ROOT / 'history/current-run-before.json'),
                                sha256=digest(old[CURRENT]), reason='full prior schema retained; old source9/source10 fields are historical'),
    historical_e03_gate=dict(path=str(old_gate_path), sha256=digest(old_gate_path.read_bytes()),
                             candidate=old_gate['candidate'], product_source=old_gate['product_source'],
                             overall=old_gate['overall'], current_candidate_credit=False),
    inherited_receipts_excluded=readback['inherited_receipts_excluded'],
    old_failures_preserved=True,
)
summary = ('T2真实工作验收仍BLOCKED。最新R31单例已消费且FAIL：初始41 UTF-16，冻结基线为空，'
           'server/CLI前停止（work_cli_count=0）；cleanup与protected boundaries PASS，输入来源无法确认。'
           '已完成输入来源观察补丁的离线准备（36项测试），未新增实跑/模型调用，独立审查未进行。'
           '已纠正跨候选验收归属：source12目录内round1 PASS来自旧118ba候选；'
           '当前7975候选已核实正例0、负例0，后续验收须从round1开始。'
           '当前8B、生产语音/KWS及历史失败保持，E01/E02和T3—T5未放行。'
           '报告：`docs/reports/jarvis-work-t2-e03-r31-diagnosis-20261105.md`。')
work_text = old[WORK].decode('utf-8-sig')
work_lines = work_text.splitlines(keepends=True)
matches = [index for index, line in enumerate(work_lines) if line.startswith('- 状态：')]
assert len(matches) == 1
newline = '\r\n' if '\r\n' in work_text else '\n'
work_lines[matches[0]] = '- 状态：' + summary + newline
append = newline + '## 2026-11-05 R31结果与当前候选验收归属校正' + newline + newline + summary + newline
new_work = (''.join(work_lines) + append).encode('utf-8')
stage_text = old[STAGE].decode('utf-8-sig')
stage_newline = '\r\n' if '\r\n' in stage_text else '\n'
new_stage = (stage_text + stage_newline + '## 2026-11-05 R31 current gate (supersedes R26 latest status)' +
             stage_newline + stage_newline + summary + stage_newline +
             'R31 terminal SHA-256: 9ca7d62d59b4f8d6993d595c03befc81b5466660eb0cde1b68db0a99780455df. '
             'Readback: e03-fixture-input-origin-20261105/verification/r31-readback.json. '
             'No allocation/retry/reviewer dispatched by this status correction.' + stage_newline).encode('utf-8')
queue_text = old[QUEUE].decode('utf-8-sig')
queue_lines = queue_text.splitlines(keepends=True)
matches = [index for index, line in enumerate(queue_lines)
           if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(matches) == 1
queue_newline = '\r\n' if '\r\n' in queue_text else '\n'
queue_lines[matches[0]] = '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | **2026-11-05 R31已失败，离线诊断准备完成**：' + summary + ' |' + queue_newline
new_queue = ''.join(queue_lines).encode('utf-8')
changes = {CURRENT: encoded(current), WORK: new_work, STAGE: new_stage, QUEUE: new_queue}
assert load(STORE) and STORE.read_bytes() == store_raw
for path, raw in old.items():
    assert path.read_bytes() == raw, 'concurrent edit: ' + str(path)
    assert not (ROOT / 'history' / snapshots[path]).exists()
assert not (ROOT / 'verification/status-reconciliation.json').exists()
for path, raw in old.items():
    new(ROOT / 'history' / snapshots[path], raw)
for path, raw in changes.items():
    assert path.read_bytes() == old[path], 'concurrent edit: ' + str(path)
    path.write_bytes(raw)
    assert path.read_bytes() == raw
assert STORE.read_bytes() == store_raw
receipt = dict(schema=1, recorded_at=now, source_receipt_sha256=digest(receipt_path.read_bytes()),
               action='receipt-derived status reconciliation; no task-state transition or execution',
               original_task_store_unchanged_sha256=digest(store_raw),
               changes=[dict(path=str(path), before_sha256=digest(old[path]), after_sha256=digest(raw),
                             preserved_before=str(ROOT / 'history' / snapshots[path])) for path, raw in changes.items()],
               current_candidate=current['candidate'], positive=0, negative=0,
               old_failures_preserved=True, new_live_cases=0, new_model_calls=0)
new(ROOT / 'verification/status-reconciliation.json', encoded(receipt))
print(json.dumps(dict(status='reconciled', current_candidate=current['candidate'], positive=0, negative=0,
                      task_store_unchanged=True, modified_files=len(changes),
                      receipt_sha256=digest((ROOT / 'verification/status-reconciliation.json').read_bytes()))))
