# 任务卡：s1-queue-engine-storage

- **task_id**：s1-queue-engine-storage
- **stage**：S1（阶段一 v0.1）
- **标题**：队列存储骨架（tasks/ 五目录 + 防膨胀索引）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 queue-spec §2 落地的首个实现

## goal

tasks/ 下落地 cards / queue / events / runs / archive 五目录 + tasks.json 瘦身索引（只存索引字段，goal 全文外置）。禁止：不实现状态机（T2）、不实现派发逻辑（T3）、不把 goal 全文写进 tasks.json。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: tasks/ 下存在 cards / queue / events / runs / archive 五目录
- [x] ACCEPT: tasks.json 只含索引字段（task_id/state/priority/dependsOn/parallelGroup/fileDomain/reasoningEffort/created_at/updated_at/terminal_reason/card_path），无 goal 全文
- [x] ACCEPT: events/<task_id>.jsonl 追加式写入（禁止原地改写历史事件）
- [x] ACCEPT: runs/<task_id>/ 六件套命名 `<task_id>.<ts>.<uuid>.{before,out,err,done,session,progress}` 就绪
- [x] ACCEPT: archive/ 只归档不删除（M9 文件级保守）

## dependsOn[]

- （无，本任务为工单①首任务）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tasks\`（本任务允许写入域）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-storage\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（规则+轻判断：目录骨架 + 索引瘦身，非主体算法）

## category + skill

- category: queue-engine · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: T1 六项隔离单测及真实目录/空索引核对通过；首次导入失败已保留，修正测试入口后复验全绿。
- stdoutText: `Ran 6 tests in 0.179s` / `OK`
- evidence: `acceptance-evidence.md`；`H:\UltimaAI\UltimaAgent\docs\reports\evidence\stage1-queue-engine\T1-storage.md`
- acceptance 逐项核对: 5/5 通过（ST-01~ST-08 均有对应测试或代码核对）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| ST-01 目录骨架 | 创建 cards/queue/events/runs/archive 五目录 | 五目录存在且可写 | 目录树 |
| ST-02 tasks.json 索引落地 | 实现瘦身索引文件 | tasks.json 存在、仅索引字段 | 索引样例 |
| ST-03 索引字段定义 | 11 个索引字段齐全 | task_id/state/priority/dependsOn/parallelGroup/fileDomain/reasoningEffort/created_at/updated_at/terminal_reason/card_path | 字段核对 |
| ST-04 goal 外置 | goal 全文存 cards/<task_id>/task.md | tasks.json 无 goal 全文 | grep 核对 |
| ST-05 events 追加式 | 状态事件追加写入 | 追加式、禁原地改写 | 事件文件样例 |
| ST-06 runs 六件套 | before/out/err/done/session/progress | 六件套命名就绪 | 目录核对 |
| ST-07 archive 归档 | 只归档不删除 | archive/ 无自动删逻辑 | 代码核对 |
| ST-08 防膨胀阈值 | 索引 >1 万条自动归档索引项 | 阈值逻辑存在且可触发 | 阈值测试 |
