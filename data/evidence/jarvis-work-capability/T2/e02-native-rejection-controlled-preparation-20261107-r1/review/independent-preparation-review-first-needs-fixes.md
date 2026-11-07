# Independent controlled preparation review

Verdict: **NEEDS_FIXES**. Preparation review only; actual_run_authorized=false.

Candidate: `d860b2ab4e4d9974e33c96472e4ea15abb807280`; HEAD and candidate tag independently matched; working tree clean. Manifest SHA256: `6bdbff35be5d300ae82fc36c9f8a3098781872923882d3e855cd87e6cf1171d7`.

## Strengths and verified evidence

- All listed current and predecessor members/inputs independently rehashed successfully; plan bytes match the external plan and required SHA. Full 75 sources independently derived from 74 inherited paths plus frozen addition and matched N18.
- All entry/bindings/adapter function and class ASTs are unchanged. Candidate and binding constants match current bytes; budgets/model/corpus/protected/previous_plumbing fields retain N17 values. No actual/release/controller-authority/native-preflight/controller-ledger artifacts exist.
- Eight fresh receipts, source snapshots, audit reports and JUnit results support 287 raw/285 unique harness cases plus 61 stdlib. Current source bytes match snapshots; old 344/909 history is not counted. Ninety-second harness limit and max_workers=2 remain.
- New observer cases install current trusted exports before the actual SDK MockTransport helper and compare raw private/public exports, actual request/response hashes, response byte length, generation/receipt identity, no-runtime/END/credit state, and differing pre-write versus post-write effects.
- Closeout uses LF-normalized report text and byte-identical mirror copies; preserves last_actual_result. Publish uses explicit pathspec and empty-index preconditions, checks staged path subset, excludes all 15 unrelated baseline paths, and checks commit/tag bytes. These remain static findings, not publication proof.

Counts: current159/input1590/check_inputs1593/source75; N18 members953/input1580; N17 preparation234/result56/input1579; supplements4 plus execution receipts/final readback3; unrelated15. AST equality: entry11/bindings6/adapter68 top-level functions/classes. Fresh harness groups79+140+19+36+13=287 raw,285 unique; stdlib16+34+11=61; total346. No tests rerun by reviewer.

## Important finding R1

`verification/closeout.py:49-65`: The input current-run has preparation_review_path pointing to e02-source13-real-controlled-preparation, preparation_tests_passed=998, preparation_sync.local_tag=ultimaagent-t2-e03-source13-negative-prep-20261106, next_action prescribing an old metadata recovery, and next_offline_plan pointing to that old plan. closeout updates preparation_review_receipt/test_count/next_work and active_preparation but neither updates nor archives these unqualified aliases. Executing the reviewed script therefore leaves contradictory current preparation pointers/counts and next actions. This is a static defect in the pending closeout, not a demand that publication already be executed.

Impact: Consumers of existing generic fields can select the wrong review, report the wrong preparation test total or follow a superseded recovery step after the package is declared ready.

Required: Reconcile all unqualified preparation and next-action aliases to the current 346-test package, current independent review, proposed local tag/sync state and execution proposal, or move obsolete values into explicitly historical records. Preserve last_actual_result exactly in meaning. Verify resulting state before publication.

No Critical findings. No additional Minor findings. The old generic pointers being present before closeout is not itself the defect; the reviewed closeout leaves them stale afterward.

## Declined to judge

- Actual 8B research delivery and exact real native refusal predicate: Allocation is zero; MockTransport refusal injection cannot prove a real model outcome or explain the old rejection.
- Continuous protected-process liveness or current runtime/network health: Read-only package review forbids runtime/network/process operations. Sealed seven-identity observations are point-in-time only.
- Executed read_ready/read_release, local commits/tags/mirrors and queue refresh: Pending root closeout after review; scripts were read statically, not executed. Root must complete and independently read back after addressing R1.
- Remote push success: Previously blocked by automatic approval policy; no retry authorized in this review.
- E02/T2/Owner acceptance and transfer of historical 344/909 tests: Preparation only. E02 remains 0/3, no transferred actual acceptance credit.
- Controller authenticity of a future fresh call_ allocation: Entry retains existing protocol and rejects the sealed actual0 direct decision. A future controller must verify the new explicit reply; old call_6f04750fa3644cc39ce356ff25b1ca6b is consumed and is not a new allocation.

## Assessment

Not ready for closeout/publication with the reviewed script unchanged. The core frozen preparation and offline evidence are consistent; reconcile R1 without altering sealed evidence and perform the root-owned closeout/readback. No new actual allocation is granted. Historical N17 FAIL_CONFIRMED remains; current E02=0/3 and T2/Owner remain unpassed.
