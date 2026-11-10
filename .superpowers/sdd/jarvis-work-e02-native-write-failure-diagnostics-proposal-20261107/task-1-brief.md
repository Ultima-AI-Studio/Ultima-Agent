## Task 1: 有限写入诊断与离线准备

新隔离候选基于0a57d50。真实SDK离线fixture复现writer拒绝后仅剩通用END错误；从可信ledger首个失败writer记录导出封闭原因码/阶段/有限类型，未知文本不直接落盘。与旧status/error/END拒绝行为并存，不放宽成功门，不相信SDK/model伪造的tool_results诊断。验证最早原因、后续END遮蔽、未知/敏感文本不泄漏、合法路径和拒绝门；相关离线回归、候选重绑、封存独审及本地commit/tag/镜像。

