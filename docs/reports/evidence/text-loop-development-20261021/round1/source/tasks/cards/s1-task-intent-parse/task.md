# 任务卡：s1-task-intent-parse

- **task_id**：s1-task-intent-parse
- **stage**：S1（阶段一 v0.3）
- **标题**：L1 意图解析（查任务状态/默认不打断）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为任务场景闭环的意图解析层

## goal

实现 L1 意图解析：识别"查任务状态"类意图，默认不打断（非明确指令不插话）。禁止：不实现队列状态读取（T2）、不实现聚合汇报（T3）、不接语音（本层只收文字，语音在独立工单验收）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: "查任务状态"意图识别率 ≥90%（用例集测试）
- [x] ACCEPT: 默认不打断（无明确指令时不主动插话）
- [x] ACCEPT: 用例集测试输出落盘 logs/intent-parse-test-<date>.md

## dependsOn[]

- 无（文字输入独立实现；版本级前置 v0.1 冻结仍由工单 wo-s1-task-text-loop 登记并强制执行，不依赖语音工单）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\`（意图解析模块）
- `H:\UltimaAI\UltimaAgent\logs\`（测试输出）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-intent-parse\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（意图识别准确率达标）

## category + skill

- category: brain · skill: eng.code（智能工程师）+ eng.voice 协作（文字输入源）

## receipt（完成时由 CodeX 回填）

- reviewReason: READY_FOR_REVIEW（仅开发自检；独立 W4 未执行）
- stdoutText: 正例 16/16 命中（100%），负例 12/12 保持静默；3 项测试通过
- evidence: `logs/intent-parse-test-2026-10-21.md`
- acceptance 逐项核对: IN-01/IN-02/IN-03 开发自检通过；等待独立 W4

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| IN-01 意图识别 | "查任务状态"类意图识别 | 识别率 ≥90% | 用例测试 |
| IN-02 默认不打断 | 无明确指令不主动插话 | 行为正确 | 场景测试 |
| IN-03 用例集落盘 | 测试输出 logs/intent-parse-test-<date>.md | 报告存在 | 文件核对 |
