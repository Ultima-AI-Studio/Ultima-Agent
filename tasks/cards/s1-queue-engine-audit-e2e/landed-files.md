# 落地文件清单

- NEW_FILE `tasks/queue_engine/audit.py`：回执/M4/角色分离审计、结构化业务判定、恢复与收尾。
- NEW_FILE `tasks/queue_engine/cli.py`：T4 真实插队命令入口。
- MODIFY_FILE `tasks/queue_engine/state_machine.py`：增加审计证据不明确时的受控 fail-closed 冻结入口。
- MODIFY_FILE `tasks/queue_engine/__init__.py`：导出审计与恢复公共接口。
- NEW_FILE `tasks/tests/test_audit_e2e.py`：T5 反例、恢复与真实空库端到端联测。
- MODIFY_FILE `tasks/cards/s1-queue-engine-audit-e2e/task.md`：回填 acceptance 与 receipt。
- NEW_FILE `tasks/cards/s1-queue-engine-audit-e2e/completion.md`：完成语。
- NEW_FILE `tasks/cards/s1-queue-engine-audit-e2e/landed-files.md`：本清单。
- NEW_FILE `tasks/cards/s1-queue-engine-audit-e2e/acceptance-evidence.md`：验收证据。
- NEW_FILE `logs/execution-reports/s1-queue-engine-audit-e2e/summary.json`：带 `version` 的执行报告。
- NEW_FILE `logs/execution-reports/s1-queue-engine-{storage,statemachine,dispatcher,priority-deps}/summary.json`：T1–T4 带版本字段的执行摘要。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/T5-audit-e2e.md`：T5 Gate 判定。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/work-order-selfcheck.md`：工单级自核摘要。
- NEW_FILE `tasks/queue/runs/queue-engine-20261021T0830/receipt.json`：本次运行结构化回执（最终自核后写入）。
