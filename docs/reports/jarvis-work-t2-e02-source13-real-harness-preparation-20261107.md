# 当前8B真实研究：原harness离线适配完成

原单 wo-ultimaagent-20261101-0021 / T2。Task2已完成，真实入口和整体独立准备审查尚待Task3。当前没有新的模型、现场用例或结果复核分配；E02/T2仍未通过。

- 使用当前候选269aca5与当前社区8B摘要，复用既有实际研究harness、SourceNavigation及官方SDK。没有改动冻结产品、模型默认配置或已通过的零推理包。
- 旧五身份改为七身份，校验原生创建时间、父PID、命令摘要和CIM身份；精确适配已接受P4快照中的CreationFileTime字段。实际child仍只安装原四来源搜索/GET夹具及导出观察器，HTTPX模型Client/send/transport保持原实现。
- 原71个测试函数、219个参数化用例身份全部保留。最后一轮219/219通过；新增10项身份及真实调用路径检查通过，已有SDK完整产物只读复放1项通过。本步骤230项，加Task1的14项输入检查，共244项离线检查；不是244次产品验收。
- SDK复放读取a47c74c4-58e7-4a63-ad7d-f63be9c17a51的原始packet、原四来源、最终ACK、引用绑定和research.md（711字节，SHA256 a7e7e5906654d1981efb48a3e8006de0d45270f27db0adfee5ee02513c549df2）。文件逐项哈希保持，历史6次Mock POST计数未计为真实推理。
- 本轮完整回归原始结果依次135/219、204/219、218/219、214/219、219/219，失败及每轮源码快照保留。最后一轮：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261106\code\harness-preparation-20261106T162116319429Z。

## 测试适配裁定与限制

1. SDK的Rust SSRF可绕过Python DNS替身；离线单测显式使用SDK自身Python检查并固定DNS。沿用已通过的精确IPv6冷导入审计和未使用Ollama客户端关闭机制。审计无拒绝事件，唯一冷导入探针已关闭；没有模型或产品启动。原生系统包数量未测，不能宣称抓包证明。
2. 旧harness漏导入产品既有稳定熵夹具，一次随机来源ID触发真实PII扫描。复用稳定熵并仅将测试UUID固定为合法version4，以符合真实外部读回器；没有放宽扫描器或UUID检查。此测试不证明生产随机ID质量，真实研究仍须按原门实际验证。

准备manifest：c90437e780770e1cf3d743735e30d316e45722b90b6ea1ea8cb76d88bbf7daab。本地检查点tag：ultimaagent-t2-e02-source13-real-harness-20261107，不构成运行批准。下一步按既有计划Task3连接RootInvocation、一次性分配和整体独立审查，保留275/310/315秒及8次POST上限，再提出真实8B单例。

E01同候选3/3和E03三正一负PASS保留。KWS/语音、生产服务未操作。远端push仍受此前自动审批blocked by policy阻断，本轮未重试或绕行。
