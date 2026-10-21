# 任务卡：s1-task-queue-source

- **task_id**：s1-task-queue-source
- **stage**：S1（阶段一 v0.3）
- **标题**：L2 任务域映射 + L3 队列状态源（真实状态读取）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为队列引擎状态的真实读取层（数据口径=queue-spec §10）

## goal

实现 L2 任务域映射（任务域清单）+ L3 队列状态源（从队列引擎读真实状态：总数/八态/异常）。禁止：不实现聚合汇报（T3）、不实现意图解析（T1 已完成）、不复用 Top 队列代码（legacy-topo M7 只读，队列引擎为本项目自研工单①）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 域清单列全（八态：QUEUED/EXECUTING/SELF-CHECK/AUDIT/COMPLETED/FAILED/BLOCKED/CANCELLED + 异常项）
- [x] ACCEPT: 状态从队列引擎真实读取（非硬编码），字段口径同 queue-spec §10
- [x] ACCEPT: legacy-topo M7 只读引用合规（仅参考，不拷贝代码）

## dependsOn[]

- s1-task-intent-parse（T1 意图解析；版本级前置 v0.1 冻结登记于工单总卡，F3 修正）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\brain\`（状态源模块）
- `H:\UltimaAI\UltimaAgent\tasks\`（队列引擎只读）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-queue-source\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（状态源读取 + 域映射，需对齐 queue-spec §10）

## category + skill

- category: brain · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: READY_FOR_REVIEW（仅开发自检；独立 W4 未执行）
- stdoutText: 八态各 1 项统计通过；当前/历史分离、空库和三类读取失败闭合通过；4 项测试通过
- evidence: `logs/queue-source-test-2026-10-21.md`
- acceptance 逐项核对: QS-01/QS-02/QS-03/QS-04 开发自检通过；等待独立 W4

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| QS-01 域清单 | 任务域清单列全（八态+异常） | 清单无缺漏 | 清单核对 |
| QS-02 真实状态读取 | 从队列引擎读真实状态 | 非硬编码 | 读取核对 |
| QS-03 字段口径对齐 | 字段同 queue-spec §10 | 无漂移 | 对照核对 |
| QS-04 M7 合规 | legacy-topo 只读引用 | 仅参考不拷贝 | 代码核对 |

## W4 打回同单修复（2026-10-21）

- 在新增 brain 层以只读 `QueueStorage` 适配器覆写布局初始化，仍调用冻结引擎真实 `load_tasks()` 读取和验证索引；未修改冻结源。
- 仅有 `tasks.json` 的空库和损坏库读取前后目录树、文件内容哈希完全相同；缺失、损坏、非法内容仍明确失败且不伪装空库。
- RED/GREEN 与独立脚本复跑证据：`logs/text-loop-w4-repair-20261021/`。
- 当前仍为开发方 `READY_FOR_REVIEW`，`independent_w4_completed=false`；未签独立 PASS。


## W4 独立技术验收收口（2026-10-21）

两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。

## Owner版本决定（2026-10-21）

用户对候选731710a明确回复“批准”。v0.3-frozen固定731710a80358b062d1064ccaf08f758483a9d958；凭据tasks/queue/gates/v0.3-frozen.json。前文待审批段落为历史记录。
