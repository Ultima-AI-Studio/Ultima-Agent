# 验收证据

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe tasks\tests\test_priority_deps.py -v`
- 结果：`Ran 7 tests in 0.227s`；`OK`。
- PD-01/PD-03：优先级 100 先于 50，同优先级按 `created_at` FIFO；范围外值拒绝。
- PD-02：`third` 插到 `first` 前，重建规划器后读取持久化顺序仍为 `third, first, second`；真实隐藏子进程调用 CLI `requeue third --before first` 退出 0 且顺序一致。
- 执行中保护：对执行中任务调优先级直接拒绝，未改状态或顺序。
- PD-04：A→B→C→A 报出完整环路径，候选 C 未写入索引。
- PD-05：依赖执行中时保持排队；依赖失败时自动冻结并记录精确原因；依赖完成后真实隐藏子进程派发并退出 0。
- PD-06：插队事件字段精确为 `ts/from/to/reason/actor`，事件追加可查。

判定：执行端自核通过；独立 W2 尚未执行。
