# 落地文件清单

- NEW_FILE `tasks/queue_engine/priority_deps.py`：优先级/FIFO、插队、DAG 环检测、依赖 Gate。
- NEW_FILE `tasks/queue_engine/cli.py`：真实 `requeue <task_id> --before <task_id>` 命令入口。
- MODIFY_FILE `tasks/queue_engine/dispatcher.py`：派发前接入依赖 Gate。
- MODIFY_FILE `tasks/queue_engine/__init__.py`：导出规划器公共接口。
- NEW_FILE `tasks/tests/test_priority_deps.py`：T4 隔离单测与真实依赖完成派发。
- NEW_FILE `tasks/queue/queue.md`：运行时派发顺序持久化文件。
- MODIFY_FILE `tasks/cards/s1-queue-engine-priority-deps/task.md`：回填 acceptance 与 receipt。
- NEW_FILE `tasks/cards/s1-queue-engine-priority-deps/completion.md`：完成语。
- NEW_FILE `tasks/cards/s1-queue-engine-priority-deps/landed-files.md`：本清单。
- NEW_FILE `tasks/cards/s1-queue-engine-priority-deps/acceptance-evidence.md`：验收证据。
- NEW_FILE `docs/reports/evidence/stage1-queue-engine/T4-priority-deps.md`：T4 Gate 判定。
- NEW_FILE `logs/execution-reports/s1-queue-engine-priority-deps/summary.json`：带版本字段的执行摘要（W2 待执行）。
