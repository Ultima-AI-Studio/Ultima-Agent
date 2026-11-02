# Combined U23 fix round1/5

Read first. Same original implementer /root/implement_navigation_unit2. Root read receiving-code-review + fix-loop before this round, complete independent report/verdict, and targeted current source: observer outer except/lock gap, discarded final timeout, optional None runtime gate, unbound writer report fields and unreachable between-snapshots branch are present. Remaining chronology/native evidence omissions are visible in packet/verifier; no conflicting original design requirement exists. Root accepts all seven, no severity downgrade or scope/acceptance relaxation. Fix one finding at a time with a meaningful RED then covering GREEN; this round finishes with SAME reviewer scoped to F1–F7 and new fix breakage only.

Original combined requirements W/task-2-navigation-code-unit23-brief.md16ebc829 and authorized availability/context extensions remain binding. BASE0e3e0edeb6d57d7d792dd5f1e40ecad58ee60642. No branch/worktree switch, new framework/agent core/registry, SDK edits, defaults/models/proxies/dependencies/queue/global memory/production/audio/UI/network/harness/actual/T3 actions or subagents. Model forever current8B, no otherweights ever. Root code-only authority persists. Exact existing10 allowed files can change; new v3 spec appendix may document revised runtime packet ABI, but five frozen originals/approved plan copies/v2 algorithms/old evidence remain immutable.

Original author report0bd8a4e9 is raw archived V/code/unit23-author-r1/report.md, prior post-commit/external/SDK/readback preserved. Append SAME W/task-2-navigation-code-unit2-report.md; keep all original bytes as complete prefix. Put new proofs/exports/JUnit/logs under NEW unit23-fix1-* paths, never overwrite original 418/8/four exports/receipts or review.

## Findings verbatim

### F1 Critical — Seal timeout and invalidate the permit inside the observer lock

src/brain/work_tools.py:146-172,360-377

TOOL_TIMEOUT raises under the RLock and the except reacquires it through seal only after leaving the with. A claimed writer waiting at write_intent can acquire the released lock in that interval, observe a live claimed permit and enter the real SDK write even though the caller has already seen timeout. An exception after publishing START but before completing its event record also releases a live permit. The real executor cannot cancel a running future.

Resolution: Catch and seal under the same acquisition, before any other thread can admit an intent. Fully validate and safely serialize the exact event before exposing the permit. Exercise the competing writer at the actual timeout observer boundary with a controlled handoff; before intent require zero file calls, after intent retain the original effect and first failure.

### F2 Important — Tie the authored body and original file to the final ACK proof

src/brain/work_research.py:660-670,690-700,713-729

The final verifier compares writer IDs but does not require the original writer receipt path/hash to equal the reopened artifact path/hash or compare the successful wire action_input to the record submitted_json it resolves. Keep the genuine final packet and change just the title consistently in the full record submitted_json/payload_json, file bytes and record/artifact hashes. All compared IDs, refs and fact evidence still match; the independent check can validate a different report from the one the original writer authored and acknowledged. The final packet contains no independent intent/file adapter record.

Resolution: Compare canonical submitted arguments directly to the native writer action, require all original visible receipt fields including fixed resolved path and exact byte hash to agree with the report/file/effect/actual reopened bytes, and export the one consumed intent and adapter records for independent replay. Add a coherent substitute-title/file counterfactual retaining the original wire and ACK.

### F3 Important — Validate event sequence, phase contents and the sealed prewrite prefix

src/brain/work_research.py:567-585,607-621,650-670; src/brain/work_tools.py:271-282

Replay splits STARTs and ENDs before matching, discarding interleaving and ignoring timeout/unexpected events and timestamps. Moving an inspector END ahead of its own START while preserving within-kind order passes these checks. The system check accepts any suffix after the template prefix, the user prompt is taken from the same packet, and the final verifier only compares its prewrite_sha256 string with the visible receipt. It never derives and verifies the prewrite bytes/prefix from the final packet. Neither a stored outer hash nor four positive fixtures verifies these invariants.

Resolution: Walk the actual ordered transcript, require consecutive matching START/END and phase transitions, reject extra/late/timeout events on success and bind the actual generation and send/return/admission ordering. Compare exact phase system text and original safe prompt to independent frozen inputs. Include or independently derive the prewrite packet and verify its hash and unchanged prefix against the final transcript. Mutate chronology with unchanged per-kind lists, or change a phase suffix consistently across entity and hashes.

### F4 Important — Retain reproducible native identity and validate the whole response policy on replay

src/brain/agent_server.py:318,380-385,408-411; src/brain/work_research.py:586-609,623-629,653-656

The live leaf checks version/tags/local manifest, while the packet retains only metadata response hashes and counters. The offline verifier never checks those metadata hashes against bytes or a checked identity. Changing the version GET response_sha256 alone is accepted by its logic. Outer model/role/extra keys, positive prompt_eval_count and total context bound are enforced live but not fully replayed; extra native options are not rejected during replay.

Resolution: Retain bounded scanner-safe verifiable identity evidence for both metadata responses and the observed local manifest digest. Verify each metadata receipt and fixed version/model/digest. Reapply exact native options, model, complete envelope/role/unknown-field and count limits against raw bytes, separately from secured-envelope validation. Mutations should include an incorrect digest and a self-consistent invalid outer response; cached counts still cannot prove full context.

### F5 Important — Install the send-time clipped timeout and record a refused admission

src/brain/agent_server.py:274-297

The timeout passed to build_request is computed before preparation/lock wait. The second timeout(ack) rechecks admission but throws away its recomputed timeouts. If remaining prewrite time falls from 60s to 56s, a five-second read/connect timeout can still be sent when the applicable budget is one second. If the second check rejects, execution precedes receipt creation and no admission-failure record distinguishes this from an unattempted POST.

Resolution: Install the final clipped timeout on the same prepared request immediately before reservation and send (including metadata limit); retain a safe refusal receipt with zero POST starts on post-metadata/pre-send rejection. Exercise integer controlled clock advance during build for both a still-admissible and an expired request, checking actual HTTPX request timeout extensions, counters and receipt.

### F6 Important — Restore the late between-snapshots negative to the actual intended race

src/brain/tests/test_work_research.py:633-635,654-678

r5_between_snapshots delays the outer writer before claim and returns at 670-672. The branch at 675 that formerly checked an actual completed file and coherent returned terminal ID is unreachable. This case never compares an already-admitted write finishing between the service outcome snapshot and error handling, despite preserving the old test ID.

Resolution: Delay the admitted SDK file operation for this variant, release/join it on compose_error access, then inspect the frozen response and separate late records after completion. Verify stable first effect/terminal IDs, no new request leakage, exact original path and bytes; keep the pre-intent zero-write case separately.

### F7 Important — Require concrete runtime evidence for fresh ACK and service verification

src/brain/work_service.py:131-134; src/brain/work_research.py:679-683,703-709

The service checks attribute existence, passes getattr with a None default, and the artifact verifier skips runtime verification when the value is None even with require_ack=True. A present-but-null final packet downgrades the fresh final check to pure issued-snapshot verification. The normal native success assignment currently supplies bytes; a missing-proof return must itself fail closed.

Resolution: Require nonempty immutable runtime bytes at fresh ACK/service gates. Keep pure issued-snapshot checks in an explicitly separate historical or isolated-unit interface. With a genuine issued snapshot/write and an absent or None final packet, require failure/needs_attention.

## Root execution and test requirements

F1 first: serialization/validation, revocation and first failure must happen while the same observer RLock is still held; deterministic competing real worker/file intent at the actual callback catch boundary, not a stand-in manual seal. Keep before-intent zero-write and admitted/late-effect paths distinct.

F2/F3/F4/F7: retain bounded immutable evidence, do not add passed=True shortcuts or a second audit framework. Native writer action/receipt/intent/file adapter/read bytes must bind the same submitted body and exact path/hash, including coherent changed-title counterfactual. Exact phase/prompt must be reconstructed from independent frozen caller/build inputs, not a field of the packet being checked. Walk ordered START/END/timeout records and actual generation/send/admission ordering. Use one declared clock domain/sequence for authority; raw SDK floating timestamp JSON stays lossless diagnostic and must not be compared to an unrelated monotonic domain. Embed or derive exact sealed prewrite bytes and unchanged prefix, with no self-referential hash shortcut.

Retain verifiable bounded metadata/local-manifest bytes or an equivalently replayable checked representation, status/path/order/hash and selected model/version/digest proof. Reapply live envelope/options/model/role/unknown fields/token/context/admission checks independently on replay; cached counts are observation, not full context proof. Use real-shaped successful native metadata/outer responses including machine numeric model sizes/nanosecond timing counters, without changing actual configured scanners or inventing opaque-ID exemptions. Unsafe string evidence must not be persisted; original raw GET restriction remains as designed.

Fresh ACK/service unconditionally require nonempty immutable runtime bytes. Pure issued-view validation can remain a clearly separate data helper USED by the strict runtime verifier; no production unit_mode/allow_fixture/native=False success bypass. If Unit1 pure data tests need that explicit helper, update their calls preserving their original purpose, not weakening fresh runtime gates.

F5 final timeout must be installed on the SAME prepared request just before reserve/send; do not reconstruct JSON/request entity. Record safe rejected admission with zero POST starts. Verify actual request.extensions timeout after controlled build-time clock changes (still admissible vs expired), including metadata clipping and no-refund semantics after real attempt.

F6 restore the actual admitted file between-snapshots race and stable frozen outcome/terminal IDs/late records; preserve separate pre-intent zero-file case. Remove no old assertions/purpose. Every mutation/race needs its intended failure gate, not an earlier missing preparer or invalid fixture failure. Test-only state belongs fixtures/helpers, not production convenience methods.

Covering files: src/brain/tests/test_work_navigation_sdk.py (F1/F6 worker/callback/intent), test_work_navigation_transport.py (F2–F5/F7 packet/options/history/native/admission), test_work_research.py (F6 and old65 negative purposes), test_work_navigation.py if separating pure-data interface, test_work_context.py only the two authorized fresh positives/helper if new strict verifier parameters require it. Use read-only V/code/run_code_tests_v2.py60f6ea3d with NEW stages. Keep all first REDs. Once all fixes are in, run full original6+new3 and safe compatibility8 once on final bytes, plus refreshed four independent external packet/file readbacks with new metadata/prewrite/intent material. Do not repeat broad suites after every edit. No tests of source text or expectations computed by the same production builder.

Before commit exact allowed paths, raw source-before/after/maps, no skip/xfail/removed IDs, frozen5 and SDK22 unchanged, targeted whitespace, all committed bytes equal tested input. New commit(s) from BASE0e3; no push/tag by you. Report commands/output/receipts/F1–F7 resolution and any real concern; root reads it before scoped rereview. If an exact requested invariant conflicts with code/design, raise concrete context rather than silently bypass; no human model-choice question.
