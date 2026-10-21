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

## W4 打回同单修复（2026-10-21）

- 修复否定、已完成历史、转述/日志引用、功能讨论句型被子串规则误判的问题；不是三句白名单。
- 原 16 条正例仍为 16/16；独立脚本正例 19/20（95%）；新增同类负例与端到端不读库回归均通过。
- RED/GREEN 与独立脚本复跑证据：`logs/text-loop-w4-repair-20261021/`。
- 当前仍为开发方 `READY_FOR_REVIEW`，`independent_w4_completed=false`；未签独立 PASS。


## W4 独立技术验收收口（2026-10-21）

两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。

## Owner版本决定（2026-10-21）

用户对候选731710a明确回复“批准”。v0.3-frozen固定731710a80358b062d1064ccaf08f758483a9d958；凭据tasks/queue/gates/v0.3-frozen.json。前文待审批段落为历史记录。
