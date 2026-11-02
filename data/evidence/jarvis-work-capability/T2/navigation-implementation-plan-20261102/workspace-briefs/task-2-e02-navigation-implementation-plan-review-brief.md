# Independent implementation-plan review, first gate

Read this first. Review only the implementability, interface consistency, task order and meaningful validation of the approved source-navigation v3 architecture. No implementation/model/test execution is released by this task. You are a fresh independent reviewer; do not dispatch subagents.

Original author requirements: C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-e02-navigation-implementation-plan-brief.md
Author SAME appended report: C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-e02-navigation-implementation-plan-report.md
Full-new-file diff package (read once, LF-aware; latest plan+analysis+report): C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-e02-navigation-implementation-plan-review-package.txt
Package SHA256 0ad2fc392ac13aed770a9f5a779e311844c9d658d6702087d5a8f36d9df9fea8.
Latest plan is revision-2/plan.md SHA a06831697d9e50e7135abde4e020f53326cb1a0e0cc88477b330b7365ef5b880 in I=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-implementation-plan-20261102. All package input hashes are in I/review-inputs-manifest.json; verify raw hashes.

Binding spec: H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-research-source-navigation-design-20261102.md SHA41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef (D/revision-3/design.md). Design independently passed; this gate judges its execution argument, with concrete contradictions or missing interfaces reported. Root reviewed concerns in I/controller-before-review-ruling.md and existing isolation in I/controller-existing-isolation-ruling.md. No code task has begun.

## Global Constraints (verbatim plan)

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。


## Review method and scope

Use the SDD task-reviewer template for SPEC and QUALITY verdicts, adapted to a planning-only diff; author claims are not evidence. Read package once instead of separately rereading changed files. Source-only targeted checks are allowed for named interface risks: actual SDK tool builder/executor/event signatures; import/data/lock dependencies across named product files; trusted output basename versus original acceptance case; existing regression/negative identities and command readiness; P4 launch/cleanup authority. Name what you checked and why. Do not crawl unrelated code or repeat prior architecture audit. No SDK/scanner/lexer/HTTPX/product runtime import, tests, models, network, process experiments, git mutation or dependency install. Ordinary read/hash/stdlib static checks use H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8.

Check that all three units can be implemented and meaningfully tested in order with concrete defined interfaces, whole-SDK tests really use actual SDK registry/worker/guard/file I/O, and the independent oracle does not share model-derived answers. Check preserving all prior negative purposes, v2 historical-only readback, no fresh v2 authority fallback; exact limits/version/context/transport proof remain binding. Four tasks include a separately gated adapter from already-proven P4, not a new native controller or automatic actual-run allocation. Explicitly preserve historical CIM/native precision gap and exact cleanup authority.

C=the existing linked worktree C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent HEAD244d2120abcd6b8d7744f74a05bd22de46a2d3a5. Root corrected the initial suggested new worktree before this review, no branch changed. Future branch codex/jarvis-work-navigation-v3-source10 only after root code-only ruling. H production HEAD0a31d84169ba8e151ec2f9a2c6fea958804daa5b. Shared frozen docs/source9 snapshots remain immutable, future allowed product paths may change only under separate source10 manifest. Plan/report is not an E02/T2 pass. Source10/model/actual/T3 budgets remain unallocated.

## Outputs

Create NEW I/review-1/review.md and verdict.json (SPEC PASS/REVISE, QUALITY PASS/REVISE, exact input hashes, numbered Critical/Important/Minor findings with package file+line references, concrete resolution, cannot_verify items, scope/no-runtime flags). Write full report to C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-e02-navigation-implementation-plan-review-report.md. Keep reply compact: verdicts, findings, output hashes. Do not edit original plan/report/package/code or old evidence. A concern about future runtime proof is distinct from a missing implementable interface; label the actual gap and next gate accurately.
