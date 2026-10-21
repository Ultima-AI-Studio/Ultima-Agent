# 工单④：S1-Task-Text-Loop（任务文本闭环）

- **工单 ID**：wo-s1-task-text-loop · 2026-10-16 · 主脑立项
- **版本归属**：v0.3 任务场景闭环·文本（本工单覆盖 U12-U14）
- **依赖**：v0.1 冻结（队列引擎工单①可用）
- **L3 结果（要什么）**：任务文本闭环可用——L1 意图解析（查任务状态/默认不打断）→ L2 域映射 + L3 队列状态源（真实读取）→ L4 编排 + L5 聚合汇报（结论先行/异常优先/可下钻，不逐条念）；"查任务状态"文字场景端到端闭环。
- **L3 Gate**：工单④内部 DoD PASS + 场景实测（20 任务 1 失败→只报异常）→ 版本级触发 `v0.3-frozen`

## 0. 范围冻结

- 本工单只做：意图解析 / 状态源 / 聚合汇报 三层（文本闭环）
- 本工单不做：语音链路（独立工单③，Owner选择仅已有音频离线验证，真机门仍待完成）、组合窗口（v0.4）、征询闭环（v1.0 U18）、队列调整写操作（v1.0 U19）

## 1. 任务清单（T ↔ U 映射表）

| 任务 ID | 标题 | 对应验收单元 | 验收门 |
|---|---|---|---|
| T1 s1-task-intent-parse | L1 意图解析 | U12 | 意图识别 ≥90% |
| T2 s1-task-queue-source | L2 域映射 + L3 状态源 | U13 | 域清单列全+真实读取 |
| T3 s1-task-aggregate-report | L4 编排 + L5 聚合汇报 | U14 | 20 任务 1 失败→只报异常 |

**写入域（fileDomain）**

| 任务 | 精确写入域 |
|---|---|
| T1 s1-task-intent-parse | `H:\UltimaAI\UltimaAgent\src\brain\`；`H:\UltimaAI\UltimaAgent\logs\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-intent-parse\` |
| T2 s1-task-queue-source | `H:\UltimaAI\UltimaAgent\src\brain\`；`H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-queue-source\` |
| T3 s1-task-aggregate-report | `H:\UltimaAI\UltimaAgent\src\brain\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-aggregate-report\` |

**推理强度（reasoningEffort）**：工单级 `medium`；T1-T3 任务卡均为 `high`，执行时以任务卡为准。

**依赖图**：T1 → T2 → T3（串行）

## 2. 任务明细

每张任务卡见 `cards/<task_id>/task.md`（11 字段齐全）。

## 3. 总验收（工单 DoD = v0.3 版本冻结门）

- [x] 全部 3 任务 PASS（T1-T3）
- [x] T↔U 映射核对：U12-U14 全部覆盖
- [x] 场景实测：20 任务 1 失败→只报异常并总结 PASS
- [x] 关联文档同步（docs/README 登记工单④）
- [ ] 冻结基线标记：tag `v0.3-frozen`

## 4. 验收要点（打勾清单）

- [x] 前置：v0.1 冻结（队列引擎可用）
- [x] 每任务回执三件套（I1）
- [x] 提交前自核闭环（§8）
- [x] 失败回执结构化（I3）；证据不明确 fail-closed（B1）
- [x] 开发与审计技能分离

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-16 | 初版：工单④ 文本闭环 3 任务 + T↔U 映射 + 总验收 |

## 2026-10-21 W4内部收口

U12-U14及10个执行单元技术验收通过，证据见docs/reports/w4-text-loop-acceptance-20261021.md。版本标签项保持未勾选；Owner批准v0.3冻结前，工单⑤不得启动。
