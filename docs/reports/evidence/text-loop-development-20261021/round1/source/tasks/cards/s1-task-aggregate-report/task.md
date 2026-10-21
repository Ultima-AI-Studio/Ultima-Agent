# 任务卡：s1-task-aggregate-report

- **task_id**：s1-task-aggregate-report
- **stage**：S1（阶段一 v0.3）
- **标题**：L4 编排 + L5 聚合汇报（结论先行/异常优先/可下钻）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为任务场景闭环的汇报层

## goal

实现 L4 编排（任务域按逻辑编排）+ L5 聚合汇报：结论先行、异常优先、可下钻，**不逐条念**（20 任务 1 失败 → 只报异常并总结，合格项聚合）。禁止：不逐条朗读所有状态、不实现窗口渲染（v0.4）、不实现征询闭环（v1.0 U18）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 20 任务 1 失败 → 只报异常并总结（场景实测输出）
- [x] ACCEPT: 结论先行（先说"有 1 异常"再说细节）
- [x] ACCEPT: 可下钻（异常项可展开看详情）

## dependsOn[]

- s1-task-queue-source（T2 状态源）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\`（编排/汇报模块）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-aggregate-report\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（编排 + 自然语言聚合，需总结逻辑）

## category + skill

- category: brain · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: READY_FOR_REVIEW（仅开发自检；独立 W4 未执行）
- stdoutText: 真实临时库 20/1 聚合、正常/失败下钻、未知/路径式 ID 拒绝、未命中不读取、CLI 正常退出；6 项测试通过
- evidence: `logs/aggregate-report-test-2026-10-21.md`
- acceptance 逐项核对: AR-01/AR-02/AR-03 开发自检通过；等待独立 W4

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| AR-01 编排 | 任务域按逻辑编排 | 编排合理 | 代码核对 |
| AR-02 聚合汇报 | 20 任务 1 失败→只报异常并总结 | 不逐条念 | 场景实测 |
| AR-03 可下钻 | 异常项可展开详情 | 下钻可用 | 场景测试 |
