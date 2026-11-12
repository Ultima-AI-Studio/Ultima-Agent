# 任务卡：orb-w5-motion-config

- **task_id**：orb-w5-motion-config
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：节奏参数可配置
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 动效参数配置实现

## goal

动效节奏参数可配置：移动时长/停顿时长/目标点数/缩放比，配置持久化。禁止：硬编码节奏参数。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 移动/停顿/目标点/缩放可配置
- [ ] ACCEPT: 配置持久化（重载生效）
- [ ] ACCEPT: 配置测试通过

## dependsOn[]

- orb-w5-motion-wake（回弹就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\motion\`（配置代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w5-motion-config\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（配置持久化）

## category + skill

- category: orb-motion · skill: eng.config（配置工程师）

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
| U-01 配置 | 四项参数可配置 | 生效 | 配置测试 |
| U-02 持久化 | 配置持久化+重载 | 生效 | 重载测试 |
| U-03 测试 | 配置测试 | 通过 | 测试输出 |
