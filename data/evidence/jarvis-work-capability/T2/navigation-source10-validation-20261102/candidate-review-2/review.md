# Source10 candidate fix-wave scoped re-review

**C1 ADDRESSED · C2 ADDRESSED · SPEC PASS · QUALITY PASS.** Code candidate ready. Task 4 adapter preparation ready. No open finding or new breakage from this wave.

## Decision and scope

The original whole-candidate review is retained at candidate-review-1. This is the same reviewer's scoped review of its two Important findings and regressions introduced by the single fix commit, 118ba152b007c30d358c8bc44c51aabe8ae820f0, relative to 6b1e07c8318a334ee1f2218863eb84254e38f526. The sealed 14257-byte full delta (851b57fd850cff17a01b7002e2fbb571aecf970f1043bb3642ce1d975439ec60) changes two product modules and one test file. The root proof (5a5cc44b39dda5de94a70213f8af47657f6db948ac4f34f15e7126b86d073f83), new author report (10b079f5bf5e1e4c1d60ef1d4cde09d4ac24fb2e8984800f4b8df6ac1fb7fa59) and original verdict matched their seals. The prior unit report remains 93985 bytes and SHA-256 d0bb89d69d668f613fef7cc3d50b56185d5317b42f8ef262e0360c22b4edc7d0.

## Findings

**C1 · ADDRESSED.** In src/brain/work_service.py:135–141, research now checks the original ledger deadline immediately after final verification, file readback and source selection, immediately before success. WorkLedger.admit_ack samples the live clock independently of the runner's permit seal. The exception path retains the completed effect and verified file. Historical replay and ordinary work keep their preceding behavior. In src/brain/tests/test_work_navigation_transport.py:406–447 the clock advances only after the original require_ack verifier returns. The original RED output shows the two erroneous succeeded results. The SDK/transport GREEN covered 135 cases. Independently reopened all three final service-deadline.json files and the corresponding research.md files, matched the root records, SHA-256, completed effect and report/file/dispatch linkage, and checked the test's adapter identity assertion. Each genuine in-time SDK ACK and final verification preceded the clock change. Each case retained one completed file, the same 15 sends (five chat generations) and its original effect. The cases used distinct test roots.

| Time at publication check | Service status | Error |
|---|---|---|
| 259.99999999999994 | succeeded | none |
| 260 | needs_attention | Research acknowledgement deadline |
| 260.00000000000006 | needs_attention | Research acknowledgement deadline |

**C2 · ADDRESSED.** In src/brain/agent_server.py:600–615 the secured response is parsed, schema-checked, scanned and compared with the raw envelope. The return-time gate still runs. Nonblank validation then precedes storing secured_envelope, marking secured and promoting the page. Valid actions and nonblank finals still traverse the previous promotion path. In src/brain/tests/test_work_navigation_transport.py:545–605, blank_final feeds a one-space final into the fourth response without mutating history/schema. The exact failure identifies the final validation gate. RED had promotions [1,2,3]. GREEN keeps [1,2], three inspect START/END pairs, four generations, three secured marks, no subsequent dispatch, file, write effect or final runtime proof. The previous failure matrix and all four positive writer flows still pass. The SDK/transport GREEN covered 136 cases.

## Independent readback and regression check

* Read raw invocation and receipt argv for all six stages and verified each receipt-listed output file against its hash. Parsed JUnit counts agree with stdout and the receipts. C1 RED had two failures and one pass. C2 RED failed on the additional third promotion. The final covering run used the fixed H venv interpreter with -B -X utf8, all original six plus three navigation suites, no cache provider and the candidate-path plugin. The final isolated compatibility run used that interpreter and run_compat.py. Exact per-stage argv/environment and output hashes are in each stage's receipt and the sealed author report. The final receipts are d12f6bd062966fce907260878e4656072ee1ea7e6b8178602febce30098da779 (479 passed in 90.25s) and 58e6b5c5ca71934effacddf30cd808ea92ec4729f561a9036a1048bee717c8a0 (8 passed with one existing warning in 0.13s). Both record zero failures, errors and skips. Multiset comparison of suite-qualified JUnit identities retained all 475 previous covering and all eight compatibility cases.
* Rehashed all 31 before/after/current final inputs, all 22 installed H venv SDK pins and 24 protected references. Cross-checked the sealed post-commit changed blob hashes with current bytes. Thirty inputs are tracked and the existing browser S3 test remains byte-bound and untracked. Existing research test bytes preserve its original 65 named purposes.
* Reopened the text, permuted, HTML and mixed report artifacts (337, 337, 370 and 341 bytes) plus each packet manifest, issued snapshot, views, runtime, prewrite and independent inputs. Their hashes match the fresh final exports. Reopened six fractional proofs and their referenced packet files and artifacts. All 90 prepared HTTPX records matched runtime receipt method, path, entity digest and timeout values. These checks used existing raw evidence and local data reads, with no new product runtime probe or suite run.

## New breakage and boundaries

No Critical, Important or Minor fix-wave issue. No new out-of-scope observation. The published issue resolutions cover all outstanding findings from the original whole-candidate review.

E02/T2 remains NOT_PASSED. The next step is separately reviewed Task 4 adapter preparation. Inert qualification, original-corpus zero-inference profiling, first bounded real 8B allocation, three same-candidate controlled passes, factual adequacy, real-network evidence, fresh same-candidate E01/E03 and negatives, independent T2 and Owner judgment remain separate gates. Generated-reference scanner rejection frequency and lower transport/native starts remain unmeasured. The source9 lexer deferral remains in force. No other model weights, T3, production release or E04–E08 completion are authorized by this review.
