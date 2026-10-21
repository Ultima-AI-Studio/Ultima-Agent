# 验收证据

## 失败测试

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_queue_source.py -v`
- 预期失败：`ModuleNotFoundError: No module named 'src.brain.queue_source'`，见 `logs/queue-source-test-2026-10-21-failing.txt`。

## 开发自检通过

- 同命令最终结果：`Ran 4 tests`，`OK`，见 `logs/queue-source-test-2026-10-21.md`。
- 真实八态：隔离库经 `QueuePlanner`/`StateMachine` 生成八种当前状态，各计 1 项；失败与冻结为 2 个当前异常，取消不计失败。
- 历史分离：事件流含历史失败的任务完成恢复后，当前状态仅为已完成且当前异常为 0。
- 字段：每项投影 `task_id/title_zh/state/priority/duration/terminal_reason`，并附 §10 中文映射。
- 失败闭合：缺失、损坏、非法状态均返回“状态读取失败”；缺失库没有被初始化成空库。
- 空生产库：如实返回总数 0，未写入示范任务，哈希不变。

判定：开发自检通过；独立 W4 尚未执行。

## W4 修复证据追加

- RED：`logs/text-loop-w4-repair-20261021/red-readonly-tree-v2.txt`。
- GREEN：`logs/text-loop-w4-repair-20261021/green-readonly-tree.txt`。
- 全套与独立脚本复跑：`logs/text-loop-w4-repair-20261021/green-text-suite.txt`、`logs/text-loop-w4-repair-20261021/independent-review-rerun/independent-results.json`。
- v0.1 仍为 36/36，生产 `tasks.json` 不变：`logs/text-loop-w4-repair-20261021/final-frozen-baseline.txt`。
- 独立签署状态：`independent_w4_completed=false`。


## W4 独立技术验收收口（2026-10-21）

两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。
