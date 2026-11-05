# E03 Fixture-only Diagnostic Implementation Plan

> **For agentic workers:** Use superpowers:executing-plans inline. Preserve all historical evidence and the pinned product worktrees. No new reviewer or live run is dispatched by this plan.

**Goal:** Collect the missing message-origin/nesting evidence around the original fixture initialization and frozen-baseline read, so the current-candidate E03 acceptance sequence can resume on evidence.

**Architecture:** Reuse the reviewed fixture adapter/input-origin recorder, controller ownership/cleanup and original observer CLI. Add one narrow orchestrator which can launch only the fixture and baseline observer, requires a new manifest-bound independent review and single-use authority, and never reaches product server/CLI/model execution.

**Tech stack:** Existing Windows Python environment, standard library, existing Win32 fixture and pytest offline tests. No new dependencies.

**Spec:** `docs/reports/jarvis-work-t2-e03-input-origin-review-20261105.md`; `data/evidence/jarvis-work-capability/T2/e03-fixture-input-origin-20261105-fix1/fix-note.md`; original E01–E08 work-capability contract.

## Constraints and decisions

- Original work order `wo-ultimaagent-20261101-0021`; candidate `7975e477665c02820fa235b73d203718bd33b2c9`; only current `qwen3-8b-uncensored` with digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`. This diagnostic makes zero model calls.
- R31 is consumed and cannot be retried. The new scope is `fixture-only-diagnostic`, case `fixture-origin-01`, cap 1, retry false, acceptance credit false. Preparation creates no authority or actual directory.
- New code stays in the isolated evidence folder `data/evidence/jarvis-work-capability/T2/e03-fixture-only-diagnostic-20261105-r1`. The existing candidate worktrees and production source stay unchanged. This location follows the established work-order evidence layout.
- Agent implementation choice: use the existing native adapter, observer and owned-process cleanup. Re-running the whole E03 path would add model/product scope without helping this pre-product failure; replacing the fixture/foreground sequence would change the phenomenon. Both alternatives are excluded.
- Preserve text, selection, foreground activation, IME settings and the original baseline observer command. Do not reset text, inject keys, add global hooks or record message payloads.
- The observer's existing full fixture readback is local evidence only. `actual/` is Git-ignored. Published summaries contain hashes, UTF-16 lengths, identity/selection and metadata, not entered text.
- Before any window, verify package bytes, reviewer binding, new authority, candidate sources and all seven protected identities/command hashes/parents. An identity mismatch stops; no automatic reenrollment or restart.
- Consume the new slot by exclusive case-directory creation and durable admission record before fixture launch. Duplicate calls fail before UI. Preserve failed attempts and run cleanup in every admitted path.
- Readiness timeout 20 seconds and observer timeout 15 seconds reuse the existing functions. A 30-second watchdog writes only the owned fixture's stop marker. The diagnostic succeeds only within 60 seconds including cleanup; cleanup still proceeds after a deadline to avoid leaving owned windows. This is not a hard process-kill deadline or a change to the original product's 60-second gate.
- Only fixture and observer subprocesses are allowed. Ownership comes from the reviewed controller's retained process identity logic; protected processes are never terminated. Capture final audit completeness and protected identities after cleanup.
- Output separates `diagnostic_status` (COMPLETE/INCOMPLETE), `phenomenon` (TEXT_CHANGED/UNCHANGED/UNKNOWN) and `product_acceptance=NOT_EVALUATED`. No outcome gives E03/T2 acceptance credit or permits an automatic rerun.
- Existing user authorization covers continued offline preparation. The previous single reviewer authorization covered the input-origin patch and its one finding closure. This new enclosing runtime package needs a newly scoped independent review and an explicit single diagnostic allocation before use.

## Review focus

1. No window or owned process can start with missing, expired, mismatched, reused or overbroad authority/review.
2. The native bridge can reach only fixture initialization, original baseline observation and cleanup; imported full-controller product branches remain unreachable.
3. Missing initial readback, lost sidecar, observer failure or altered protected identity yields INCOMPLETE with retained evidence, never UNCHANGED or product PASS.
4. The stop watchdog and cleanup operate solely on this exclusive folder/owned process tree; timeout does not skip cleanup or claim a strict wall-clock kill guarantee.
5. Raw readback stays local and historical receipts are immutable; current-candidate counters remain 0 positive / 0 negative until real acceptance.

## Task 1: Single-use diagnostic orchestrator and native bridge

**Files:** Create `code/fixture_diagnostic.py`, `code/native_bridge.py`, `code/test_fixture_diagnostic.py`, `code/test_native_bridge.py`, `.gitignore`, and `manifest.json` within the evidence folder. Copy the exact reviewed `controller.py`, `fixture_adapter.py`, `fixture_input_origin.py` and the two existing offline test files from fix1; copy the pinned R31 `source_candidate_guard.py` and `preparation-support/acceptance_adapter.py`. Record every copied hash.

**Interfaces:** Pure `validate_authority(authority, manifest_hash, review, now)` rejects anything beyond the fixed case/scope/candidate/cap and a short validity interval. `run_once(package_root, authority_path, backend)` verifies release, claims once and calls only `backend.preflight`, `start`, `capture`, `close`, `postflight`, `audit`; the native backend implements those using the reviewed controller and existing fixture. Tests inject a fake backend and clock, never Win32 or model calls.

- [x] Write failing tests for release denial, consumption/duplicate prevention, exact operation order, timeout/failure cleanup, classification and metadata-only summary.
- [x] Implement the minimum orchestrator and bridge. Keep native imports behind the release gate and byte verification.
- [x] Run the new offline suite and the retained 42 audit tests once all fixes are in; inspect exact results. No live fixture/model execution. Final: 87 passed, including 45 wrapper/bridge cases.
- [ ] Seal the copied dependencies, implementation, tests/logs and review request; record syntax/hash checks and source/candidate immutability.
- [ ] Publish a concrete review/run proposal, state update, project report and mirror, then commit/tag. New review and one live diagnostic require explicit scope approval; no authority is included in preparation.

## Continuation to the actual product goal

Use the resulting live trace to identify or narrow the cause before changing fixture behavior. A non-reproduction is not a fix. Once the blocker is resolved, start current-candidate E03 round1 and meet all three consecutive positive rounds plus the original negative, then same-candidate E01 and E02; T3–T5 remain closed until T2 exits. Do not substitute this diagnostic, its tests or review for the requested E01–E08 delivery.
