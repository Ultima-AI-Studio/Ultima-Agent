# 任务卡：orb-w3-ipc-backend

- **task_id**：orb-w3-ipc-backend
- **stage**：ORB v0.1（毒液悬浮球首期）
- **标题**：后台 Agent IPC 通道
- **创建**：2026-10-24 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 ORB 与后台 IPC 实现

## goal

实现悬浮球与后台 Agent 的 IPC 状态回传通道：后台推送状态（idle/thinking/talking/processing/failed）+ 可选消息（如任务完成摘要），球体实时响应 ≤1s。通道失败显示离线态不阻塞主程序。禁止：不实现 Computer Use、不实现交互（W4）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 后台 IPC 推送状态，球体 ≤1s 响应
- [ ] ACCEPT: 可选消息（任务完成摘要）传递
- [ ] ACCEPT: 通道失败显示离线态、不阻塞主程序

## dependsOn[]

- orb-w3-state-machine（状态机就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\orb\state\`（IPC 代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\orb-w3-ipc-backend\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（IPC + 看门狗）

## category + skill

- category: orb-state · skill: eng.ipc（IPC 工程师）

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
| U-01 推送 | IPC 状态推送 | ≤1s 响应 | 计时日志 |
| U-02 消息 | 完成摘要传递 | 可达球体 | 消息日志 |
| U-03 离线 | 通道失败离线态 | 不阻塞主程序 | 故障测试 |
