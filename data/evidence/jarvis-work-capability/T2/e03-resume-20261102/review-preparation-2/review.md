## Independent review of preparation-r2, fix 1/5

**SPEC FAIL. QUALITY FAIL. Five groups addressed, two open. actual_release=false.** T2 product exit NOT_PASSED. Root reports the repair queue EXECUTING.

**SPEC1 ADDRESSED**. Lines 47–88, 97–105, 350–383, 396. Canonical, short-lived admission and native/source/protected preflight precede owned UI for both paths. Positive health follows the required fixture policy. Admission is reread before CLI and native identity is rechecked after work. Root ordering is sufficient.

**SPEC2 ADDRESSED**. Lines 309–329, 384–407. Once case work starts, timeout, nonzero exit, malformed result, absent inference and readback errors all enter the pre-teardown capture path. Outputs, attempted live window read, raw logs, separate product JSON when present and any returned completed events are retained. A missing product response gives no observed completions and no reliable total. Overall failure survives cleanup, independently of product success. Correct interpretation of a later conflicting observation is still open under SPEC3.

**SPEC3 NOT_ADDRESSED**. Lines 254–296, 330–347 substantially repair fresh capture/selection/ID, call and send evidence, exact output set, service/file matching, windows/caret and negative focus/range refusal. Remaining blocker B2: independently observed later contradictory bytes are ignored. The inventory path set alone is compared. The last owned window/output effects are also collected but their contents are never reconciled with the successful readback before terminal PASS. The independent file/target consistency requirement remains open.

**SPEC4 ADDRESSED**. Lines 206–217, 369–383 check unique OS listener, retained identity, exact service argv and owned roots before trusting health and again before CLI. An unexpected owner fails closed. Fixed server arguments are distinct from the Chinese work query issue under QUALITY2.

**QUALITY1 ADDRESSED**. Lines 24–40, 219–239 require canonical UUID4, strict lexical and resolved direct task parent, absolute path, reparse and alternate stream checks before result-directed file read. The original absolute-task escape fails lexically.

**QUALITY2 NOT_ADDRESSED**. Lines 124–204, 384. Retained launcher times, exe/argv/creation checks, exited-launcher discovery, observation-only conhost, exact identity termination and overall cleanup failures fix the first-round ASCII cases. B1 prevents reliable discovery and cleanup of an actual Chinese-argument CLI after launch. Direct-parent-only scanning also does not detect an unknown process below the already-discovered base interpreter; such an auxiliary must at least fail cleanup if present. The genuine headless proof covers direct redirector/base-child identities and real child exit, while the unseen live-child branch is simulated.

**QUALITY3 ADDRESSED**. Lines 47–88, 410–413 bind the canonical authority/ledger/preflight/preparation review to the current package and root-issued schema. They enforce ordered preconsumption, exact siblings, predecessor terminal PASS with successful cleanup/boundaries, and separate matching independent factual/target/file/mechanical reviews. This is within the documented root-controlled filesystem trust model.

### Fix-induced breakage

**B1 P1**. R2 exact argv comparison consumes P1 process_snapshot stdout using UTF-8 errors=replace. The selected Windows PowerShell pipe actually emits GB2312. A fresh bounded CIM query filtered only to the pinned Python probe process returned its Chinese argument exactly when decoded as GBK and corrupted it using the P1 decoder. R2 candidate_valid compares that corrupted value to the original Unicode query. If the child is present, it becomes ambiguous after Popen has already dispatched, its identity is omitted from the termination set, and ownership/cleanup cannot be assured. Record own-argv-proof.json includes the raw JSON bytes and both comparisons. Require lossless OS argv transport and exercise actual Owned.launch/discover/cleanup with the Chinese/multiline arguments using a harmless headless process. Keep ambiguous identities outside termination authority.

**B2 P1**. The first independent raw hash is checked against the service. A subsequent output_inventory detects new raw bytes, but mechanical compares only the pathname set (260). A controlled pure call using the existing valid R2 test fixture plus a different later SHA returned mechanical PASS. The final effects snapshot also can contain a different file hash/set, text or caret without an errors entry (392–406). Match every required final, actually observed state to the accepted evidence, or record overall FAIL/unknown with the conflicting observations preserved. Do not infer any mutations occurred on this host from this synthetic reproducer.

### Reviewed evidence and limits

- controller_sha256 9f030a8f7a272b6cdc11978412cbab4c7c940fda09928eab7c8776565bd2a9b4
- manifest_sha256 a49a7281e1cc73ade42fe95c96cdbaceffb07fd62bf36b387620cf715da9a6ed
- diff_sha256 1251d84707a08213aedda4c55aec881622973f6487933c25807d130338704cef

All 15 manifest file/diff/verification bindings rehashed. Existing R2 receipts report 80 focused passes and two final headless cases. No unchanged suite rerun. Only the two named local probes were executed. Their SHA256 values are in review.json. A successful ASCII headless run cannot establish that the Chinese argv transport is lossless. Factual/live E03/E01 acceptance remains unverified.
