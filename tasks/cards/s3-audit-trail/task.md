# 任务卡：s3-audit-trail
- **task_id**：s3-audit-trail
- **标题**：审计留痕与独立复核框架
- **优先级**：80（P0）
- **reasoningEffort**：medium
- **category**：audit　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，凭证审计追加日志已有；依据 docs/specs/plugin-bus-spec.md §10、docs/specs/sequencing.md §3

## goal
审计 M21 基础留痕 + 独立复核框架：
1. 追加式轨迹全量留痕：运行日志按会话/时间/来源/事件类型可检索；日志只追加不可改写；
2. 回执证据闭环：每交付回执携带 reviewReason/stdoutText/evidence/acceptance；
3. 独立 Reviewer 复核框架：独立于开发执行器（eng.audit/eng.security 角色），分级结论 blocker/major/minor，高危项清零方可进入交付门；
4. 事件审计：违规直连、未声明调用、热插拔操作全部记审计项。

**禁止**：
- 禁止日志可改写；禁止开发执行器自证清白；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：追加式日志可检索（会话/时间/来源/事件类型），改写被拒
- [ ] ACCEPT-2：回执四字段完整可核对
- [ ] ACCEPT-3：独立复核角色分离（eng.audit/eng.security），分级结论可验证
- [ ] ACCEPT-4：违规项（直连/未声明调用/热插拔）全部记审计
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data / logs）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：审计留痕与独立复核（P0） |
