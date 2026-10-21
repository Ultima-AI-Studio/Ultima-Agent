# 任务卡：s1-queue-engine-statemachine

- **task_id**：s1-queue-engine-statemachine
- **stage**：S1（阶段一 v0.1）
- **标题**：八态状态机（含非法迁移拦截）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；状态机为 queue-spec §4 的首个实现

## goal

实现八态状态机 QUEUED → EXECUTING → SELF-CHECK → AUDIT → COMPLETED / FAILED / BLOCKED / CANCELLED，含依赖方自动 BLOCKED 与非法迁移拦截。禁止：不实现派发调度（T3）、不实现存储持久化细节（T1 已完成，只调用其接口）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 状态迁移单测全绿（合法路径：QUEUED→EXECUTING→SELF-CHECK→AUDIT→COMPLETED）
- [x] ACCEPT: 失败路径 FAILED→（retryCount<2）→QUEUED（修正 ~rN）／（≥2）→BLOCKED 正确
- [x] ACCEPT: CANCELLED（用户取消 / 被覆盖）可达
- [x] ACCEPT: 依赖方 FAILED/BLOCKED → 被依赖方自动 BLOCKED（reason 记录"依赖 <task_id> 未完成"）
- [x] ACCEPT: 非法迁移拦截：EXECUTING 直跳 COMPLETED、AUDIT 未过跳 COMPLETED 均被拒并报错
- [x] ACCEPT: BLOCKED 解除仅允许人工/主脑裁决转 QUEUED 或 CANCELLED

## dependsOn[]

- s1-queue-engine-storage（T1 骨架落地后）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\tasks\`（状态机模块文件）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-statemachine\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（状态迁移 + 非法拦截为核心逻辑，需边界推演）

## category + skill

- category: queue-engine · skill: eng.code（智能工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 八态、合法/非法迁移、依赖冻结、重试上限与人工解除均经隔离测试；重试次数从追加事件恢复，未污染 11 字段索引。
- stdoutText: `Ran 8 tests in 0.068s` / `OK`
- evidence: `acceptance-evidence.md`；`H:\UltimaAI\UltimaAgent\docs\reports\evidence\stage1-queue-engine\T2-statemachine.md`
- acceptance 逐项核对: 6/6 通过（SM-01~SM-08 全覆盖）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| SM-01 八态定义 | QUEUED/EXECUTING/SELF-CHECK/AUDIT/COMPLETED/FAILED/BLOCKED/CANCELLED | 八态枚举齐全 | 枚举核对 |
| SM-02 主路径迁移 | QUEUED→EXECUTING→SELF-CHECK→AUDIT→COMPLETED | 单测全绿 | 单测输出 |
| SM-03 失败路径 | FAILED→(retryCount<2)→QUEUED（~rN） | 修正重试正确 | 单测输出 |
| SM-04 超限路径 | FAILED→(≥2)→BLOCKED | 超限转 BLOCKED | 单测输出 |
| SM-05 取消路径 | CANCELLED（用户取消/被覆盖） | 取消可达 | 单测输出 |
| SM-06 非法迁移拦截 | EXECUTING 直跳 COMPLETED 拒绝 | 非法迁移全拒并报错（含 EXECUTING→CANCELLED 覆盖） | 拦截用例 |
| SM-07 依赖自动 BLOCKED | 依赖方失败→被依赖方 BLOCKED | reason 记录"依赖 <id> 未完成" | 用例输出 |
| SM-08 BLOCKED 解除 | 仅人工/主脑裁决 | 无自动绕过上限 | 代码核对 |
