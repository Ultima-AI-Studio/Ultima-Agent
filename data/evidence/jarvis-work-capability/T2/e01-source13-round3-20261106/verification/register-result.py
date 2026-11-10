"""Register the independently reviewed third positive, preserving raw evidence."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
REPO = Path(r'H:\UltimaAI\UltimaAgent')
MIRROR = Path(r'H:\UltimaAI\ultima-docs-repo\docs\shared\research\ultimaagent-work-capability')
NOW = dt.datetime.now(dt.timezone.utc).isoformat()
EXPECTED_REVIEW = 'a63b1d08a5afcb65a79dc03c701e6d7cf33b8a88b975b85a326cfccd9b854c74'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path):
    return json.loads(path.read_bytes())


def save(path, value):
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write('\n')


a = ROOT / 'actual/e01-round3'
t = load(a / 'terminal.json')
r = load(ROOT / 'review/independent-result-review.json')
prior_path = ROOT / 'inputs/prior-e01-round2/registration.json'
prior = load(prior_path)
res = load(a / 'product-result.json')
artifact = Path(res['artifacts'][0]['path'])
readback = load(ROOT / 'verification/result-content-readback.json')
post = load(ROOT / 'verification/result-protected-readback.json')
rh = sha(ROOT / 'review/independent-result-review.json')
th = sha(a / 'terminal.json')
plan = REPO / 'docs/plans/jarvis-work-e02-source13-reentry-plan-20261106.md'
report = REPO / 'docs/reports/jarvis-work-t2-e01-source13-round3-result-20261106.md'
reconciliation = ROOT.parent / 'e02-source13-reconciliation-20261106/reconciliation.json'
assert rh == EXPECTED_REVIEW
assert r['scope'] == 'e01-round3-result-review' and r['case'] == 'e01-round3'
assert r['candidate'] == t['candidate'] == prior['candidate']
assert r['reviewer'] == 'root-independent' and r['independent_from_preparation_reviewer'] is True
assert r['agent_identity'] == '/root/review_e01_source13_round3_result'
assert r['findings'] == []
assert all(r[k] == 'PASS' for k in ('verdict', 'evidence_verdict', 'case_verdict',
    'mechanical_verdict', 'facts_verdict', 'file_verdict', 'final_claim_verdict', 'cleanup_verdict', 'environment_verdict'))
assert r['target_verdict'] == 'NOT_APPLICABLE' and r['ui_target_scope'] == 'NOT_APPLICABLE_E01_NO_UI'
assert r['terminal_sha256'] == th and r['product_result_sha256'] == sha(a / 'product-result.json')
assert r['preparation_manifest_sha256'] == sha(ROOT / 'manifest.json')
assert r['result_evidence_manifest_sha256'] == sha(ROOT / 'verification/result-evidence-manifest.json')
assert r['artifact_sha256'] == readback['artifact_sha256'] == sha(artifact)
assert r['no_new_facts']['verdict'] == 'PASS' and artifact.stat().st_size == 100
assert r['facts']['complete_artifact_text'] == artifact.read_text(encoding='utf-8')
assert r['recommendation']['acceptance_credit_recommended'] is True
assert r['recommendation']['current_case_positive_credit'] == 1
assert r['recommendation']['previous_registered_e01_positives'] == 2
assert r['recommendation']['eligible_cumulative_e01_positives_after_root_registration'] == 3
assert r['recommendation']['cumulative_work_cli_count_after_root_registration'] == 3
assert r['recommendation']['cumulative_completed_inference_events_after_root_registration'] == 6
assert r['execution']['task_id'] == res['task_id'] and r['execution']['work_cli_launches'] == 1
assert r['execution']['completed_inference_end_events'] == 2
assert r['execution']['completed_sdk_write_calls'] == 1 and r['execution']['automatic_retry_recorded'] is False
assert t['overall'] == 'PENDING_FACT_REVIEW' and t['acceptance_credit'] is False and t['errors'] == []
assert post['status'] == 'PASS_POINT_IN_TIME_POSTCHECK'
assert len(post['protected']) == 7 and all(row['match'] for row in post['protected'])
assert len(post['owned']) == 6 and all(row['original_identity_absent'] for row in post['owned'])
assert post['isolated_port_closed'] and post['isolated_port'] == 53621
assert prior['positive_passed'] == 2 and prior['facts'] == 'PASS'
assert sha(prior_path) == '57f194fe94e41954a87df1299c6eccff5978e47eea839ea9ccd0724ff967f5ae'
old = prior['same_candidate_e01_terminal_bindings']
assert len(old) == 2 and [row['case'] for row in old] == ['e01-round1', 'e01-round2']
assert len({row['task_id'] for row in old} | {res['task_id']}) == 3
assert dt.datetime.fromisoformat(old[0]['finished_at']) < dt.datetime.fromisoformat(old[1]['finished_at']) < dt.datetime.fromisoformat(t['finished_at'])
assert r['prerequisites']['registered_E01_rows'] == old
assert len(r['prerequisites']['ordered_credentials']) == 6
assert plan.is_file() and not report.exists()
assert sha(reconciliation) == '7e0337b7b335d5c678fc560c9c09c400f0ba0397c462177aafd728a359e9d398'
for name in ('manifest.json', 'verification/result-evidence-manifest.json'):
    for row in load(ROOT / name)['files']:
        path = ROOT / row['path']
        assert sha(path) == row['sha256'] and path.stat().st_size == row['bytes'], str(path)

binding = dict(case='e01-round3', candidate=t['candidate'], terminal_sha256=th,
    review_sha256=rh, task_id=res['task_id'], finished_at=t['finished_at'], case_verdict='PASS',
    work_cli_count=1, completed_inference_events=2, artifact_sha256=sha(artifact))
registration = dict(recorded_at=NOW, controller='root', scope='E01_CURRENT_CANDIDATE_POSITIVE_CHAIN',
    case='e01-round3', candidate=t['candidate'], candidate_manifest_sha256=r['candidate_runtime_manifest_sha256'],
    preparation_manifest_sha256=r['preparation_manifest_sha256'], result_manifest_sha256=r['result_evidence_manifest_sha256'],
    terminal_sha256=th, result_review_sha256=rh, product_result_sha256=r['product_result_sha256'],
    artifact_sha256=sha(artifact), artifact_path=str(artifact), task_id=res['task_id'], case_verdict='PASS', facts='PASS',
    delivery='PASS', final_claim='PASS', cleanup='PASS', environment='PASS_AT_SAVED_CASE_BOUNDARY_AND_POSTCHECK',
    target='NOT_APPLICABLE_NO_UI', acceptance_credit=True, E01_credit=1, positive_passed=3, positive_required=3,
    same_candidate_e01_terminals=3, cumulative_work_cli_count=3, current_case_work_cli_count=1,
    cumulative_completed_inference_events=6, current_case_completed_inference_events=2, actual_native_start_count=None,
    same_candidate_e01_terminal_bindings=old + [binding], predecessor_registration_sha256=sha(prior_path),
    consecutive_positive_cases=['e01-round1', 'e01-round2', 'e01-round3'],
    E01='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS',
    E03_prerequisite_registration_sha256=prior['E03_prerequisite_registration_sha256'],
    qualified_E03_work_cli_count=3, qualified_E03_completed_inference_events=9,
    raw_terminal_overall=t['overall'], raw_terminal_acceptance_credit=False,
    actual_case_count=1, independent_result_reviews=1, remaining_actual_case_cap=0, remaining_result_review_cap=0,
    next_live_authority_issued=False, T2='NOT_PASSED', E02='NOT_PASSED', goal_complete=False,
    acceptance_scope='Same candidate, current8B and fixed E01 corpus only; no open-task reliability claim.')
save(ROOT / 'verification/result-registration.json', registration)
save(ROOT / 'verification/result-review-disposition.json', dict(recorded_at=NOW, controller='root',
    decision='ACCEPT_CURRENT_CASE_PASS_REGISTER_E01_FIXED_CORPUS_3_OF_3', review_sha256=rh,
    regrading={'Critical': 0, 'Important': 0, 'Minor': 0},
    decline_dispositions=[dict(item=item, ruling='ACCEPT_SCOPE_LIMIT', effect='No broader acceptance or future/runtime claim')
                          for item in r['declined_to_judge']],
    original_terminal_unchanged=True, next_execution_authorized=False, T2='NOT_PASSED'))
save(ROOT / 'verification/result-review-completion.json', dict(recorded_at=NOW, agent=r['agent_identity'], review_sha256=rh,
    case='e01-round3', allocated=1, completed=1, remaining=0, verdict='PASS', next_review_authorized=False))
registration_hash = sha(ROOT / 'verification/result-registration.json')
report.write_text(f'''# E01 source13 round3 实际文件交付结果

原工单 wo-ultimaagent-20261101-0021；冻结候选 {t['candidate']}，当前 qwen3-8b-uncensored。用户授权的一次 E01 round3 和一次只读独立结果复核已完成。实际文件交付、事实、最终保存声明、清理及保存时点的环境证据均 PASS，无发现；root 已登记同候选 E01 固定样本连续正例 3/3。E03 固定样本三正例与一负例保持通过，E02/T2 及后续门尚未通过。

任务 ID：{res['task_id']}。实际交付文件：{artifact}；100 字节，SHA-256 {sha(artifact)}。全文为“摘要”标题及三条要点：项目代号松林、交付形式 Markdown 文档、截止日期 2026 年 11 月 8 日。独立复核确认三项事实完整且没有新增事实。实际 SDK 写入、服务端/外部/root/reviewer 读回字节一致，最终回复给出本轮真实绝对路径。

本轮一次真实工作 CLI、一次成功 SDK 文件写入、两条完成的 inference_end 事件，无重试。三轮累计 CLI 3、完成推理事件 6。原生总启动数和未完成数保持 null，断连后是否继续生成保持 unknown；两条 tool_results 是同一调用的 SDK 摘要与 ledger，不能计成两次写入。本例无窗口或音频操作。

原 proof 60 秒、authority 120 秒、CLI 300/SDK 1800/controller 315 秒门保持。独审根据原生 FILETIME 核对 CLI 提交时 proof 年龄 22.8997915 秒、authority 年龄 22.8082805 秒。本次入口耗时约 48.04 秒，含检查和清理，不作为开放任务或语音延迟指标。

机械终态 {t['finished_at']}；cleanup/audit/boundaries 均 PASS。root 只读后查 {post['recorded_at']} 至 {post['finished_at']} 确认 6 本例原身份消失、隔离端口 53621 关闭、7 保护身份匹配、Ollama 0.32.15 与当前 8B 摘要匹配、官方语音 ready/fresh 及原身份/run_id 一致。仅为保存时点证据，不代表连续/未来可用或声音功能验收；未重启服务或额外推理。

准备 manifest 69 文件 SHA-256 {r['preparation_manifest_sha256']}；结果 manifest 44 文件 SHA-256 {r['result_evidence_manifest_sha256']}。原 terminal SHA-256 {th}；product-result SHA-256 {r['product_result_sha256']}；独立 reviewer {r['agent_identity']}，review SHA-256 {rh}；root 登记 SHA-256 {registration_hash}。原 terminal 保持 PENDING_FACT_REVIEW、facts=PENDING_ROOT_INDEPENDENT_REVIEW 和 credit=false；事实通过与验收登记另存，没有回写原始记录。

306 项离线检查属于此前准备证据，实际后没有重跑；产品 57 源码、7 依赖及 1346 SDK 文件绑定保持。三轮通过只完成当前候选和模型的固定 E01 样本组，不代表任意文件摘要的可靠率。旧实际失败、旧环境故障及离线 RED 全部保留，6 项未裁定范围由 root 接受。本次实际及结果复核额度均已用完，没有授予下一用例。

下一步按 docs/plans/{plan.name} 准备 E02 当前候选验证。只读核对已发现旧验证包绑定与当前候选的差异，证据见 {reconciliation}，SHA-256 {sha(reconciliation)}；当前只完成历史/候选核对，没有新 E02 测试、产品调用或运行权。保留原题、四份资料及受控研究和真实联网的独立验收要求。

项目与 UltimaDocs 本地结果 tag 为 ultimaagent-t2-e01-source13-round3-result-20261106；精确提交及字节读回见 verification/result-local-checkpoint.json。远端 push 此前被自动审批以 blocked by policy 拒绝，本轮未重试或换通道；本地留档和实际验收不等于远端同步。
''', encoding='utf-8')

mirrors = []
for path, folder in ((report, 'reports'), (plan, 'plans')):
    target = MIRROR / folder / path.name
    assert not target.exists()
    target.write_bytes(path.read_bytes())
    mirrors.append(dict(source=str(path), mirror=str(target), sha256=sha(path)))
save(ROOT / 'verification/result-document-mirror-readback.json', dict(recorded_at=NOW, mirrors=mirrors, byte_identical=True))

state_path = ROOT.parent / 'current-run.json'
state = load(state_path)
state.update(phase='SOURCE13_E01_COMPLETE_E02_RECONCILIATION_PLAN_READY', updated_at=NOW, active_review_agent=None,
    active_report=str(report), e01='PASS_CURRENT_CANDIDATE_FIXED_CORPUS', e01_current_candidate_positive_passed=3,
    e01_current_result_review='PASS', e01_current_review_path=str(ROOT / 'review/independent-result-review.json'),
    e01_current_review_sha256=rh, e01_current_result_registration=str(ROOT / 'verification/result-registration.json'),
    e01_current_result_registration_sha256=registration_hash, e01_current_result_review_remaining=0,
    e01_execution_released=False, live_gate_released=False, next_stage_released=False,
    explicit_user_execution_status='COMPLETE_E01_ROUND3_AND_ONE_RESULT_REVIEW', blocking_condition=None,
    next_offline_plan=str(plan), e01_last_completed_case='e01-round3',
    e01_actual_cases=3, e01_actual_work_cli_count=3, e01_actual_completed_inference_events=6,
    e01_actual_counter_basis='Same candidate E01 actual cases 3 and formally accepted fixed-corpus positives 3; each case CLI1/completed inference events2.',
    e02='NOT_PASSED_HISTORY_RETAINED', e02_reconciliation_receipt=str(reconciliation),
    e02_reconciliation_sha256=sha(reconciliation),
    latest_readonly_runtime_receipt=str(ROOT / 'verification/result-protected-readback.json'),
    latest_readonly_runtime_sha256=sha(ROOT / 'verification/result-protected-readback.json'))
state['next_action_scope'] = dict(scope='e02-source13-current-candidate-preparation-plan',
    actual_case_allocation=0, actual_result_review_allocation=0, authority_issued=False,
    product_model_calls=0, audio_actions=0, candidate=t['candidate'], plan=str(plan),
    current_completed_work='READ_ONLY_HISTORY_AND_CANDIDATE_RECONCILIATION',
    legacy_runtime_or_repair_allocations_reopened=False)
state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

status = '当前269aca5与当前8B的E03三正例3/3及负例1/1已PASS；E01 round1—round3实际文件交付和独立事实复核全部PASS，同候选固定样本连续3/3。round3单例与一次复核已耗尽，6本例身份清理与7保护身份保存后查通过。下一步E02当前候选验证准备，已完成旧包/源码只读差异核对；无E02运行额度，T2及后续原门保持。'
append = f'\n\n## 2026-11-06 E01 round3实际与独立事实复核PASS，固定样本3/3\n\n{status}\n\n报告：docs/reports/{report.name}。独审SHA {rh}；登记SHA {registration_hash}。下一步计划docs/plans/{plan.name}。原始terminal及全部旧失败保持，E02/T2未通过。\n'
wo = REPO / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
lines = wo.read_text(encoding='utf-8').splitlines()
assert sum(line.startswith('- 状态：') for line in lines) == 1
wo.write_text('\n'.join('- 状态：' + status if line.startswith('- 状态：') else line for line in lines).rstrip() + append, encoding='utf-8')
stage = REPO / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
stage.write_text(stage.read_text(encoding='utf-8').rstrip() + append, encoding='utf-8')
queue = Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
lines = queue.read_text(encoding='utf-8').splitlines()
needle = '| UltimaAgent | wo-ultimaagent-20261101-0021 |'
assert sum(line.startswith(needle) for line in lines) == 1
queue.write_text('\n'.join(needle + ' executing | ' + status + ' |' if line.startswith(needle) else line for line in lines) + '\n', encoding='utf-8')
q = subprocess.run([sys.executable, '-B', '-X', 'utf8', r'H:\UltimaAI\_shared\queue\queue-status-gen.py'], capture_output=True, text=True, encoding='utf-8')
save(ROOT / 'verification/result-queue-refresh.json', dict(recorded_at=NOW, exit_code=q.returncode,
    stdout=q.stdout, stderr=q.stderr, scope='Original0021 only; generated totals describe registration, not live execution.'))
assert q.returncode == 0
assert sha(a / 'terminal.json') == th and sha(ROOT / 'review/independent-result-review.json') == rh
print(json.dumps(dict(registration_sha256=registration_hash, E01='3/3', review='PASS', mirrors=len(mirrors),
                     next_actual_allocation=0, E02='NOT_PASSED', T2='NOT_PASSED')))
