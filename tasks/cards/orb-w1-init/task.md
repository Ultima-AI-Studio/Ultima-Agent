# 任务卡：orb-w1-init

- **task_id**：orb-w1-init
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：WPF 解决方案骨架
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为毒液悬浮球 ORB 首单骨架

## goal

创建 Ultima Agent 毒液悬浮球 WPF 解决方案骨架：分层结构（壳/渲染/状态/交互分目录），项目可构建零错误零警告。禁止：不实现渲染（W2）、不实现状态机（W3）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: WPF 解决方案创建成功，分层结构符合方案 §4.1
- [ ] ACCEPT: 项目引用无缺漏
- [ ] ACCEPT: dotnet build 零错误零警告

## dependsOn[]

- 无（ORB 串行链首单）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\`（球体代码根目录）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w1-init\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（骨架结构决定后续三单可扩展性）

## category + skill

- category: orb-shell · skill: eng.ui（UI 工程师）

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
| U-01 骨架 | WPF 解决方案分层结构 | 结构符合方案 §4.1 | 目录树 |
| U-02 引用 | 项目依赖引用正确 | 引用无缺漏 | 构建输出 |
| U-03 构建 | dotnet build 全绿 | 零错误零警告 | 构建输出 |
