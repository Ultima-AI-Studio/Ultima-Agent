# T1 temporary global table sample

This is the expected output shape produced in a pytest `tmp_path`. It is not copied from or written to the real global table.

<!-- queue-summary:start -->
| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| UltimaConsole | 1 | 0 | 1 | 0 | 0 | 0 |
| UltimaAgent | 1 | 0 | 0 | 0 | 0 | 1 |
| 合计 | 2 | 0 | 1 | 0 | 0 | 1 |
<!-- queue-summary:end -->

<!-- queue-items:start -->
| 项目 | 工单 | 状态 | 依据/说明 |
|---|---|---|---|
| UltimaConsole | wo-console-20261029-0001 | executing | fixture |
| UltimaAgent | wo-ultimaagent-20261029-0001 | frozen | 运行时状态聚合 |
<!-- queue-items:end -->

Canonical detail states remain `pending/executing/audit/frozen`, matching `queue-status-gen.py`; the summary retains the existing Chinese column order and semantics.
