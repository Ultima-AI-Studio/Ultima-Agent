# 任务卡：orb-w6-sentinel

- **task_id**：orb-w6-sentinel
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：常驻监工 Agent（30s 心跳 + 三判据异常检测）
- **创建**：2026-11-08 · 主脑立项（用户批 A 方案）
- **M1 声明**：已查能力注册表，`DispatchLock` 复用做单例互斥、`process_identity` 复用做进程判定；监控主循环为唯一自研点（已在工单 §5 开源排查表登记）

## goal

新增 `src/brain/sentinel.py`，实现 ⑤ 分发·监控的常驻监工：30s 一 tick 写心跳，三判据同时成立且连续 3 tick 才判异常并写事件文件。禁止：不杀进程、不重派、不判业务成败、不改主表。

## acceptance[]

- [x] ACCEPT: `Sentinel(order, run_dir, pid, expected_identity, interval=30, missed=3)` 可实例化，`tick()` 返回 `{ts, pid_alive, final_message, log_age_s}`
- [x] ACCEPT: 每 tick 向 `heartbeat.jsonl` 追加一行，UTF-8、不覆盖历史
- [x] ACCEPT: 进程不在 + 无 `final-message.json` + 日志静默 >90s 三判据同时成立，连续 3 tick 才写 `anomaly.json`，`kind=="exit-anomaly"`
- [x] ACCEPT: 仅 2 tick 异常不产生 `anomaly.json`（证明 missed=3 生效）
- [x] ACCEPT: 异常后恢复写 `recovered.json`，且 `anomaly.json` 不被删除
- [x] ACCEPT: 单例互斥用 `DispatchLock` 抢 `run_dir/.sentinel.lock`，抢不到退出码 2
- [x] ACCEPT: 单测 4 用例（正常 / 进程消失 / 日志静默仅2tick / 恢复）全绿，进程判定打桩不真杀进程，interval 用 0.05 不 sleep 30s

## dependsOn[]

- 无

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\sentinel.py`
- `H:\UltimaAI\UltimaAgent\tests\test_sentinel.py`
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w6-sentinel\`

## priority

- 95

## reasoningEffort

- high

## category + skill

- category: eng-orchestration · skill: eng.backend（监工与事件契约）

## receipt

- reviewReason: T2 自检通过；仅供后续独立审计，不构成 G-ORCH 验收
- stdoutText: `5 passed in 0.10s`（固定解释器，`pytest -q -p no:cacheprovider -o addopts= tests/test_sentinel.py`）
- evidence: `src/brain/sentinel.py`；`tests/test_sentinel.py`
- acceptance 逐项核对: 7/7 PASS；心跳追加、三判据、missed=3、恢复留痕、单例锁及全打桩场景均由专项断言覆盖

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 心跳 | `tick()` + `heartbeat.jsonl` | 每 tick 一行 | 文件样例行数 |
| U-02 异常判定 | 三判据 + missed=3 | 2 tick 不报、3 tick 报 | 测试输出 |
| U-03 事件文件 | `anomaly.json` / `recovered.json` | 字段齐全且不互删 | 产物样例 |
| U-04 单例 | `DispatchLock` 抢锁 | 第二个实例退出码 2 | 测试输出 |
