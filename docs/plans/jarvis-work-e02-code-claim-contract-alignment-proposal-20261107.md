# E02代码事实生成契约对齐：待授权提案

原工单wo-ultimaagent-20261101-0021 / T2。产品目标仍是用当前社区8B完成可追溯、能实际交付的研究工作。本提案未实施、未新建候选、未运行新测试或模型，也未分配下一例。

## 当前证据与局限

来源与证据关联候选a0d21ebf167c41a76410075f7a92f1680926213f完成857项离线检查及独立准备审查；唯一8B原题四来源运行dc3dbef6-ef60-4ba6-8d54-79c9c93d99df耗时43.4456879秒，未交付research.md。原失败及源码冻结保留。

本例写入诊断CODE_OPERATION_REQUIRED，ValueError，42字符摘要b577a36cbea9c8b39ba76e2b324ea4d08c17c11baaf5fa26612325718559096b，匹配work_research.py:329–332的唯一复合拒绝条件：symbol必须有效且长度不超过200，并在claim中以规定边界准确出现。当前检查到的事实已跨过引用存在/来源归属；具体claim、symbol、来源与引用ID未导出，不能确定哪个子条件失败，也不能声称全部后续事实合格。独立结果复核负责确认这一边界。

## 建议路线

继续使用现有可信证据卡、JSON Schema、SDK和事实核验器。先把当前写入器的全部前置条件列成一份对照表：哪些已在生成schema表达，哪些属于结构限制，哪些必须保留到事实审查。此盘点不放宽任何条件，也不把未处理项伪称解决，避免只追逐下一条错误码。

本轮实现范围限于代码事实的可见契约：从同一请求、同一阶段已经确认可见的证据卡投影source_id、evidence_id、kind和operation；只有经过原格式/长度规则校验的operation可成为code事实选项。对每张code证据卡，在其evidence_id对应的fact分支中声明claim必须包含该精确操作名；优先使用现有anyOf/enum和官方支持、经本地回归验证的pattern表达，不新增生成后改写器，不向模型虚构事实或补全函数名。非code事实仍用原有claim规则。

生成时的native format、本地strict schema、phase文本和独立runtime重放必须使用同一可信可见集合及相同约束；重放从验证后的reads重建，不能只信任wire自报schema。原writer的symbol、事实、代码AST/词法证据、来源去重、END、ACK和两次外部读回全部保留。

JSON Schema到原生采样器的正则支持及上下文体积必须先验证。不能仅把原Python lookbehind表达式直接塞进采样schema；若现有机制不能准确表达，准备阶段应明确失败并停止，不扩大时限、删来源、改模型或绕过事实门。

## Task 1: 新隔离候选与离线准备

- 从a0d21eb新建隔离候选，不改旧候选或旧证据。写域限研究schema/可信卡片投影、generation和独立replay及必要测试。
- 先写RED：匹配同一证据ID但claim省略operation、只写近似名称/不合法前后边界、选择其他证据operation；证明当前schema接受而原writer拒绝。另有合法代码事实、非code事实、无效/过长operation、空卡片、跨请求和pending第三页用例。
- 最小实现配对契约。真实SDK mock transport必须核对format/strict/sampler/phase一致；错误claim在writer派发前拒绝且无文件/effect，合法三来源链路完成写入、ACK、SHA读回和独立重放。
- 对改写自报hash/native entity后的schema、operation映射、phase伪造做重放负例。保留所有原诊断与事实门；测试故障注入只能用于检验失败路径，不能进入产品路径。
- 最多6页48卡/5来源核对原32768/49152字节门、输出及次数预算；超限失败关闭，不静默截断约束。列出仍未通过或尚未覆盖的契约，不宣布实际研究成功。
- 运行受影响离线回归，提交/tag，重绑候选和输入哈希，必要独立准备审查；旧失败及原HTTP/junction排除保留。保护基线使用既有七角色强校验，任何再次漂移先只读核对，不控制服务。

## Task 2: 仅在准备独审PASS后的新单例

- 需要新范围明确授权后，才分配一例当前qwen3-8b-uncensored原题四来源研究及一次只读独立结果复核；失败不重试。
- 原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。不增加重试或模型轮次，无14B、UI、音频或生产服务操作。
- 成功必须有实际research.md、可信SDK packet、ACK、外部读回和逐事实审查，最多该新候选受控1/3；失败保留首结果及有限诊断。
- 原E02完整门、同候选后续例数、真实联网、当前候选E01/E03及T2/Owner出口仍保留。旧269aca5信用不转移。

## Review Focus

operation必须来自当前阶段可信卡片；claim约束不能接受其他operation或只有子串命中；非code语义不改；采样schema方言和严格校验一致；动态分支不能突破原字节/次数/时间门；结果不得由生成后拼字或自动放宽规则制造。具体失败文本未知的边界须继续如实记录。

远端push仍受此前自动审批blocked by policy阻断，本提案不包含重试或绕行。此文件只是可审阅的下一步，当前授权单例已结束，不能把本提案当作新执行许可。
