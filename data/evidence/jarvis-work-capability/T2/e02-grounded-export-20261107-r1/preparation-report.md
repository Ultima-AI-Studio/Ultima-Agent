# E02 grounded-export 准备完成记录

原工单 wo-ultimaagent-20261101-0021 / T2。产品隔离候选 9e2716a6bc8dc1a51218257b89a581f968d8444a，父候选 1ecd75d061fd20e78c790c506cac76847f8e63bf；tag ultimaagent-e02-grounded-export-candidate-20261107。准备阶段没有实际研究、模型推理、UI、音频或服务操作。E02、T2 仍未通过。

## 已实现

1. 导出观察器追加有限诊断，区分 runtime_verify、structure_scan、member_preserve。只保存固定类别、可信文件函数/行号、有限原因码或消息长度/摘要、packet 字节数/摘要；不保存动态错误原文、locals、源码行或原始 packet。诊断失败仍抛原异常，旧失败协议、拒绝门与 retry0 保持。
2. 使用已保存的本机元数据、原 SDK 与 MockTransport，复现旧导出器对 ModelDetails.context_length、embedding_length 的拒绝。Ollama v0.32.15 官方服务端类型确实声明这两个 int 字段；仅增加这两字段的严格非 bool、非负、64 位有界整数兼容，其他字段与扫描规则保持。官方源码和 SHA 已保存。N8 没保存原始失败 packet，因此这不追认 N8 的历史异常必定来自该分支。
3. 文档目录增加来自安全可见原文的短标题/内容提示，原 8 landmark、4096 字节和真实坐标约束保持。代码 operation 名保持。
4. 生成与独立重放共用纯函数 phase，解释七字段卡片、锚点与上下文区别、TODO 不证明实现、三来源可写不证明原题覆盖。提示通用，不包含题目答案；writer/schema/事实门没有放宽，也不在生成后重写模型文稿。
5. 入口支持本会话直接用户消息的精确哈希绑定，真实内容为“按建议的顺序继续推进”。它不是平台消息 ID，不伪造 call_；旧分配分支不变。仍绑定当前候选/模型/准备 manifest/独审哈希，TTL≤120秒、预消费一例、一独审、零重试。

## 离线验证

verify_preparation.py 当前字节读回 PASS，935 项唯一检查：产品 608、harness 268、绑定/入口/边界 59。harness 四组原始计数 79+140+19+32=270，其中两个旧测试重复，去重后 268；不累加历史重复运行。产品两项原 HTTP/junction 排除仍明确保留，不当通过。所有选定成功回执、JUnit、源快照及 offline guard 已核对；候选工作区干净，1560 项输入绑定及 9 项无关工作文件保持，N8 封存证据和源码保持。

RED 和过程异常原位保留：诊断 6 FAIL/1 PASS；初始 grounding 10 FAIL/1 PASS 中两项是测试夹具/断言错误，已记录并修正；一次 HTTP fixture 预消费响应已修正；真实元数据兼容 RED 7 FAIL/23 PASS，GREEN 32 PASS；入口直接消息 RED 两个 ValueError，最终 32 PASS。一组并行 harness 因时间戳目录碰撞在测试启动前失败，顺序运行该组 140 PASS。没有由这些离线失败触发产品单例或模型调用。

## 后续门与限制

独立计划审查及直接消息入口计划审查均 PASS_PLAN_ONLY。当前文件与全部准备成员封存后，须由新的 root-independent reviewer 核对 exact manifest，结论 PASS_PREPARATION_ONLY 才能进入实际例。准备 PASS 与离线测试不能证明语义正确。

仅当前 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四完整来源、原预算和七保护身份基线保持。E01/E03 在旧候选 269aca5 的通过不转移。准备通过后的一例仍需文稿、可信 packet、ACK、读回、事实/覆盖/协议独审及清理同时通过；最多本新候选受控 1/3，不代表真实联网或整个 T2 通过。

本地提交/tag/镜像后核对字节。远端 push 曾被自动审批以 blocked by policy 拒绝，本轮不重试或换通道。生产语音和默认模型不变；本记录不声称本轮已重新验证运行中的服务。
