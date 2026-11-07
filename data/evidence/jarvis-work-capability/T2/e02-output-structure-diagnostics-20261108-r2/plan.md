# E02 输出结构诊断实施计划

> For agentic workers: use superpowers:executing-plans；主会话实施，独立精确计划审查与最终准备包审查，不派实施子代理。

**Goal:** 在保持当前 8B 和全部交付门的前提下，让下一次原生拒绝留下可判断输出结构的受限证据。
**Architecture:** 复用原拒绝捕获、严格 JSON、jsonschema、安全扫描及16KiB导出。新 v5 仅在确实捕获同请求结构证据时生成；不改变请求/采样/写入/ACK。v3/v4继续可读，空间或采集不足时保留原v4。
**Tech Stack:** 现有 Python、OpenJarvis/HTTPX MockTransport、jsonschema、固定离线审计守卫；无新依赖。
**Spec:** docs/plans/jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md；原单 wo-ultimaagent-20261101-0021 / T2；用户恢复 active 持续交付目标。本轮接续已确定的诊断方向，实际研究仍另需明确单例分配。

## Global Constraints

- 父0421a54cab572be013c3f7ad562e86406bfe8e52冻结，N19/N21失败及N22只读审查不改。新候选分支codex/jarvis-e02-output-structure，使用原生managed worktree；现有候选均属于冻结历史，不复用写入。
- 新证据根N23=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-diagnostics-20261108-r1。下一受控入口另根，不覆盖旧绑定。actual_case_allocation=result_review_allocation=model_calls=0；必要准备审查与结果审查分账。
- 固定qwen3-8b-uncensored/digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四来源、完整事实/引用/覆盖/文件门，E02/T2/Owner未通过。
- CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315秒；context16384，messages+strict32768/entity49152，响应65536、诊断16384字节，原阶段输出256/2048及小allowance保持。
- 无服务、UI、音频、安装、下载或外部请求。保护既有进程与15个无关改动。离线每组90秒、最多2并发，复用原冷导入守卫与原两项不适用排除；不执行真实profile或entry。
- 不接受length为成功、不恢复残缺JSON、不向下一轮输入失败正文、不改变选页/来源/事实数或生成schema。不新增成功信用，不迁移旧E01/E03到新候选。先前push自动审批blocked by policy保持。
- 执行方法沿用主会话实施；本次持续推进用于离线诊断实现和必要准备审查，不将旧单例/旧独审回执复用为新authority。精确计划独审PASS后实施，最终准备独审PASS后方准备真实入口。

## Review Focus

- content是完整JSON但done_reason=length：必须仍拒绝、write0；诊断COMPLETE不成为接受凭据。
- 诊断自身失败、过大、畸形Unicode或安全扫描拒绝：保留原失败与原v4证据，不把内容泄漏到公共结果。
- 中文、转义、片段拼接导致编码扩张：以完整canonical packet字节计数，边界恰好16384接受、超出不扩大限额。
- 写入已确认后的ACK拒绝：文件/效果如实保留，诊断不得将其变成未写入或成功。
- 请求/响应摘要、阶段、片段位置或FULL状态被篡改：v5验证拒绝；旧v3/v4不偷偷接受扩展字段。

## Task 1: 原生拒绝输出结构诊断

**Files:** modify src/brain/agent_server.py、src/brain/work_research_diagnostics.py、src/brain/tests/test_work_native_response_diagnostics.py；create src/brain/tests/test_work_output_structure_diagnostics.py。必要测试迁移仅限v5版本与legacy去扩展构造，原断言语义保持。

**Interfaces:**
- 原函数为 `record_native_response_rejection(ledger, transport, raw_bytes, raw, max_tokens, reason)` 六个位置参数，全部保留，仅新增keyword-only `request_context=None`。leaf只在原拒绝分支提供`entity:bytes, strict_schema:dict, ack:bool`；没有上下文或采集失败时原v4仍可用。
- 内部 `build_output_structure(raw, entity, strict_schema, ack, max_tokens, scan, *, native_record) -> dict`：native_record必须是本次recorder先由原 `_bound_native(transport,last,value)` 核对、保存的native拒绝投影；其中response_sha256和response_bytes来自实际接收的raw_bytes，禁止对解析后raw重序列化求响应摘要。snapshot新增闭合native_binding，复制其generation/receipt_index/request_sha256/response_sha256/response_bytes/content_chars/max_tokens。v5验证要求该binding逐值等于同包已验证的native_response相应字段；actual entity摘要也必须等于request_sha256。
- build复用现有 `_strict_json` 和 `_research_sampler_schema`；请求actual格式必须等于strict投影，num_predict等于本次max_tokens。用实际entity而非历史输入生成请求摘要、flags/options、strict/sampler SHA与编码长度、允许动作/schema内source_id枚举集合/引用数量；schema来源集合不冒充已读来源。字段闭合，枚举固定，数量有界。
- 输出结构记录：request投影；response_sha256；message已知键存在性及unknown数量；content/thinking类型、字符/UTF8长度/SHA（thinking不留正文）；JSON状态COMPLETE/INVALID/NON_STRING/UNAVAILABLE，错误固定类别和pos/line/column。重复键/非标准常量等严格解析错误不保存异常原文。
- 完整JSON才用Draft7Validator判断schema并统计分支、标题长度、section/fact数量和有限长度表。INVALID等状态结构为null。最多记录5个section、每个6个claim长度，超出明确标记统计不全；不以截断后的统计当完整。schema错误最多首个、仅固定关键词与安全字段路径/数组下标，未知名称替换为固定OTHER。
- 内容证据包含mode、原字符/字节/SHA、fragments(start,end,text)、omitted_chars。安全扫描完整content后才能保留文本，禁止thinking正文和未知message字段值。先尝试FULL；否则确定性选择头/尾及错误位置附近片段，合并重叠范围，最多3片段，偏移是原Python字符下标。预算不足逐级缩减到无文本；扫描失败用OMITTED_POLICY，不红删冒充原文。
- `attach_output_structure(packet, snapshot, scan) -> dict`：先保留完整原v4 packet，按最终canonical编码长度<=16384选择v5证据形式；没有合适v5就返回原v4。整体扫描与闭合验证失败也回退原v4；原捕获/验证失败仍按既有UNAVAILABLE处理。不得删来源页以给正文腾空间。
- v5在v4顶层新增output_structure；kind=research_failure_diagnostic_v5。`validate_failure_diagnostic`接受三版本，v5要求native_response非null且同generation/receipt/request/response与长度绑定；闭合类型和范围、片段位置/不重叠/省略量、FULL哈希/长度一致。v4/v3字段集不变。capture_failure公共summary的kind跟随实际packet，正文不出现在summary。

- [ ] 精确计划独审PASS，登记DoR、当前WIP与原失败哈希；创建新worktree和本计划ledger，记录native方法及范围裁定。
- [ ] 写新测试，旧代码下运行`run_product_checks.py structure-red`；Expected: 新结构证据断言失败，非依赖/collection错误。使用既有native_refusal/early_case/genuine_navigation真实SDK MockTransport夹具。
- [ ] 仅实现上述文件范围，先生成原v4 native拒绝，再尽力构造结构证据；主异常和拒绝顺序不变。目标文件已有私有JSON辅助方法，避免新通用parser/框架。
- [ ] 测试length+完整JSON/半字符串/半数组/半对象、重复键、非string/额外message字段、Unicode/转义/安全文本、摘要/位置/版本篡改、无context/诊断异常、原成功写ACK重放与写后ACK拒绝。使用不同空白/键顺序的原始响应字节，断言snapshot与native/HTTP receipt绑定真实raw_bytes SHA/长度，且不等于重新canonical序列化raw的摘要；篡改binding/actual entity必须拒绝v5。所有失败不得启动新请求或分派残缺工具参数。
- [ ] 运行`run_product_checks.py structure-green`与`native-green`；Expected: 所有收集项通过、offline-audit清洁、原生拒绝仍无交付信用。

## Task 2: 兼容、整包准备复核与本地冻结

**Files:** N23/inputs/offline/review/verification/ledger；必要测试迁移仍限Task1；项目计划/报告/原单/t2/current-run/全局表及UltimaDocs镜像。
**Interfaces:** Task1产生闭合v5及既有公共摘要。原harness的export_failure_diagnostic调用产品validator且上限16384，无需改原adapter。新候选的离线export_checks复用该函数、绑定确切旧adapter SHA；只Mock，不执行安装hook或profile主入口。

- [ ] 完成v3/v4保存包可读、v5安全导出/跨请求拒绝/总cap、非2xx不读正文和旧失败封存测试。保留旧native131项全部用途，版本适配逐项记录。
- [ ] 按固定守卫执行相关回归：structure/native/failure/http/diagnostics/navigation/transport/research-a/research-b/delivery/grounding/coverage/reference/claim/unique/target/json/metadata/budget与离线export兼容；每组90秒、最多2并行。仅既有delivery两项排除；不裸跑会连服务的全仓pytest。Expected: 适用项全过、JUnit去重、旧门不变，数量由实际结果计算。
- [ ] 整理真实RED/GREEN、argv/退出码/审计/XML/同字节源码快照、旧包/依赖/15文件保全；没有真实响应正文补证，不虚构改善。
- [ ] 冻结候选commit/tag，生成当前输入与源码清单、精确diff及准备manifest；安排一次fresh root-independent整包准备审查，范围只读、actual/model0。发现阻断在同诊断范围内最小修正并补验证，旧审查不覆盖新字节。
- [ ] 计划/准备报告/镜像本地提交tag与读回；current-run保留last_actual_result，不记E02成功。下一步仅准备新候选受控入口；正式研究仍另行明确分配。

**Verification command:** 固定解释器 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -I -B -X utf8 N23/verification/run_product_checks.py <group>`；每次日志/审计/源码快照独立目录。不在本计划中调用模型或改变模型参数。

Ruling：恢复持续目标允许推进已确定方向的离线准备；沿用主会话实施并保留独立准备门。writing-plans的再次询问执行方式与用户既定持续推进意图重复，故不再询问。旧worktree已冻结，using-git-worktrees的复用默认不适用；无安装或全仓有副作用测试。若判断错误，停止准备候选发布，不给实际用例或验收信用。
