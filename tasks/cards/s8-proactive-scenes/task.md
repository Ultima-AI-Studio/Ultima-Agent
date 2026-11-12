# 任务卡：s8-proactive-scenes
- **task_id**：s8-proactive-scenes
- **标题**：主动调度铺开（C 类 · 主动提醒与异常上报场景）
- **优先级**：80（P1）
- **category**：core　**skill**：engineering
- **依赖**：s3-heartbeat（M27 TICK/抢占/预算/发言边界已建）
- **依据**：jarvis-reverse-architecture M27 + G6（规则巡检+历史偏差告警，不做预测性结论）；对齐报告维度 2 主动智能度

## goal
在既有 HeartbeatTicker 之上做实主动场景（不动 TICK 内核，挂场景供给器）：
1. 主动提醒：注册定时提醒条目（schedule：一次性 at / 周期 interval），到点产出"主动发声"提案；
2. 异常上报：注册关注异常（任务失败/进程异常等），规则巡检产出异常上报提案；
3. 场景引擎 ProactiveSceneEngine：条目持久化（JSON 文件）、到期判定（基于 tick 时间/周期）、
   产出提案文本；与 Ticker 的抢占/预算/发言边界衔接（Ticker 只负责发声时机，场景引擎负责"说什么"）。
   
**禁止**：不做预测性结论；不无限自转；异常未确认不重复轰炸（单条目单周期一次）。

## acceptance[]
- [ ] ACCEPT-1：注册/取消定时提醒条目（at/interval），持久化可恢复
- [ ] ACCEPT-2：到期判定产出主动提醒提案（含目标时间与文案）
- [ ] ACCEPT-3：异常上报条目注册，规则巡检产出异常提案（单周期一次，不重复轰炸）
- [ ] ACCEPT-4：与 HeartbeatTicker 衔接：Ticker 空闲态取场景提案发声，忙碌/抢占让位不受影响
- [ ] ACCEPT-5：回执完整（ReceiptValidator 0 issues + tasks.json COMPLETED）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/heartbeat + tests + tasks）
