# E02 原生 HTTP 诊断：离线准备记录

候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0，父版本2b42b3e19516154a26cbc895a3d9e69fabb07ab2；代码tag为ultimaagent-e02-native-http-diagnostics-candidate-20261107。本记录在独立候选审查前封存，审查结论另见后续独立回执。

产品仅修改 work_research_diagnostics.py：私有诊断v3投影最后一个可信HTTP receipt，包括代次、固定路由、状态码、请求摘要/大小、预留标记和有界字节计数。timeline与wire代次/请求SHA共同约束身份；HTTP成功与内容已验证是两个字段。未发包/无响应/500/200后坏JSON或schema/扫描失败分别保留实际信息；正文、任意URL、异常文本不进入诊断。原异常、扫描、冻结一次、16384字节上限、complete=false/credit0保持。agent_server.py及模型请求/传输/预算/schema/写入不改。

RED：38个新增用例在旧代码失败，保存为http-red-20261107T083618967067Z，无导入或网络审计错误。当前字节GREEN：700项产品回归（含43个HTTP诊断新例）及6项原受限导出helper兼容检查，共706项、无重复。旧两项HTTP/junction排除保持；不将未重跑的整套实际harness或原生二进制推理声称通过。每组保留源码快照、JUnit、受限Python审计、stdout/stderr和receipt。完整读取结果见verification/offline-readback.json与提交后读回。

原生兼容性核对见research/compatibility-findings.md：当前8B内置模板支持enable_thinking=false，产品已传think=false。固定版Ollama源码对参数/format有相应映射，但参考grammar转换不是本机原生解析通过。前例500与peg-native日志关联尚不能证明具体原因，本候选没有猜测调整native格式/模板/输出上限。

2026-11-07T08:29:29.501933Z及08:44:12.776509Z的只读核对中，七保护身份、Ollama0.32.15、当前8B摘要均匹配；不主张连续存活。前例2501准备成员、49结果成员、4补充成员、1563原输入、9无关文件均保持。前例清理PASS/无重试仍仅属于前例。

本轮实际例0、模型调用0、服务操作0，未生成实际harness/authority/release。当前候选E02仍0/3，T2/Owner未通过；历史E01/E03不迁移。新的事实/引用/原题覆盖/写入/ACK/时间/清理验收仍未发生。本记录是离线候选准备，不是产品工作能力通过。
