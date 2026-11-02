# Task 4 · fix2 independent scoped re-review

**SPEC FAIL · QUALITY NEEDS_FIXES.** Five of six open findings are addressed. F1-N01 still permits unsafe raw export. The same change also rejects valid ACK prose; two enumeration regressions are recorded separately. Candidate `118ba152b007c30d358c8bc44c51aabe8ae820f0`, base `b67231103cdf00e5c4c6cf60d2c8b6f80192f424b712e40c927093d663a40cbb`, reviewed harness `e16609e14f5b0cc5e9805f1a0b2e66f99c2d8a450429c2dd2535abf8fbb83cec`.

## Dispositions

### H01 · ADDRESSED

adapter.py:403–445,447–460,929–932; test_adapter.py:874–901

Clearance requires exactly one retained launcher and one validated base. The caller must equal the base's native identity; the launcher is ancestry evidence only. Matching siblings fail before publication and the original owned set remains intact.

### H02 · ADDRESSED

headless_proof.py:20–26; adapter.py:483–500,874,941; test_adapter.py:782–788,805–809,821–839

Parent calls original get_json on the admitted endpoint, proves listener ownership, checks exact bool True, and closes a timestamped record retained independently in memory. The witness compares it to that copy. The positive checks exactly one mocked HTTP open with two-second timeout and negatives cover missing, altered, wrong-type and late records.

### H14 · ADDRESSED

adapter.py:739–773,876–880,944; test_adapter.py:948–973

The named recursive observer listings now guard directory open, each iterator advance and no-follow stat, and close iterators in finally. An overrun on the first directory prevents subsequent enumeration/stat/hash; each root member hash has a separate allowance. Two independent changes to enumeration semantics are listed below.

### F1-N01 · NOT_ADDRESSED

adapter.py:613–669, especially 645,659–668; test_adapter.py:919–946

Closed outer keys and the anchored timeline exception fix the reported top-level and clock-name variants. The new walker still parses nested string values with permissive json.loads, silently discarding earlier duplicate members. It selects serialized fields by the final key name even outside a producer-defined path; a scanner-positive numeric string under an untrusted entity key becomes an unscanned int. In the real final synthetic packet, setting execution.files[0].result to JSON with a scanner-positive first slot shadowed by a safe second slot, or to an object containing entity equal to that synthetic string, passed both real verify_runtime_packet and the new validation inside export_completed. Both reached the mocked publication function with unchanged raw bytes. The baseline also reached it, and the real scanner detected the sentinel before nesting. Reject duplicate keys at every decoded boundary and select decoding/numeric exceptions by exact producer path and type; arbitrary string-valued metadata must receive its string scan. Add both controls and assert no raw member is written.

### F1-N02 · ADDRESSED

adapter.py:981–1003,1005–1019; test_adapter.py:902–918,975–998

Both final child entry points guard the original work deadline immediately after setup and before runpy or listener construction. Delayed setup cannot call either injected entry; reservation consumption remains retained.

### F1-N03 · ADDRESSED

adapter.py:555–561,783–784,953–956; test_adapter.py:59–128,999 onward

Pre-cleanup observed output is compared immediately to accepted output and any discrepancy is latched. Witness reads the actual closed pre-map and compares again. The transient-extra case remains failed after cleanup restores the accepted set.

## New findings

### F2-N01 · Important · adapter.py:661

**A valid scanner-clean acknowledgement can prevent publication of a complete safe packet.** The prefix test treats every string starting with 'Observation: ' as serialized JSON, even wires[-1].secured_envelope.final_answer. A coherent rewritten final ACK 'Observation: the report is complete.' passed the original verify_runtime_packet(require_ack=True) and both original scanners, but validate_export_structure raised JSONDecodeError. No unsafe material or oversized packet was involved.

Decode Observation JSON only at the exact SDK transcript path/role where its format is defined. Scan legitimate free text as text. Retain this otherwise-valid ACK as a positive alongside the negative F1-N01 cases.

### F2-N02 · Important · adapter.py:944

**Inert output evidence silently accepts output directories that the prior witness rejected.** The previous inert predicate rejected any child of outputs via rglob('*'). The new predicate tests only the file list from guarded_files. Lines 768–770 recurse through directories but append only regular files. An outputs/unexpected-task/ empty directory is therefore observed and discarded; the witness reports clean despite a visible unexpected task-output effect.

Use a budgeted no-descendants predicate for inert outputs, or expose directory entries as well as files for that check. Add a closed inert package with a single unexpected empty task directory.

### F2-N03 · Minor · adapter.py:770

**The highest previously supported closed member count now fails only when the observer rereads the package.** At 843–849 the writer may index 256 data files and then creates seal-index.json. At 876 the observer uses the same 256-file walker on the same directory, now containing 257 files. It fails before comparing the admitted 256 members plus the index. The final 145-unit run does not exercise this boundary.

Apply the common 256 budget to data members only; allow the one fixed index on the observation path and test exactly 256 versus 257 data members.

## Checks and limits

- Read the sealed fix2 brief, previous findings, author appendix after byte 52443 and scoped b672→e166 diff. No broad harness or product review, historical suite rerun, or source mutation.
- Matched all companion-listed hashes, six live harness files and final receipt source copies, and the current 64 pins against the final source-before map. Read final argv (no -k), stdout 145 passed in 24.59s, empty stderr, JUnit counts and equal before/after hashes. Root proof records the full 123 earlier IDs and all 20 complete focused/whole records. A focused selected run is not a whole-suite pass.
- Scoped pure checks reused only test_fix1_genuine_synthetic_ex0's archived synthetic packet, inputs, snapshot and collection, the pinned verifier/scanners and synthetic test helpers escaped_scanner_fixture/rewrite_response. Two Python -B -X utf8 invocations used a write/connect/bind/subprocess-denying audit hook. The first replaced only preserve_completed_members with an in-memory marker. Observed synthetic_string_detected=True; base, shadowed duplicate and wrong-path entity each reached publication. The second obtained product_verifier_passed=True, prose_scanner_clean=True, and export rejected JSONDecodeError for the ACK. Neither probe published data. Product module import printed the existing voice-reference fallback diagnostic; no playback, capture, device, HTTP, model or service was invoked.
- Only the six reopened controls and fix-induced regressions were evaluated. Twelve previous dispositions stand. No process ownership, live inert timing, original-corpus dimensions, model comprehension or actual-case result has been qualified.
- The earlier historical RED limitations remain. No concrete root caller, baseline, approval or authority exists here. Current 8B-only policy remains fixed and E02/T2, T3, Owner and production gates remain closed.

Previously closed findings held: H03, H04, H05, H06, H07, H08, H09, H10, H11, H12, H13, H15. No out-of-scope observations. E02/T2 remains NOT_PASSED. Execution release is false.

## Reviewed SHA256

- companion `62fd385b00fc3c52623ae6f0882626fbe50e1e2460c15105b4fa805e8822e473`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix2-rereview-brief.md `e4b6413911e592796d5d30a5788b198cfbe399db795597f8c9aadd5e0ac4a26b`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix2-review-package.txt `9877e3519fc0fcc842680b0c85f2da42735f44d84b026a324e1379678e22dfbc`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-adapter-report.md `6f9926ac5819579c80367fa2c510fe0f9654839e3a6b185d9e66219bc1a56168`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix2-brief.md `46d3bd93e9504a7af222088d6c48dc293ec8d64a1f4dc1954edadf021915b2f3`
- harness-review-2/verdict.json `b47f96afb1d2167f29143334ee9e0ac61177f4570b2159423095961929b0017c`
- harness-review-2/review.md `62b6641916331ed920d33ee197113ede502c43f2f622c186e529d0a662c38351`
- harness-preparation-author-r3/report.md `594584b5ad328070a41d3b9f6a5f29f4f74a0ba8bbd08115932adf968011452b`
- code/root-harness-fix2-before-review.json `36f47e5b525bd22f22155f488a0089f1e44ce6e29631ecf443129c0334d01c0b`
- harness/manifest.json `e16609e14f5b0cc5e9805f1a0b2e66f99c2d8a450429c2dd2535abf8fbb83cec`
- harness-preparation-20261102T213445388959Z/receipt.json `1566655186013d56ed1c4b567c7423cba1cceed4136ed7238d917065bf357fd4`
- harness/adapter.py `b5b96b8eb8c1eccfec6d841e9a53724a49da610ca76145244e2a88be3453e9a1`
- harness/headless_proof.py `0cc928afd81310907e46e318f9aee7d299480f40192158a2203f4c26f896d4f3`
- harness/README.md `bc89a0ce8ff78dea98304682224d2f19de6bcc416c4181caebf1729a45b2afec`
- harness/run_checks.py `58a2a44691559f63f8b2d9dbc15aff20bf0afc094e6177d8d7cf78115bace03f`
- harness/test_adapter.py `31d20b69bd526eb589f40d2c691ef96b456e4bc127d6f6bbb6d5cae800c50d07`
- final_junit `1065ef2dab3f3f65e45359e5c916a87bd9bf8c040fc96a72a8c9b5178d79541a`
- source_before_after `4edf6caf3bd0cd1fc63df2602a27b9419692c01b877e38ae143288ad3525e3ce`
