# s4-state-axis 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：COMPLETED
- 实现：状态与记忆共享轴 `src/brain/state/axis.py`（M04）
- 聚合源（真实组件，只读消费不改底层）：BondSystem.state_axis() / DeviceRegistry.all() / TaskQueue.view() / BehaviorMapper.map()

## 实际命令与结果

1. `python -m unittest src.brain.state.tests.test_state_axis_s4 -v`
   - `Ran 7 tests` → `OK`（ACCEPT-1~6 + unsubscribe）
2. 回归 `python -m unittest src.brain.display.tests.test_behavior_layer_s3 src.brain.orchestration.tests.test_orchestrator_s3 src.brain.iot.tests.test_device_profile_s3 src.brain.persona.tests.test_bond_s3`
   - `Ran 21 tests` → `OK`（既有行为层/队列/设备/羁绊不倒退）
3. 测试数据全落 tempfile，未污染真实库

## ACCEPT-1~6

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 四类聚合只读视图可用（session/identity/device/tasks），身份含 tier、设备列表、队列 total |
| ACCEPT-2 | PASS | 每类带 updated_ts + 聚合 version；voice 状态更新后版本递增 |
| ACCEPT-3 | PASS | 跨形态消费同一快照：visual_snapshot() 与 categories.session.visual 一致（行为层状态机接入） |
| ACCEPT-4 | PASS | 订阅推送生效：on_bus_event（voice./bond./device./queue./task.）→ 刷新 → 订阅者收到同版本新快照；unsubscribe 后不再推送 |
| ACCEPT-5 | PASS | 回归 21/21 全绿（行为层/队列/设备/羁绊） |
| ACCEPT-6 | PASS | 回执字段完整（version/updated_at/categories） |

## 关键实现约束

- 统一只读视图：消费方只拿 snapshot()，不直接改底层；
- 事件推送：总线事件回调挂点 on_bus_event(event_type, payload)，订阅者模式；
- 单类失败不阻断聚合（error 字段标记）；
- 跨形态：悬浮球/组合窗口消费同一 visual_snapshot()。
