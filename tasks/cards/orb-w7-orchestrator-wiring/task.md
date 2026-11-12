# 任务卡：orb-w7-orchestrator-wiring

- **task_id**：orb-w7-orchestrator-wiring
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：orchestrator 接入派发链（编排入口 + 回执契约对齐）
- **创建**：2026-11-08 · 主脑过渡托底（DeepSeek 未接线，接线后交还外脑）
- **M1 声明**：已查能力注册表，`src/brain/orchestrator.py` 的 `run_stage`/`call_deepseek` 已存在并单测全绿；`requests`/`tenacity` 已实测可用；回执解析落在 `tasks/queue_engine/`，无需新依赖、无重复组件

## goal

新增 `scripts/orchestrate-order.py`，让 ②拆解 / ③工单 / ④排程 能从命令行一次跑完并落盘；同时把 `done.json` 的 `receipt_valid` 判据对齐 Codex 真实回执，使"待审计"落 `audit`、"BLOCKED"落 `blocked`。禁止：不改状态机 8 态、不改派发器 CLI、不打 tag、不真调 API 做验收。

## acceptance[]

- [ ] ACCEPT: `orchestrate-order.py --requirement <文本|文件> --run-dir <目录>` 顺序跑 decompose→work_order→schedule，产物落 `<run-dir>/stages/<stage>.json`
- [ ] ACCEPT: 任一 stage 失败立即停，退出码非 0，且落 `<stage>-failed.json`，后续 stage 不执行
- [ ] ACCEPT: `--dry-run` 不发真实请求、不改动任何 stage 文件、退出码 0
- [ ] ACCEPT: 缺 `DEEPSEEK_API_KEY` 时明确报错退出，不静默、不落伪产物
- [ ] ACCEPT: `done.json` 解析能把 `…133604629405Z/final.json`（待审计）判为 `audit`
- [ ] ACCEPT: `done.json` 解析能把 `…125637445858Z/final.json`（BLOCKED）判为 `blocked`
- [ ] ACCEPT: 未知/空回执仍落 `blocked`（fail-closed 不放宽）
- [ ] ACCEPT: 单测全 mock 全绿，断言无 `assertTrue(True)`，且不持久化 `DEEPSEEK_API_KEY`
- [ ] ACCEPT: `status` 字段为 list / dict 等非字符串时，`classify_receipt_path` 必须 fail-closed 返回 `blocked, valid=False`，**不得抛 `TypeError`**（实测 `status=[]` + 有效 evidence 会抛 `unhashable type: 'list'`）
- [ ] ACCEPT: `work_order` 匹配必须按完整工单号边界，不得子串串单（`wo-orb-w7` 不得匹配 `wo-orb-w7x`）

## dependsOn[]

- 无

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\scripts\orchestrate-order.py`
- `H:\UltimaAI\UltimaAgent\src\brain\orchestrator.py`
- `H:\UltimaAI\UltimaAgent\tasks\queue_engine\`
- `H:\UltimaAI\UltimaAgent\tests\test_orchestrate_order.py`
- `H:\UltimaAI\UltimaAgent\tests\test_receipt_contract.py`
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w7-orchestrator-wiring\`

## priority

- 95

## reasoningEffort

- high

## category + skill

- category: eng-orchestration · skill: eng.backend（编排入口与回执契约）

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
| U-01 编排入口 | CLI 参数解析 + 三 stage 顺序调度 | 三 stage 产物齐全 | 产物样例 |
| U-02 短路与 dry-run | 失败即停 + 无副作用 dry-run | 失败后无后续 stage；dry-run 零写入 | 测试输出 |
| U-03 回执判据 | 待审计/BLOCKED/未知三类判定 | 两份真实回执回归 | 测试输出 |
| U-04 fail-closed | 缺 key / 未知回执 | 报错退出、落 blocked | 测试输出 |
