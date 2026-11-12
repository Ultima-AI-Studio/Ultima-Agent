# 任务卡：orb-w2-transparent

- **task_id**：orb-w2-transparent
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：透明背景合成
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 透明背景合成实现

## goal

球体渲染透明背景合成：窗口透明、球体悬浮于桌面之上、无黑块。禁止：不实现状态机（W3）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 桌面透出（球体外区域透明）
- [ ] ACCEPT: 无黑块、无白边
- [ ] ACCEPT: 深色/浅色桌面均可见

## dependsOn[]

- orb-w2-material（材质就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\web\`（透明合成代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w2-transparent\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（透明合成 + WebView2 配置）

## category + skill

- category: orb-render · skill: eng.webgl（WebGL 工程师）

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
| U-01 透出 | 球体外透明 | 桌面透出 | 截图 |
| U-02 无黑块 | 透明配置正确 | 无黑块白边 | 截图 |
| U-03 双桌面 | 深浅色桌面验证 | 均可见 | 双截图 |
