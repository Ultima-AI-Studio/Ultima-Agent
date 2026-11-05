# Same-reviewer closure: FIXTURE-SOURCE-ENTRY-01

User authorization call_8a6fef41fb9445a988111284dd48982b covers one independent
review and one fixture-only diagnostic only after PASS. No actual slot has been
consumed and no authority exists. The initial R1 package and NEEDS_FIXES receipt
remain immutable. This fixes the same reviewer's single P1 finding.

Review the delta in code/native_bridge.py and code/test_native_bridge.py against
R1. Preflight and postflight now use the unchanged pinned standalone candidate
guard, rather than legacy controller.source_check's package-specific inputs file.
The wrapper's existing verify_package still seals all local runtime dependencies.
Tests isolate the real legacy function definition and prove the absent-input
failure, correct source-guard routing and rejection propagation. Three cases
failed before the fix, and all 90 focused offline cases then passed. The actual
unchanged candidate guard also passed a separate read-only source check.

Verify fixed-package hashes, delta provenance and the guard's complete candidate
checks. Reuse the previous full wrapper review; examine the fix and any introduced
risk. Do not reopen unchanged input-origin review without a concrete new reason.
Return PASS or NEEDS_FIXES bound to this fix1 manifest and state whether the P1 is
closed. Root records your response with clear attribution.

Read-only shell/hash/AST inspection only. Do not import/execute the code or tests,
create windows, call model/audio/network, issue authority, write files, change
Git, or spawn reviewers. Product acceptance and live Windows behavior remain
unverified. A PASS permits only the single conditional fixture diagnostic; no
retry, E03 acceptance, E01/E02 execution or product/model call is added.
