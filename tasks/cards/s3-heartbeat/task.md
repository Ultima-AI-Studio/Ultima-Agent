# 任务卡：s3-heartbeat
- **task_id**：s3-heartbeat
- **标题**：主动心跳（TICK 周期 + 空闲思考边界）
- **优先级**：55（P2）
- **reasoningEffort**：low
- **category**：core　**skill**：engineering
- **依赖**：s3-orchestrator
- **登记核验**：已查注册表，无常驻主动循环；依据 docs/research/agent-capability-notes-bailongma-20261026.md §②（TICK 主动循环与看门狗）、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（主动心跳与调度 M27）

## goal
主动心跳 M27（对齐白龙马 TICK 理念，边界克制）：
1. TICK 周期主循环（心跳可配置）；
2. 消息抢占（高优先级输入可打断后台思考）；
3. 空闲思考边界受控（有预算上限、不无限自转；不做无价值空转）；
4. 主动发言边界（不打扰：仅高价值事件主动开口）；
5. 定时任务触发（现有队列联动）。

**禁止**：
- 禁止无边界空闲自转（预算封顶）；
- 禁止打扰式主动发言；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：TICK 心跳按配置周期运行
- [ ] ACCEPT-2：消息抢占生效（高优先级打断后台思考）
- [ ] ACCEPT-3：空闲思考预算封顶验证（无无限自转）
- [ ] ACCEPT-4：主动发言仅高价值事件触发（边界用例验证）
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：主动心跳（P2） |
