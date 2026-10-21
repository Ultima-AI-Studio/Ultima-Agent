# 落地文件清单

- NEW_FILE `tasks/queue_engine/state_machine.py`：八态定义、迁移守卫、依赖冻结、人工解除、事件恢复重试计数。
- MODIFY_FILE `tasks/queue_engine/__init__.py`：导出状态机公共接口。
- NEW_FILE `tasks/tests/test_state_machine.py`：T2 隔离单测。
- MODIFY_FILE `tasks/cards/s1-queue-engine-statemachine/task.md`：回填 acceptance 与 receipt。
- NEW_FILE `tasks/cards/s1-queue-engine-statemachine/completion.md`：完成语。
- NEW_FILE `tasks/cards/s1-queue-engine-statemachine/landed-files.md`：本清单。
- NEW_FILE `tasks/cards/s1-queue-engine-statemachine/acceptance-evidence.md`：验收证据。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/T2-statemachine.md`：T2 Gate 判定。
- NEW_FILE `logs/execution-reports/s1-queue-engine-statemachine/summary.json`：带版本字段的执行摘要（W2 待执行）。
