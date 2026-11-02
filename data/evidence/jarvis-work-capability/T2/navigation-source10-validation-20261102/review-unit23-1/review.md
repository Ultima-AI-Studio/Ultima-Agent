# Combined U2/U3 independent integration review

**SPEC REVISE. QUALITY REVISE.**

Combined original T2 U2/U3 candidate only. Static SPEC then QUALITY review of the supplied diff, requirements, root rulings and specified synthetic readbacks. No product changes or runtime/test/git/model/network operations. File paths/lines in findings are candidate HEAD.

BASE 494e544788c287defbf1208967444e733df5501a through HEAD 0e3e0edeb6d57d7d792dd5f1e40ecad58ee60642.

## SPEC

Findings 1-5 and 7 violate worker cutoff, replay and admission contracts. The required historical negative in finding 6 no longer exercises its original outcome.

## QUALITY

The lock boundary allows a real late side effect. Replay validates internal agreement between subsets without tying the submitted report and final artifact to the original wire. The green cases validate genuine positive files but do not detect these substitutions.

### 1. Critical | Seal timeout and invalidate the permit inside the observer lock

`src/brain/work_tools.py:146-172,360-377`

TOOL_TIMEOUT raises under the RLock and the except reacquires it through seal only after leaving the with. A claimed writer waiting at write_intent can acquire the released lock in that interval, observe a live claimed permit and enter the real SDK write even though the caller has already seen timeout. An exception after publishing START but before completing its event record also releases a live permit. The real executor cannot cancel a running future.

**Resolution.** Catch and seal under the same acquisition, before any other thread can admit an intent. Fully validate and safely serialize the exact event before exposing the permit. Exercise the competing writer at the actual timeout observer boundary with a controlled handoff; before intent require zero file calls, after intent retain the original effect and first failure.

### 2. Important | Tie the authored body and original file to the final ACK proof

`src/brain/work_research.py:660-670,690-700,713-729`

The final verifier compares writer IDs but does not require the original writer receipt path/hash to equal the reopened artifact path/hash or compare the successful wire action_input to the record submitted_json it resolves. Keep the genuine final packet and change just the title consistently in the full record submitted_json/payload_json, file bytes and record/artifact hashes. All compared IDs, refs and fact evidence still match; the independent check can validate a different report from the one the original writer authored and acknowledged. The final packet contains no independent intent/file adapter record.

**Resolution.** Compare canonical submitted arguments directly to the native writer action, require all original visible receipt fields including fixed resolved path and exact byte hash to agree with the report/file/effect/actual reopened bytes, and export the one consumed intent and adapter records for independent replay. Add a coherent substitute-title/file counterfactual retaining the original wire and ACK.

### 3. Important | Validate event sequence, phase contents and the sealed prewrite prefix

`src/brain/work_research.py:567-585,607-621,650-670; src/brain/work_tools.py:271-282`

Replay splits STARTs and ENDs before matching, discarding interleaving and ignoring timeout/unexpected events and timestamps. Moving an inspector END ahead of its own START while preserving within-kind order passes these checks. The system check accepts any suffix after the template prefix, the user prompt is taken from the same packet, and the final verifier only compares its prewrite_sha256 string with the visible receipt. It never derives and verifies the prewrite bytes/prefix from the final packet. Neither a stored outer hash nor four positive fixtures verifies these invariants.

**Resolution.** Walk the actual ordered transcript, require consecutive matching START/END and phase transitions, reject extra/late/timeout events on success and bind the actual generation and send/return/admission ordering. Compare exact phase system text and original safe prompt to independent frozen inputs. Include or independently derive the prewrite packet and verify its hash and unchanged prefix against the final transcript. Mutate chronology with unchanged per-kind lists, or change a phase suffix consistently across entity and hashes.

### 4. Important | Retain reproducible native identity and validate the whole response policy on replay

`src/brain/agent_server.py:318,380-385,408-411; src/brain/work_research.py:586-609,623-629,653-656`

The live leaf checks version/tags/local manifest, while the packet retains only metadata response hashes and counters. The offline verifier never checks those metadata hashes against bytes or a checked identity. Changing the version GET response_sha256 alone is accepted by its logic. Outer model/role/extra keys, positive prompt_eval_count and total context bound are enforced live but not fully replayed; extra native options are not rejected during replay.

**Resolution.** Retain bounded scanner-safe verifiable identity evidence for both metadata responses and the observed local manifest digest. Verify each metadata receipt and fixed version/model/digest. Reapply exact native options, model, complete envelope/role/unknown-field and count limits against raw bytes, separately from secured-envelope validation. Mutations should include an incorrect digest and a self-consistent invalid outer response; cached counts still cannot prove full context.

### 5. Important | Install the send-time clipped timeout and record a refused admission

`src/brain/agent_server.py:274-297`

The timeout passed to build_request is computed before preparation/lock wait. The second timeout(ack) rechecks admission but throws away its recomputed timeouts. If remaining prewrite time falls from 60s to 56s, a five-second read/connect timeout can still be sent when the applicable budget is one second. If the second check rejects, execution precedes receipt creation and no admission-failure record distinguishes this from an unattempted POST.

**Resolution.** Install the final clipped timeout on the same prepared request immediately before reservation and send (including metadata limit); retain a safe refusal receipt with zero POST starts on post-metadata/pre-send rejection. Exercise integer controlled clock advance during build for both a still-admissible and an expired request, checking actual HTTPX request timeout extensions, counters and receipt.

### 6. Important | Restore the late between-snapshots negative to the actual intended race

`src/brain/tests/test_work_research.py:633-635,654-678`

r5_between_snapshots delays the outer writer before claim and returns at 670-672. The branch at 675 that formerly checked an actual completed file and coherent returned terminal ID is unreachable. This case never compares an already-admitted write finishing between the service outcome snapshot and error handling, despite preserving the old test ID.

**Resolution.** Delay the admitted SDK file operation for this variant, release/join it on compose_error access, then inspect the frozen response and separate late records after completion. Verify stable first effect/terminal IDs, no new request leakage, exact original path and bytes; keep the pre-intent zero-write case separately.

### 7. Important | Require concrete runtime evidence for fresh ACK and service verification

`src/brain/work_service.py:131-134; src/brain/work_research.py:679-683,703-709`

The service checks attribute existence, passes getattr with a None default, and the artifact verifier skips runtime verification when the value is None even with require_ack=True. A present-but-null final packet downgrades the fresh final check to pure issued-snapshot verification. The normal native success assignment currently supplies bytes; a missing-proof return must itself fail closed.

**Resolution.** Require nonempty immutable runtime bytes at fresh ACK/service gates. Keep pure issued-snapshot checks in an explicitly separate historical or isolated-unit interface. With a genuine issued snapshot/write and an absent or None final packet, require failure/needs_attention.

## Positive and bounded checks

The request-bound caller filter, exact enrolled object on worker claim, per-request capability narrowing, single real SDK file writer, stage/END/next-generation promotion, fixed path and real-ID scanning are visible in the diff. The isolated availability correction removes only placeholder exposure scanning. The actual page still calls scan_view before returning bytes. Both modified context tests still assert their GET/file or SDK-registry purposes, and their deterministic fixture is opt-in. The closed-loop fixture chooses its next unused available source and authors from observed lines/cards. Its literal per-source oracle and real SDK/file checks are meaningful. The two historical maxLength paths now use pure projection and real writer/ACK phase coverage separately. Historical v2 decode remains behind its version branch.

For the four supplied positive exports I used only stdlib JSON/hash/Path reads. I resolved the writer END path, matched the external manifest path, reopened that original file, verified all four manifest hashes, checked fixture lines against stored GET bodies and reconstructed the literal Markdown bytes without product rendering. Text/permuted/HTML/mixed had 337/337/370/341 bytes, eight tool events and five wires each. These positive checks leave the counterfactuals above open. The final-only fixture exports contain the prewrite digest but omit the original prewrite bytes and adapter/intent records. A future trusted harness can capture more from the ledger; that availability is distinct from what these four exports demonstrate.

Named unchanged SDK reads were openjarvis/tools/_stubs.py (START, running-future timeout, END), core/events.py (observer exception swallowing), cli/ask.py (registry name builder), and agents/native_react.py (ordered USER observations/max-turns). The diff cut test_r4b_late_report before its stage and barrier setup, and verify_research_artifacts in the middle of the v3 path. Only those functions' required current source slices were read to resolve the late-snapshot and submitted/file-link risks. No general repository or SDK audit. The fixed H Python was used for stdlib static parsing, hashing and byte readback; no proposed race or mutation tests were executed.

## Cannot verify and status

- Real inference, model comprehension/semantic coverage of original four-source E02, native timing, actual source10 search/GET, live model identity, production readiness and harness acceptance are unproven.
- Root supplied 418 covering and 8 safe-compat passing results, SDK22/current bytes and frozen5 verification. These tests were not rerun. Existing anyio rewrite warning and optional voice fallback remain; no audio.
- The remaining real-ID PII rejection rate is unmeasured.

Model/actual/harness/T3/production release false. E02/T2 NOT_PASSED. No modifications to allocations or frozen inputs.

## Exact inputs (SHA-256)

- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-review-brief.md`  `608d54a05c50a5c60611b57a9bcc4a8aaa8708065053c7a7f054afa0affdbd68`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-brief.md`  `16ebc8291dca7e1d3ca92deaff1ec1494decf0f4adeacdd6797e41174db8645c`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit2-report.md`  `0bd8a4e9f3e64ebc475dbd3c5e67e2581ab0cd50f20e3dd8d21c7bf803182587`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-review-package.txt`  `d8524eccb9d80966005fc5ad52f8cb80dbb11a107410e7561d7cfcbe929f7a7c`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-unit23-availability-scan-ruling.md`  `74b5c652f80dc182e1c1b3e6e24f5216892b4beb1b99356ce8bc598d4297c304`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\docs\plans\jarvis-work-research-source-navigation-design-20261102.md`  `41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\docs\plans\jarvis-work-research-source-navigation-implementation-20261102.md`  `a8419b773d7cf67f1b9754cdf4475aba32b1f6be8591335792f9d1122f3e6195`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\root-test-context-fixture-extension.json`  `199cad6cd6250ab05fa861faf7576aba9f4862696c8487782049aa7daee2da31`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\root-unit23-coalescing-ruling.json`  `0efcb20cf045ee0ba343565172052560a14027d5a33b9f0f18a9bf3af2488b09`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-delivery-covering\receipt.json`  `21757553d052ff4f85ead7964fc5620ca2a1d7ccb37d4fcf0a37ef83843daead`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-delivery-compat\receipt.json`  `af6f8f915a3d08e8ae046858ec86ed552ede4c907bb01bd357d37d86667c3bab`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-delivery-readback\external-verification.json`  `28ce3ec2f1f44ce11fbb63160d6389e67101c10c956bc20dc07765af6d7a1e77`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-delivery-readback\sdk-sources.json`  `e0b0817c172a605193f76a640977bd815ae1cb45e297da29273d2ebe879ec691`
