# E02研究写入失败诊断：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_948abbc3ba2948a9b3441d57051d9b27已授权有限诊断补修、必要独审、PASS后一例当前8B研究及一次只读独立结果复核；失败不重试。候选6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696基于0a57d50，工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent。

## 定位与改动

旧实际91fb07e8的writer报ValueError，但具体原因没有落盘，仍为UNKNOWN。静态读回纠正前份报告：_CapabilityTool.execute已在请求内ledger存入error/error_type，丢失位置是WorkService公开回执裁剪，不能据此反推旧具体原因。原失败和独审材料保持原SHA；项目结果报告只追加勘误并镜像。

唯一已有产品文件变动work_service.py。研究模式在最终裁剪前从可信ledger outcome snapshot的首个失败ultima_work_research_write记录生成research_failure。30个精确固定ValueError消息映射封闭原因码；不做子串或前缀猜测。阶段固定research.write，类型为固定白名单；未知原因UNKNOWN。任意异常原文不新增导出，只保存长度以及最多4096字符的SHA-256（surrogatepass，超长hash为null）。原公共error和tool_results行为保持；新增诊断不是成功判据，不改变writer/END/事实/引用/身份/文件字节/ACK/截止门。

诊断只读records，不读SDK/model提供的tool_results；最早原因不被后续通用END/后续writer记录替换。没有修改模型、参数、来源、预算、默认路径、UI/语音或生产服务。旧269aca5的E01/E03信用保持在旧候选，新候选没有现场信用。

## 离线证明与边界

有效RED为14失败/3通过，失败均为缺research_failure；一次早期测试对Unicode孤代理字符错误误期望通用END，已按实际已有UTF-8错误纠正，不修改产品异常控制流，该早期失败保留。GREEN诊断17，包含实际SDK/executor/writer/END合成原生传输流程、未签发/跨来源引用、重复来源、多行claim、未知/超长/Unicode异常、类型白名单、SDK伪造、最早原因和合法交付。

产品检查518：诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。延续两项原离线排除：本地HTTP集成与cmd junction，不计通过。测试native传输/GET为离线fixture，无真实模型调用。原Python审计guard与SSRF离线fixture不改；不把Python审计当作OS全流量测量。

验收harness原函数保持，只重绑新候选、路径及哈希；共享P4/P1不变。原238 harness案例与51入口/边界/输入检查必须在新绑定上通过，封存readback给出最终807项。60来源及1549输入绑定由生成清单核实。全部旧失败保持，新例在准备PASS前未释放。

## Review Focus

只从可信ledger选择最早writer失败；稳定诊断与任意异常/模型文本严格隔离；新增数据不能成为成功判据或改变END拒绝顺序；原schema/API成功与失败行为、模型/预算/时限/保护身份不变；新候选来源绑定与旧失败完整保留。

准备完成不代表E02通过。真实单例仍须SDK packet、research.md、ACK、两次外部字节读回、事实引用及原清理/时限。E02/T2当前NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。

## 独立准备审查结果

PASS_PREPARATION_ONLY；manifest 27b40bb96214db7480ea50e23926aaf6b72dcf429b768e13cf274cf5fb19671d（410成员），review SHA256 de10c96571ea29e7bf7af3d42e1aabc282b62dac105c07443816b37a98d1df5d。807项离线检查、1549绑定输入与60来源读回；实际入口尚未调用，按既有完整授权继续一例。
