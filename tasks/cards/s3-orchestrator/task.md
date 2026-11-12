# 任务卡：s3-orchestrator
- **task_id**：s3-orchestrator
- **标题**：队列编排与子代理调度（接总线 + 权限受控）
- **优先级**：75（P1）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：s3-bus-kernel、s3-guard-resident
- **登记核验**：已查注册表，任务队列引擎已建（codex-task-queue-spec）、子代理派发工具已存在，本单为接入总线与受控；依据 docs/specs/codex-task-queue-spec.md、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（域④ 任务执行与编排）

## goal
编排 M10 + 子代理调度 M11：
1. 任务队列接入总线与主脑回路（立项→排队→派发→执行→自检→审计→回执闭环）；
2. 子代理权限继承受控（执行器不互相持有对方权限；子任务动作同样过闸门与审计）；
3. 失败重规划与征询闭环；
4. 队列视图与宿主端一致（跨形态队列视图一致预留）；
5. 7 环范式检查串接（L10 前置，随 M26 驻留联动）。

**禁止**：
- 禁止子代理提权（超出主任务权限）；
- 禁止绕过闸门派发执行；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：任务闭环链路端到端通过（立项→回执）
- [ ] ACCEPT-2：子代理权限继承受限，越权被拒
- [ ] ACCEPT-3：失败重规划触发并留痕
- [ ] ACCEPT-4：队列视图宿主端一致
- [ ] ACCEPT-5：7 环范式前置检查生效
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：队列编排与子代理调度（P1） |
