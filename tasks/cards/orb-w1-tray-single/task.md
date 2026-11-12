# 任务卡：orb-w1-tray-single

- **task_id**：orb-w1-tray-single
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：托盘 + 单实例
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 托盘与单实例实现

## goal

实现托盘图标（找回悬浮球/设置/退出）与单实例（Named Mutex + NamedPipe 通知既有实例）。禁止：不实现渲染（W2）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 托盘图标显示，找回/设置/退出可用
- [ ] ACCEPT: Named Mutex 单实例生效
- [ ] ACCEPT: 二次启动经 NamedPipe 通知既有实例

## dependsOn[]

- orb-w1-webview2（画布就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\`（托盘/单实例代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w1-tray-single\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（托盘 + 单实例 IPC）

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
| U-01 托盘 | 托盘图标+菜单 | 找回/设置/退出可用 | 截图 |
| U-02 单实例 | Named Mutex | 二启提示既有实例 | 测试日志 |
| U-03 通知 | NamedPipe 通知既有实例 | 既有实例响应 | 测试日志 |
