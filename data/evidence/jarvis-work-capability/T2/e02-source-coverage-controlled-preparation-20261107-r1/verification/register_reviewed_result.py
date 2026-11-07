"""Record the independently reviewed first outcome; no actual execution or retry."""
from pathlib import Path
import datetime as dt, hashlib, json, re, subprocess, sys

N = Path(__file__).resolve().parents[1]
R = N.parents[4]
M = Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
CANDIDATE = 'e40a55b40c223181040dbb6a09d0c4d2da5026cf'
RUN = '5e6ea89c-8e47-43a6-9480-7a11d72cabf5'
RESULT_MANIFEST = 'e0fc7084754d492d7166e219e2596b15f5f2562783721e9ca80a85c2c9168b5a'
QUESTION = 'call_95815376c4ef4b3499fc52d9fdbdf0df'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def save(p, value):
    with p.open('x', encoding='utf8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)

review_path = N/'review/independent-result-review.json'
review = load(review_path)
assert review['reviewer'] == 'root-independent' and review['verdict'] == 'FAIL_CONFIRMED'
assert review['candidate'] == CANDIDATE and review['run_id'] == RUN
manifest_path = N/'review/result-inputs/result-manifest.json'
assert sha(manifest_path) == RESULT_MANIFEST == review['result_manifest_sha256']
assert review['acceptance_credit'] == 0
for name, digest in load(manifest_path)['files'].items():
    assert sha(N/name) == digest, name
A = N/'actual/E02-controlled-1'
product = load(A/'product-result.json')
diagnostic = load(A/'trusted-failure-diagnostic.raw')
terminal = load(A/'terminal.json')
execution = load(N/'release/tool-execution-receipt.json')
readback = load(N/'review/result-inputs/byte-readback.json')
assert execution['question_id'] == QUESTION and execution['invocations'] == 1 and execution['retry'] == 0
assert terminal['run_id'] == RUN and terminal['overall'] == 'FAIL' and terminal['cleanup']['status'] == 'PASS'
assert product['status'] == 'failed' and product['content'] == '本次研究未交付。'
assert product['error'] == 'Research HTTP status'
assert diagnostic['branch'] == 'unvalidated_response' and diagnostic['last_http']['status'] == 500
assert diagnostic['last_http']['request_sha256'] == 'f2fa2d8c6520f04ac22ed4563d66b722fb1686e5dab6cf4680daba62d8c786f1'
assert len(diagnostic['pages']) == 6 and diagnostic['eligible_source_ids'] == ['S1','S2','S3']
assert diagnostic['final_answer'] is None and not diagnostic['write_confirmed'] and not diagnostic['ack_confirmed']
assert readback['research_files'] == 0 and readback['owned_identities_absent'] and readback['isolated_port_free']
report = R/'docs/reports/jarvis-work-t2-e02-source-coverage-controlled-result-20261107.md'
proposal = R/'docs/plans/jarvis-work-e02-native-writer-http500-diagnostics-proposal-20261107.md'
text = f'''# E02 来源预算联动候选：唯一实际结果与独立复核

候选 {CANDIDATE} 的一次真实当前 8B 受控研究已完成，独立结果为 **FAIL_CONFIRMED**。本例没有交付 research.md，E02 仍 0/3，T2/Owner 未通过。读取预算与来源覆盖联动、公开“未交付”文案均得到本例证据支持；端到端研究仍被原生 HTTP 500 阻断。

## 本例观察到的变化

原预算仍为六次读取。实际顺序是 S1 的 26、50、74、98 行起页，随后 S2 的 20 行起页和 S3 的 25 行起页。诊断记录六次确认读取、S1/S2/S3 三个具备证据卡的来源。前五页 visible=true，第六页 confirmed=true 但 visible=false：后续请求失败，没有把该页提升为已通过响应确认可见。不能据此宣称模型已确认阅读第六页，更不能把来源资格当作已完成原题的事实覆盖。

旧例六读仅有 S1/S2，本例保留四次同源读取后，余下两次用于未覆盖来源，达到了三来源写入资格。冻结源码与可信前缀可重建第七代为 writer/未交付分支、无 inspect 分支，输出上限 2048；完整请求正文没有保留，这些属于源码重建。该请求实际返回 HTTP 500。

产品公开 content 精确为“本次研究未交付。”，status=failed、error=Research HTTP status。没有写入/ACK/research.md，也没有可信成功 runtime proof；私有 final_answer 为空。事实、引用和原题交付覆盖均不可按报告产物验收，零接受信用保留。

## 真实请求与预算

run {RUN}；用户分配 {QUESTION}；入口一次、重试零。执行区间 {execution['started_utc']} 至 {execution['finished_utc']}，外层耗时 {execution['outer_elapsed_seconds']:.6f} 秒。应用记录 native POST 7 次、完成 6 次；最后一次 generation=7、chat、HTTP500、send_reserved=true、transport_failed=true、validated_response=false。

最后请求实体 31270 字节，SHA-256 f2fa2d8c6520f04ac22ed4563d66b722fb1686e5dab6cf4680daba62d8c786f1。错误正文 downloaded/inspected/admitted/retained 均为0。受限诊断 SHA-256 {sha(A/'trusted-failure-diagnostic.raw')}，5481字节，branch=unvalidated_response。预算快照 reads_used=6/6、native_posts=7/8、尚余227.192952秒。该值排除了该快照下的时限耗尽，不能解释 HTTP500 的内部原因；短耗时不是计时验收 PASS。

上层失败 product.tool_results 仅含搜索1/GET4，没有已返回的 inspect 条目；六读次数来自绑定的私有诊断，二者分别保留，不能把上层列表的0误报成没有读取。未测量服务器实际生成开始总数，不用应用计数冒充。

## 独立复核、保护与保全

结果 manifest {RESULT_MANIFEST}，56成员；独立复核 {sha(review_path)}，FAIL_CONFIRMED。准备 manifest 与342项离线检查只证明准备；产品746项是先前封存基线，本例和结果 reviewer 均没有重跑测试。旧候选 E01/E03 通过不迁移至当前候选。

原清理回执 PASS，登记的六个本例进程身份均已消失、隔离端口关闭、日志关闭。七保护身份在实际边界和随后只读核对点相符，不宣称连续存活。未操作 UI/音频或生产服务，未更换8B或原预算。旧实际91406fa9-5952-4e3a-99af-a94c8857c8d3及N14/N13/N12/N11封存保持，当前失败也不覆盖。结果复核为只读，无额外模型或实际调用。

## 接续

本次实际1与结果复核1均已消费，剩余0，失败不重试。下一步见 jarvis-work-e02-native-writer-http500-diagnostics-proposal-20261107.md：先核对写入阶段原生请求与可取得的错误证据，仅根据确证问题设计最小兼容修改。当前状态码和请求摘要不能证明 grammar/解析、上下文、输出或运行器中的任何单一根因。未取得新授权前不修改冻结产品或发起新模型请求。

当前结果和提案同步至项目 docs 与 UltimaDocs，本地 commit/tag/逐字节读回由 result-publication-readback.json 单独记录。此前远端 push 被自动审批以 blocked by policy 拒绝，本轮没有重试。证据根：{N.as_posix()}。
'''
assert not report.exists()
report.write_text(text, encoding='utf8', newline='\n')
pairs = [(report, M/'reports'/report.name), (proposal, M/'plans'/proposal.name)]
for source, target in pairs:
    assert source.exists() and not target.exists()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())
    assert sha(source) == sha(target)
paths = [R/'data/evidence/jarvis-work-capability/T2/current-run.json',
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
    Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-source-coverage-controlled-entry-plan-20261107/progress.md']
before = {str(p): p.read_bytes() for p in paths}
state = json.loads(before[str(paths[0])])
assert state['current_one_case_allocation']['question_id'] == QUESTION
last_actual = dict(schema=1, work_order='wo-ultimaagent-20261101-0021', stage='T2', case='E02-controlled-1',
    purpose='source_coverage_budget_one_case', run_id=RUN, candidate=CANDIDATE, model='qwen3-8b-uncensored',
    model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330', question_id=QUESTION,
    result='FAIL', independent_review='FAIL_CONFIRMED', review_path=str(review_path), review_sha256=sha(review_path),
    result_manifest_sha256=RESULT_MANIFEST, terminal_sha256=sha(A/'terminal.json'), product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1, work_cli_attempts=1, controlled_search_success=1, controlled_GET_success=4,
    confirmed_inspect_pages=6, visible_inspect_pages=5, top_level_successful_inspect_results=0,
    write_attempts=0, successful_write_count=0, research_artifacts=0, application_native_POST_attempts=7,
    completed_native_posts=6, actual_native_start_count=None, outer_elapsed_seconds=execution['outer_elapsed_seconds'],
    cleanup='PASS', root_witness_eligible=False, public_content=product['content'], product_error=product['error'],
    failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'), failure_diagnostic_bytes=5481,
    branch=diagnostic['branch'], eligible_source_ids=diagnostic['eligible_source_ids'], last_http=diagnostic['last_http'],
    selected_pages=[dict(source_id=p['source_id'],start=p['requested_start'],range=p['range'],confirmed=p['confirmed'],visible=p['visible']) for p in diagnostic['pages']],
    budget=diagnostic['budget'], write_confirmed=False, ack_confirmed=False, final_answer_preserved=False,
    false_completion_claim_preserved=False, facts='NOT_ASSESSABLE_NO_ARTIFACT', original_question_coverage='NOT_PASSED_NO_ARTIFACT',
    coverage_budget_link_observed=True, sixth_page_response_confirmed=False, non_delivery_reply_observed=True,
    protected_at_recorded_boundaries=True, protected_after_readonly=True, continuous_liveness_measured=False,
    acceptance_credit=0, controlled_passed=0, controlled_required=3, actual_case_allocation_remaining=0,
    result_review_allocation_remaining=0, retry=0, next_case_released=False, E02='NOT_PASSED', T2='NOT_PASSED',
    Owner='NOT_PASSED', old_credit_transferred=False, remote_synced=False,
    cause='Native generation7 returned HTTP500 after six confirmed reads with three eligible sources; no write or ACK',
    native_compatibility_limit='HTTP500 internal cause unproven; body not read; writer phase is source reconstruction, not retained request body',
    previous_actual_preserved_at=str(N/'inputs/previous-current-run.json'), recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase='SOURCE25_E02_COVERAGE_CONTROLLED_FAIL_REVIEWED',
    workflow_status='blocked', stage_queue_state='BLOCKED', active_review_agent=None, active_evidence=str(N),
    active_product_candidate=CANDIDATE, active_report=str(report), active_plan=str(proposal),
    last_actual_result=last_actual, actual_case_allocation_remaining=0, result_review_allocation_remaining=0,
    e02_execution_released=False, live_gate_released=False, next_stage_released=False, E02='NOT_PASSED', T2='NOT_PASSED',
    current_one_case_allocation=dict(question_id=QUESTION,candidate=CANDIDATE,status='CONSUMED_FAIL_REVIEWED',remaining=0,result_review_remaining=0,retry=0),
    next_action_scope=dict(authorized=False,scope='Follow-up diagnosis proposal only; no new product modification or model request allocated',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(proposal),status='PROPOSAL_ONLY',actual_case_allocation=0,result_review_allocation=0),
    e02_source_coverage_result=last_actual)
state.pop('pending_actual_result', None)
summary = 'E02 e40a55b唯一实际FAIL_CONFIRMED：六读取得三来源证据、回复明确未交付；第7次原生HTTP500，无research.md/写入/ACK；清理及保护核对PASS，单例与独审已耗尽，不重试。'
texts = {str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo, count = re.subn(r'(?m)^- 状态：.*$', '- 状态：'+summary, before[str(paths[1])].decode('utf8'), count=1)
assert count == 1
append = '\n\n## 2026-11-07 E02 source coverage controlled result\n\n'+summary+'\n报告：'+str(report)+'\n后续提案：'+str(proposal)+'\n'
texts[str(paths[1])] = wo+append
texts[str(paths[2])] = before[str(paths[2])].decode('utf8')+append
index, count = re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |', before[str(paths[3])].decode('utf8'))
assert count == 1
texts[str(paths[3])] = index
texts[str(paths[4])] = before[str(paths[4])].decode('utf8')+'\n- Explicit '+QUESTION+' actual1/review1 completed; run '+RUN+' FAIL_CONFIRMED, no retry. Coverage reservation and public refusal observed; native generation7 HTTP500 remains unproven internally.\n- Result manifest '+RESULT_MANIFEST+'; independent review '+sha(review_path)+'. Proposal-only follow-up, allocations0, E02/T2/Owner remain not passed.\n'
snapshot = N/'verification/result-closeout-before'
snapshot.mkdir(exist_ok=False)
for i, p in enumerate(paths):
    assert p.read_bytes() == before[str(p)]
    (snapshot/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:
    p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(summary=summary,review_sha256=sha(review_path),
    result_manifest_sha256=RESULT_MANIFEST,before={p:hashlib.sha256(v).hexdigest() for p,v in before.items()},
    after={str(p):sha(p) for p in paths},mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],
    actual_remaining=0,result_review_remaining=0,acceptance_credit=0))
q = Path('H:/UltimaAI/_shared/queue')
run = subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],
    capture_output=True,text=True,encoding='utf8',timeout=30,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/result-queue-refresh.json',dict(exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,
    generator_sha256=sha(q/'queue-status-gen.py'),queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True))
assert run.returncode == 0
with (N/'verification/result-queue-status.json').open('xb') as stream:
    stream.write((q/'queue-status.json').read_bytes())
print(json.dumps(dict(result='FAIL_CONFIRMED',report=str(report),mirror_files=len(pairs),allocations=0),ensure_ascii=False))
