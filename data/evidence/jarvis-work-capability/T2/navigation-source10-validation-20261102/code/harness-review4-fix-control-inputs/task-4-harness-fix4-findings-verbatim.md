# Task 4 · fix3 independent scoped re-review

**SPEC FAIL · QUALITY NEEDS_FIXES.** Three of four attempted remedies are addressed. F1-N01 remains open because a declared text field can be replaced with an integer carrying the same scanner-positive digits. This crossed both real verification boundaries in a read-only synthetic check. There are no additional findings. Candidate `118ba152b007c30d358c8bc44c51aabe8ae820f0`, base `e16609e14f5b0cc5e9805f1a0b2e66f99c2d8a450429c2dd2535abf8fbb83cec`, reviewed harness `84b85517f7aafe985d0c33a354ba3b5f9736ecb64f6e52d9da6eb9520a7bdcc3`.

## Dispositions

### F1-N01 · Important · NOT_ADDRESSED

adapter.py:608–615,644–659,683–685; test_adapter.py:1005–1019,1050–1065

The two previous string-valued counterexamples now fail before publication and actual serialized slots reject duplicate keys. The remaining numeric exemption is still based on the supplied value's Python type in the generic prose walk, without checking that the producer permits numbers at that field. Pinned SDK core/types.py:125–130 declares ToolResult.content as str, tools/file_write.py:201 returns success text, and candidate src/brain/work_tools.py:511–514 copies it directly into execution.files[0].result. The confirmed synthetic baseline has a string there. Replacing only that field with the reviewed scanner-positive digit sequence as a JSON integer, or with an unissued object containing that integer, passed original verify_runtime_packet and all fix3 checks and reached the mocked raw publication boundary. The exact decimal digits are preserved; the same digits supplied as a string were rejected. This is malformed evidence the harness would preserve, not an observation of malformed product output.

Require the producer-declared type at the field before scanning. More generally, allow unscanned numeric/bool/null/container values only where the producer contract actually permits that type, including nested data not fully checked by the original replay. Keep free prose as text and keep decoding confined to the declared serialized slots. Add original-replay-positive, publication-negative controls for numeric and object substitutions at a text slot, beside the existing genuine/export and string controls.

### F2-N01 · Important · ADDRESSED

adapter.py:644–673,674–680,698–707; test_adapter.py:1021–1036

Decoding of SDK observations is now limited to the expected alternating user turn after an assistant turn. Native assistant envelope content is decoded at its producer boundary; final_answer itself is scanned as prose. The previously rejected clean 'Observation: the report is complete.' ACK passes genuine replay, export, and independent readback. Candidate agent_server.py:559–569 and work_research.py:763–764 corroborate the transcript positions.

### F2-N02 · Important · ADDRESSED

adapter.py:826–842,1009–1013; test_adapter.py:1079–1085 and closed-witness empty-task-directory parameter

The inert witness checks for any first descendant rather than counting regular files. Missing/empty output root is accepted; a file or empty task directory is rejected. lstat/open/iterator admission share the deadline and the iterator closes in finally. The otherwise-valid substantive inert mock has an empty-directory counterexample.

### F2-N03 · Minor · ADDRESSED

adapter.py:793–824,943–949; test_adapter.py:1038–1048,1067–1077

The observer reserves exactly the regular fixed root seal-index.json and charges all other files against the same 256 DATA limit as the writer. The observer still hashes the index and compares the observed set against indexed members plus the fixed index. 256 DATA plus index succeeds, 257 DATA fails, nested/suffixed/other lookalikes count as DATA. The minor RED TypeError was a missing interface, while the final controls exercise actual writer/observer behavior.

## Checks and limitations

- Read scoped requirements, prior findings, full new author appendix and the e166→84b8 contextual diff once. No broad review, Git action or unchanged suite rerun. Inspected only named producer couplings for the typed result and SDK transcript positions.
- Rehashed companion-listed inputs and six live harness files; matched six final source copies and all 64 current pinned inputs. The final receipt recorded fixed H Python -B -X utf8, pytest with no -k, driver/pytest exit 0, stdout 162 passed in 27.96s, empty stderr, JUnit 162 cases/0 failures/errors/skips and equal source-before/after digests. The sealed root check records six stages and all 145 prior IDs.
- Pure targeted check of the missing declared-type guard used H Python -B -X utf8 with final archive temp/test_fix1_genuine_synthetic_ex0, read-only synthetic runtime, issued snapshot, independently frozen inputs and collection. The real pinned scanners and export_completed protocol+structure checks ran in memory. Only final preserve_completed_members was replaced by a publication marker. Console results: sentinel decimal round-trip exact=True; scanner-positive=True; baseline reached publication; string control rejected ValueError Unsafe export decoded value; wrong numeric type reached publication; wrong object type reached publication. No raw member was written. An audit hook denied writes, connect/bind and process launches during the probe. Candidate import emitted its existing voice-reference fallback diagnostic; no audio device, playback or capture was invoked.
- The counterexample concerns acceptance of malformed bytes. It does not claim that the pinned normal SDK emits an integer result, or that unsafe material was published in this review.
- The 17 previously closed findings retain their disposition. No separate new fix-caused regression or out-of-scope finding is reported. Historic RED source/field limitations remain as recorded.
- Only the current 8B digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330 is in scope. Actual/inert timing, owner/production, original-corpus profile, original case, real-network and later same-candidate acceptance remain unreleased and unverified.

Held closed: H01, H02, H03, H04, H05, H06, H07, H08, H09, H10, H11, H12, H13, H14, H15, F1-N02, F1-N03. E02/T2 remains NOT_PASSED. Execution release is false.

## Reviewed SHA256

- companion `214d932d787439ca8684a068c5da850e5255f2fb92304caf81d92ec4ba724b4c`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix3-rereview-brief.md `11f8a19e4ac76e6a42a7f8d21af450344f582f86052d2cf901b9fbc6580daa98`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix3-review-package.txt `fc4b790a6342207529a0d540f262f727a6405c4b81913f2a43e0375de244a682`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-adapter-report.md `51cd77d1d09527bc26462724e2ee07191e3378e895c23a49ccc3d96ab4f09269`
- jarvis-work-capability-delivery-plan-20261101/task-4-navigation-harness-fix3-brief.md `60eea6e2f678479733e0c173b23fcf9a75678bec133da82a5080ceeba2d323ca`
- harness-review-3/verdict.json `8f6fb218f9ab5671ac45650ce7a3461e95b2de19e868214e6622d878024085b5`
- harness-review-3/review.md `38d49ba31373f9ef17ba2f7b1568df187e680798ab5c236cf6a3e54feb477578`
- harness-preparation-author-r4/report.md `6f9926ac5819579c80367fa2c510fe0f9654839e3a6b185d9e66219bc1a56168`
- code/root-harness-fix3-before-review.json `246d2425112cbc340bb45cc17ffe57c8aba2777da1a157be71e767d6a2ef8e60`
- harness/manifest.json `84b85517f7aafe985d0c33a354ba3b5f9736ecb64f6e52d9da6eb9520a7bdcc3`
- harness-preparation-20261102T215807022506Z/receipt.json `d34ab34e7a9bd5253983577d8d73904ab90a460a2f2cc21398f381596d688825`
- harness/adapter.py `25f3befa2f3a9e5ccf66bdbf1bb954019de4296e3ea2ddf76f13f54230618093`
- harness/headless_proof.py `0cc928afd81310907e46e318f9aee7d299480f40192158a2203f4c26f896d4f3`
- harness/README.md `f7db0b2991e7df040960d40641fd8c1bf53bc3f0027b679796a4ee06d0a90e75`
- harness/run_checks.py `6f2c3267c75e0f0b83e39353518769051f72fd464016b17767a71d6a158bf511`
- harness/test_adapter.py `5b96ffec0a2b4c0ac329bebda0062996ba07fdd126ae144e9e22417bea99a1e3`
- final_junit `f008ffc89c6665704c94f276208abbc23d06834ddf95ee5911bd709ba01365e2`
- final_stdout `9029ab9b27fa2d469416811bca584565805ee0eed04d40bb4f292d490e6e695f`
- source_before_after `4edf6caf3bd0cd1fc63df2602a27b9419692c01b877e38ae143288ad3525e3ce`
