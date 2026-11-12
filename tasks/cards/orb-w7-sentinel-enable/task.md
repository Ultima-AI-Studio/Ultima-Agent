# 任务卡：orb-w7-sentinel-enable

- **task_id**：orb-w7-sentinel-enable
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：sentinel 挂上 run 目录（判据对齐 + 派发自动拉起）
- **创建**：2026-11-08 · 主脑过渡托底（DeepSeek 未接线，接线后交还外脑）
- **M1 声明**：已查能力注册表，`src/brain/sentinel.py` 已有 `Sentinel.run`/`tick` 与 `DispatchLock` 单例，`dispatcher.process_identity` 可复用；本次只改判据与派发器挂载点，无新依赖

## goal

让 `sentinel.py` 真正观察到每一单的 run 目录：判据认派发器实际产出的 `final.json`（现在错判成 `final-message.json`），派发器 spawn codex 后无窗拉起 sentinel，收尾时不留孤儿。禁止：不改派发器 CLI 参数、不改 WIP 闸门、不改主表口径、不真实杀进程。

## acceptance[]

- [ ] ACCEPT: `final.json` 存在时 sentinel 不判 anomaly（`final_message` 判据同时认 `final.json` 与 `final-message.json`）
- [ ] ACCEPT: 假 run 目录 + 假 pid 连跑 3 tick，`heartbeat.jsonl` 恰 3 行
- [ ] ACCEPT: 进程死 + 两份 final 都不存在 + 日志超 90s → 第 3 tick 落 `anomaly.json`（kind=exit-anomaly, consecutive=3）
- [ ] ACCEPT: 恢复后落 `recovered.json`，`_anomaly_active` 复位
- [ ] ACCEPT: 第二个 sentinel 抢同一 run 目录时返回 2（单例锁生效）
- [ ] ACCEPT: 派发器 `--order/--prompt/--execute/--repair` 参数与 dry-run 输出 `{"ready": true, …}` 格式不变
- [ ] ACCEPT: sentinel 仍只读：不写主表、不改 `done.json`、不 kill 任何 pid
- [ ] ACCEPT: 单测全绿，断言无 `assertTrue(True)`

## dependsOn[]

- 无

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\sentinel.py`
- `H:\UltimaAI\UltimaAgent\scripts\dispatch-work-order.py`
- `H:\UltimaAI\UltimaAgent\tests\test_sentinel.py`
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w7-sentinel-enable\`

## priority

- 95

## reasoningEffort

- high

## category + skill

- category: eng-orchestration · skill: eng.backend（常驻观察者与派发器挂载）

## receipt

- reviewReason: 待 Codex 执行后回填
- stdoutText: 待回填
- evidence: 待回填
- acceptance 逐项核对: 待回填

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 判据对齐 | final 文件名兼容 | 两种文件名都不误判 | 测试输出 |
| U-02 心跳与异常 | tick / anomaly / recovered | 3 tick 三场景 | 测试输出 |
| U-03 单例锁 | `DispatchLock(.sentinel.lock)` | 第二个返回 2 | 测试输出 |
| U-04 派发器挂载 | spawn sentinel + 收尾退出 | dry-run 格式不变、无孤儿 | dry-run 输出 |
