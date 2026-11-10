# E02 输出结构失败诊断补充提案

原单 wo-ultimaagent-20261101-0021 / T2，父候选 0421a54cab572be013c3f7ad562e86406bfe8e52。依据：同日输出结构只读审查、N19/N21 两次封存的 length/2048 拒绝。本文是具体改动提案，不是代码已修改、独立准备 PASS 或实际研究分配。

## 裁定

下一候选先改失败证据采集，不先改 writer schema、原生接受条件或交付事务。现有证据能证明原生输出额度耗尽，不能证明 JSON 必定不完整，也不能确定耗在何种字段。保留当前 8B、原题四来源、事实/引用/覆盖门、所有调用/时间/字节/输出预算及失败不重试。

只在新隔离候选实施。冻结父候选与 N19/N21 失败包不改。当前实际研究和结果独审分配仍为 0；此提案本身不产生分配。

## 需要补充的最小证据

| 证据 | 采集边界与用途 | 禁止推断 |
| --- | --- | --- |
| 同请求的 phase、ack、实际 num_predict/num_ctx、think/stream/truncate/shift，strict/sampler schema SHA 与字节数、允许动作、可用来源/引用数量 | 在实际 entity 已序列化、同一响应已完整收到后，投影实际请求；绑定 generation、receipt、request/response SHA。避免仅从源码猜当前请求形态 | 允许 write 不等于实际生成了 write；不能从旧候选请求复制字段 |
| 外层 message 的已知字段存在性、类型；content 的字符/UTF-8 字节数及 SHA；thinking 只记存在性/类型/长度/SHA | 原生拒绝处 raw_bytes/raw 仍存在，补齐之前被短路校验遮住的元数据 | think=false 不直接等于 thinking 字段缺失；eval_count 不分摊成各字段 token 数 |
| 对完整 message.content 执行一次现有严格 JSON 解析；记录 COMPLETE / INVALID / NON_STRING / UNAVAILABLE | INVALID 只记录受限错误类别及字符位置、行列；不输出异常原文，不修 JSON。异常类型不可识别时保留 UNKNOWN | INVALID 时章节数、事实数、所选分支均为 null/UNKNOWN，不能对部分文本冒充结构解析成功 |
| 仅完整 JSON 时的严格 schema 判定、分支、章节/事实数量、各标题/claim 长度、schema 错误的受限路径和关键词 | 使用既有 jsonschema；只保留当前闭合契约的字段名与有界数组下标，未知字段不原样外泄 | 完整 JSON、schema 合格仍不是来源支持、事实正确、覆盖充分或 stop；length 仍拒绝 |
| 安全扫描后的 content 全文或有界片段；保留方式、原长度/SHA、片段字符偏移与被省略量 | 优先完整保存；受原 16,384 字节诊断上限限制时才保留头/尾或解析错误附近片段，标记 FULL / EXCERPTS / OMITTED_POLICY / OMITTED_BUDGET | 片段不能重建整份响应，不能拿片段去执行工具；hash 不等于正文 |

不另建超预算 sidecar，不把 raw body 放入公共 result、stdout、业务回复或下一轮模型提示。非 2xx 正文仍不读。诊断仅使用已接收且处于原响应上限内的字节，不新增请求、解码补救、采样回退或 token 预算。

## 保存和验证约束

- 在 `_NativeResearchLeaf.generate` 原 `checked_native_response` 拒绝分支采集；保持第一个原生拒绝原因和原异常。当前诊断只覆盖已成功解析的外层原生拒绝；外层 JSON 无法解析的情况继续标为诊断不可用，不能冒充已完成结构审查。
- request 证据必须从本次实际发送的 entity 得到，并与 receipt SHA/字节数及 expected schema/phase 一致。完整严格 schema 与 sampler schema 分别计算摘要，不能用单个摘要混淆两个契约。
- 文本保留前使用当前请求的既有安全扫描器。扫描失败仅保留固定状态与安全计数；不能红删后将结果标成原始全文。扫描或诊断异常不得覆盖原失败、开放工具权限或变更已有写入事实。
- 先保留现有来源页、预算与原生拒绝元数据，再按实际 canonical JSON 编码后的剩余空间分配片段。不是按字符数猜字节。16,384 字节总上限不变；多字节、引号、反斜杠、控制字符和片段拼接后的整体扫描都要覆盖。若容不下新字段，保留原 v4；版本为 v4 明确表示新结构证据未捕获，不在闭合旧包内偷偷追加字段，也不能静默删旧证据。
- 新闭合诊断版本建议 v5；原 v3/v4 仍可读。每个新字段有类型/范围/关联校验；身份/哈希/长度或 partial/full 状态矛盾即拒绝该诊断。private diagnostic 始终 complete=false、END=false、acceptance_credit=0。
- 不引入部分 JSON 修复器或自研通用语法解析器。复用现有严格 JSON 解析、jsonschema、官方 SDK/HTTPX 和当前导出器；无新依赖、无 vendor 修改。

## 预计最小文件范围

| 文件 | 变更边界 |
| --- | --- |
| `src/brain/agent_server.py` | 原拒绝处传入本请求必要上下文；请求生成、输出预算、think、strict/sampler 投影、成功路径和 writer 准入保持 |
| `src/brain/work_research_diagnostics.py` | 增加受限结构投影、文本保留模式和 v5 闭合验证；保留 v3/v4 与原失败语义 |
| `src/brain/tests/test_work_native_response_diagnostics.py`、新增 `test_work_output_structure_diagnostics.py` | 真实 SDK MockTransport 路径的诊断、预算、扫描、身份篡改和拒绝不产生写入测试 |
| 既有 failure/http 诊断兼容测试；新候选的受控入口绑定与 harness 诊断测试副本 | 核验原 16KiB 导出上限、版本兼容和公共摘要；原 adapter 已调用产品 validator，不能仅为升级版本复制一套解析器 |

`work_navigation.py`、`work_research.py::checked_native_response`、`work_tools.py::WorkResearchWriteTool` 暂无功能改动依据。旧 harness 和旧输入绑定保持冻结；未来入口必须重新绑定新候选，旧准备 PASS 不转授。

## 离线判据与后续顺序

必要的离线样例包括：length+完整 JSON、length+字符串/数组/对象截断、无 content/多 message 字段、正常 stop 的原成功路径、畸形/重复键 JSON、schema 不合格、非 2xx、Unicode/转义使编码超限、敏感文本、跨请求篡改、诊断自身异常，以及写入后 ACK 拒绝仍保留真实效果。长度拒绝不得因 JSON 看似完整而被放行；diagnostic 内的文本不能触发 SDK action。

先完成精确计划与必要独立准备审查，再实施和离线验证、新候选绑定；之后仍需用户明确分配一次实际研究及结果复核，才能取得新真实正文证据。本轮只完成提案，不提前花费该额度。

真实证据到功能修改的判定：

1. 若确定是长字段或重复事实挤占输出：先在原生同版本转换机制上离线证明较紧凑、仍可表达原题的结构可用，再同步生成/严格校验/重放；不能直接恢复曾导致 grammar 400 的大 maxLength，不能强制“一源一事实”当验收。
2. 若完整且 schema 合格但 done_reason=length：先查原生终止兼容与请求边界，不能擅自接受 length。
3. 若正文已经混淆项目、证据不支持核心机制或遗漏原题：处理证据表达/导航和事实契约；仅缩短字符串不能算修复。
4. 若考虑逐来源暂存：必须先证明同一原题在总 8 POST、原输出预算与时限内、每个局部事实可重放绑定，最后只提交一次完整文件。现有“6 inspect 后再分源生成”不满足预算，不作为本轮最小补丁。

最终仍以完整 research.md、真实写入读回、ACK、可信 runtime、逐事实/引用/原题覆盖、时限及独立结果审查共同验收。离线诊断通过、单例通过和 E02/T2 全部通过是不同状态。
