# 任务卡：s1-queue-engine-audit-e2e

- **task_id**：s1-queue-engine-audit-e2e
- **stage**：S1（阶段一 v0.1）
- **标题**：审计闭环 + 空任务库端到端联测
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；审计闭环为 queue-spec §9 的首个实现

## goal

实现审计闭环（回执三件套 I1 校验 + 审计独立于开发 + 执行报告落 logs/execution-reports/<task_id>/summary.json + M4 三项核对）+ 空任务库端到端联测（立项→派发→自检→审计→收尾全链路走通）。禁止：不实现状态机/派发器内部（T2/T3 已完成）、不代改队列引擎核心、审计只核对不代修。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 任务完成必须回执（M5）：reviewReason / stdoutText / evidence / acceptance 逐项核对；无回执不判 COMPLETED
- [x] ACCEPT: 审计独立于开发（谁开发谁不能自审）；审计输出 PASS 或修正任务
- [x] ACCEPT: 执行报告落 logs/execution-reports/<task_id>/summary.json
- [x] ACCEPT: 审计轮核对三项（M4）：产物路径 vs fileDomain、新组件 vs 注册表、报告完整性
- [x] ACCEPT: 空任务库端到端联测：立项→派发→自检→审计→收尾 全链路走通 PASS

## dependsOn[]

- s1-queue-engine-storage（T1 骨架）
- s1-queue-engine-statemachine（T2 状态机）
- s1-queue-engine-dispatcher（T3 派发器）
- s1-queue-engine-priority-deps（T4 插队/依赖）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tasks\`（审计模块文件）
- `H:\UltimaAI\UltimaAgent\logs\execution-reports\`（执行报告落点）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-audit-e2e\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（审计核对 + 端到端联测，规则明确）

## category + skill

- category: queue-engine · skill: eng.audit（审计工程师，独立于开发技能）

## receipt（完成时由 CodeX 回填）

- reviewReason: 回执、角色分离、M4、业务结果、恢复和空库全链路均在隔离库验证；T5 机制自核通过但不替代监督端 W2。
- stdoutText: `Ran 36 tests in 3.095s` / `OK`；`AST_COMPILE_OK 12`
- evidence: `acceptance-evidence.md`；`H:\UltimaAI\UltimaAgent\docs\reports\evidence\stage1-queue-engine\T5-audit-e2e.md`；`H:\UltimaAI\UltimaAgent\logs\execution-reports\s1-queue-engine-audit-e2e\summary.json`
- acceptance 逐项核对: 5/5 通过（AU-01~AU-07 全覆盖；监督端 W2 待执行）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| AU-01 回执三件套 | reviewReason/stdoutText/evidence/acceptance 逐项 | 回执结构完整 | 回执样例 |
| AU-02 无回执不判完成 | 缺回执不判 COMPLETED | 校验拦截生效 | 拦截用例 |
| AU-03 审计独立 | 开发与审计技能分离 | 谁开发谁不自审 | 角色核对 |
| AU-04 执行报告 | 落 logs/execution-reports/<task_id>/summary.json | 报告存在 | 文件核对 |
| AU-05 M4 核对 | 产物路径 vs fileDomain / 新组件 vs 注册表 / 报告完整性 | 三项核对可执行 | 审计输出 |
| AU-06 端到端联测 | 空任务库立项→派发→自检→审计→收尾 | 空库走通 PASS | 运行输出 |
| AU-07 fail-closed | 证据不明确判 BLOCKED 留主脑 | 不猜测 PASS | 判定用例 |
