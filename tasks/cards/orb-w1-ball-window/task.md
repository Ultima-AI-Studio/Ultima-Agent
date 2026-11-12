# 任务卡：orb-w1-ball-window

- **task_id**：orb-w1-ball-window
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：球窗 96×96 透明置顶非激活
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 球窗窗口属性实现

## goal

实现球窗 96×96px：无边框、透明背景、始终置顶、非激活不抢焦点（WS_EX_NOACTIVATE + WS_EX_TOOLWINDOW + SWP_NOACTIVATE）。禁止：不实现渲染（W2）、不实现拖动交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 球窗 96×96、无边框、透明、置顶
- [ ] ACCEPT: 非激活（WS_EX_NOACTIVATE + WS_EX_TOOLWINDOW）生效
- [ ] ACCEPT: 真机截图可证（多 DPI 下逻辑尺寸正确）

## dependsOn[]

- orb-w1-init（骨架就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\`（球窗窗口代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w1-ball-window\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（Win32 窗口属性 + 防闪屏）

## category + skill

- category: orb-shell · skill: eng.win（Win32 工程师）

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
| U-01 球窗属性 | 96×96 无边框透明置顶 | 属性正确 | 截图 |
| U-02 非激活 | WS_EX_NOACTIVATE+TOOLWINDOW+SWP_NOACTIVATE | 不抢焦点 | 焦点测试 |
| U-03 多 DPI | 高 DPI 逻辑尺寸正确 | 无偏移 | 真机测试 |
