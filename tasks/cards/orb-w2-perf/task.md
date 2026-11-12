# 任务卡：orb-w2-perf

- **task_id**：orb-w2-perf
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：帧率节流 + 性能
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 渲染性能验证

## goal

渲染性能达标：待机 CPU ≤5%、内存增量 ≤150MB、渲染帧率 ≥50fps；离开视口暂停渲染（帧率节流）。禁止：不实现状态机（W3）、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 待机 CPU ≤5%
- [ ] ACCEPT: 渲染帧率 ≥50fps
- [ ] ACCEPT: 离开视口暂停渲染生效

## dependsOn[]

- orb-w2-transparent（透明合成就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\web\`（性能代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w2-perf\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（性能分析与节流）

## category + skill

- category: orb-render · skill: eng.perf（性能工程师）

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
| U-01 CPU | 待机 CPU 占用 | ≤5% | 采样日志 |
| U-02 帧率 | 渲染帧率 | ≥50fps | 帧率采样 |
| U-03 节流 | 离开视口暂停渲染 | 生效 | 采样日志 |
