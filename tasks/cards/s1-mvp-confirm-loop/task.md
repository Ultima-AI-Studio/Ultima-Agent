# 任务卡：s1-mvp-confirm-loop

- **task_id**：s1-mvp-confirm-loop
- **stage**：S1（阶段一 v1.0）
- **标题**：L7 征询闭环（"你觉得怎么样"→调整→重呈现）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 MVP 的征询交互闭环

## goal

实现 L7 征询闭环：交付后征询（"你觉得怎么样？"）→ 用户调整请求 → 重呈现；调整类请求走确认不静默执行。禁止：不实现凭证授权（T3）、不实现队列调整写操作（T2，本层只接需求）、越界操作。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 征询链路 PASS（交付→征询→调整→重呈现 场景实测）
- [x] ACCEPT: 调整请求确认后才执行（不静默改）
- [x] ACCEPT: 越界请求不执行（返回需授权提示）

## dependsOn[]

- （无任务级前置；版本级前置 v0.2+v0.4 冻结登记于工单总卡 wo-s1-mvp-freeze.md，F3 修正）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\`（征询模块）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-confirm-loop\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（交互闭环 + 边界判定）

## category + skill

- category: brain · skill: eng.code + eng.ui 协作（窗口重呈现）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑直做验收（L7 交互循环此前批次已落地，本卡补登记验收）；实现 src/brain/interaction.py 征询状态机（pending_confirm→confirmed）
- stdoutText: 征询链路场景实测 PASS（test_interaction.py + test_interaction_orb.py 全绿）
- evidence: src/brain/tests/test_interaction.py、test_interaction_orb.py + 真机联调报告（任务状态闭环端到端验证）
- acceptance 逐项核对: 3/3 全绿（征询链路/确认门/越界拒绝）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| CL-01 征询触发 | 交付后征询"你觉得怎么样？" | 触发正确 | 场景实测 |
| CL-02 调整重呈现 | 调整请求→重呈现 | 重呈现生效 | 场景实测 |
| CL-03 确认门 | 调整请求确认后才执行 | 不静默改 | 场景实测 |
| CL-04 越界拒绝 | 越界请求返回需授权提示 | 拒绝正确 | 场景实测 |
