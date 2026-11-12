# 任务卡：s4-state-axis
- **task_id**：s4-state-axis
- **标题**：状态与记忆共享轴（M04）：四类全局状态统一供读
- **优先级**：65（P1）
- **reasoningEffort**：low
- **category**：core　**skill**：engineering
- **依赖**：s3-bond-system、s3-device-profile、s3-orchestrator、s3-behavior-layer
- **登记核验**：已查注册表与产品对齐报告（product-alignment-20261027.md 缺口 N3）；bond 已预留跨形态共享状态轴（src/brain/persona/bond.py）；队列视图（s3-orchestrator）、设备档案（s3-device-profile）、行为层三态（s3-behavior-layer）均为既有组件，本单为聚合供读，不另造体系。

## goal
建立状态与记忆共享轴（M04）：
1. StateAxis 聚合四类全局状态：会话（voice 三态）+ 身份关系（bond 状态轴）+ 设备档案（device-profile 摘要）+ 任务队列（orchestration 视图）；
2. 统一只读视图：每类状态含更新时间戳 + 聚合版本号；任何消费方不直接改底层；
3. 跨形态同步：悬浮球/组合窗口消费同一 StateAxis 快照（复用 display/behavior 状态机订阅）；
4. 事件推送：订阅者模式（复用总线事件流，bus 事件 → StateAxis 刷新 → 订阅者）。

**禁止**：
- 禁止绕过既有组件直接改底层状态；
- 禁止测试污染真实库（全部 tempfile 临时目录）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：四类状态聚合只读视图可用（会话/身份关系/设备档案/任务队列）
- [ ] ACCEPT-2：每类状态带更新时间戳 + 聚合版本号
- [ ] ACCEPT-3：跨形态消费同一快照（行为层状态机接入）
- [ ] ACCEPT-4：事件推送订阅生效（刷新→订阅者收到新快照）
- [ ] ACCEPT-5：回归不倒退（既有行为层/队列/设备/羁绊测试全绿）
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：状态与记忆共享轴（M04，P1） |
