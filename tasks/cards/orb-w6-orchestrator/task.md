# 任务卡：orb-w6-orchestrator

- **task_id**：orb-w6-orchestrator
- **stage**：G-ORCH 编排层（v0.1）
- **标题**：DeepSeek 外脑调用封装（②③④ 三 stage 独立会话）
- **创建**：2026-11-08 · 主脑立项（用户批 A 方案）
- **M1 声明**：已查能力注册表，`requests` 2.34.2 与 `tenacity` 已在 venv-openjarvis 实测可用；`process_identity`/`DispatchLock` 复用 queue_engine，无重复组件、无新增依赖

## goal

新增 `src/brain/orchestrator.py`，把 DeepSeek 外脑接进派发链：②拆解 / ③工单 / ④排程 三个环节各自独立会话调用，产物规范落盘，失败 fail-closed。禁止：不改状态机、不碰派发器、不打 tag、不真调 API 做验收。

## acceptance[]

- [x] ACCEPT: `call_deepseek()` 读 `DEEPSEEK_API_KEY`，POST `https://api.deepseek.com/chat/completions`，model `deepseek-chat`，key 缺失抛 `OrchestratorError`
- [x] ACCEPT: `run_stage()` 落 `stages/<stage>.json`，字段含 `stage/model/system_digest/prompt/response/tokens{in,out}/elapsed_s/verdict/created_at` 九项
- [x] ACCEPT: 三 stage 的 `system_digest` 两两不同（证明未共享 system）
- [x] ACCEPT: 失败写 `stages/<stage>-failed.json` 并抛异常，不静默降级
- [x] ACCEPT: tenacity 仅对 429/5xx/超时重试 3 次，4xx（除 429）不重试
- [x] ACCEPT: 单测 4 用例（200 正常 / 429 退避后成功 / 非法 JSON / 空 content）全 mock 全绿，断言无 `assertTrue(True)`
- [x] ACCEPT: 不把 `DEEPSEEK_API_KEY` 写入任何落盘文件

## dependsOn[]

- 无

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\orchestrator.py`
- `H:\UltimaAI\UltimaAgent\tests\test_orchestrator.py`
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w6-orchestrator\`

## priority

- 95

## reasoningEffort

- high

## category + skill

- category: eng-orchestration · skill: eng.backend（外脑接线与产物契约）

## receipt

- reviewReason: T1 自检通过；仅供后续独立审计，不构成 G-ORCH 验收
- stdoutText: `8 passed in 0.09s`（固定解释器，`pytest -q -p no:cacheprovider -o addopts= tests/test_orchestrator.py`）
- evidence: `src/brain/orchestrator.py`；`tests/test_orchestrator.py`
- acceptance 逐项核对: 7/7 PASS；HTTP、九字段、独立 digest、fail-closed、重试边界、全 mock、密钥不落盘均由专项断言覆盖

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 HTTP 封装 | `call_deepseek` + tenacity 退避 | 四场景 mock 全绿 | 测试输出 |
| U-02 stage 落盘 | `run_stage` 九字段产物 | 字段齐全断言 | 产物样例 |
| U-03 会话独立 | 三 stage system 独立 | digest 两两不同 | 断言输出 |
| U-04 fail-closed | 失败路径与 `-failed.json` | 异常抛出且文件存在 | 测试输出 |
