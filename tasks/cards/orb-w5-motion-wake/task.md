# 任务卡：orb-w5-motion-wake

- **task_id**：orb-w5-motion-wake
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：唤醒回弹动效
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 唤醒回弹动效实现

## goal

唤醒回弹动效：回弹至中心并展开面板，回弹流畅、带毒液拉伸感。禁止：不实现语音（二期）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 唤醒回弹流畅
- [ ] ACCEPT: 带拉伸感（前导冲/收束）
- [ ] ACCEPT: 帧序列截图可证

## dependsOn[]

- orb-w5-motion-stretch（巡游就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\motion\`（回弹代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w5-motion-wake\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（回弹手感）

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
| U-01 回弹 | 唤醒回弹流畅 | 生效 | 帧序列 |
| U-02 拉伸 | 拉伸感 | 生效 | 帧序列 |
| U-03 截图 | 帧序列截图 | 可证 | 截图 |
