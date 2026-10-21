# 任务卡：s1-queue-engine-dispatcher

- **task_id**：s1-queue-engine-dispatcher
- **stage**：S1（阶段一 v0.1）
- **标题**：派发器（串行闸门 + 并行组 + 幂等 + 无窗口）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；派发器为 queue-spec §5 的首个实现

## goal

实现派发器：串行闸门（默认一次一主，B2）+ 并行组上限（全队列 EXECUTING ≤ 2）+ 幂等防重派（M9-C2 三重判定）+ 全程无窗口（ops-selfcheck §3）+ 暂停开关（.pause-dispatch）。禁止：不实现优先级插队（T4）、不实现审计回执判定（T5）、不实现状态机内部（T2 已完成，只调用其接口）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 默认一次只派一个；派发前检查串行闸门
- [x] ACCEPT: parallelGroup 组内允许并行，但全队列同时 EXECUTING ≤ 2；超限任务留 QUEUED 并记录等待原因
- [x] ACCEPT: 幂等防重派三重判定（①派发进程在跑 ②执行会话在跑 ③有活跃 run → 本轮不派）；探测失败默认按"忙"处理，宁可不派也不重派
- [x] ACCEPT: 前台零弹窗——所有派发/看门狗/探活子进程启动点强制 CREATE_NO_WINDOW / pythonw / Hidden 包装；运行期窗口枚举全程计数 0（任何窗口闪一下都不行，ops-selfcheck §3）
- [x] ACCEPT: 存在 .pause-dispatch 标记时只读审计、不派发

## dependsOn[]

- s1-queue-engine-storage（T1 骨架）
- s1-queue-engine-statemachine（T2 状态机）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tasks\`（派发器模块文件）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-dispatcher\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（派发纪律多约束组合，需边界推演）

## category + skill

- category: queue-engine · skill: eng.code（智能工程师）+ eng.infra 协作（无窗口子进程）

## receipt（完成时由 CodeX 回填）

- reviewReason: 串行/并行 WIP、真实锁竞争、三重幂等、重复派发、暂停、父失联及真实隐藏子进程均在隔离库验证。
- stdoutText: `Ran 8 tests in 2.025s` / `OK`
- evidence: `acceptance-evidence.md`；`H:\UltimaAI\UltimaAgent\docs\reports\evidence\stage1-queue-engine\T3-dispatcher.md`
- acceptance 逐项核对: 5/5 通过（DI-01~DI-06 全覆盖）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| DI-01 串行闸门 | 默认一次一主，派发前检查闸门 | EXECUTING>1 时拒绝新派发 | 派发日志 |
| DI-02 并行组上限 | parallelGroup 组内并行，全队列 EXECUTING≤2 | 超限留 QUEUED+记录等待原因 | 并行用例 |
| DI-03 幂等防重派 | 三重判定（派发进程/执行会话/活跃 run） | 探测失败按忙处理，宁可不派不重派 | 幂等用例 |
| DI-04 零弹窗 | 所有子进程启动点 CREATE_NO_WINDOW/pythonw/Hidden + 运行期窗口枚举全程计数 0 | 前台零弹窗（闪一下都不行） | 窗口枚举输出 |
| DI-05 暂停开关 | .pause-dispatch 标记时只读审计不派发 | 暂停生效 | 暂停用例 |
| DI-06 守护器生命周期 | 守护器=主脑子进程，父死降级只读静默+优雅退出 | 无主自治禁止 | 生命周期用例 |
