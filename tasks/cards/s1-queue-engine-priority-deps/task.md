# 任务卡：s1-queue-engine-priority-deps

- **卡编号**：U08b（原并入 U08，AUDIT-S1-FIX 拆分）

- **task_id**：s1-queue-engine-priority-deps
- **stage**：S1（阶段一 v0.1）
- **标题**：优先级插队 + 依赖环检测（audit event 留痕）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；插队/依赖为 queue-spec §6/§7 的首个实现

## goal

实现 priority 插队/调整（只作用于 QUEUED，不打断 EXECUTING）+ dependsOn DAG 环检测（DFS，有环拒绝入队并报出环路径）+ 所有插队/调优先级操作写 audit event 留痕。禁止：不实现派发调度主循环（T3）、不打断正在执行的任务、不自动解除 BLOCKED。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 插队/调整只作用于 QUEUED 任务；EXECUTING 任务不被打断（正在跑的让它跑完）
- [x] ACCEPT: `requeue --before <task_id>` 插到指定任务前生效；同优先级按 created_at FIFO
- [x] ACCEPT: 入队时对 dependsOn 跑 DAG 环检测（DFS），有环 → 拒绝入队并报出环路径
- [x] ACCEPT: 派发条件：依赖全部 COMPLETED 才派发；依赖方 FAILED/BLOCKED → 被依赖方自动 BLOCKED（reason 记录），不空等
- [x] ACCEPT: 插队/调优先级必须写 audit event（events/<task_id>.jsonl：{ts, from, to, reason, actor}），审计可追溯

## dependsOn[]

- s1-queue-engine-statemachine（T2 状态机，依赖/插队作用于状态机 QUEUED）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tasks\`（插队/依赖模块文件）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-priority-deps\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（DFS 环检测 + 插队规则，规则明确）

## category + skill

- category: queue-engine · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 优先级/FIFO、持久化插队、执行中保护、三节点环拒绝、依赖派发 Gate 与审计事件均经隔离测试。
- stdoutText: `Ran 7 tests in 0.227s` / `OK`
- evidence: `acceptance-evidence.md`；`H:\UltimaAI\UltimaAgent\docs\reports\evidence\stage1-queue-engine\T4-priority-deps.md`
- acceptance 逐项核对: 5/5 通过（PD-01~PD-06 全覆盖）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| PD-01 priority 语义 | 0-100 默认 50，越大越先派 | 语义正确 | 字段核对 |
| PD-02 插队命令 | requeue --before <task_id> | 插到指定任务前生效 | 插队用例 |
| PD-03 FIFO 排序 | 同优先级按 created_at | FIFO 正确 | 排序用例 |
| PD-04 环检测 | 入队时 dependsOn DFS 环检测 | 有环拒绝入队+报环路径 | 环检测用例（A→B→C→A） |
| PD-05 派发条件 | 依赖全 COMPLETED 才派发 | 未满足不派发 | 派发日志 |
| PD-06 audit event | 插队/调优先级写 events（ts,from,to,reason,actor） | 留痕可查 | 事件日志 |
