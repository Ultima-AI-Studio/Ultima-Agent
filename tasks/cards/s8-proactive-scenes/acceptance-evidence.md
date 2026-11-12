# s8-proactive-scenes 验收证据

- 验收人：主脑（豆包直做）
- 验收时间：2026-10-27
- 依据：jarvis-reverse-architecture M27 + G6（规则巡检，不做预测性结论）；对齐报告维度 2 主动智能度

## 实现范围（增量，不推倒 TICK 内核）

新建 `src/brain/heartbeat/proactive_scenes.py`（ProactiveSceneEngine）：
- 定时提醒：`register_reminder`（一次性 at_ts / 周期 interval）、`cancel_reminder`，JSON 持久化可恢复；
- 异常巡检：`register_watch`（name + check 函数返回 (ok, detail)）、`cancel_watch`；
- `collect(now_ts, fire_interval_seconds=300)`：到期产出提案（reminder/watch），单条目防重复轰炸，
  恢复后窗口重置；
- 与 HeartbeatTicker 衔接不变：Ticker 负责发声时机（空闲/抢占/预算），场景引擎负责"说什么"。

## 验收项逐条

| 项 | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 注册/取消提醒（at/interval）持久化 | 通过 | test_register_cancel_reminder / test_register_reminder_invalid / test_reminder_persistence_reload |
| ACCEPT-2 到期产出提醒提案（一次性不重复） | 通过 | test_reminder_due_fires_once / test_interval_reminder_repeats |
| ACCEPT-3 异常巡检单周期一次不轰炸 | 通过 | test_watch_fires_and_no_bombard / test_watch_recovers_resets / test_watch_rejects_bad_check |
| ACCEPT-4 与 Ticker 衔接（空闲发声/抢占让位） | 通过 | test_ticker_integration |
| ACCEPT-5 回执完整 | 通过 | 本文件 + receipt.json，ReceiptValidator 0 issues |

## 测试结果

- 新增：src/brain/heartbeat/tests/test_proactive_scenes_s8.py — 9/9 通过
- 回归：test_heartbeat_s3 + test_proactive_scenes_s8 — 14/14 通过

## 边界确认

- 不做预测性结论（G6 边界）；单条目单周期一次（防重复轰炸）；恢复后解除轰炸窗口。
