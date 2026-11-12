# 任务卡：orb-w4-panel-window

- **task_id**：orb-w4-panel-window
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：信息面板窗
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 信息面板窗实现

## goal

独立信息面板窗：毛玻璃（Acrylic/DWM）、可拖动、可置顶；内容：状态/会话摘要/设置入口。禁止：不实现语音（二期）、不实现后台 Agent 功能（范围外）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 面板独立窗口、毛玻璃
- [ ] ACCEPT: 可拖动、可置顶
- [ ] ACCEPT: 状态/会话摘要/设置入口显示

## dependsOn[]

- orb-w4-edge-dock（贴边就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\interaction\`（面板代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w4-panel-window\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（毛玻璃 + 置顶）

## category + skill

- category: orb-interaction · skill: eng.ui（UI 工程师）

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
| U-01 毛玻璃 | Acrylic/DWM 毛玻璃 | 生效 | 截图 |
| U-02 窗口 | 可拖可置顶 | 生效 | 测试 |
| U-03 内容 | 状态/摘要/设置入口 | 显示 | 截图 |
