# Task4C independent caller review

SPEC FAIL. QUALITY NEEDS_FIXES. Original order wo-ultimaagent-20261101-0021. C118 and the accepted six-file harness remain the review baseline. Caller manifest 83a55d081afd4ca945b18284097885041737bdbf9ad40d0674f1b0394ec58dfd. This is a preparation verdict. Execution release is false, E02/T2 NOT_PASSED, and T3/Owner/production remain closed.

## RC-01 · P1 · root-inert-invocation.py:141-145

The digest-checked harness manifest and the manifest supplying executable module digests are separate reads. If the manifest and adapter are replaced after line 141, checked_import executes the replacement using its replacement digest before the next control scan. The same check-then-reopen pattern separates the verdict and historical proof hashes from the JSON actually interpreted at lines 157–160 and 237–238.

Required fix. For each pinned JSON control, read bytes once, compare the sealed digest, and decode that buffer. Exercise a mocked second-read substitution and assert no unapproved definitions or identities are used.

## RC-02 · P1 · root-inert-invocation.py:229-240

Freshness is checked before the folder and release hash I/O, P4 loading, package and source scans, and historical proof reads. A valid 1-second release can expire during those operations. The 275-second work budget still admits P4 loading or the first native scan. The authority expiry check at line 257 only refuses later, after native effects.

Required fix. Recheck the bound release and its expiry at each admission to P4/native work and immediately before delegation, after potentially blocking prerequisite I/O. Mock a stall before the first such boundary and verify zero calls after expiry.

## RC-03 · P1 · root-inert-invocation.py:212-221,270-275

If the exclusive claim open raises before creating the file (for example a transient permission or sharing error), consumed stays false and the invocation exits with no terminal consumption evidence. The same still-current release can be used by another invocation once the error clears. Failed write/close after successful open is a different, tested case.

Required fix. Establish a durable one-use allocation boundary under ROOT control that fails closed even when the caller cannot create its claim. If the existing filesystem protocol cannot represent that failure, return it to ROOT for a protocol ruling before release. Include a mocked pre-creation open failure followed by replay.

## RC-04 · P1 · root-inert-invocation.py:223-231

The exclusion scan checks three canonical files and only the newly generated UUID directory. An existing V/inert/<different UUID>/attempt.json with missing global markers is ignored. The new UUID selects another attempt despite the requirement to refuse existing attempt evidence.

Required fix. Check the fixed inert namespace for evidence of a prior attempt under any UUID before P4 entry and fail closed on residual or unreadable state. Add a mock for an orphan attempt with a different UUID and preserve its bytes.

## RC-05 · P1 · root-inert-invocation.py:248-265

After creating the baseline, the caller binds a reread from disk. After creating authority it never compares the canonical authority to the exact bytes it issued. check_controls omits both dynamic objects. A change from port 18765 to 8756 in this interval survives adapter.inert_admit (adapter.py:1081-1095 permits this port). The harness can pin the replacement as its initial operational state and use it unchanged. Even a complete subsequent witness proves only the admitted port. The test at test_root_inert_invocation.py:182-187 reads an undisturbed authority.

Required fix. Bind both documents to the exact serialized bytes generated in memory and protect those bindings across handoff through actual harness admission, with no writable substitution window. Confirm the existing trusted admission/witness uses those bindings. If that requires an interface change, seek ROOT ruling before editing the accepted harness. Test a replaced authority before admission and require zero off-scope launches.

## RC-06 · P2 · root-inert-invocation.py:265-280

An ineligible witness can return with the original failure in inv.budget.failure (adapter.py:1003-1011). If a subsequent controls check raises, first_cause is set to this later exception. Line 279 then skips the original failure, although the two failures have different causes and times.

Required fix. Capture the returned original failure before supplemental checks and keep any later control failure as a separate veto. Cover the combined ineligible-witness plus control-drift case and preserve the returned witness verbatim.

## RC-07 · P1 · root-inert-invocation.py:79-89,281-288

The final eligible JSON is written directly to its canonical path before flush/fsync and close succeed. A flush that exposes all bytes followed by fsync/close failure can leave a complete parseable ELIGIBLE_FOR_ROOT_REVIEW result even though publication raised. The claim prevents a retry but cannot tell a later reader whether result closure succeeded.

Required fix. Prepare and durably close a new outside-case result before publishing it atomically with no replacement, or have ROOT define equivalent independent close-success evidence. Reject orphan and uncertain writes. Mock a failure after all bytes are visible and require no consumable canonical eligible result.

## Evidence and limits

The diff covers the five new caller files, including the false template, immutable dependency manifest, preparation driver and tests. The intended path samples its monotonic origin before case I/O, adopts it through Deadline.adopt_parent, installs the verified adapter temporarily for headless.a and delegates once. No replacement native controller, new model route or automatic retry appears. Direct inspection of P4's protected alias and P1.identity confirms the returned FILETIME integer comes from GetProcessTimes. The initial native timestamp precedes the first scan. RootInvocation returns the enclosing observer's witness after package inspection. These couplings do not resolve the admission and persistence findings above.

Reviewed the complete requirements and author report, exact five-file diff and named input hashes. ROOT's separate evidence readback records 75 fixed dependencies and 80 matching current pins. Independently checked each stage's exact argv, raw output, JUnit counts and 80+80 archived copy digests. The retained stages show 1/1 failed, 4/9 failed, 9/9 passed, 49/49 passed, then 50/50 passed with no selection, errors or skips and empty stderr. The initial RED covers a late claim after creation. The first follow-up failed on fixture binding. The first three receipts omit a separate pytest exit and launch count. No additional test or runtime call was needed to trace these findings.

The named interface checks were confined to Deadline/RootInvocation, headless entry/import, P4/P1 identity, schema/operational pins and the returned witness/first-failure contract. No code, test, harness or canonical runtime object was modified. Actual runtime behavior, native precision on this host today, launch, physical cleanup and OS persistence remain unverified. ROOT alone owns the next ruling.

Schema addendum SHA-256 fd7b0e350a3bbde93d43bf44f67754bec484089739e6b6d37110988d1bf6fa1b. The machine verdict contains canonical spec/quality and matching aliases. Full input hashes are recorded in verdict.json.
