# Scoped U1 nonce F1 re-review

Same original reviewer. Use SDD scoped re-review template. Original requirements W/task-2-navigation-code-unit1-brief.md; exact author correction requirements W/task-2-navigation-code-unit1-nonce-correction-brief.md; SAME author report W/task-2-navigation-code-unit1-report.md now appended, SHA5e510e84 (original51432c36 prefix byte-exact archived V/code/unit1-author-r1/report.md).

Previous sole finding verbatim: Minor — src/brain/work_navigation.py:357 uses uuid.uuid4().hex for nonce. Binding design Exact replay format requires16 random bytes encoded as32 lowercase hex. UUIDv4 fixes version/variant bits, providing122 random bits with fixed structure, rather than the exact128-random-bit contract. Required resolution: secrets.token_hex(16) or equivalent16-byte cryptographic randomness, generated once, with a deterministic focused test proving all supplied random bytes survive (including UUID version/variant positions). Avoid probabilistic uniqueness/entropy tests.

Fix BASE e0b04d6a68f7851d2dfc6c516bc7701896355b69 → HEAD494e544788c287defbf1208967444e733df5501a. Full fix package C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-nonce-review-package.txt SHA648865bf68d9ad64142f61586f75580aef25364cf538bbb8e948c7d341f6a790. Read it once, no git. Scope ONLY F1 ADDRESSED/NOT_ADDRESSED plus new breakage in this two-file fix. Out-of-scope observations go separately, not a new whole-unit review.

Root verified actual two changed paths, code/blob/raw test inputs, same report prefix, RED235(1expectedassertionfailure), GREEN235clean, unchanged input hashes and empty unexpected paths. V/code/root-unit1-nonce-before-rereview.json will bind inputs with explicit paths. Do not rerun tests; no runtime/product/SDK/scanner/lexer imports or network/models/process experiments/installs/subagents/mutations. Read-only stdlib checks under fixedH python-B-Xutf8 allowed. Native/randomness test evidence is already in report/logs; inspect meaningful behavior and exact source delta.

## Global Constraints (verbatim)

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。


Create NEW V/review-unit1-2/review.md and verdict.json (directory not precreated; ensure no overwrite), full W/task-2-navigation-code-unit1-rereview-report.md. Include input paths/hashes, F1 verdict, SPEC/QUALITY, new-fix issues/out-of-scope, no-runtime flags. Return compact. U2/U3/actual/harness/T3 gates and prior cannot_verify remain as before; E02/T2 NOT_PASSED. No code/model/source reallocation is implied.
