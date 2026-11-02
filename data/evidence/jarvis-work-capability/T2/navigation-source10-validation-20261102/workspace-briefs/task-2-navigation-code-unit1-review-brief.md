# Independent source10 unit1 task review

Read first. You review one pure-data implementation task for original T2, spec compliance then code quality. No subagents. Use superpowers:subagent-driven-development task-reviewer method. Read original requirements C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-brief.md, author report C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-report.md, and full diff C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-review-package.txt once. BASE244d2120abcd6b8d7744f74a05bd22de46a2d3a5 → HEADe0b04d6a68f7851d2dfc6c516bc7701896355b69. Package SHA39e391cef7c73cff5aaa431dc0143b84be96ac9ab4d536eb13ce1d3390eccfcb. Treat author report as claims. Your read-only C checkout is pinned at this HEAD; do not mutate files/index/refs or re-run git. Full diff includes two byte-exact approved docs, canonical copies are verified in root receipt. Binding design41998861 and corrected implementation plan a8419b77 are in diff; exact Task1 and global constraints in original brief. Architecture has its own completed review, this gate checks concrete implementation and test sufficiency.

## Global Constraints (verbatim)

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。


## Root execution/interface rulings

- Root code-only authority V/root-code-only-authority.json0ec6abcd permits this candidate, isolated SDK/scanner/unit tests and exact allowlist. All model/actual/harness-inert/T3/prod release false. H production remains0a31d84 and protected5 unchanged. Current8B forever, no other weights.
- build_page retains exact pure-data signature/safe-only catalogue. Unit1 adds scan_view(view,policy); actual final-wire scan occurs via trusted narrow read callable before staging/exposure in Task2, without inspector retaining policy/raw caps. Preparation placeholders prove availability only. Check actual helper correctness and downstream obligations, not report assurances.
- seal_snapshot is pure data for already-issued reads, not runtime issuance authority. Later ledger must enforce actual END/native-wire/guard/issuance and seal those records; pure replay must enforce its own stored source/page/card/hash chain. Runtime proof obligations remain future units. Report any concrete inability to satisfy these interfaces.
- v1 runner lacked source before/after pinning. Root NEW v2 runner60f6ea3d copies baseline21/allowlist/test raw bytes before and asserts hashes unchanged after. Last final341 suite source maps and commit blobs independently matched; V/code/root-unit1-before-review-readback.json records this. Earlier failures preserved and not upgraded to final-byte proof. No repeated test requested by this gate.
- Wrong draft spec basename was corrected to authority exact path before final run/commit. Known approved plan doc EOF/CRLF cosmetics preserve canonical bytes; product/test/spec targeted check clean. Judge real semantic/quality issues and severity independently.

## Named risks for focused checks

Exact canonical authority fields/IDs/collision/replay line domains; HTML suffix and scanner policy redaction/projection configuration; actual successful GET linkage; legal-page availability/final-fit/witness/card/citation completeness; pure-safe data vs raw/scanner authority; v2 historical rendering/verification preservation and strict fresh-v3 requirements. Inspect unchanged source only for a concrete named risk and report what/why. Real configured scanner support/replay should be consistent with checked product security, whose source excerpts are in report and src/brain/agent_server.py:305..332 if needed. No broad code crawl.

Do not re-run implementer tests (final341 and all TDD logs available). If a concrete doubt is unanswered, ask root for a focused safe test or report it; no runtime SDK/scanner/lexer/HTTPX imports, network/models/audio/UI/process experiments/installs in this read-only review. Stdlib static read/hash/AST allowed with fixed H python-B-Xutf8. Report cannot_verify items with precise later gate instead of assigning nonexistent runtime success.

## Outputs

V=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102. Create NEW V/review-unit1-1/review.md + verdict.json (SPEC and QUALITY each PASS/REVISE; input hashes, numbered Critical/Important/Minor concrete file:line findings, required resolution, cannot_verify and scope flags). Full report C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-review-report.md. Reply compact verdicts/findings/output hashes. Do not edit author artifacts/code or stage anything. Root owns fixes and next unit dispatch.
