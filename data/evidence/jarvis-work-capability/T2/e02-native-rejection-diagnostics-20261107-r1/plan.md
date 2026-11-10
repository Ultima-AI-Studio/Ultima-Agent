# E02 原生响应拒绝诊断实施计划

> For agentic workers: use superpowers:executing-plans。主会话实施，独立精确计划审查和整包准备审查；不派实施子代理。

**Goal:** 在原生响应被拒绝时记录确切的固定拒绝原因及受限、请求绑定的元数据，使后续兼容修复有证据依据。
**Architecture:** 保持 `checked_native_response` 的接受域、原短路顺序和公开 ValueError 文案；拒绝时附固定原因码。仅真实原生 leaf 的该校验失败可生成受限快照，私有失败诊断升级 v4，严格兼容读取旧 v3。所有原生/语义/写入/ACK 门不放宽。
**Tech Stack:** 现有 Python / HTTPX / OpenJarvis SDK / pytest / Windows；不安装依赖。
**Spec:** docs/plans/jarvis-work-e02-native-response-rejection-diagnostics-proposal-20261107.md；原单 wo-ultimaagent-20261101-0021/T2 持续目标及用户“明确分配单例后”要求。

## 全局约束与证据

父候选 C14=C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent，6d758d9c3961f156a062e349ec4a949e2ee7a9a9，保持HEAD/tag/clean；其真实run bc216374-f59c-4967-99f2-ded53a4ea49d FAIL_CONFIRMED保留。N17=e02-json-string-controlled-preparation-20261107-r1，准备manifest ac1fba00bd3af0cb0e16a5736d8ac6c8ec3ffd1949b0383d0bdc7a2275c90b97；结果manifest 3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b；结果独审762f6483fa2dff866d1fd6c3ec7d24fb90c3997d37bead205785d6ba91fa2cf7。上一实际/结果复核额度均已消费。

新证据根 N18=data/evidence/jarvis-work-capability/T2/e02-native-rejection-diagnostics-20261107-r1。先登记/DoR/独审计划，再用应用原生worktree工具从6d758d9创建新候选C15（name=jarvis-e02-native-rejection；实际返回路径落盘），分支codex/jarvis-e02-native-rejection；当前已隔离工作区仍须保留，不能原地修改已绑定实际证据的C14。全部现有附加worktree都属于既有候选/失败链，不复用或删除。

产品写域仅新C15的src/brain/work_research.py、agent_server.py、work_research_diagnostics.py、tests/test_work_failure_diagnostics.py和新tests/test_work_native_response_diagnostics.py。此外写N18、项目本计划/报告、原单/t2/current-run/global登记、UltimaDocs镜像。旧根和9个无关文件不动。

仅当前qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题四来源、至少三来源事实门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict32768/entity49152、输出256/2048不变。本轮model_calls=actual_cases=actual_case_allocation=result_review_allocation=0；无UI/音频/生产服务操作、安装、14B、真实研究重试。可只读核对七保护身份、版本/模型固定元数据和端口；不等于连续存活或模型推理。

持续目标授权本轮必要离线诊断实施及项目规定独审；上一单例只对实跑和结果独审消费，不被复制成新实际授权。E02仍0/3，T2/Owner未过，旧E01/E03信用不迁移。远端push此前被自动审批blocked by policy，本轮不重试。

## Task 1 — 固定拒绝原因与受限私有诊断

**Interfaces:** `checked_native_response(raw,max_tokens)` 仍成功返回None、失败抛同文案ValueError；异常可附 `native_response_reason` 固定枚举。新 `record_native_response_rejection(ledger,transport,raw_bytes,raw,max_tokens,reason)` 只写本请求ledger私有快照，不返回产品结果。`validate_failure_diagnostic(raw,binding_key)` 接受闭合v3原结构及闭合v4新结构。

- [ ] 先写新测试：覆盖字段集合、模型、done、done_reason、message类型/字段/角色/content类型/空白、prompt/eval计数类型及正值、completion上限/context总量、四类duration、created_at类型；每项断言固定原因与旧ValueError文案。多项错误同时出现必须保持原短路顺序。有效别名、缺省可选字段和所有边界仍通过。
- [ ] RED：用原90秒离线守卫运行新测试；旧候选缺失原因/私有字段的断言失败，不以collection错误或放宽旧断言充当RED；保留日志、JUnit、源码/审计快照。
- [ ] 将原合并校验拆成同顺序分支，原因枚举为extra_fields/model/done/done_reason/message_type/message_fields/message_role/content_type/content_empty/prompt_eval_count/eval_count/completion_limit/context_limit/total_duration/load_duration/prompt_eval_duration/eval_duration/created_at。不改原条件的类型语义、阈值、异常文案和返回行为。只从实际被拒分支附原因，不把模型文本当原因。
- [ ] leaf在checked_native_response的ValueError边界捕获，受限记录后原异常重抛；诊断异常被隔离，不替换原失败，不重发请求。JSON解码、scanner、typed或内层envelope/schema失败不得被标记为该原生校验拒绝。
- [ ] 快照闭合字段：generation、receipt_index、request_sha256、response_sha256、response_bytes、reason、max_tokens、done、done_reason、prompt_eval_count、eval_count、content_chars。计数仅精确int且在signed64范围内才记录，否则None；content_chars仅str且0..65536否则None；done仅bool否则None；done_reason只映射stop/length/missing/other/type，绝不保存任意原文；max_tokens必须为256或2048。不得保存模型/角色/字段名/created_at/异常等任意不可信字符串、content正文或思考文本。
- [ ] 在记录时核对最新POST/chat已保留响应的receipt与raw_bytes SHA/长度、request SHA、generation和receipt_index；仅send_reserved、HTTP2xx、无transport error且response SHA一致时记录。 `_project`再次将该快照与最后HTTP回执的代次、索引、请求SHA、response SHA/长度绑定，拒绝旧代次或串请求。
- [ ] 当前生产诊断kind升级research_failure_diagnostic_v4，新增native_response（上述闭合对象或None）；原v3必须维持原闭合字段集合，不接受新扩展，旧v2等仍拒绝。v4有native_response时要求最后chat响应已发送、2xx、未通过validated_response；允许写后ACK的原生拒绝，不能把已有写入抹去。保留16KiB、冻结一次、扫描、公开仅摘要、complete=false/credit0。
- [ ] 仅更新旧test_work_failure_diagnostics.py的当前kind预期为v4，原时间55秒边界、整数类型、无写入/零信用断言全部保持。GREEN：新测试及原HTTP/failure诊断组通过。

## Task 2 — 实际SDK离线链及旧回执兼容

**Interfaces:** 消费Task1的固定原因和v4字段，使用已有sdk_io/mock_jar/early_case/genuine_navigation及原审计守卫；不自造一份诊断包代替调用链。

- [ ] 参数化MockTransport外层拒绝：length、未知外层字段、坏token计数、坏message字段，验证公开失败不变、私有固定原因、实际请求/响应SHA和长度绑定，无正文/任意字段文本泄漏。加入六读后的2048相位以及一次写后ACK拒绝，分别验证无写入和原write_without_ack状态。
- [ ] 正常成功链仍完成写入/哈希读回/ACK/严格runtime replay；HTTP500保持错误正文零读取，坏JSON/scan/inner-schema失败native_response=None；不能误用上一代拒绝。
- [ ] 变异测试覆盖未知原因、bool伪计数、越界数、摘要/代次/索引/长度不一致、跨请求、过期快照、追加任意正文、捕获函数抛错、冻结后的transport突变。失败诊断不可替代原失败或授予END/credit。
- [ ] 旧v3合成回执按原结构验证；再用新decoder离线读取N17封存的真实v3包及其原binding，保留原字节及SHA。旧adapter的export_failure_diagnostic函数复用候选decoder且无kind写死：做当前候选绑定的离线观察器导出检查，函数体不得更改；新旧摘要绑定和原16KiB不变。
- [ ] 最终回归复用N16 product_pytest守卫，按原90秒及≤2并行跑相关产品各组：新diagnostics、failure/http、metadata、coverage/json/claim、reference/target/write-diagnostics/unique/grounding、research-a/b、navigation/transport/delivery；按JUnit身份去重。未改变采样schema，不重跑官方参考converter6项；N16旧781和N17旧344只核验不计为本轮新鲜结果。对新改动及失败涉及分片才重复，所有最终计数绑定最终源码快照。

## Task 3 — 冻结候选、独审与本地交付

- [ ] 核验N17准备/实际/输入及旧依赖链、九无关文件、父候选HEAD/tag/clean；记录C15最终源码、完整继承输入清单与新增测试，不以顶层快照代替完整清单。
- [ ] 新候选精确5文件commit/tag；封存源码/RED/GREEN/审计/JUnit/兼容/保护读回，独立整包准备复核。Expected：PASS_PREPARATION_ONLY，不能宣称已知道本次真实拒绝谓词或修复实际8B交付。
- [ ] 项目报告、原单/current-run及UltimaDocs镜像本地commit/tag/逐字节读回。报告明确本轮修复的是证据缺口，后续仍须准备新候选受控入口后，由用户明确分配真实单例；本轮不创建grant、authority、release或actual，不进入T3—T5/Owner。

## Review Focus

1. 合并校验拆分是否完整保持原接受域与短路顺序，包括bool/int、可选字段、边界值及多错并存；Task1参数化断言和源码对照覆盖。
2. 恶意或异常原生元数据不得经诊断变成任意文本泄漏，未知字段/超大数字/敏感content只输出固定原因和有界投影；Task2毒化输入覆盖。
3. 请求/响应SHA、代次与最后receipt必须同一发送，旧拒绝不能污染后续或ACK；Task2串请求/陈旧快照及ACK拒绝覆盖。
4. v3/v4闭合读取、旧真实包与原导出函数、诊断失败不替换主失败；Task2兼容与故障注入覆盖，诊断绝不当runtime/END。
5. 真实本例具体谓词仍未知，离线模拟/源码拆分不充当模型或事实验收；Task3审查区分新鲜测试、冻结历史、离散保护点与新实际额度0。

## 执行裁定

Windows原生ledger与应用worktree工具；不安装shell，不删除证据或旧工作区。Task2依赖Task1最终结构；最终验证/封存/独审必须使用同一最终字节。已有持续目标覆盖必要离线实施与独审，单例分配门只在新实际前保留，不重复询问常规可逆准备。
