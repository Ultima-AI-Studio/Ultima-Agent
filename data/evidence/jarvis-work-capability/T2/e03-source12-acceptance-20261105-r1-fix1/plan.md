# Current-candidate E03 round1 acceptance entry implementation plan

> **For agentic workers:** Use superpowers:executing-plans in this session. Preserve every prior package and failure; no new product candidate or live allocation is implied by this preparation.

**Goal:** Prepare an auditable entry for the first genuine E03 acceptance case on candidate `7975e477665c02820fa235b73d203718bd33b2c9`, continuing the original E01–E08 delivery goal.

**Architecture:** Reuse the sealed controller's Case/Owned, original fixture activation and observer, mechanical artifact/window checks, effect reconciliation and exact-owned cleanup. A small standalone admission module binds the new package, independent review, one round1 authority and fresh native proof; a backend drives the existing fixture/server/CLI sequence. Do not reuse the legacy controller.execute/validate_authority, which are fixed to a consumed round2 recovery diagnostic.

**Tech Stack:** Existing pinned Windows Python, standard library, Win32 helpers, candidate's original acceptance harness and current local community 8B. No installation, vendor change or product source modification.

**Spec:** `docs/specs/jarvis-work-capability-contract-20261101.md`, the original work order and T2 stage, and the unchanged current candidate/source manifest. The fixture-only result report supplies new evidence, not acceptance credit.

## Boundaries and exact interfaces

Package root: `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-source12-acceptance-20261105-r1-fix1`.

Frozen dependencies come from `e03-fixture-only-diagnostic-20261105-r1-fix1`: controller, input-origin fixture/validator, candidate guard, support adapter, seven-process baseline, and retained audit tests. Seven dependencies are copied byte for byte. The controller differs only in guarding its stop-marker write so cleanup continues with a recorded failure. `package_io.py` contains only the exact previously reviewed IO helper definitions extracted from fixture_diagnostic.py, with provenance hashes.

New files: `code/acceptance_entry.py`, `code/acceptance_backend.py`, their two test files, and `code/package_io.py`. Preparation records live here; product source and both candidate worktrees remain unchanged.

- `verify_package(root) -> manifest_sha256`: exact root/scope/candidate/interpreter, canonical no-reparse paths, sealed dependency bytes, no unsealed runtime modules.
- `validate_release(root, now, active=False) -> admission`: root-issued authority, matching independent PASS, pinned model/digest and candidate, exact `e03-round1`, cap 1, no retry, no inherited predecessors, short admission lifetime at most 120 seconds, and a referenced native proof no older than 60 seconds. The original 60-second gate is proof freshness, not product completion time.
- `write_preflight(root, backend_factory=None) -> proof receipt`: matching package review required; read-only source/protected/model checks, a unique immutable preflight receipt, no actual directory or inference.
- `run_once(root, backend_factory=None) -> terminal`: reject a consumed actual slot before native import, compare fresh inspection with the pinned proof, claim once and fsync admission before UI. Always collect effects, cleanup, audit and boundary evidence after claim. No automatic second run.
- Backend methods `inspect`, `start`, `product`, `effects`, `close`, `audit`: reuse existing implementation helpers. `product(revalidate, admit_cli)` runs all non-UI checks before final focus/selection activation and original dispatch observation, then starts exactly one real work CLI. No model warmup or alternate model.
- Keep original CLI timeout 300, SDK timeout 1800, controller wait 315, max_turns 10 and work_max_tokens 2048. Do not change product defaults or introduce a 60-second product timeout from the fixture-only diagnostic.
- Formal terminal records candidate, manifest, actual result hashes, mechanical result, effect consistency, cleanup and boundaries. Facts remain `PENDING_ROOT_INDEPENDENT_REVIEW`; mechanical success alone grants no acceptance credit or round2 release.
- A later result review must bind this exact terminal/product/window/file evidence and verify the three original facts with no added facts. Current-case failure stops the allocation. Remaining E03 rounds, original negative, same-candidate E01 and E02 are still required.

## Task 1: Implement and verify the bounded acceptance entry

**Files:** New code/test modules above; copied sealed dependencies; manifest, provenance, plan, review request and verification logs in the package. Project plan/report/state and UltimaDocs mirror record the actual prepared status.

**Consumes:** Existing `controller.Case`, `fixture_command`, `validate_fixture_readback`, `validate_fixture_audit`, `mechanical`, `read_artifacts`, `output_inventory`, `reconcile_effects`, `protected`, `snapshot_identity_matches`, `listener_owner/assert_listener`, and the pinned source guard. Original implementation signatures are authoritative.

**Produces:** A concrete sealed package with no authority or actual case. Reviewed entry can later execute only current-candidate E03 round1 when its own release exists.

- [ ] Write admission tests: wrong/absent review, scope/case/model/manifest/proof, bool caps, predecessor reuse, expiry and exact 60-second proof-age boundary, path escape/reparse, stale or consumed slot before native construction.
- [ ] Run the focused tests with pinned Python `-B -m pytest`, no cache provider, isolated basetemp; observe RED.
- [ ] Implement the admission and readonly preflight wrapper using the exact IO helpers and deferred native import.
- [ ] Write execution/backend tests: exclusive claim, fsynced admission before UI, original fixture/server/CLI ordering, no call on drift, final revalidation before activation, exactly one CLI, baseline identity/content/selection checks, failures retaining effects/cleanup/audit/boundary evidence, no factual self-approval. Isolate real dependency definitions where mocks would hide path binding.
- [ ] Observe RED, then implement the narrow backend using existing helpers. No raw user/window content in public preparation summaries.
- [ ] Run the full focused suite plus retained input-origin tests. Expected: all pass; no live UI/product/model/audio call. Check AST, dependency/source hashes, no candidate changes, and no actual/release authority.
- [ ] Seal code, tests, evidence and review request. Prepare one fresh independent review with exact manifest and bounded scope; do not treat this plan as a new actual-case authority.
- [ ] Update original work-order/state/report and mirror; commit/tag/push the prepared checkpoint. Report missing gates honestly.

## Review focus

1. Real copied dependency bindings must not read another package's inputs or consumed authority; test actual definitions and pin every import.
2. Preserve all mechanical checks and pre-cleanup effect reconciliation; exceptions before or after CLI cannot evade cleanup or manufacture a pass.
3. Native proof binds the exact current source, local 8B manifest/tag/daemon and all seven protected identities, including parent/command evidence; freshness is checked again before final activation/CLI.
4. Case allocation is exclusive and retained on failure; a diagnostic receipt or old-candidate PASS cannot become a predecessor or acceptance credit.
5. Mock tests do not prove real focus/IME behavior, model facts or latency. Those remain for the separately released actual case and independent result review.

## Fix1 independent-review closure

Base manifest 7078209f8881b4278a07c121b280bf7a9704ccb2a38aca2a3eed8c3e8781eb0d remains NEEDS_FIXES and has never run. OWNED-STOP-CLEANUP-01 now records the persistent marker error inside the actual cleanup definition while continuing exact-owned termination, waits, log closure and receipt. PRE-SUBMIT-EXPIRY-01 now keeps the full pre-activation review and adds a binding/time-only admission check after final window observation. Seven new regression tests observed RED and then GREEN. No authority, live case, retry or acceptance credit is supplied by this revision.
