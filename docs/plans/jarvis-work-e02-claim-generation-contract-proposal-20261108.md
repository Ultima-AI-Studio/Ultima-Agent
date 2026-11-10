# E02 代码事实生成契约：基于实测截断的下一步提案

状态：**提案，未实施、未独审、没有新实跑分配**。沿用原单wo-ultimaagent-20261101-0021 / T2，当前冻结父候选bf7f7a9cf0e4ba559c29daa388c00379d12d345a。本文件来自唯一实跑c4caa739-c466-44f3-866b-0c57ea8c5e40和独立FAIL_CONFIRMED结果，不扩展刚完成的actual1/review1授权。

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

取得下一范围后，新隔离worktree以bf7f7a9cf0e4ba559c29daa388c00379d12d345a为父；产品差异仅限确证所需的共享writer采样表达/提示及其回归，优先agent_server.py中_research_code_claim_sampler_pattern和_research_sampler_schema。若需要超出这些边界，先把理由、差异和原题表达证明写入计划，不自动扩大。原导航、工具语义、实际写入事务和验收器保持。报告、计划、独审、入口及镜像按原规范留档。

离线通过必须包括：当前失败样本可复核；已定位的无界前缀不再属于新生成表达；所有允许输出都能作为合法JSON字符串并经原strict约束复核；原题事实/来源容量未缩减；生成与重放一致；当前8B、上下文16384、最多8次POST和输出2048及原时限均不变。离线检查只证明对应属性，不证明语言模型交付成功。

真实通过继续要求research.md、可信runtime proof、write/readback、ACK、逐事实/引用、完整原题覆盖、原时限、清理及结果独审全部通过。新候选通过信用从0开始，旧E01/E03不挪用。受控corpus阶段不替代原真实联网门。

## 不在本提案内

不接受length响应、不修补残缺JSON、不从片段执行工具、不按关键字拼装或代写答案；不改模型、不加预算、不更新下载、不操作UI/音频/生产服务或保护身份。当前一次运行与一次复核已耗尽，失败不重试。本文件没有生成grant或预分配下一例。

## 证据依据

- [独立结果复核](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-controlled-preparation-20261108-r1/review/independent-result-review.md)；结果manifest 2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0，复核JSON 119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58。
- [本次结果报告](H:/UltimaAI/UltimaAgent/docs/reports/jarvis-work-t2-e02-output-structure-controlled-result-20261108.md)。
- 冻结产品agent_server.py:217–259；官方固定转换器H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-pattern-json-20261107-r1/inputs/upstream/json-schema-to-grammar.cpp:961–975，SHA256 65786b134832a4272f85671c11687cb05f6e92b0f9d3079536a8071fd3a20ec0。
- [封存后源码分析补充](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-controlled-preparation-20261108-r1/review/result-inputs/structural-analysis.json)，不在原56成员manifest中；本提案本身尚未实施或独审。
