# 任务卡：s12-health-repair
- **task_id**：s12-health-repair
- **标题**：系统体检自动修复闭环（M16 深化：先报告后执行）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：brain　**skill**：engineering
- **依赖**：s3-env-cognition（已验收，环境体检基线）、s3-guard-resident（已验收，审批门基线）
- **登记核验**：已查注册表，无重复；依据 docs/plans/roadmap.md Next「系统体检自动修复闭环（先报告后执行）」+ tasks/queue/stage2-batch-plan.md（S12 工单）

## goal
系统体检自动修复闭环（先报告后执行）：
1. **问题分级**：体检结果按 severity 分级（P0 阻塞 / P1 影响 / P2 建议），确定性规则（磁盘/内存/异常/基线变化）；
2. **修复提案生成**：对可修复项生成提案（改什么/影响面/回滚方式 三字段必填）；
3. **先报告后执行**：审批门 fail-closed——未批准不执行；高危动作（删除/系统级修改）自动拒，需用户显式批准；
4. **修复执行与回执**：仅执行已注册安全动作；执行后复检；回执落盘（含执行前/后对比）+ 审计留痕。

**禁止**：
- 禁止自动执行未注册/高危修复动作；
- 禁止修改冻结参数基线之外的既有组件行为；
- 禁止越权删除用户文件或改系统设置（仅注册表内安全动作）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [x] ACCEPT-1：问题分级 P0/P1/P2 确定性正确（磁盘/内存/异常/基线变化）
- [x] ACCEPT-2：修复提案三字段（改什么/影响面/回滚方式）必填
- [x] ACCEPT-3：审批门未批准不执行；高危自动拒；显式批准后放行
- [x] ACCEPT-4：修复执行仅注册动作；复检 + 回执落盘；审计链未被破坏
- [x] ACCEPT-5：venv-openjarvis 全量测试全绿（既有功能零回归）
- [x] ACCEPT-6：回执完整（含变更登记）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/health、src/brain/tests、tasks/cards/s12-health-repair）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：系统体检自动修复闭环（P1） |
