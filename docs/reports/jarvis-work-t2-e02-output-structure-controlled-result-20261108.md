# E02 输出结构诊断候选：单例结果与独立复核

原工单 wo-ultimaagent-20261101-0021 / T2。候选 bf7f7a9cf0e4ba559c29daa388c00379d12d345a 的唯一当前 8B 原题四来源研究已经结束，独立结论 **FAIL_CONFIRMED**。没有交付 research.md，E02 仍 0/3，T2/Owner 未通过。本轮新增的是完整截断内容的证据，未证明研究能力修复成功。

## 运行与结果

用户问题 call_5c06d21b59b8475b873814f857990cc3 明确分配 actual 1 / 结果独审 1 / retry 0。run c4caa739-c466-44f3-866b-0c57ea8c5e40，北京时间 2026-11-08T01:26:45.985775+08:00 至 2026-11-08T01:27:51.448580+08:00，外层耗时 65.463732 秒。只调用原入口一次，CLI 一次；应用原生 POST 7 次、完成 7 次，服务端实际生成启动总数未测量。

产品 status=failed，error=Invalid native research response，公开回复“本次研究未交付。”。research.md、write、ACK 均为 0，无可信 runtime END。没有重试，本次运行及结果复核额度均已消费。

原预算保持：CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315 秒；context16384，输出最多2048，阶段较小上限保持。模型仍 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四来源、事实/引用/覆盖门保持；没有 UI、音频、生产服务、安装下载或14B操作。

## 本次新确证的截断位置

第7次 HTTP200 响应 done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8908。请求 33719 字节，SHA256 7ea5d03b00114892b37051cd2aa098527c6d785d5d45dc137de8014c9e29a156；响应计数 9313 字节，SHA256 e74c0488b0101002e58930780774e517f5dadd26ee2cb8894a457bef63b3effe。这些摘要在可信诊断中交叉绑定，独审没有重放完整 HTTP 请求/响应。

v5 私有诊断 23b5ccbff7f8dd1fc849351bee6ccaa734eb82cebd8ec7926cc233ce967aed36，16301 字节，未超过原16384上限。FULL 保留完整 content 3818 字符 / 8872 UTF-8 字节，无省略；content SHA256 1f6b669b10cd3418e3ea6279a0c5253ec239184a6eab2efa1642d47963cec4de。完整正文严格 JSON 解析失败，UNTERMINATED_STRING，pos1339 / line45 / column22；独审重算相同。

未闭合 claim 引号后有2478字符，其中“支持多种LLM模型和工具的集成，实现灵活的交互方式。”出现50次，“支持本地和云服务的混合使用，以平衡速度与隐私。”出现49次，之后耗尽输出额度。以上为完整原文统计，没有补括号、修复JSON或执行残缺动作。schema_valid/shape仍为空。请求think=false、消息thinking字段缺失，不能据此反推所有内部token分配。

旧候选0421a54及d860b2a的失败仍原样保留；旧回执未保存正文，不能用本次正文补写旧结论，也不能认定它们必然有相同重复模式。

## 事实、引用与原题覆盖

独审发现残缺原文中的具体错配风险：N3.42ae675651f972c7对应S1第28–29行融资/开源背景，却伴随UnifiedAgent工具断言；N3.1eb7eea60301cfb6对应S2第39行OpenAI/Gemini尚待实现的TODO，却伴随集成和模块化泛述。末尾“效率、用户体验改善”也不是S3日志和时间戳代码可单独证明的效果。

这些是原文与证据卡/原始来源的诊断对照，不是接受部分JSON或完成事实验收。事实、引用、原题覆盖均NOT_PASSED；修复截断不自动修复以上问题。

search1/GET4；六次确认读取分布为S1四页、S2一页、S3一页，没有S4 inspect。S3 confirmed=true / visible=false保持原账本含义，不把visible=false解释为未读。顶层成功inspect结果0与私有六次确认读取属于不同观察层。三来源写入资格不能代替完整原题；受控corpus也不能代替原真实联网门。

## 源码检查与后续顺序

当前agent_server.py:217–259的采样投影移除了maxLength，代码事实pattern允许在精确operation前后继续生成无界合法JSON字符。冻结的llama.cpp b10488转换器json-schema-to-grammar.cpp:961–975先处理pattern，后处理maxLength，不能假设恢复maxLength就会同时限制有pattern的字段。这是可疑结构条件，不是对模型内部重复机制的唯一归因。

建议按[下一步提案](H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-claim-generation-contract-proposal-20261108.md)先离线处理代码事实的生成表达：核验“先输出证据绑定的精确operation，再写原子说明”的官方pattern表示与有界表达兼容性；将本次重复及引用错配作为必须保留的负例。暂不改写事务、加预算或迁移模型。新设计须证明原题完整表达能力、JSON合法性、同请求生成/重放一致，再确定最小代码差异。提案尚未实施或独审，不授予下一例。

## 清理、时限与归档

原cleanup PASS；六个本例身份在事后核对点不在、隔离端口18799关闭、日志闭合。保存的运行边界及事后七个保护身份一致，不声称连续存活或报告时仍为同一实时状态。root witness eligible=false、observation_error=ValueError，时限资格仍UNOBSERVED_NEVER_TIMED_PASS；65.46秒观测不能升级为时限通过。

结果manifest 2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0（56成员），独立结果JSON SHA256 119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58，Markdown SHA256 8cd8a688ba46904df153cc95677546bb2ce49900cc442d0ad9d0ff8c6b7bfa0b。175准备成员、77产品源码及1598输入钉住值保持；979产品/兼容检查和350入口检查属于既有准备，不是本次新通过的实际验收。旧E01/E03通过信用不转移到本候选。

output-text-observation.json及structural-analysis.json是封存后只读补充，明确不在原56成员结果manifest中；本次结果发布另行收录。项目/UltimaDocs本地提交、tag及读回见本证据根verification/result-publication-readback.json、result-final-readback.json。本地归档不代表远端同步；此前自动审批以blocked by policy拒绝push，本轮未重试或更换通道。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-controlled-preparation-20261108-r1。
