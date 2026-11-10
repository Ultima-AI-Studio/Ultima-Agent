# Independent E02 native HTTP diagnostics preparation review

Reviewer: `/root/review_e02_native_http_preparation`. Recorded UTC: 2026-11-07T08:49:46.888Z. Original work order: `wo-ultimaagent-20261101-0021`, stage T2.

Reviewed candidate `ee1bef61f04169c64978538dbc4ba799ef7be6c0`, based on `2b42b3e19516154a26cbc895a3d9e69fabb07ab2`, with local candidate tag `ultimaagent-e02-native-http-diagnostics-candidate-20261107`. The candidate worktree is clean. The committed diff contains exactly the three authorized files; `git diff --check` is clean.

Sealed [preparation manifest](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/manifest.json): `26977820632f6dbac4bafa286533c48eb883907129ae6a2bb04e5beb7d2c3298` (808 verified members). The [approved plan](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/plan.md) remains SHA256 `4d91295ad0a9582ae5808d3b841082178d6909d792aeef2e2a80b1b882cb9574`, matches its project copy, and has independent `PASS_PLAN_ONLY`. The detailed [JSON review](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/review/independent-preparation-review.json) contains exact evidence hashes and independent readback results.

## Code and specification findings

No blocking or nonblocking code finding remains in this candidate.

The sole product change is [work_research_diagnostics.py](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/work_research_diagnostics.py:35), SHA256 `24f2d14a9791d89d5bee5be22bedc3bad220c485d6f427fc5caa0beea411056d`. It adds a closed v3 `last_http` projection from the existing transport receipt and ledger timeline. The existing [failure diagnostic test](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/tests/test_work_failure_diagnostics.py:37) only changes its private version assertion; the new [HTTP diagnostic suite](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/tests/test_work_http_failure_diagnostics.py:21) has 43 cases.

- The last receipt is identified by its zero-based index and exactly one corresponding send/admission-refused event. Fixed method/path/domain triples select version, tags or chat. No receipt produces null; inconsistent provenance makes capture unavailable.
- Status comes from the original transport after HTTP return. Non-2xx is rejected before body iteration. The HTTP500 fixture checks that a private, oversized stream is never iterated, is closed, and preserves the original `Research HTTP status` failure.
- `send_reserved` means admission reservation, not network delivery. `transport_failed` reports exchange failure; a 200 response can still fail JSON, schema or scanning. These distinctions are preserved in the new tests.
- `validated_response` requires a matching chat wire generation and entity digest, a secured envelope, reserved send, 2xx status and no transport error. An earlier response or metadata exchange cannot supply validation for a new chat receipt. Validation does not establish factual correctness or delivery.
- Exact numeric/boolean types, request digest, route/status limits, generation/index bounds, request and response caps, and counter coherence are enforced. GET request bytes remain zero with the empty-entity digest. Extra body, URL and exception-text fields are rejected.
- Scanning, canonical encoding, request binding, 16,384-byte packet cap, freeze-once behavior, `complete=false` and zero acceptance credit remain. Original failure and write/ACK distinctions survive capture failure or late receipt mutation.

These conclusions were traced through unchanged [transport and native response validation](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/agent_server.py:272), [secured-envelope assignment](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/agent_server.py:598), [ledger scan/freeze behavior](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/work_tools.py:300), and [service failure capture](C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent/src/brain/work_service.py:203). There are no model, request construction, transport, body-read, schema/replay, write or acceptance-gate changes.

## Independent evidence readback

The reviewer read and hashed existing evidence only; no tests, product/profile code, model, network, process/service or UI/audio actions were executed. Independent verification matched all 808 sealed members, all 1,568 current inputs, and 585 source/snapshot pairs across 39 current paths. The selected [post-commit readback](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/verification/offline-post-commit-readback.json) matches SHA256 `29ed590df61b3a0fc5c244849585a24684cf45f3079d17ea70ac8badb44e03e2`.

| Saved group | Passing cases |
| --- | ---: |
| http-green | 43 |
| export | 6 |
| failure-green | 31 |
| metadata-green | 43 |
| diagnostics-green | 17 |
| target-green | 19 |
| reference-green | 29 |
| claim-green | 28 |
| unique-green | 21 |
| grounding-green | 11 |
| research-a | 68 |
| research-b | 110 |
| navigation | 90 |
| transport | 104 |
| delivery | 86 |
| **Total, distinct JUnit IDs** | **706** |

There are 700 product tests and six exporter-helper compatibility tests, with no duplicates, JUnit failure/error/skip entries or stderr content in the selected runs. All selected guard receipts are clean. The immutable [RED run](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/offline/http-red-20261107T083618967067Z/receipt.json) retains 38 assertion failures and the exact base diagnostic blob. The GREEN test changes retain those 38 assertions and add five cases. These are fresh executor results bound to current source bytes, independently read back by this reviewer; they are not an independent rerun.

The [exporter checks](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/verification/export_checks.py) exercise the unchanged predecessor helper's payload export/rejection behavior against v3. They intentionally substitute its OS path guard and do not rerun actual authority or reparse checks. The existing HTTP legacy/CLI and junction cases remain explicitly excluded. The Python audit is not a packet sniffer.

## Compatibility and preserved evidence

The [compatibility findings](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-diagnostics-20261107-r1/research/compatibility-findings.md) distinguish supported interface mappings from unresolved native causality. Seven saved upstream files match size, SHA256 and computed Git blob SHA1; four also match separately recorded expected blob references. The saved Ollama v0.32.15 source maps `think` to `enable_thinking` and object `format` to JSON schema. The saved current-8B template supports disabled thinking, which product already requests. The pinned b10488 path combines grammar and native response parsing.

The evidence does not prove installed-binary equivalence, full 5GB model integrity, or the exact cause of the predecessor's native parse failure. Bounded metadata inspection and an offline reference grammar converter do not establish native response compatibility. No parameter/schema/token-limit change is justified or claimed by this package.

Independent hashing also matched all 2,501 prior preparation members, 49 result members, four native-log supplement members, 1,563 accepted prior inputs and nine unrelated files. The predecessor result-review digest remains `24c356987ade22a6e501e9aa084eec74214320beb7fcf2af321ba2fde59ff122` with verdict `FAIL_CONFIRMED`; the old worktree remains clean at the base. The saved runtime receipts have the same seven identities/version/model digest at 08:29:29 and 08:44:12 UTC. This reviewer did not perform live checks or assert continuous liveness.

## Declined to judge

- **Exact native template/schema/parser causality, installed-binary equivalence and a live current-8B rerun:** The saved source and predecessor logs do not prove request-bound native causality; this preparation has zero actual/model allocation.
- **Factual correctness, original-question coverage, citation correctness, real writer/readback/ACK/timing/cleanup and E02/T2/Owner acceptance:** No new actual case or qualifying deliverable exists; synthetic SDK tests cannot establish these acceptance gates.
- **Continuous protected-process liveness or present service readiness:** Only the saved before/after identity receipts were read; their observations are not continuous monitoring and the reviewer performed no live checks.
- **The excluded HTTP legacy/CLI and Windows junction tests, or full exporter OS reparse/authority and actual harness behavior:** The disclosed offline suite excludes the two operation-dependent tests; exporter fixtures deliberately isolate payload compatibility. No broader pass is claimed.
- **Full model tensor integrity and current official upstream retrieval:** Saved bounded metadata and pinned-source provenance were reviewed. The full 5GB model was not rehashed, and this reviewer made no network requests.
- **Project-document/mirror/queue closeout commits, pushes, stage freezing or release approval:** The sealed candidate commit and its local candidate tag were verified. Later integration and Owner/release actions are coordinator obligations and are not authorized by this verdict.

## Verdict

**PASS_PREPARATION_ONLY.** The exact sealed candidate meets the approved offline diagnostic preparation scope. No new actual harness, authority or release was published in this package. Current 8B and original budgets remain; actual cases and model calls are zero. E02 remains **0/3**, T2 and Owner acceptance remain unpassed, and the native parser root cause remains unresolved. This verdict grants no actual run, retry, model call, service operation, factual/delivery credit, stage freeze or release.

