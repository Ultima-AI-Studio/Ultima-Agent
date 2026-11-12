# 任务卡：s7-memory-temperature
- **task_id**：s7-memory-temperature
- **标题**：记忆热度分层（热/温/冷分级 + 中期层 + 打断单元入记忆层）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：memory　**skill**：engineering
- **依赖**：s3-memory-base（已验收）、s3-bus-kernel（已验收）
- **登记核验**：已查注册表，无重复；依据 docs/plans/memory-temperature-tiering-20261027.md（用户 10-27 拍板补设计）+ ADR-008 冻结基线（本单为增量，不推翻）

## goal
记忆热度分层补设计落地（对齐 memory-temperature-tiering-20261027.md）：
1. **热度三档**：MemoryEntry.meta 增 temperature（hot/warm/cold）/access_count/last_access；写入与召回自动打标；
2. **升降级四动作**：promote_hot / demote_warm / archive_cold / thaw_cold，各动作状态迁移正确，归档留痕可回溯；
3. **三级检索路由**：热（内存索引）→ 温（磁盘 jsonl + 向量）→ 冷（gz 归档解冻），命中即停，降级不丢；
4. **中期层**：declarative 温档条目 = 中期活跃记忆语义（不新增存储文件）；
5. **打断单元入记忆层**：kind=pending_interrupt（working 层，默认热档），被打断轮次写入原指令/执行状态/打断点，下轮合并上下文可续；
6. **会话结束钩子**：brain_loop 调 demote_warm；未闭环打断单元转温档。

**禁止**：
- 禁止推翻 ADR-008 冻结基线（五层性质分层与遗忘边界不动）；
- 禁止引入第三方记忆库/云端同步/模型微调；
- 禁止向 fileDomain 之外写文件；
- 禁止删改既有归档与审计记录。

## acceptance[]
- [x] ACCEPT-1：三档热度可标记（写入/召回后 temperature 字段正确）
- [x] ACCEPT-2：升降级四动作单测通过，状态迁移正确
- [x] ACCEPT-3：三级检索路由按序命中即停；冷归档条目可解冻召回
- [x] ACCEPT-4：中期层成立（declarative 温档，无独立存储文件）
- [x] ACCEPT-5：打断单元写入与下轮合并上下文闭环
- [x] ACCEPT-6：venv-openjarvis 全量测试全绿（既有功能零回归）
- [x] ACCEPT-7：回执完整（含变更登记）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/brain/memory、src/brain/loop、data/memory）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：记忆热度分层（P1） |
