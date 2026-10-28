# 任务卡：s11-learning-loop
- **task_id**：s11-learning-loop
- **标题**：学习闭环（M21 深化：轨迹→评测→改进，不做模型微调前期）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：brain　**skill**：engineering
- **依赖**：s3-audit-trail（已验收）、s4-brain-loop（已验收）、s7-memory-temperature（已验收）
- **登记核验**：已查注册表，无重复；依据 docs/plans/jarvis-reverse-architecture-20261026.md §4.3.1 阶段二第 5 项（M21 学习闭环）+ tasks/queue/stage2-batch-plan.md（S11 工单）

## goal
学习闭环三段落地（不做模型微调前期）：
1. **轨迹采集标准化**：从追加式审计日志（AppendOnlyAuditLog）提取执行轨迹（意图/工具/耗时/成败），按 flow 分组，输出可评测 TraceRecord；
2. **评测器**：对批次轨迹评分（成功率/平均耗时/P90/兜底命中/各意图聚合），输出 EvalReport 与基准线（首次建立基线，后续与基线比较产生信号）；
3. **改进闭环**：根据评测结果调整可配置范式参数（工具优先级前移、重试上限上调且封顶），失败/兜底轨迹沉淀为回归用例，全程留痕（append-only 调整日志）；
4. **确定性**：同输入同结果，无随机；审计日志只读不破坏（verify 仍 ok）。

**禁止**：
- 禁止模型微调/引入第三方学习库；
- 禁止修改冻结参数基线之外的既有组件行为；
- 禁止破坏审计日志 hash 链（只读）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [x] ACCEPT-1：轨迹采集按 flow 分组、状态判定（approved/rejected/replanned/partial）正确
- [x] ACCEPT-2：评测指标可复算；首次评测建立基准线，后续产生 steady/improved/degraded 信号
- [x] ACCEPT-3：改进器调整工具优先级/重试上限（封顶）且留痕可回读
- [x] ACCEPT-4：失败/兜底轨迹沉淀回归用例（落盘 case-*.json）且审计链未被破坏
- [x] ACCEPT-5：venv-openjarvis 全量测试全绿（既有功能零回归）
- [x] ACCEPT-6：回执完整（含变更登记）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/learn、src/brain/tests、tasks/cards/s11-learning-loop）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：学习闭环（P1） |
