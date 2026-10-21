# 落地文件清单

- NEW_FILE `tasks/queue_engine/__init__.py`：存储接口导出。
- NEW_FILE `tasks/queue_engine/storage.py`：五目录、瘦身索引、追加事件、运行六件套、保守归档。
- NEW_FILE `tasks/tests/test_storage.py`：T1 隔离单测。
- NEW_FILE `tasks/tasks.json`：真实任务库初始空索引（创建前不存在）。
- NEW_FILE `tasks/events/.gitkeep`：事件目录占位。
- NEW_FILE `tasks/runs/.gitkeep`：运行记录目录占位。
- NEW_FILE `tasks/archive/.gitkeep`：归档目录占位。
- MODIFY_FILE `tasks/cards/s1-queue-engine-storage/task.md`：回填 acceptance 与 receipt。
- NEW_FILE `tasks/cards/s1-queue-engine-storage/completion.md`：完成语。
- NEW_FILE `tasks/cards/s1-queue-engine-storage/landed-files.md`：本清单。
- NEW_FILE `tasks/cards/s1-queue-engine-storage/acceptance-evidence.md`：验收证据。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/T1-storage.md`：T1 Gate 判定。
- NEW_FILE `logs/execution-reports/s1-queue-engine-storage/summary.json`：带版本字段的执行摘要（W2 待执行）。
