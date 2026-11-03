# Original-corpus zero-inference profile implementation plan

> **For agentic workers:** Use superpowers:executing-plans task by task only after separate code-preparation authority. This design grants no runtime permission. Steps use checkbox syntax.

**Goal:** Prepare one independently reviewable, case-private, zero-inference mechanical profile for the original E02 corpus.

**Architecture:** One five-file preparation package composes the real isolated factory, request-local mock transport, WorkService and V2 strict exporter. A separately reviewed root control owns confinement, time, one-shot allocation, closure and independent verification.

**Tech Stack:** Existing Python/PowerShell, installed OpenJarvis 1.0.4, HTTPX MockTransport, pytest, V2 harness. No added dependency.

**Spec:** sibling task-4-original-corpus-profile-design.md. Read with this plan.

## Global constraints

Use C118 source31/SDK22/manifest cdfbfb05, harness 3d0b47c9, caller 0e91519c, original corpus 9e7cdfe6 and original readback 7b1410b7. Preserve query 774 B and bodies 7236/3252/4643/13559 B. Only current 8B 6d7230a9 forever; actual network/inference 0. Full hashes and exact source/response/clock contracts appear in spec.
One request, one fixture search, four fixture GETs, six reads/18432 B, 24 positions/8 cards/3072 B, >=3 distinct sources, one write and ACK, 8 research POST/16 research GET, one separate bootstrap fixture GET, no retry. Work/cleanup/observation 275/310/315 s, service/client/outer 260/300/315 s. No configuration, persona, scanner, entropy or clock edits. No native ownership/controller duplication, Git publication or runtime execution by implementer.

## Review focus

1. A default engine health check can escape before research_client exists; T1 proves earliest denial and scoped restoration.
2. One altered byte/content type or inherited loader changes what is measured; T2 pins inputs, config and real persona assembly.
3. A card from an earlier binding or invisible line can manufacture a plausible write; T3 accepts current SDK observations only.
4. File success can precede missing/mismatched END or byte drift; T4 discriminates each stage without exposing content.
5. Late/partial evidence can look successful after cleanup; T5 requires independent readback, containment and one nonrenewable clock.

## Files under V/profile-preparation only

profile.py defines import-side-effect-free private context, fixture handlers, one worker entry and bounded diagnostics. test_profile.py tests synthetic contracts offline only. run_checks.py runs a fixed non-runtime test allowlist with fresh scratch/receipt; no arbitrary entry point. manifest.json pins package members (except itself, root pins its raw bytes), external origins, dependencies, actual fixture paths/digests, roles and test IDs. README.md documents guard prerequisites, report schema and mechanical-only verdict. Code review receipts and later root control live outside this package under separate authority; no product, accepted harness, or portable product-test edits.

## T1. Bind the worker before construction

**Interfaces** in profile.py: read_pins(manifest: Path) -> dict; private_scope(folder: Path, pins: dict, guards: dict) -> ContextManager[dict]. guards is a trusted control reference bound to worker identity/run, never a worker-supplied boolean. Context contains server, adapter, p4, owner and counter records. Fixed test entry from V/profile-preparation, PY = H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe.

- [ ] Add test_guard_before_constructor_and_restore (fake constructors append ordered events). Assert pin/guard refusals precede any SDK/client construction, owner health allows only one tags fixture, a second tags or ordinary fallback fails, and exception at each installer restores every previous identity. Add test_missing_containment_fails_closed, including a forged self-attestation.
- [ ] RED: run `& $PY -B -X utf8 -m pytest -q test_profile.py -k 'guard_before or missing_containment'`. Expect missing interface/assertion cited in fresh receipt.
- [ ] Implement pin checks, one-worker audit deny and safe counters, private module facade and reversible installer stack described in spec. Validate before imports, including cwd/import paths, existing cache, fresh root/empty output, 8B local digest. No runner may launch a child. Deny and count unknown routes, wrong hosts, redirection, proxies or async paths.
- [ ] GREEN: rerun that selector, require all collected cases PASS and no profile, native or network starts. Record diff and exact IDs for review.

## T2. Preserve original source and real factory

**Interfaces** in profile.py: original_inputs(adapter: ModuleType, pins: dict) -> dict; make_service(scope: dict, folder: Path) -> WorkService. Source of allowed synthetic assertions is test_profile.py only.

- [ ] Write test_original_input_binding rejecting same-length byte edit, reordered source/URL, content-type change, old request ID and altered query. test_real_factory_contract checks source-side entry calls plus private test doubles capturing keyword arguments and original hook restoration. Assert no assigned scanner/max_turns/persona flags, no second loader installation or old hook/fixtures, no network/executable spawned. These tests cannot qualify the actual factory at runtime.
- [ ] RED: `& $PY -B -X utf8 -m pytest -q test_profile.py -k 'original_input or real_factory'`; require intended failure.
- [ ] Implement real server get_jarvis path, its actual isolated relocation/config and native_react loader assertions. Attach adapter.install_browser_fixture, narrow fixture DNS, and real BrowserChannel/WorkService callbacks, new IDs and exactly research=True. Validate before/after real wrapper identities, policy, rate limiter and case-private audit path. Keep P4/P1/helper read only. Inspect source/synthetic records for missing conftest references; never import product tests.
- [ ] GREEN: same selector passes, mutation checks fail as expected and raw inputs stay unchanged.

## T3. Script native transport using only visible observations

**Interfaces** in profile.py: next_reply(entity: dict, seen: dict) -> dict; handle_native(request: httpx.Request, seen: dict, metadata: dict) -> httpx.Response. seen is per submission and records phase/order/source starts, no access to ledger, disk corpus or product resolver; metadata contains only pinned UTF8 version/tags bytes. Keep health handler separate.

- [ ] Add test_visible_choices with no-card/duplicate/foreign/fresh reference, exhausted landmarks, three usable sources, unsupported claim, final-only refusal vs true writer ACK. Assert chosen start/card is observable, exact 3 distinct IDs, maximum 6 reads, no synthetic END and no success ACK for a failed writer.
- [ ] Add test_native_boundaries for paths/order, sampler-vs-strict schema, count caps, 256/2048/256 and unchanged prepared entities. Mock streams fail if preconsumed; exercise header/overflow/unknown-route/refusal without socket calls. Separate reservations, handlers, bootstrap, completed and actual counters.
- [ ] RED: `& $PY -B -X utf8 -m pytest -q test_profile.py -k 'visible_choices or native_boundaries'`; require expected failure.
- [ ] Implement chooser from spec, feed ByteStream envelopes to the real product transport at runtime. Use the pinned archived identity bytes. Validate nonce/binding through current context/SDK transcript and final replay; never open old issued/response content in chooser. If schema/budget/choice is unavailable, report refusal/failure, no reroll.
- [ ] GREEN: same selector passes with no unconsumed expected request or implicit fallback.

## T4. Preserve independent inputs, writer evidence and strict replay

**Interfaces** in profile.py: failure_summary(ledger: WorkLedger, result: dict, stage: str) -> dict; run_profile(folder: Path, pins: dict, guards: dict) -> dict; read_profile(folder: Path, first: dict, p4: ModuleType) -> dict. Worker entry is callable only with pre-admitted private context, exactly once. Fresh reader uses bounded pinned inputs, file handles and readonly verifier.

- [ ] Add test_failure_strata for unclaimed START, writer exception before file, negative file result, on-disk file with failed/mismatched END, ACK absent and first cause vs cleanup error. Require tri-state fields, typed linkage/hash/size, no unbounded text; require original failure to propagate. test_replay_tamper rejects missing separately captured RuntimeInputs, forged type, partial export, swapped collection, other binding, unexpected extra output, byte drift including CRLF, or missing final ACK even when file exists.
- [ ] RED: `& $PY -B -X utf8 -m pytest -q test_profile.py -k 'failure_strata or replay_tamper'`; inspect assertion.
- [ ] Use install_trusted_exports and existing real verifier, capture baseline/first result and restricted diagnostics independent of exporter outcome. Validate original source identity before publication and enforce spec's closed member/4 MiB bounds. Record file policy and nested actual SDK writer path without calling it outside enrolled dispatch. Hold partial outputs in case-private quarantine. A failed result or unsafe publication path cannot be upgraded by replay.
- [ ] GREEN: same selector passes; inspect synthesized failure receipt for meaningful bounded distinctions. No historical audit reproduction, real original-corpus invocation or blind rerun.

## T5. Seal preparation, then separate control and one allocation

**Interfaces** run_checks.py: main(argv: list[str]) -> int supports only --contracts. README/manifest fix full hashes, selector/node-ID allowlist, receipt schema, private control requirements, externally observable vs unknown fields and no automatic execution.

- [ ] Add test_observation_gate for a stale/missing enforcement witness, hook-counter-only proof, earlier runner close followed by late readback, expired 275/310/315, mutated closed file and attempted second invocation. Use synthetic clocks only in offline contract tests for the control predicate, never in an original case. Require FAIL/unknown and zero released slots.
- [ ] RED: `& $PY -B -X utf8 -m pytest -q test_profile.py -k observation_gate`. Then implement receipt/index and pure predicate for documented gates. Separately label bootstrap/fixture and real endpoint starts; a denied unexpected operation invalidates PASS.
- [ ] GREEN: run same selector. From package directory run `& $PY -B -X utf8 .\run_checks.py --contracts`; require exact tests collected/run/passed, recorded interpreter/versions, raw stdout/exit, nonzero if missing tests, zero original-profile runs, no actual model/network. Root reads hashes and receipts independently. Review synthetic test verification only.
- [ ] Independent code reviewer verifies complete diff against full spec and five risks, hard-denial ordering, permission path, strict export/prewrite/firstcause and restoration. Root alone records code gate and publishes. Fix findings under separate authorization before any runtime consideration.
- [ ] Separately root prepares/reviews concrete restricted-worker control, exact executable/environment/identity, zero-egress proof including native code, protected baseline, one allocation consumption before work, deadlines and closed outcome observer. Existing inert caller is not a compatible direct entry. Absence of containment or time-bounded observer blocks release. Only a later explicit root allocation may run one in-process original query, seal first outcome, independently reopen/check hashes and close 1/1 even on failure. No retry or upgrade to real 8B.

## Self-review

Checked coverage against original draft, new brief and C118 transport, SDK and V2 exporter. T1 covers discovery health and runtime startup, T2 input/persona/security, T3 visibility/native limits, T4 independent inputs/real writer events/file/typed export, T5 containment/time/authority. Every review risk has a named adverse test; public signatures above share the same folder, pins, guards and first-result types. A successful mocked check establishes only code-contract behavior. Real configuration, random IDs, budgets, END reliability and file bytes remain empirical until the one allocated case. No implementation commit or runtime release is a step in this design delivery.
