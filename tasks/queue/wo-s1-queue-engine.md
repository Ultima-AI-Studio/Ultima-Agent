# 工单①：S1-Queue-Engine（任务队列引擎）

- **工单 ID**：wo-s1-queue-engine · 2026-10-16 · 主脑立项
- **版本归属**：v0.1 环境基线（本工单覆盖 U06-U09 四个单元；U01-U05 宿主壳属工单②）
- **L3 结果（要什么）**：任务队列引擎可用——空任务库端到端（立项→派发→自检→审计→收尾）走通，一次一主串行派发、八态状态机、优先级/依赖/审计闭环；成为后续所有工单的承载底座。
- **L3 Gate**：工单①内部 DoD PASS（5 任务全过 + 总验收）——注意：**不是 v0.1-frozen**，版本冻结归版本级（工单② U01-U05 完成后才触发 v0.1 冻结门）

## 0. 范围冻结

- 本工单只做：队列引擎五任务（存储骨架/状态机/派发器/插队依赖/审计联测）
- 本工单不做：宿主壳（U01-U05，工单②）、语音链路（U10-U11，v0.2）、窗口渲染（U15-U17，v0.4）、Top 代码复用（legacy-topo M7 只读，只借鉴经验）

## 1. 任务清单（T ↔ U 映射表）

| 任务 ID | 标题 | 对应验收单元 | 验收门 |
|---|---|---|---|
| T1 s1-queue-engine-storage | 存储骨架（五目录+防膨胀索引） | U06 | 结构符合 queue-spec §2 |
| T2 s1-queue-engine-statemachine | 八态状态机（非法迁移拦截） | U07 | 状态迁移单测全绿 |
| T3 s1-queue-engine-dispatcher | 派发器（串行闸门+并行组+幂等+无窗口） | U08 | 派发纪律实现 |
| T4 s1-queue-engine-priority-deps | 优先级插队+依赖环检测（audit 留痕） | U08b | 插队生效/环拒绝/留痕可查 |
| T5 s1-queue-engine-audit-e2e | 审计闭环+空任务库端到端联测 | U09 | 空库走通 PASS + 无回执不判完成 |

**写入域（fileDomain）**

| 任务 | 精确写入域 |
|---|---|
| T1 s1-queue-engine-storage | `H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-storage\` |
| T2 s1-queue-engine-statemachine | `H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-statemachine\` |
| T3 s1-queue-engine-dispatcher | `H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-dispatcher\` |
| T4 s1-queue-engine-priority-deps | `H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-priority-deps\` |
| T5 s1-queue-engine-audit-e2e | `H:\UltimaAI\UltimaAgent\tasks\`；`H:\UltimaAI\UltimaAgent\logs\execution-reports\`；`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-audit-e2e\` |

**推理强度（reasoningEffort）**：工单级 `high`；逐任务以任务卡为准：T1 `medium`，T2 `high`，T3 `high`，T4 `medium`，T5 `medium`。

**依赖图**（T5 依赖 T1-T4；T3/T4 依赖 T2；T2 依赖 T1）：

```
T1 storage ──→ T2 statemachine ──┬──→ T3 dispatcher ──┐
                                 ├──→ T4 priority-deps ─┤──→ T5 audit-e2e（联测收口）
                                 └──────────────────────┘
```

## 2. 任务明细

每张任务卡见 `cards/<task_id>/task.md`（11 字段齐全：task_id/goal/acceptance[]/dependsOn[]/fileDomain[]/priority/reasoningEffort/category+skill/receipt/retryCount/M1 声明）。

## 3. 总验收（工单 DoD，非版本冻结）

- [ ] 全部 5 任务 PASS（T1-T5）
- [ ] T↔U 映射核对：U06/U07/U08/U08b/U09 全部覆盖（T5 并入 U09）
- [ ] 空任务库端到端联测 PASS（立项→派发→自检→审计→收尾）
- [ ] 关联文档同步（docs/README 权威清单登记工单①）
- [ ] 冻结基线标记：工单① 内部 tag `wo-s1-queue-engine-done`（**版本 tag v0.1-frozen 待工单②完成后由版本级触发**）

## 4. 验收要点（打勾清单）

- [ ] 前置：环境门（U01）由工单②并行执行；本工单开工不等待 U01，但 L3 Gate 判定时要求 U01 已全绿
- [ ] 每任务回执三件套（I1：完成语+落地文件清单+验收证据）
- [ ] 提交前自核闭环（§8）：未全绿先自修 ≤2 次再交回执
- [ ] 失败回执结构化（I3）；证据不明确 fail-closed 判 BLOCKED（B1）
- [ ] 开发与审计技能分离（T1-T4 eng.code / T5 eng.audit）

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.2 | 2026-10-20 | AUDIT-S1-FIX：L3 结果状态机口径统一为八态，与状态机任务卡及队列 SM-01 一致 |
| v1.1 | 2026-10-20 | AUDIT-S1-FIX：工单①/②依赖口径统一；开工互不阻塞，L3 Gate 收口时要求 U01 全绿 |
| v1.0 | 2026-10-16 | 初版：工单① 队列引擎 5 任务 + T↔U 映射 + 依赖图 + 总验收（修复清单审计后重拆） |
