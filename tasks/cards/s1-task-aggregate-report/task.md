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

## W4 打回同单修复（2026-10-21）

- 聚合与下钻实现未改；新增端到端回归确认否定、历史、转述和功能讨论不进入 reporter，且实际读库次数为 0。
- 20/1、正常/失败下钻、错误闭合与 CLI 全部继续通过；证据位于 `logs/text-loop-w4-repair-20261021/`。
- 当前仍为开发方 `READY_FOR_REVIEW`，`independent_w4_completed=false`；未签独立 PASS。


## W4 独立技术验收收口（2026-10-21）

两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。

## Owner版本决定（2026-10-21）

用户对候选731710a明确回复“批准”。v0.3-frozen固定731710a80358b062d1064ccaf08f758483a9d958；凭据tasks/queue/gates/v0.3-frozen.json。前文待审批段落为历史记录。
