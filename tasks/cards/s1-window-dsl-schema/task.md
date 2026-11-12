# 任务卡：s1-window-dsl-schema

- **task_id**：s1-window-dsl-schema
- **stage**：S1（阶段一 v0.4）
- **标题**：组件树 DSL + schema 校验（ADR-007 / component-dsl-schema）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为组合窗口的 DSL 底座（ADR-007 落地）

## goal

实现组件树 DSL 与 schema 校验：定义可组合组件树语法 + 校验规则（结构合法、无死页面）。禁止：不实现渲染（T2）、不实现主题（T3）、不改 UI 范式（ui-kit-standard 冻结）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: DSL 语法定义落盘（component-dsl-schema；A2UI v0.8 扁平邻接表）
- [x] ACCEPT: 校验通过（合法树通过、非法树拒绝：缺必填/死页面）
- [x] ACCEPT: 无死页面（所有组件从最终 root 可达；真实 DFS 拒绝环/悬空/孤立）

## dependsOn[]

- （无任务级前置；版本级前置 v0.3 冻结登记于工单总卡 wo-s1-composite-window.md，F3 修正）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\window\`（DSL 模块）
- `H:\UltimaAI\UltimaAgent\docs\specs\`（schema 文档）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-dsl-schema\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（DSL 设计 + 校验规则）

## category + skill

- category: window · skill: eng.ui（UI 工程师）+ eng.code 协作

## receipt（完成时由 CodeX 回填）

- reviewReason: READY_FOR_REVIEW；已按最新独立审查修复 Video 资源白名单遗漏，等待新独立 T1 审查，不代表 T2/T3/W5 或 v0.4 完成
- stdoutText: Video final/final=False RED 后最小修复；35 tests OK；最新审查探针 91/91 与 Video 定向探针 10/10 开发重放符合预期；冻结基线核对 PASS
- evidence: `evidence/20261024T081918+0800/`（RED、35 项原测试、91 项旧探针回归、10 项 Video 探针、冻结清单、来源 pin、旧失败与范围读回）
- acceptance 逐项核对: DS-01~04 开发自检均 PASS；这是开发回执，独立 T1 审查仍待执行

## retryCount

- 历史 I1/I2/I3 修复 2/2；本次 Video 续行独立计数 1/2

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| DS-01 DSL 语法定义 | 组件树 DSL 语法落盘 | 语法文档存在 | 文档核对 |
| DS-02 schema 定义 | component-dsl-schema 校验规则 | schema 完整 | 文档核对 |
| DS-03 合法树校验 | 合法组件树通过 | 校验通过 | 校验用例 |
| DS-04 非法树/死页面 | 非法树拒绝、无死页面 | 校验拒绝 | 校验用例 |
