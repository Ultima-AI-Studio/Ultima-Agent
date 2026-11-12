# 任务卡：orb-w3-state-visual

- **task_id**：orb-w3-state-visual
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：状态 → 视觉映射
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 状态视觉映射实现

## goal

五态颜色语义按方案 §4.3：idle 冷蓝 #8AA0FF 系、thinking 亮蓝 #5A7BFF→#7FA3FF、talking 峰值 #7FA3FF、processing 琥珀 #FFA94D、failed 红 #FF5A5A；状态驱动球体活跃度（RMS 能量 EMA，只调活跃度不驱动整圈半径）。禁止：整圈同步缩放动画。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 五态颜色语义正确
- [ ] ACCEPT: 活跃度参数只调球体表面，不整圈缩放
- [ ] ACCEPT: 截图可证五态视觉差异

## dependsOn[]

- orb-w3-state-easing（easing 就绪）
- orb-w3-ipc-backend（IPC 就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\state\`（视觉映射代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w3-state-visual\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（视觉映射调参）

## category + skill

- category: orb-state · skill: eng.render（渲染工程师）

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
| U-01 颜色 | 五态颜色映射 | 语义正确 | 五态截图 |
| U-02 活跃度 | RMS EMA 驱动活跃度 | 不整圈缩放 | 视频帧 |
| U-03 差异 | 五态视觉差异 | 可辨 | 五态截图 |
