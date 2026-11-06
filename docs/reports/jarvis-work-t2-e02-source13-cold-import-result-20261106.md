# E02 SDK 冷导入补修与单例结果

结论：冷导入兼容修复通过，实际接线单例仍 FAIL。一次运行与一次结果独立复核均已完成，未重试；E02 真实研究和 T2 仍未通过。

## 已完成的修复与验证

profile 仅精确放行 socket.gethostname 本机元数据读取，保留其他 socket/subprocess 拒绝、原四来源和 275/310/315 秒截止。根入口只重新绑定目录和 profile 摘要，SDK/vendor、产品候选269aca5、当前8B及语音链路不改。

真实 worker/reader 全新进程 RED 均复现旧拒绝，GREEN 均完成真实 Ollama/HTTPX 导入与关闭。最终 profile 回归561/561（原557全部保留）、根入口89/89通过。保留最初88/89路径绑定失败及两轮RED/GREEN；原540个证据绑定无变化。准备独审PASS（报告SHA cc00876f08fca31496b80bcf22381e31fa1c7ed7720efab383998f7483f5d466），准备提交 0dc7174b217f4739007dc81ee92d51108a0c3d01，镜像 4636dff33a17574ca9ab9370cd910ce48311ab11，tag ultimaagent-t2-e02-source13-cold-import-ready-20261106。

## 实际单例

run_id：726b5883-f57c-4693-899e-17c9d1719b22。根入口约20.4197258秒退出1；terminal机械FAIL，无验收计分。

- 已越过原冷导入失败点。原SDK完成一次文件写入，research.md为711字节，SHA-256 a7e7e5906654d1981efb48a3e8006de0d45270f27db0adfee5ee02513c549df2。服务返回succeeded，写入与ack记录存在。
- profile最终failed：audit_clean=false、scope_clean=false、eager_clean=false，clients_closed=true；private_scope退出门报告拒绝或清理不合格。不能把外层异常传播造成的eager_clean=false单独判作eager关闭故障。
- root因worker非成功退出而停止。新reader没有启动，两次原读回没有发生，因此该文件为MATERIALIZED_NOT_ACCEPTED，不能当成E02交付。
- 6次SDK推理事件/POST及12次metadata来自原固定MockTransport流程，不是实际8B推理或真实11434请求的次数。原资料fixture读取和SDK写入有记录；OS全局数据包及Rust原生DNS次数未测量，保持null。
- 清理PASS：运行自己的worker解释器/launcher及观察到的console已退出，日志关闭；独立只读后检确认root原身份亦不在。七个保护进程的原生创建身份、exe、parent及命令摘要均匹配，结论仅覆盖记录时点。

## 独立结果复核

结论PASS_FAILED_RESULT_PRESERVATION，表示失败事实及证据保存通过复核，不表示运行通过。报告：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-cold-import-20261106\review\independent-cold-import-result-review.json，SHA-256 bf2a9b142ca667213c6a1bcefec2c1ca6996b5fede6b982b8189de2b3f41aa75。结果manifest：6bdd53ed92fa3ae7b6691e8ca4d2f1933c5c71a22ad79e28969d8d18e9e4316c，52个绑定。运行、日志、单次release/consumed及旧失败均保留。

## 未解决项与下一步

audit_clean=false证明出现过被拒绝的审计事件，但当前导出没有保存具体事件名或调用位置，因此不能诚实地给出更细根因，也不能直接扩大放行规则。现有audit_closeout可导出事件计数；建议先补这条证据并做限定诊断，再据事件判断最小修复。具体提案：docs/plans/jarvis-work-e02-source13-audit-closeout-diagnosis-plan-20261106.md。本轮没有实施该提案或再跑用例。

本轮用户授权call_c6b188dbc9514611ad330bb3b8829619中的一次实跑和一次结果复核已使用完。E01三轮、E03三正一负保持PASS；E02/T2和后续/Owner门未过。零推理接线即使将来通过，也不能代替E02三轮真实研究。

本地结果tag：ultimaagent-t2-e02-source13-cold-import-fail-20261106；项目docs、UltimaDocs镜像及本地提交读回分别登记在execution/result-checkpoint.json。远端push仍保留此前自动审批blocked by policy，本轮没有重试或换渠道。
