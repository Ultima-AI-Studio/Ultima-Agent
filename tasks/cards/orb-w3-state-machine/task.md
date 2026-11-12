# 任务卡：orb-w3-state-machine

- **task_id**：orb-w3-state-machine
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：五态状态机
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 状态机实现

## goal

实现五态状态机：idle/thinking/talking/processing/failed，状态迁移正确、非法跃迁被拒绝。禁止：不实现交互（W4）、不实现语音（二期）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 五态齐全（idle/thinking/talking/processing/failed）
- [ ] ACCEPT: 状态迁移正确、非法跃迁被拒绝
- [ ] ACCEPT: 状态机测试覆盖全迁移路径

## dependsOn[]

- orb-w2-perf（渲染层就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\state\`（状态机代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w3-state-machine\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（状态机正确性）

## category + skill

- category: orb-state · skill: eng.state（状态机工程师）

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
| U-01 五态 | 五态定义 | 状态齐全 | 代码核对 |
| U-02 迁移 | 迁移表 + 非法拒绝 | 迁移正确 | 状态测试 |
| U-03 覆盖 | 全迁移路径测试 | 测试通过 | 测试输出 |
