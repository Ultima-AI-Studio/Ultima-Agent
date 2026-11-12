# 任务卡：orb-w5-motion-stretch

- **task_id**：orb-w5-motion-stretch
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：拉伸巡游动效
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 拉伸巡游动效实现

## goal

拉伸式巡游：uniforms uLead/uTail/uDir/uStretch，前导先冲、后尾拖胶丝、8字哑铃、到达收束；毛刺顺运动方向；节奏移动 1.5s / 停顿 2.4s / 4 目标点。禁止：整圈同步缩放、同相位粒子动画。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 拉伸巡游（前导先冲/后尾拖胶丝/8字哑铃/到达收束）
- [ ] ACCEPT: 毛刺顺运动方向
- [ ] ACCEPT: 帧序列截图可证

## dependsOn[]

- orb-w4-wake-expand（唤醒就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\motion\`（巡游代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w5-motion-stretch\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（毒液运动规律）

## category + skill

- category: orb-motion · skill: eng.anim（动效工程师）

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
| U-01 巡游 | 拉伸巡游四阶段 | 生效 | 帧序列 |
| U-02 毛刺 | 毛刺顺运动方向 | 生效 | 帧序列 |
| U-03 节奏 | 1.5s/2.4s/4目标点 | 可配置 | 配置测试 |
