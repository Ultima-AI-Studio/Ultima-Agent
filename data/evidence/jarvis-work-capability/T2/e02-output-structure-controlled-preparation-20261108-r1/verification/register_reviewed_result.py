"""Publish the first reviewed failure as metadata; no product or runtime execution."""
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
C = Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
A = N / 'actual/E02-controlled-1'
HEAD = 'bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
RUN = 'c4caa739-c466-44f3-866b-0c57ea8c5e40'
QUESTION = 'call_5c06d21b59b8475b873814f857990cc3'
RESULT = '2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0'
REVIEW = '119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58'
REVIEW_MD = '8cd8a688ba46904df153cc95677546bb2ce49900cc442d0ad9d0ff8c6b7bfa0b'

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def load(p):
    return json.loads(p.read_bytes())

def save(p, value):
    with p.open('x', encoding='utf8', newline='\n') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)

review_path = N / 'review/independent-result-review.json'
review = load(review_path)
assert sha(review_path) == REVIEW
assert sha(N / 'review/independent-result-review.md') == REVIEW_MD
assert review['reviewer'] == 'root-independent' and review['verdict'] == 'FAIL_CONFIRMED'
assert review['candidate'] == HEAD and review['run_id'] == RUN
assert review['result_manifest_sha256'] == RESULT and review['acceptance_credit'] == 0
assert review['actual_run_authorized'] is False
manifest_path = N / 'review/result-inputs/result-manifest.json'
assert sha(manifest_path) == RESULT
manifest = load(manifest_path)
for name, digest in manifest['files'].items():
    assert sha(N / name) == digest, name

product = load(A / 'product-result.json')
d = load(A / 'trusted-failure-diagnostic.raw')
terminal = load(A / 'terminal.json')
execution = load(N / 'release/tool-execution-receipt.json')
rb = load(N / 'review/result-inputs/byte-readback.json')
observed = load(N / 'review/result-inputs/readonly-closeout.json')
witness = load(N / 'release/root-outcome.json')['outcome']['witness']
native = d['native_response']
http = d['last_http']
structure = review['output_structure']
assert execution['question_id'] == QUESTION and execution['invocations'] == 1 and execution['retry'] == 0
assert terminal['run_id'] == RUN and terminal['overall'] == 'FAIL' and terminal['cleanup']['status'] == 'PASS'
assert product['status'] == 'failed' and product['content'] == '本次研究未交付。'
assert product['error'] == 'Invalid native research response'
assert native == review['protocol']['native_response'] and http == review['protocol']['last_http']
assert native['reason'] == 'done_reason' and native['done_reason'] == 'length'
assert native['eval_count'] == native['max_tokens'] == 2048
assert native['generation'] == http['generation'] == 7
assert native['receipt_index'] == http['receipt_index'] == 20 and http['status'] == 200
assert http['request_sha256'] == '7ea5d03b00114892b37051cd2aa098527c6d785d5d45dc137de8014c9e29a156'
assert native['response_sha256'] == 'e74c0488b0101002e58930780774e517f5dadd26ee2cb8894a457bef63b3effe'
assert structure['mode'] == 'FULL' and structure['omitted_chars'] == 0
assert structure['content_chars'] == 3818 and structure['content_utf8_bytes'] == 8872
assert sorted(structure['literal_repeat_counts'].values()) == [49, 50]
assert rb['research_files'] == 0 and not d['write_confirmed'] and not d['ack_confirmed']
assert rb['owned_identities_absent'] and rb['isolated_port_free']
assert observed['protected_count'] == 7 and observed['protected_all_equal']

report = R / 'docs/reports/jarvis-work-t2-e02-output-structure-controlled-result-20261108.md'
proposal = R / 'docs/plans/jarvis-work-e02-claim-generation-contract-proposal-20261108.md'
china = dt.timezone(dt.timedelta(hours=8))
started = dt.datetime.fromisoformat(execution['started_utc']).astimezone(china).isoformat()
finished = dt.datetime.fromisoformat(execution['finished_utc']).astimezone(china).isoformat()
converter = N.parent / 'e02-native-pattern-json-20261107-r1/inputs/upstream/json-schema-to-grammar.cpp'
analysis = dict(
    kind='READONLY_SOURCE_ANALYSIS_AFTER_SEALED_RESULT', candidate=HEAD, run_id=RUN,
    result_manifest_sha256=RESULT, review_sha256=REVIEW,
    sources={str(p): sha(p) for p in (C / 'src/brain/agent_server.py', C / 'src/brain/work_navigation.py', converter)},
    evidence_observation='FULL content repeats inside an unterminated claim string before length/2048 refusal',
    source_observation='Sampler drops maxLength and permits an unbounded JSON-character prefix/suffix around an exact code operation; pinned converter handles pattern before maxLength',
    inference_limit='Possible structural contributor, not a proven sole internal cause; restoring maxLength alone is not demonstrated as effective',
    next_design_status='PROPOSAL_ONLY_NOT_IMPLEMENTED_OR_INDEPENDENTLY_APPROVED',
    model_calls=0, actual_cases=0, product_changes=0)
save(N / 'review/result-inputs/structural-analysis.json', analysis)

report_text = f'''# E02 输出结构诊断候选：单例结果与独立复核

原工单 wo-ultimaagent-20261101-0021 / T2。候选 {HEAD} 的唯一当前 8B 原题四来源研究已经结束，独立结论 **FAIL_CONFIRMED**。没有交付 research.md，E02 仍 0/3，T2/Owner 未通过。本轮新增的是完整截断内容的证据，未证明研究能力修复成功。

## 运行与结果

用户问题 {QUESTION} 明确分配 actual 1 / 结果独审 1 / retry 0。run {RUN}，北京时间 {started} 至 {finished}，外层耗时 {execution['outer_elapsed_seconds']:.6f} 秒。只调用原入口一次，CLI 一次；应用原生 POST 7 次、完成 7 次，服务端实际生成启动总数未测量。

产品 status=failed，error=Invalid native research response，公开回复“本次研究未交付。”。research.md、write、ACK 均为 0，无可信 runtime END。没有重试，本次运行及结果复核额度均已消费。

原预算保持：CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315 秒；context16384，输出最多2048，阶段较小上限保持。模型仍 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四来源、事实/引用/覆盖门保持；没有 UI、音频、生产服务、安装下载或14B操作。

## 本次新确证的截断位置

第7次 HTTP200 响应 done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8908。请求 {http['request_bytes']} 字节，SHA256 {http['request_sha256']}；响应计数 {native['response_bytes']} 字节，SHA256 {native['response_sha256']}。这些摘要在可信诊断中交叉绑定，独审没有重放完整 HTTP 请求/响应。

v5 私有诊断 {sha(A / 'trusted-failure-diagnostic.raw')}，16301 字节，未超过原16384上限。FULL 保留完整 content 3818 字符 / 8872 UTF-8 字节，无省略；content SHA256 {structure['content_sha256']}。完整正文严格 JSON 解析失败，UNTERMINATED_STRING，pos1339 / line45 / column22；独审重算相同。

未闭合 claim 引号后有2478字符，其中“支持多种LLM模型和工具的集成，实现灵活的交互方式。”出现50次，“支持本地和云服务的混合使用，以平衡速度与隐私。”出现49次，之后耗尽输出额度。以上为完整原文统计，没有补括号、修复JSON或执行残缺动作。schema_valid/shape仍为空。请求think=false、消息thinking字段缺失，不能据此反推所有内部token分配。

旧候选0421a54及d860b2a的失败仍原样保留；旧回执未保存正文，不能用本次正文补写旧结论，也不能认定它们必然有相同重复模式。

## 事实、引用与原题覆盖

独审发现残缺原文中的具体错配风险：N3.42ae675651f972c7对应S1第28–29行融资/开源背景，却伴随UnifiedAgent工具断言；N3.1eb7eea60301cfb6对应S2第39行OpenAI/Gemini尚待实现的TODO，却伴随集成和模块化泛述。末尾“效率、用户体验改善”也不是S3日志和时间戳代码可单独证明的效果。

这些是原文与证据卡/原始来源的诊断对照，不是接受部分JSON或完成事实验收。事实、引用、原题覆盖均NOT_PASSED；修复截断不自动修复以上问题。

search1/GET4；六次确认读取分布为S1四页、S2一页、S3一页，没有S4 inspect。S3 confirmed=true / visible=false保持原账本含义，不把visible=false解释为未读。顶层成功inspect结果0与私有六次确认读取属于不同观察层。三来源写入资格不能代替完整原题；受控corpus也不能代替原真实联网门。

## 源码检查与后续顺序

当前agent_server.py:217–259的采样投影移除了maxLength，代码事实pattern允许在精确operation前后继续生成无界合法JSON字符。冻结的llama.cpp b10488转换器json-schema-to-grammar.cpp:961–975先处理pattern，后处理maxLength，不能假设恢复maxLength就会同时限制有pattern的字段。这是可疑结构条件，不是对模型内部重复机制的唯一归因。

建议按[下一步提案]({proposal.as_posix()})先离线处理代码事实的生成表达：核验“先输出证据绑定的精确operation，再写原子说明”的官方pattern表示与有界表达兼容性；将本次重复及引用错配作为必须保留的负例。暂不改写事务、加预算或迁移模型。新设计须证明原题完整表达能力、JSON合法性、同请求生成/重放一致，再确定最小代码差异。提案尚未实施或独审，不授予下一例。

## 清理、时限与归档

原cleanup PASS；六个本例身份在事后核对点不在、隔离端口18799关闭、日志闭合。保存的运行边界及事后七个保护身份一致，不声称连续存活或报告时仍为同一实时状态。root witness eligible=false、observation_error=ValueError，时限资格仍UNOBSERVED_NEVER_TIMED_PASS；65.46秒观测不能升级为时限通过。

结果manifest {RESULT}（56成员），独立结果JSON SHA256 {REVIEW}，Markdown SHA256 {REVIEW_MD}。175准备成员、77产品源码及1598输入钉住值保持；979产品/兼容检查和350入口检查属于既有准备，不是本次新通过的实际验收。旧E01/E03通过信用不转移到本候选。

output-text-observation.json及structural-analysis.json是封存后只读补充，明确不在原56成员结果manifest中；本次结果发布另行收录。项目/UltimaDocs本地提交、tag及读回见本证据根verification/result-publication-readback.json、result-final-readback.json。本地归档不代表远端同步；此前自动审批以blocked by policy拒绝push，本轮未重试或更换通道。

证据根：{N.as_posix()}。
'''
proposal_text = f'''# E02 代码事实生成契约：基于实测截断的下一步提案

状态：**提案，未实施、未独审、没有新实跑分配**。沿用原单wo-ultimaagent-20261101-0021 / T2，当前冻结父候选{HEAD}。本文件来自唯一实跑{RUN}和独立FAIL_CONFIRMED结果，不扩展刚完成的actual1/review1授权。

## 目标与确证问题

继续只用当前社区8B、原预算及完整原题验收。目标仍是实际读取原四来源、形成逐事实可核验的完整research.md，并完成原写入读回和ACK；不能把生成合法JSON或诊断成功当交付。

本次完整正文证明：第7响应在未闭合claim中重复两句50/49次，length/2048终止，未写入。独审还记录两组具体证据卡错配和效果泛述风险。该结果支持缩小生成表达的自由度，不证明单改提示、恢复maxLength或缩短文本就能满足事实与覆盖要求。

## 建议的离线工作顺序

1. 从本次封存FULL正文及其请求摘要建立只读失败样本，保留pos1339/line45/column22、重复计数、四来源与预算绑定。核对源码与冻结官方转换器；不导入或运行生产服务，不调用模型。
2. 优先审查最小方向：代码事实的采样表达从“无界前缀后再出现精确operation”改为“先输出本证据卡绑定的精确operation，再给原子说明”，保留JSON完整转义与解码后严格词边界。这只调整同一受支持官方pattern/schema对接，不自造采样器或代写研究正文。前缀收敛不等于后缀有界，必须一并评估后缀与其他自由字符串；不得宣称只去前缀即解决重复。
3. 在冻结转换器上验证有界JSON字符表达、转义和Unicode边界以及语法规模/生成代价。pattern分支优先于maxLength，因此不能机械恢复一个maxLength字段后宣称修好。严格策略原claim上限2000及完整原题事实容量保持；不得为跑通而任意压缩事实数、来源数或删掉题目。若拟采用更紧的生成表示，应证明原题信息仍可完整表达，字符上限也不能冒充2048 token总量保证。
4. 对本次融资背景卡/TODO卡与对应泛述建立诊断和验收负例，核对证据发行、提示和写入路径分别能保证什么。精确operation约束只保证可定位术语，不等于语义蕴含；保留独立逐事实复核。没有定位到新的接口错误前，不凭猜测大改导航或写入事务，也不声称引用问题已修复。
5. 只有离线兼容证据支持后，才在新的隔离候选做最小产品改动及有意义回归：合法JSON/转义、错误operation和来源卡拒绝、生成与重放相同schema、原读取覆盖与未交付语义、原预算/时钟/写入读回/ACK和旧失败保留。必要计划/准备独审通过，再准备并封存受控入口；真实8B单例仍另行明确分配。

## 拟议写域与通过条件

取得下一范围后，新隔离worktree以{HEAD}为父；产品差异仅限确证所需的共享writer采样表达/提示及其回归，优先agent_server.py中_research_code_claim_sampler_pattern和_research_sampler_schema。若需要超出这些边界，先把理由、差异和原题表达证明写入计划，不自动扩大。原导航、工具语义、实际写入事务和验收器保持。报告、计划、独审、入口及镜像按原规范留档。

离线通过必须包括：当前失败样本可复核；已定位的无界前缀不再属于新生成表达；所有允许输出都能作为合法JSON字符串并经原strict约束复核；原题事实/来源容量未缩减；生成与重放一致；当前8B、上下文16384、最多8次POST和输出2048及原时限均不变。离线检查只证明对应属性，不证明语言模型交付成功。

真实通过继续要求research.md、可信runtime proof、write/readback、ACK、逐事实/引用、完整原题覆盖、原时限、清理及结果独审全部通过。新候选通过信用从0开始，旧E01/E03不挪用。受控corpus阶段不替代原真实联网门。

## 不在本提案内

不接受length响应、不修补残缺JSON、不从片段执行工具、不按关键字拼装或代写答案；不改模型、不加预算、不更新下载、不操作UI/音频/生产服务或保护身份。当前一次运行与一次复核已耗尽，失败不重试。本文件没有生成grant或预分配下一例。

## 证据依据

- [独立结果复核]({(N / 'review/independent-result-review.md').as_posix()})；结果manifest {RESULT}，复核JSON {REVIEW}。
- [本次结果报告]({report.as_posix()})。
- 冻结产品agent_server.py:217–259；官方固定转换器{converter.as_posix()}:961–975，SHA256 {sha(converter)}。
- [封存后源码分析补充]({(N / 'review/result-inputs/structural-analysis.json').as_posix()})，不在原56成员manifest中；本提案本身尚未实施或独审。
'''
for path, text in ((report, report_text), (proposal, proposal_text)):
    with path.open('x', encoding='utf8', newline='\n') as f:
        f.write(text)
mirror = []
for path, category in ((report, 'reports'), (proposal, 'plans')):
    target = M / category / path.name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as f:
        f.write(path.read_bytes())
    mirror.append(dict(source=str(path), target=str(target), sha256=sha(path)))

paths = [N.parent / 'current-run.json', R / 'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
         R / 'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',
         Path('H:/UltimaAI/_shared/queue/global-queue-index.md'), N / 'progress.md']
before = {str(p): p.read_bytes() for p in paths}
state = json.loads(before[str(paths[0])])
assert state['current_one_case_allocation']['question_id'] == QUESTION
assert state['last_actual_result']['run_id'] == '9dbe192a-3bc1-4a4d-a218-581846d5f654'
actual = dict(
    schema=1, work_order='wo-ultimaagent-20261101-0021', stage='T2', case='E02-controlled-1',
    purpose='output_structure_evidence_one_case', run_id=RUN, candidate=HEAD,
    model='qwen3-8b-uncensored', model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',
    question_id=QUESTION, result='FAIL', independent_review='FAIL_CONFIRMED',
    review_path=str(review_path), review_sha256=REVIEW, result_manifest_sha256=RESULT,
    terminal_sha256=sha(A / 'terminal.json'), product_result_sha256=sha(A / 'product-result.json'),
    entry_invocations=1, work_cli_attempts=terminal['work_cli_attempts'],
    controlled_search_success=1, controlled_GET_success=4, confirmed_inspect_pages=6, visible_inspect_pages=5,
    top_level_successful_inspect_results=0, write_attempts=0, successful_write_count=0, research_artifacts=0,
    application_native_POST_attempts=7, completed_native_posts=7, actual_native_start_count=None,
    outer_elapsed_seconds=execution['outer_elapsed_seconds'], timing_eligibility=terminal['timing_eligibility'],
    cleanup='PASS', root_witness_eligible=False, root_witness_observation_error=witness.get('observation_error'),
    public_content=product['content'], product_error=product['error'],
    failure_diagnostic_sha256=sha(A / 'trusted-failure-diagnostic.raw'), failure_diagnostic_bytes=16301,
    branch=d['branch'], eligible_source_ids=d['eligible_source_ids'], last_http=http, native_response=native,
    output_structure=structure,
    selected_pages=[dict(source_id=p['source_id'], start=p['requested_start'], range=p['range'], confirmed=p['confirmed'], visible=p['visible']) for p in d['pages']],
    budget=d['budget'], write_confirmed=False, ack_confirmed=False, final_answer_preserved=False,
    facts='NOT_PASSED_NO_ARTIFACT_WITH_RAW_CITATION_MISMATCH_RISKS', original_question_coverage='NOT_PASSED_NO_ARTIFACT',
    diagnostic_fact_observations=review['facts']['diagnostic_observations'], non_delivery_reply_observed=True,
    protected_at_recorded_boundaries=True, protected_after_readonly=True, continuous_liveness_measured=False,
    acceptance_credit=0, controlled_passed=0, controlled_required=3,
    actual_case_allocation_remaining=0, result_review_allocation_remaining=0, retry=0, next_case_released=False,
    E02='NOT_PASSED', T2='NOT_PASSED', Owner='NOT_PASSED', old_credit_transferred=False, remote_synced=False,
    cause='Generation7 HTTP200 length/2048 refusal; FULL content proves repetitive text inside an unterminated claim string',
    native_rejection_predicate_proven=True, real_delivery_improvement_proven=False,
    native_compatibility_limit='Same-request FULL content evidence; sole internal repetition cause and efficacy of future repair not proven',
    previous_actual_preserved_at=str(N / 'verification/result-closeout-before/0-current-run.json'),
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state['previous_actual_result'] = state['last_actual_result']
next_work = 'Review concrete claim-generation contract proposal; no new product change, actual run or independent review allocated'
state.update(
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(), phase='SOURCE33_E02_OUTPUT_STRUCTURE_CONTROLLED_FAIL_REVIEWED',
    workflow_status='blocked', stage_queue_state='BLOCKED', active_review_agent=None,
    active_evidence=str(N), active_candidate=HEAD, active_product_candidate=HEAD, active_report=str(report),
    active_plan=str(N / 'execution-proposal.md'), last_actual_result=actual, latest_actual_candidate=HEAD,
    active_result_review=dict(verdict='FAIL_CONFIRMED', path=str(review_path), sha256=REVIEW, scope='LATEST_ACTUAL_CURRENT_CANDIDATE_BF7F7A9'),
    actual_case_allocation_remaining=0, result_review_allocation_remaining=0, e02_execution_released=False,
    live_gate_released=False, next_stage_released=False, E02='NOT_PASSED', T2='NOT_PASSED', e02='NOT_PASSED', t2='NOT_PASSED', owner_gate='NOT_PASSED',
    current_e02_controlled_passed=0, e02_output_structure_result=actual,
    current_one_case_allocation=dict(question_id=QUESTION, candidate=HEAD, status='CONSUMED_FAIL_REVIEWED', remaining=0, result_review_remaining=0, retry=0),
    current_actual_execution=dict(question_id=QUESTION, candidate=HEAD, run_id=RUN, status='COMPLETE_FAIL_REVIEWED', entry_invocations=1, retry=0),
    new_live_cases_this_execution=1, new_work_cli_submissions_this_execution=1,
    new_completed_inference_events_this_execution=None, new_completed_native_posts_this_execution=7,
    new_native_total_start_count_this_execution=None,
    new_model_calls_counter_basis='Seven completed native HTTP POST receipts; server-side total starts not measured',
    explicit_user_execution_status='COMPLETE_OUTPUT_STRUCTURE_ONE_CASE_AND_RESULT_REVIEW_FAIL',
    goal_turn_outcome='ONE_CASE_AND_REVIEW_COMPLETED_REPETITIVE_UNTERMINATED_CLAIM_CONFIRMED',
    goal_registry_status='blocked', goal_status='blocked',
    goal_registry_note='Fresh goal tool still reports blocked; explicit user grant authorized and completed this case. No tool-controlled resume performed; objective remains incomplete.',
    latest_readonly_runtime_receipt=str(N / 'review/result-inputs/readonly-closeout.json'),
    latest_readonly_runtime_sha256=sha(N / 'review/result-inputs/readonly-closeout.json'),
    next_action_scope=dict(authorized=False, scope='Proposed offline claim-generation contract repair and preparation; future actual allocation separate', actual_case_allocation=0, result_review_allocation=0, model_calls=0, service_operations=0),
    next_proposal=dict(path=str(proposal), kind='EVIDENCE_LED_OFFLINE_PRODUCT_REPAIR_PROPOSAL', status='PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED', actual_case_allocation=0, result_review_allocation=0),
    next_work=next_work, next_action=next_work, next_offline_plan=str(proposal))
state['source33_preparation']['status'] = 'COMPLETED_USED_BY_ONE_ACTUAL'
state['active_preparation']['status'] = 'COMPLETED_ACTUAL_CONSUMED'
state.pop('pending_actual_result', None)
summary = 'E02 bf7f7a9唯一实际FAIL_CONFIRMED：FULL正文证实claim重复50/49次后length/2048截断，引用亦有错配风险；无research.md/写入/ACK，清理及保护点核对PASS，单例与独审均耗尽，不重试。'
texts = {str(paths[0]): json.dumps(state, ensure_ascii=False, indent=2) + '\n'}
wo, count = re.subn(r'(?m)^- 状态：.*$', '- 状态：' + summary, before[str(paths[1])].decode('utf8'), count=1)
assert count == 1
append = '\n\n## 2026-11-08 E02 output structure controlled result\n\n' + summary + '\n报告：' + str(report) + '\n后续提案（尚未实施）：' + str(proposal) + '\n'
texts[str(paths[1])] = wo + append
texts[str(paths[2])] = before[str(paths[2])].decode('utf8') + append
index, count = re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$', '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | ' + summary + ' |', before[str(paths[3])].decode('utf8'))
assert count == 1
texts[str(paths[3])] = index
texts[str(paths[4])] = before[str(paths[4])].decode('utf8') + f'\n- Explicit {QUESTION} actual1/review1 completed; {RUN} FAIL_CONFIRMED; remaining0/retry0.\n- FULL content 3818 chars, repetitive unclosed claim50/49; no artifact/write/ACK. Result manifest {RESULT}; review {REVIEW}; proposal only, no product change.\n'
backup = N / 'verification/result-closeout-before'
backup.mkdir(exist_ok=False)
for i, p in enumerate(paths):
    assert p.read_bytes() == before[str(p)]
    (backup / (str(i) + '-' + p.name)).write_bytes(before[str(p)])
for p in paths:
    p.write_text(texts[str(p)], encoding='utf8', newline='\n')
save(N / 'verification/result-closeout-registration.json', dict(
    summary=summary, review_sha256=REVIEW, result_manifest_sha256=RESULT,
    before={p: hashlib.sha256(b).hexdigest() for p, b in before.items()}, after={str(p): sha(p) for p in paths},
    mirror=mirror, actual_remaining=0, result_review_remaining=0, acceptance_credit=0))
q = Path('H:/UltimaAI/_shared/queue')
assert sha(q / 'queue-status-gen.py') == 'da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
run = subprocess.run([sys.executable, '-I', '-B', '-X', 'utf8', str(q / 'queue-status-gen.py')], capture_output=True, creationflags=subprocess.CREATE_NO_WINDOW)
save(N / 'verification/result-queue-refresh.json', dict(exit_code=run.returncode, stdout=run.stdout.decode('utf8'), stderr=run.stderr.decode('utf8'), generator_sha256=sha(q / 'queue-status-gen.py'), queue_sha256=sha(q / 'queue-status.json'), semantic_registration_only=True))
assert run.returncode == 0
with (N / 'verification/result-queue-status.json').open('xb') as f:
    f.write((q / 'queue-status.json').read_bytes())
print(json.dumps(dict(result='FAIL_CONFIRMED', report=str(report), proposal=str(proposal), mirror_files=2, allocations=0), ensure_ascii=False))
