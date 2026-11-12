# 任务卡：orb-w1-webview2

- **task_id**：orb-w1-webview2
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：WebView2 嵌入 + 空画布
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB WebView2 画布宿主实现

## goal

在球窗中嵌入 WebView2 控件并载入空画布（透明背景），作为渲染层宿主。禁止：不实现渲染内容（W2）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: WebView2 Runtime 初始化无异常
- [ ] ACCEPT: 空画布渲染成功
- [ ] ACCEPT: 透明背景（AllowTransparency + 无底色，无黑块）

## dependsOn[]

- orb-w1-ball-window（球窗就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\`（WebView2 代码）
- `H:\UltimaAI\UltimaAgent\src\orb\web\`（空画布 HTML）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w1-webview2\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（WebView2 透明背景配置）

## category + skill

- category: orb-shell · skill: eng.web（Web 工程师）

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
| U-01 初始化 | WebView2 Runtime 初始化 | 无异常 | 运行日志 |
| U-02 空画布 | 载入占位 HTML/Canvas | 渲染成功 | 渲染截图 |
| U-03 透明背景 | 透明背景配置 | 无黑块 | 截图 |
