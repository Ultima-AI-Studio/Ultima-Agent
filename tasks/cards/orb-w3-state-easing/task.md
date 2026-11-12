# 任务卡：orb-w3-state-easing

- **task_id**：orb-w3-state-easing
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：状态过渡 easing
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 状态过渡动画实现

## goal

状态切换过渡全部 easing（非瞬切），参考 @breadai/ui-orb 的 idle/thinking 实现方式。禁止：状态瞬切、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 状态过渡全部 easing
- [ ] ACCEPT: 过渡流畅、无跳变
- [ ] ACCEPT: 帧序列截图可证

## dependsOn[]

- orb-w3-state-machine（状态机就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\state\`（easing 代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w3-state-easing\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（过渡动画）

## category + skill

- category: orb-state · skill: eng.anim（动效工程师）

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
| U-01 easing | 过渡 easing 实现 | 非瞬切 | 帧序列 |
| U-02 流畅 | 过渡流畅无跳变 | 通过 | 帧序列 |
| U-03 截图 | 帧序列截图 | 可证 | 截图 |
