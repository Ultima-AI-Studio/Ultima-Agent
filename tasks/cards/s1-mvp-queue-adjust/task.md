# 任务卡：s1-mvp-queue-adjust

- **task_id**：s1-mvp-queue-adjust
- **stage**：S1（阶段一 v1.0）
- **标题**：队列调整（插队/改优先级，操作留审计 event）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为队列引擎的 MVP 写操作层（工单①引擎已就绪）

## goal

实现队列调整：查看队列 / 调整优先级 / 插队（requeue --before），操作写 audit event 留痕，只作用于 QUEUED。禁止：不打断 EXECUTING、不自动解除 BLOCKED、未授权不执行（T3 凭证）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 队列调整生效（插队/改优先级用例）
- [x] ACCEPT: 审计留痕（events/<task_id>.jsonl 可查 {ts,from,to,reason,actor}）
- [x] ACCEPT: EXECUTING 任务不被打断（正在跑让它跑完）

## dependsOn[]

- s1-mvp-confirm-loop（T1 征询确认）
- s1-queue-engine-priority-deps（工单① T4 引擎能力）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\`（调整模块）
- `H:\UltimaAI\UltimaAgent\tasks\`（队列只读+events 写）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-queue-adjust\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（调用引擎接口 + 留痕）

## category + skill

- category: brain · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑直做验收（队列调整此前批次已落地，本卡补登记验收）；实现走冻结队列引擎官方入口（QueuePlanner.adjust_priority / requeue_before），写 audit event
- stdoutText: 队列调整 + 审计留痕 + EXECUTING 保护 PASS（test_queue_source.py 全绿）
- evidence: src/brain/tests/test_queue_source.py + interaction.py（requeue_before/adjust_priority）
- acceptance 逐项核对: 3/3 全绿（调整生效/审计留痕/EXECUTING 不打断）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| QA-01 查看队列 | 展示队列（字段口径同 queue-spec） | 展示正确 | 用例输出 |
| QA-02 调优先级 | 调整 priority 生效 | 生效 | 调整用例 |
| QA-03 插队 | requeue --before 生效 | 插队生效 | 插队用例 |
| QA-04 审计留痕 | 操作写 audit event | 留痕可查 | 事件日志 |
