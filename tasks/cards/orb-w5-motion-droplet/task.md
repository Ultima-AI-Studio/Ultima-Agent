# 任务卡：orb-w5-motion-droplet

- **task_id**：orb-w5-motion-droplet
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：游离液滴
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 游离液滴实现

## goal

球体表面游离 1-2 个液滴，随表面流动。禁止：液滴脱离球体坠落（非本期）、不实现其他动效。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 1-2 个游离液滴在表面流动
- [ ] ACCEPT: 液滴与球体一体运动
- [ ] ACCEPT: 帧序列截图可证

## dependsOn[]

- orb-w5-motion-stretch（巡游就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\motion\`（液滴代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w5-motion-droplet\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（液滴物理）

## category + skill

- category: orb-motion · skill: eng.anim（动效工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 待回填
- stdoutText: 待回填
- evidence: 待回填
- acceptance 逐项核对: 待回填

## retryCount

- 0

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| U-01 液滴 | 1-2 液滴表面流动 | 生效 | 帧序列 |
| U-02 一体 | 与球体一体运动 | 生效 | 帧序列 |
| U-03 截图 | 帧序列截图 | 可证 | 截图 |
