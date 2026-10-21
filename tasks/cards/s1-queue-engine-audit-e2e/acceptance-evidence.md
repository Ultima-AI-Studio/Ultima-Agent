# 验收证据

## T5 专项

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe tasks\tests\test_audit_e2e.py -v`
- 最终结果：7 项通过、0 失败。
- AU-01/AU-02：完整回执需完成语、落地清单、reviewReason、stdoutText、evidence、acceptance 全绿；缺回执时审计判冻结且任务不能完成。
- AU-03：开发技能与审计技能相同会判冻结；仅 `eng.audit` 可作为运行时审计技能。
- AU-04/AU-05：summary 强制 `version=S1/v0.x` 及完整字段；校验产物路径、注册表 `task-queue-engine` 登记和报告完整性。
- AU-06：全新临时库从空数组立项，实际隐藏派发、自检、审计、收尾到已完成；事件序列为 `EXECUTING → SELF-CHECK → AUDIT → COMPLETED`，运行期可见窗口捕获数 0。
- AU-07：证据不明确转冻结；已知业务缺陷输出修正任务并转失败。

## 强制反例

- 非法迁移：T2 覆盖执行中直跳完成、审计未明确通过完成、执行中取消。
- 重复派发：真实重复调用只产生一组六件套。
- 依赖环：A→B→C→A 在落盘前拒绝并报告完整路径。
- WIP/锁：同组最多 2；独立隐藏进程真实持锁时竞争方按忙拒绝。
- 进程退出 0 但业务失败：真实子进程输出 `business_success=false` 且退出 0；恢复到自检后读取六件套业务结果并转失败，未进入完成。
- 无回执：审计判冻结，未完成。
- 恢复不重跑：实际子进程仅将计数器写为 1；恢复到自检后再次派发被拒，六件套仍仅 6 个文件。
- 实际无窗口：T3/T5 均以实际指定 Python 子进程约 10ms 轮询枚举，捕获可见窗口数 0。

## 工单全量回归

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -m unittest discover -s tasks\tests -p test_*.py -v`
- 结果：`Ran 36 tests in 3.095s`；`OK`。
- 语法核对：`AST_COMPILE_OK 12`。
- 真实任务库：`tasks/tasks.json` 独立回读仍为 `[]`；真实 `tasks/events`、`tasks/runs`、`tasks/archive` 仅含占位文件，测试未写入产品任务。

判定：机制实现自核通过，工单进入 `READY_FOR_REVIEW`；独立 W2 尚未执行。
