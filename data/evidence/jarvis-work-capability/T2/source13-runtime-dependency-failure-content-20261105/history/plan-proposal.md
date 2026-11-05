# E03 runtime dependency and truthful failure implementation plan

> **For agentic workers:** Use `superpowers:executing-plans` inline, with test-driven development and the original independent review gate. This is a concrete proposal, not a new source or live-case release.

**Goal:** Fix the two product defects observed in the single R3 E03 run: the missing local execution dependency and a completion claim surviving a failed tool.

**Architecture:** Keep OpenJarvis and the existing `WorkReplaceTool → LocalExecChannel → approved context provider` path. Include the existing `environment_upgrade.py` in a fresh candidate/runtime package with exact provenance. Replace unverified model completion prose with a server-owned failure message when `WorkService` catches a failure; keep status, error, trace, effect tracking and no-replay behavior.

**Tech stack:** Existing Python environment and OpenJarvis SDK. No added dependency or new agent loop.

**Spec:** `H:/UltimaAI/UltimaAgent/docs/specs/jarvis-work-capability-contract-20261101.md`, R03/R05/R07 and E03/E06; original work order `wo-ultimaagent-20261101-0021`.

## Authority and current result

The latest explicit grant `request_user_input_async/call_e5ec88e4cdf4454ab35c587eb3b71261/0` allocated one E03 and one result review, both now consumed. R3 is FAIL with zero acceptance credit. Product source implementation is currently not released in `T2/current-run.json`; original bounded repair history is retained. This plan proposes the next bounded source revision, cumulative source13, without issuing it or resetting prior counts. It grants no new actual case, UI/model call, retry or Owner release.

The exact proposed production delta is `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-source12-input-guidance-20261105-r3/verification/source13-proposed-change.diff`. It is not applied. Static diagnosis and independent actual-result review are adjacent; the diagnosis itself is Root's static analysis, not another independent review.

## Global constraints

- Only `qwen3-8b-uncensored`, digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`; no model change or download.
- Preserve both pinned source12 worktrees, all historical failures and sealed case evidence. Use a new isolated `codex/` worktree for implementation after release.
- No production process, voice/KWS, microphone, recording, playback, user file, network research or shared model call in offline verification.
- Keep primary/secondary window identity, exact selection, before-send revalidation, file readback, audit, cleanup and factual gates. Original proof freshness60s, admission120s and CLI/SDK/controller300/1800/315s remain.
- No exception swallowing, fabricated successful tool response, automatic tool replay or assertion of unchanged effects after an uncertain write.
- Remote push remains blocked by prior automatic approval. No alternate route to retry it. Earlier rejected standalone import probe is not retried.

## Task 1: Restore the missing existing dependency in the next package

**Files:** Copy exactly `H:/UltimaAI/UltimaAgent/src/brain/environment_upgrade.py` into the new candidate at `src/brain/environment_upgrade.py`; SHA-256 `a4cb891bb217aac90ba6ca51e5fdfa57bb8ce0d5698d6b6958b1aecbca682c1b`. Update only the new candidate source/package manifest and provenance. Add `src/brain/tests/test_work_runtime_dependencies.py` in the new candidate.

**Interfaces:** `scan_processes(top_n: int = 15) -> list[ProcessInfo]` remains existing code. The runtime already has `.environment` and all five names imported by this module. Do not overwrite the runtime's pinned `environment.py` with the differing main-project version.

- [ ] Write a package regression which walks the declared local imports for the approved selection-write path using AST and checks that their files exist and are in the new manifest. The current package must fail specifically on `src/brain/environment_upgrade.py`; do not count a test-setup exception as RED.
- [ ] Record that RED, then include the exact existing file and hash it into the new candidate manifest. Retain the source12 manifest unchanged.
- [ ] Require GREEN for the missing-dependency regression, altered/missing manifest-entry negative cases, and the existing fake-native `test_work_context.py` selection-write tests. Native calls, process scans and model requests must be test doubles or fail if unexpectedly reached. This is a fresh offline regression of the repaired package, not a retry of the rejected standalone probe; any policy rejection stops that action.

## Task 2: Make a failed task's visible content truthful

**Files:** New candidate `src/brain/work_service.py` and `src/brain/tests/test_work_delivery.py`; retain existing context tests.

**Interface:** `WorkService.submit_work(...)` keeps the same result schema. In the exception path, after effects/status/error are computed, set `content` to `本次任务未完成。` when there are no recorded effects, otherwise `本次任务未完成，部分操作可能已生效，请核对结果。`. Preserve verified artifacts, failure details and tool records. No extra inference or replay.

- [ ] Add RED tests using a runner that returns the actual misleading completion text with a failed tool record; assert `status == 'failed'`, truthful `content`, one runner invocation and no artifact.
- [ ] Add RED coverage for a potentially committed failed mutation; assert `status == 'needs_attention'`, the partial-effect message, retained tool/error evidence, and no replay. Also cover failure before runner return and successful delivery retaining its successful content.
- [ ] Apply only the exception-path content assignment, then require GREEN. Do not hard-code fixture facts or inspect model wording to decide truth.
- [ ] Run `test_work_runtime_dependencies.py`, `test_work_delivery.py`, `test_work_context.py` plus the existing offline work navigation/research regressions relevant to `WorkService`. Use the pinned Python, `-B`, `PYTHONDONTWRITEBYTECODE=1`, `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`, `-p no:cacheprovider`, and a new evidence-only basetemp. Preserve any existing failures separately; never present a failing suite as all green.

## Task 3: Review and prepare the next gate

- [ ] Record candidate/source hashes, RED/GREEN logs, exact changed-file list, model policy and protected-process readback. Source change means a new candidate; no historical E03 pass is transferable.
- [ ] One independent code/package review verifies both fixes and test coverage. Do not let this review substitute for later generated-content review.
- [ ] Only after the offline fix and review pass, prepare a new explicit single-case E03 proposal. No new live run is included in this source-fix proposal. E03 remains0/3 and negative0 until fresh actual evidence passes; then same-candidate E01, current8B E02, T3—T5 and Owner follow the original order.

## Review focus

1. A complete hash inventory can still omit required files: require the actual selection path's local dependency closure, not just matching listed hashes.
2. The existing main `environment_upgrade.py` is untracked and absent from source12: provenance must be explicit, and the differing pinned `.environment` must be preserved.
3. Failure after a possibly committed mutation must say incomplete/uncertain, retain effects and never replay.
4. Failure before a response exists must produce truthful content without depending on a model response variable.
5. Successful delivery must remain compatible; generic failure wording must not hide error or verified partial artifacts.

Self-review: this is limited to two observed E03 defects under R03/R05/R07, not T4's full recovery implementation. No code, offline tests or new authority has been issued by writing this plan. General import completeness, model reliability and real E03 delivery remain unproven.
