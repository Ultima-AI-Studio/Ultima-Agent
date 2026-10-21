# 落地文件清单

- NEW_FILE `tasks/queue_engine/dispatcher.py`：串行/并行闸门、OS 锁、三重幂等、隐藏派发、暂停、父失联退出。
- MODIFY_FILE `tasks/queue_engine/__init__.py`：导出派发器公共接口。
- NEW_FILE `tasks/tests/test_dispatcher.py`：T3 隔离及实际 Windows 子进程联测。
- MODIFY_FILE `tasks/cards/s1-queue-engine-dispatcher/task.md`：回填 acceptance 与 receipt。
- NEW_FILE `tasks/cards/s1-queue-engine-dispatcher/completion.md`：完成语。
- NEW_FILE `tasks/cards/s1-queue-engine-dispatcher/landed-files.md`：本清单。
- NEW_FILE `tasks/cards/s1-queue-engine-dispatcher/acceptance-evidence.md`：验收证据。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/T3-dispatcher.md`：T3 Gate 判定。
- NEW_FILE `logs/execution-reports/s1-queue-engine-dispatcher/summary.json`：带版本字段的执行摘要（W2 待执行）。
