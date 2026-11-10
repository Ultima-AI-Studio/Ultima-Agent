"""Register the reviewed first result without changing the sealed product or case."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys

N = Path(__file__).resolve().parents[1]
R = N.parents[4]
M = Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
A = N / 'actual/E02-controlled-1'
HEAD = 'd8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
RUN = '1496a844-668d-407a-a91b-89be246ba05b'
QUESTION = 'call_c910dd9e4819410492607baac9ed63bf'
RESULT = 'ab388abe9d994ee56b985c14183d14e2af3530a499de4cfe116a8c1a2315dddf'
REVIEW = '065d3f6fa910976672f01c02850d0c52f1f34567ccaa295451e427efbe0bb9af'
REVIEW_MD = 'fcbb6812680107f7e64597cf5ba35b8da821cf6c39df5469c62ca05ffdaeb84d'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def save(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

def main():
    review_path = N / 'review/independent-result-review.json'
    review = load(review_path)
    assert sha(review_path) == REVIEW and sha(N / 'review/independent-result-review.md') == REVIEW_MD
    assert review['reviewer'] == 'root-independent' and review['verdict'] == 'FAIL_CONFIRMED'
    assert review['candidate'] == HEAD and review['run_id'] == RUN
    assert review['result_manifest_sha256'] == RESULT and review['acceptance_credit'] == 0
    assert review['actual_case_allocation_remaining'] == review['result_review_allocation_remaining'] == 0
    assert not review['next_case_authorized'] and not review['retry']
    assert sha(N / 'review/result-inputs/result-manifest.json') == RESULT
    manifest = load(N / 'review/result-inputs/result-manifest.json')
    for name, digest in manifest['files'].items():
        assert sha(N / name) == digest, name
    product = load(A / 'product-result.json')
    terminal = load(A / 'terminal.json')
    execution = load(N / 'release/tool-execution-receipt.json')
    runtime = load(A / 'trusted-runtime.raw')
    witness = load(N / 'release/root-outcome.json')['outcome']['witness']
    observed = load(N / 'review/result-inputs/readonly-closeout.json')
    protocol = review['protocol_assessment']
    assert execution['question_id'] == QUESTION and execution['invocations'] == 1 and execution['retry'] == 0
    assert terminal['run_id'] == RUN and terminal['overall'] == 'PENDING_ROOT_INDEPENDENT_REVIEW'
    assert terminal['cleanup']['status'] == 'PASS' and product['status'] == 'succeeded' and product['error'] is None
    assert protocol['actual_report_dispatches'] == protocol['actual_file_writes'] == protocol['accepted_effects'] == protocol['files'] == 1
    assert protocol['raw_research_write_success_rows'] == 2 and protocol['export_complete'] and protocol['END'] and protocol['ack_admitted']
    assert runtime['transport']['posts'] == runtime['transport']['completed'] == terminal['application_native_POST_attempts'] == 8
    assert review['full_question_coverage']['verdict'] == 'FAIL' and len(review['claim_reviews']) == 9
    assert sum(row['citation_verdict'] == 'PASS' for row in review['claim_reviews']) == 1
    assert review['timing_assessment']['verdict'] == 'ORIGINAL_TIMING_GATE_SUPPORTED' and witness['eligible']
    assert all(witness['proofs'].values()) and observed['protected_count'] == 7 and observed['protected_all_equal']
    artifact = review['artifact']
    assert sha(Path(artifact['path'])) == artifact['sha256'] == 'ac34309cd889594ef4569020d1ac922290aba38fa8285e82748d549925785e0f'
    assert len(Path(artifact['path']).read_bytes()) == artifact['bytes'] == 2458
    effects = load(A / 'accepted-effects.json')
    assert len(effects) == 1 and effects[0]['sha256'] == artifact['sha256']
    report = R / 'docs/reports/jarvis-work-t2-e02-claim-generation-controlled-result-20261108.md'
    proposal = R / 'docs/plans/jarvis-work-e02-source-grounding-and-coverage-proposal-20261108.md'
    paths = [N.parent / 'current-run.json', R / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
             R / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md', Path('H:/UltimaAI/_shared/queue/global-queue-index.md'), N / 'progress.md']
    before = {str(p): p.read_bytes() for p in paths}
    state = json.loads(before[str(paths[0])])
    assert state['current_one_case_allocation']['question_id'] == QUESTION
    assert state['last_actual_result']['run_id'] == 'c4caa739-c466-44f3-866b-0c57ea8c5e40'
    assert state['pending_actual_result']['run_id'] == RUN
    assert state['actual_case_allocation_remaining'] == state['result_review_allocation_remaining'] == 0
    for p in [report, proposal, M / 'reports' / report.name, M / 'plans' / proposal.name,
              N / 'verification/result-closeout-registration.json', N / 'review/result-final-registration.json',
              N / 'verification/result-source-analysis.json', N / 'verification/result-goal-registry-observation.json',
              N / 'verification/result-closeout-before']:
        assert not p.exists(), str(p)
    china = dt.timezone(dt.timedelta(hours=8))
    started = dt.datetime.fromisoformat(execution['started_utc']).astimezone(china).isoformat()
    finished = dt.datetime.fromisoformat(execution['finished_utc']).astimezone(china).isoformat()
    analysis = dict(kind='ROOT_READONLY_SOURCE_ANALYSIS_AFTER_SEALED_RESULT', candidate=HEAD, run_id=RUN,
        result_manifest_sha256=RESULT, review_sha256=REVIEW,
        source_hashes={str(p): sha(p) for p in (C / 'src/brain/agent_server.py', C / 'src/brain/work_navigation.py')},
        confirmed_facts=dict(artifact=True, writer_stop_eval_count=728, ack_stop_eval_count=31,
            source_pages=review['full_question_coverage']['source_coverage']['inspect_pages'],
            citation_pass_claims=[7], independent_blockers=[row['id'] for row in review['findings']]),
        static_observations=[
            'work_navigation.py:415-437 already requires exact anchors, distinct projects, TODO/runtime separation and original-question coverage; adding the same admonition alone is not evidence of a fix.',
            'work_navigation.py:465-486 reserves remaining inspect calls only for the minimum of three sources; available fourth source is not reserved by this contract.',
            'agent_server.py:616-634 and work_navigation.py:500-556 enable and bind writer structure/cards after three sources; valid IDs/exact operation do not prove semantic entailment.',
            'Actual generation7 sampler fact properties are claim then evidence_id; this is a candidate design question, not proof that property order caused misattribution.',
        ],
        limits='No product edits, tests, model calls or next candidate. Proposed evidence-first generation and task-relevant read coverage require independent design review; no guarantee from keyword/card/field-order checks.',
        actual_cases=0, model_calls=0, product_changes=0, in_original_result_manifest=False)
    report_text = f'''# E02 代码事实生成候选：单例结果与独立复核

原工单 wo-ultimaagent-20261101-0021 / T2；冻结候选 {HEAD}。本次唯一当前 8B 受控研究实际生成并写入 research.md，读回和 ACK 成立；独立结论 **FAIL_CONFIRMED**，因为事实引用和完整原题覆盖失败。E02 仍 0/3，T2/Owner 未通过。本报告保留真实产物，不把内容失败误写成“未生成文件”。

## 已完成的实际链路

用户问题 {QUESTION} 分配 actual1 / result review1 / retry0。run {RUN}，北京时间 {started} 至 {finished}；外层耗时 {execution['outer_elapsed_seconds']:.6f} 秒。原入口仅调用一次、CLI一次；应用原生 POST8、完成8。服务端实际生成启动总数未测量，保持 null。模型 qwen3-8b-uncensored，digest {protocol['model_digest']}。

第7次 writer HTTP 响应 done_reason=stop、eval_count=728，原输出上限2048；第8次 ACK stop、eval_count=31，阶段上限256。八次均 stop。本例没有出现上一例的 length/2048 截断；这只证明本例完成，不能从单例推断重复问题已稳定解决。

产品 status=succeeded；可信导出 complete/END/ack_admitted 均成立。实际报告分派1、文件写入1、接受副作用1。顶层两条 research_write 成功行分别是 SDK 摘要与带 call_id 的账本记录，不是两次写入；seq7、同一 dispatch、嵌套 file_call 与唯一 effect 一致。

- [实际生成的 research.md（事实验收未通过）]({Path(artifact['path']).as_posix()})，2458字节，3节9条事实；SHA256 {artifact['sha256']}。
- [独立逐事实复核]({(N / 'review/independent-result-review.md').as_posix()})；JSON SHA256 {REVIEW}，Markdown SHA256 {REVIEW_MD}。

## 内容失败的确证

九条陈述中仅第7条 Date.now 查询开始时间的局部事实及引用通过；其余8条存在错引、所引范围不足或实现上下文遗漏。这不等同于“八条全是假话”：有些结论在完整源码中可得到支持，但本报告指定的引用不能支持它们。

| 陈述 | 独审确证问题 |
| --- | --- |
| 1、2 | 把模型名称和双击 Fn 等不同位置内容合并到较窄的单一证据卡；所引范围不足。 |
| 3、5、6 | 分别把 unified-agent 工具调用、日志、OpenJarvis 行为挂到 README 或 AgentManager TODO 的无关证据卡。 |
| 4 | TODO确实存在，但据此描述 Gemini 仍待未来接入，遗漏同版本 AgentManager L48–51 已构造 GeminiProvider 的代码。 |
| 8、9 | 单处日志调用被扩成初始化与查询全过程的广泛结论，并重复占用正文。 |

原题要求任务架构与现有开源接入，产物没有连贯说明 AgentManager、provider、UnifiedAgent、ToolRegistry 的执行关系与回退路径，也没有正确区分 Jarvis.ceo 参考项目与现有 OpenJarvis 执行底座。不能从本资料断言 Jarvis.ceo 本身接入了 OpenJarvis。

search1/GET4；inspect6的分布为 S1四页（26–49、53–76、92–115、121–144）、S2一页（20–43）、S3一页（25–48），S4 inspect0。S4下载成功不等于实际阅读；目录导航提示不是事实证据。三来源只满足写入最低资格，不满足原题覆盖。本次仍为固定受控corpus验证，不代替真实互联网搜索验收。

## 原约束、时限与保护

原预算 CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384；输出最多2048，较小阶段上限保持。没有重试、换模型、加预算或修改产品默认值，没有UI、音频、生产服务操作。

原terminal的 timing_eligibility=UNOBSERVED_NEVER_TIMED_PASS 和 PENDING_ROOT_INDEPENDENT_REVIEW 原样保留，不改封存终态。独审使用绑定本run、terminal哈希、seal及38成员的外层 root witness：eligible=true，closed/cleanup/pins/protected/readback均true；最终运行事件及74.2462801秒的root观测处在原截止内。原时限证据成立，不能只凭75.54秒墙钟得出此结论。

清理PASS：本例六个身份均退出、18799端口关闭、日志闭合；原边界及事后保存观测点七个保护身份相符。上述结论仅覆盖保存的观测点，不保证持续存活或报告时实时状态。

## 登记与下一步

本次一例及一次结果独审已全部消费，剩余0，不释放下一例。结果manifest {RESULT}，67成员；394准备成员、78源码pin及1602输入保持，1004产品准备检查/350入口检查是既有离线准备，本次没有重跑或转为实际信用。旧失败及旧E01/E03历史保留，不将旧候选通过信用转移到当前候选。

下一步[具体提案]({proposal.as_posix()})围绕逐来源证据表达与题目覆盖，先核对真实选页、证据卡和生成表达，再确定最小改动。现有提示已包含“精确锚点、TODO不是实现、区分项目、完整原题”等约束；不能只重复提示后宣布修好，也不能把schema合法当语义可信。提案未实施、未独审，没有新的产品或实跑授权。

结果与本提案镜像至 UltimaDocs；本地提交/tag和逐文件读回见 verification/result-publication-readback.json、result-final-readback.json。result-source-analysis.json是封存后根controller只读补充，未加入原67成员manifest，另随本次发布保留。远端push此前被自动审批以blocked by policy拒绝；本轮不重试或换通道，本地归档不等于远端同步。

证据根：{N.as_posix()}。
'''
    proposal_text = f'''# E02 逐来源事实绑定与原题覆盖：下一步提案

状态：**提案，未实施、未独审、无新单例分配**。原工单 wo-ultimaagent-20261101-0021 / T2；冻结父候选 {HEAD}。依据唯一run {RUN}及独立FAIL_CONFIRMED结果，保持当前社区8B、原预算和完整原题验收。

## 目标与已确证问题

目标仍是实际阅读、完成有准确来源的研究文档，并通过事实、原题覆盖、写入读回、ACK、原时限与独立结果复核。本例已完成写入链路，但9条陈述只有1条事实和所选引用同时通过；第3/5/6条错引其他来源，第1/2/8/9条合并超出锚点的内容，第4条将TODO扩为当前实现结论。S4仅GET未inspect；架构和现有接入未完整回答。不得用机械成功掩盖上述失败。

## 建议顺序与范围

1. 固定本次实际research.md、九条独立判定、writer请求、六页及卡片为只读负例。分清“来源没有读到”“页面读到但卡片未选”“卡片已选但断言超出锚点”三类；不能手改本次报告或给旧失败补证据。
2. 先审查选页与题目覆盖的衔接：现在六读预算只为最低三来源保底，S1消耗四次后只剩S2/S3各一次。核对目录对题目相关架构入口、实现分支和独立底座的表达，以及如何在原六次读取内保留这些信息的覆盖机会。缺证时应明确未交付或不足，不能用日志细节凑满三来源。不得由harness硬编码页号、替模型选页或放宽原题。
3. 审查“先绑定该来源证据，再写由锚点直接支持的原子断言”的生成结构。当前同一事实对象为claim后evidence_id，评论/文档自由文本仍可挂错来源；精确operation只约束术语，不约束语义。优先核验官方schema能否表达更清楚的逐来源、逐证据关系及生成/重放一致性，再决定最小改动；仅调整字段顺序或增加提示不能宣称证明真实，不能引入关键词判真或由controller代写内容。
4. 保留原严格事实门和独立复核。TODO仅能证明该注释存在；陈述当前接入必须实际读取相关实现，不得把“未读取”写成“未实现”。区分Jarvis.ceo参考项目与OpenJarvis底座；组合多个锚点的信息时应能表达准确出处，或拆成各自可支持的原子事实，不能扩大证据卡含义。
5. 只有离线设计和负例证明定位到具体接口问题后，才在新隔离候选做最小修复、必要回归与独立准备审查，再准备受控入口。当前候选和本次失败原样冻结。新真实8B单例仍需另行明确分配，不自动重跑。

## 拟议写域及离线验收

取得下一范围后，先在docs/plans落具体实施方案并独立审查；产品差异优先限于src/brain/work_navigation.py的选页覆盖/逐来源生成契约及src/brain/agent_server.py的对应共享适配，加确证所需回归。若必须改证据协议、渲染/写入语义或更多文件，先把理由、兼容差异、完整原题表达能力写入新方案，不自动扩大。

原页/卡片权限、实际写入事务、END/读回/ACK、原时钟和清理保持。离线验收必须说明每项修复能保证哪一个结构属性、仍需独立语义复核的边界；真实错引和跨锚点泛述必须保留为验收负例。保持原题、四来源固定版本、三来源最低门及原完整覆盖要求，不通过压缩题目、降低事实标准或手工填充事实取得通过。

继续qwen3-8b-uncensored，CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒，context16384，输出最多2048及较小阶段上限保持。零新增模型调用的离线准备不能证明模型实际成功；单例写入成功也不能证明稳定性。原受控3/3、真实联网和T2/Owner门保持；不挪用旧E01/E03信用。

本提案不包含换模型、14B、下载更新、UI/音频、生产服务或保护进程操作；不允许修补残缺JSON、接受length或按固定题目拼装答案。若现有证据不足以支持最小代码改动，应交付明确设计缺口，不再盲改提示并消耗实跑。

## 审查依据与授权边界

- [本次独立结果复核]({(N / 'review/independent-result-review.md').as_posix()})：JSON {REVIEW}，结果manifest {RESULT}。
- [结果报告]({report.as_posix()})与[根controller只读源码分析]({(N / 'verification/result-source-analysis.json').as_posix()})。补充分析不冒充原结果独审的一部分。
- 当前work_navigation.py:415–437已有语义提示；465–486只为三来源预留读额度；500–556绑定可见卡片与writer结构。agent_server.py:616–634负责阶段资格与共享schema。这些源码事实支持审查方向，不证明未来修复效果。

用户本次明确仅分配一例实际研究和一次只读结果复核，两项已用完。建议下一授权只覆盖本提案的离线设计核验、依据确证的最小补修、必要独审和入口准备；新候选实跑另行分配。此文件不生成任何grant或运行权。
'''
    save(N / 'verification/result-source-analysis.json', analysis)
    save(N / 'verification/result-goal-registry-observation.json', dict(
        source='get_goal tool read during this closeout; no update_goal called', thread_id='01a19670-9bc2-7c01-b42a-c298e043954c',
        status='blocked', tool_updated_at=1794072224, tokens_used=42351234, time_used_seconds=256646,
        note='Existing goal status remains blocked; explicit current one-case grant completed, broad E01-E08 objective incomplete. No resume or complete claim.'))
    for p, text in ((report, report_text), (proposal, proposal_text)):
        with p.open('x', encoding='utf8', newline='\n') as f:
            f.write(text)
    mirror = []
    for p, category in ((report, 'reports'), (proposal, 'plans')):
        target = M / category / p.name
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open('xb') as f:
            f.write(p.read_bytes())
        mirror.append(dict(source=str(p), target=str(target), sha256=sha(p)))
    actual = dict(schema=1, work_order='wo-ultimaagent-20261101-0021', stage='T2', case='E02-controlled-1',
        purpose='claim_generation_contract_one_case', run_id=RUN, candidate=HEAD, model=protocol['model'], model_digest=protocol['model_digest'],
        question_id=QUESTION, result='FAIL', independent_review='FAIL_CONFIRMED', review_path=str(review_path), review_sha256=REVIEW,
        result_manifest_sha256=RESULT, terminal_sha256=sha(A / 'terminal.json'), product_result_sha256=sha(A / 'product-result.json'),
        entry_invocations=1, work_cli_attempts=1, controlled_search_success=1, controlled_GET_success=4, confirmed_inspect_pages=6,
        raw_research_write_success_rows=2, actual_report_dispatches=1, write_attempts=1, successful_write_count=1, research_artifacts=1,
        artifact_path=artifact['path'], artifact_sha256=artifact['sha256'], artifact_bytes=2458,
        application_native_POST_attempts=8, completed_native_posts=8, actual_native_start_count=None,
        outer_elapsed_seconds=execution['outer_elapsed_seconds'], timing_eligibility=terminal['timing_eligibility'],
        independent_timing_assessment=review['timing_assessment'], cleanup='PASS', root_witness_eligible=True,
        root_witness_observation_error=witness.get('observation_error'), product_status='succeeded', product_error=None,
        public_content=product['content'], write_confirmed=True, ack_confirmed=True, runtime_END=True,
        writer_done_reason='stop', writer_eval_count=728, ack_done_reason='stop', ack_eval_count=31,
        facts='FAIL', original_question_coverage='FAIL', claim_reviews=review['claim_reviews'], findings=review['findings'],
        coverage=review['full_question_coverage'], protected_at_recorded_boundaries=True, protected_after_readonly=True,
        continuous_liveness_measured=False, acceptance_credit=0, controlled_passed=0, controlled_required=3,
        actual_case_allocation_remaining=0, result_review_allocation_remaining=0, retry=0, next_case_released=False,
        E02='NOT_PASSED', T2='NOT_PASSED', Owner='NOT_PASSED', old_credit_transferred=False, remote_synced=False,
        cause='Artifact/write/readback/ACK completed; independent facts, exact citations and original-question coverage failed',
        mechanical_delivery_observed=True, acceptable_research_delivery_proven=False, stability_proven=False,
        previous_actual_preserved_at=str(N / 'verification/result-closeout-before/0-current-run.json'),
        recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    state['previous_actual_result'] = state['last_actual_result']
    next_work = 'Review concrete source-grounding and coverage proposal; no new product change, actual case or independent review allocated'
    state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase='SOURCE35_E02_CLAIM_GENERATION_CONTROLLED_FAIL_REVIEWED',
        workflow_status='blocked', stage_queue_state='BLOCKED', active_review_agent=None, active_evidence=str(N), active_candidate=HEAD,
        active_product_candidate=HEAD, active_report=str(report), active_plan=str(N / 'execution-proposal.md'), last_actual_result=actual,
        latest_actual_candidate=HEAD, active_result_review=dict(verdict='FAIL_CONFIRMED', path=str(review_path), sha256=REVIEW, scope='LATEST_ACTUAL_CURRENT_CANDIDATE_D8F8D97'),
        actual_case_allocation_remaining=0, result_review_allocation_remaining=0, e02_execution_released=False, live_gate_released=False,
        next_stage_released=False, E02='NOT_PASSED', T2='NOT_PASSED', e02='NOT_PASSED', t2='NOT_PASSED', owner_gate='NOT_PASSED',
        current_e02_controlled_passed=0, e02_claim_generation_result=actual,
        current_one_case_allocation=dict(question_id=QUESTION, candidate=HEAD, status='CONSUMED_FAIL_REVIEWED', remaining=0, result_review_remaining=0, retry=0),
        current_actual_execution=dict(question_id=QUESTION, candidate=HEAD, run_id=RUN, status='COMPLETE_FAIL_REVIEWED', entry_invocations=1, retry=0),
        new_live_cases_this_execution=1, new_work_cli_submissions_this_execution=1, new_completed_inference_events_this_execution=None,
        new_completed_native_posts_this_execution=8, new_native_total_start_count_this_execution=None,
        new_model_calls_counter_basis='Eight completed native HTTP POST receipts; server-side total starts not measured',
        explicit_user_execution_status='COMPLETE_CLAIM_GENERATION_ONE_CASE_AND_RESULT_REVIEW_FAIL',
        goal_turn_outcome='ONE_CASE_AND_REVIEW_COMPLETED_DELIVERY_OBSERVED_FACTS_AND_COVERAGE_FAILED',
        goal_registry_status='blocked', goal_status='blocked',
        goal_registry_note='get_goal remains blocked; explicit single-case grant completed. No tool-controlled resume or completion; broad objective incomplete.',
        latest_readonly_runtime_receipt=str(N / 'review/result-inputs/readonly-closeout.json'),
        latest_readonly_runtime_sha256=sha(N / 'review/result-inputs/readonly-closeout.json'),
        live_runtime_readiness='PASSED_AT_SAVED_CASE_PREFLIGHT_NOT_A_CURRENT_LIVENESS_CLAIM',
        next_action_scope=dict(authorized=False, scope='Proposed offline source grounding and task coverage review and evidence-led repair; future actual allocation separate',
            actual_case_allocation=0, result_review_allocation=0, model_calls=0, service_operations=0),
        next_proposal=dict(path=str(proposal), kind='EVIDENCE_LED_OFFLINE_SOURCE_GROUNDING_AND_COVERAGE_PROPOSAL', status='PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED',
            actual_case_allocation=0, result_review_allocation=0), next_work=next_work, next_action=next_work, next_offline_plan=str(proposal))
    state['source35_preparation']['status'] = 'COMPLETED_USED_BY_ONE_ACTUAL'
    state['active_preparation']['status'] = 'COMPLETED_ACTUAL_CONSUMED'
    state['e02_claim_generation_controlled_preparation'].update(status='COMPLETED_USED_BY_ONE_ACTUAL', scope='Historical offline preparation only; latest result in e02_claim_generation_result',
        new_candidate_actual_output_not_yet_captured=False, actual_result_run_id=RUN, mechanical_delivery_observed=True, acceptable_research_delivery_proven=False)
    state.pop('pending_actual_result', None)
    summary = 'E02 d8f8d97唯一实际已写research.md并完成读回/ACK；独审FAIL_CONFIRMED：引用错配、锚点范围不足及原题覆盖失败，0/3。清理及保护观测点PASS；一例与一次复核耗尽，不重试。'
    wo, count = re.subn(r'(?m)^- 状态：.*$', '- 状态：' + summary, before[str(paths[1])].decode('utf8'), count=1)
    assert count == 1
    appendix = '\n\n## 2026-11-08 E02 claim generation controlled result\n\n' + summary + '\n报告：' + str(report) + '\n后续提案（尚未实施）：' + str(proposal) + '\n'
    index, count = re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
        '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | ' + summary + ' |', before[str(paths[3])].decode('utf8'))
    assert count == 1
    texts = {str(paths[0]): json.dumps(state, ensure_ascii=False, indent=2) + '\n', str(paths[1]): wo + appendix,
             str(paths[2]): before[str(paths[2])].decode('utf8') + appendix, str(paths[3]): index,
             str(paths[4]): before[str(paths[4])].decode('utf8') + f'\n- Explicit {QUESTION} actual1/review1 completed: {RUN} FAIL_CONFIRMED; remaining0/retry0.\n- research.md/write/readback/END/ACK completed; facts/citations and coverage FAIL, acceptance0. Native POST8, writer stop728, ACK stop31.\n- Result manifest {RESULT}; independent review {REVIEW}; next offline proposal only, product unchanged.\n'}
    backup = N / 'verification/result-closeout-before'
    backup.mkdir(exist_ok=False)
    for i, p in enumerate(paths):
        assert p.read_bytes() == before[str(p)], str(p)
        (backup / (str(i) + '-' + p.name)).write_bytes(before[str(p)])
    for p in paths:
        p.write_text(texts[str(p)], encoding='utf8', newline='\n')
    registration = dict(summary=summary, run_id=RUN, candidate=HEAD, review_sha256=REVIEW, review_markdown_sha256=REVIEW_MD,
        result_manifest_sha256=RESULT, result='FAIL_CONFIRMED', before={p: hashlib.sha256(b).hexdigest() for p, b in before.items()},
        after={str(p): sha(p) for p in paths}, mirror=mirror, actual_remaining=0, result_review_remaining=0, acceptance_credit=0)
    save(N / 'verification/result-closeout-registration.json', registration)
    save(N / 'review/result-final-registration.json', dict(status='FAIL_CONFIRMED', run_id=RUN, candidate=HEAD,
        supersedes_pending_registration_sha256=sha(N / 'review/result-registration.json'), review_sha256=REVIEW,
        result_manifest_sha256=RESULT, actual_remaining=0, result_review_remaining=0, research_files=1, write_confirmed=True, ack_confirmed=True,
        facts='FAIL', coverage='FAIL', acceptance_credit=0, next_case_authorized=False, retry=False))
    q = Path('H:/UltimaAI/_shared/queue')
    assert sha(q / 'queue-status-gen.py') == 'da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
    refresh = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(q / 'queue-status-gen.py')], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
    save(N / 'verification/result-queue-refresh.json', dict(exit_code=refresh.returncode, stdout=refresh.stdout.decode('utf8'), stderr=refresh.stderr.decode('utf8'),
        generator_sha256=sha(q / 'queue-status-gen.py'), queue_sha256=sha(q / 'queue-status.json'), semantic_registration_only=True))
    assert refresh.returncode == 0
    with (N / 'verification/result-queue-status.json').open('xb') as f:
        f.write((q / 'queue-status.json').read_bytes())
    print(json.dumps(dict(result='FAIL_CONFIRMED', report=str(report), proposal=str(proposal), mirror_files=2,
        actual_remaining=0, review_remaining=0, research_files=1, acceptance_credit=0), ensure_ascii=False))

if __name__ == '__main__':
    main()
