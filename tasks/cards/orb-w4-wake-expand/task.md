# 任务卡：orb-w4-wake-expand

- **task_id**：orb-w4-wake-expand
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：唤醒回弹 + 面板展开
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 唤醒展开实现

## goal

点击球体唤醒：回弹至屏幕默认位置并展开信息面板。禁止：不实现语音唤醒（二期）、不实现拉伸巡游（W5）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 点击唤醒、回弹至默认位置
- [ ] ACCEPT: 信息面板展开
- [ ] ACCEPT: 帧序列截图可证

## dependsOn[]

- orb-w4-panel-window（面板就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\interaction\`（唤醒代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w4-wake-expand\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（唤醒回弹动画）

## category + skill

- category: orb-interaction · skill: eng.anim（动效工程师）

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
| U-01 唤醒 | 点击唤醒回弹 | 生效 | 帧序列 |
| U-02 展开 | 面板展开 | 生效 | 截图 |
| U-03 截图 | 帧序列截图 | 可证 | 截图 |
