# Task4C fix2 independent scoped review

SPEC PASS. QUALITY APPROVED. Original order wo-ultimaagent-20261101-0021. Caller manifest d4b73f6cf7731e149323d016c590a27656eefdd54d2fcf426d9b037e592168af. Approval applies to the reviewed caller preparation bytes. Execution remains unreleased.

## RC-08 · ADDRESSED

root-inert-invocation.py:332-371. Original inert_admit resolves the patched private module's load for authority and baseline (adapter.py:1080-1082,1087-1089). P1.no_reparse:21-27 returns the fixed absolute path. Lines 335-345 compare the actual read buffer against the issued bytes and digest, then decode that buffer. Other paths delegate to original_load(path). Lines 351-355 restore the loader even on original admission failure. Lines 356-362 retain the effective-state and operational-pin checks before headless continues. Lines 369-371 restore both private bindings.

test_root_inert_invocation.py:676-724,750-763. Both p4.identity and p4.listener_owner spies record their target before returning. Substitution at the later original authority read cannot reach PID 424242 or port 8756. The positive case proceeds to the mocked launch boundary at 18765. Pass-through and restoration are asserted.

## RC-09 · ADDRESSED

root-inert-invocation.py:402-413. One encoded result buffer supplies both the pending write and the expected publication bytes. The existing binary writer flushes, fsyncs and closes before the no-replacement hardlink. Reading the canonical path and comparing exact raw bytes now precedes return. Read failure or mismatch propagates and preserves the evidence and consumed allocation.

test_root_inert_invocation.py:727-747,766-785 exercise ordinary-file substitution after close, matching publication, and unreadable canonical readback. The adapted earlier close/fsync/collision tests still cover their original boundaries.

## Verification and limits

Verified the scoped review inputs, prior report and verdict, both report-prefix seals in ROOT proof, five current caller hashes, and the exact base-to-head contextual diff. Reviewed the full fix2 appendix and T4C-READ-02.

Independently reopened three exact command lines, raw stdout/stderr and JUnit. RED 4 cases, 3 behavioral failures and 1 positive. Targeted GREEN 16/16. Final unselected 84/84 in 12.87 seconds with 0 errors/skips and empty stderr. ROOT readback confirms 82 current pins and all 77 prior IDs retained. Independently rehashed all 490 raw copies across these three stages.

Inspected only the original two load sites and the returned absolute-path contract to verify the private hook's scope. Prior seven findings stay closed. No new finding in the fix2 diff. No suite rerun, runtime handshake, native operation or case execution.

Future adjudication requires actual process exit 0 and ROOT's independent comparison of canonical bytes with the expected serialization of the returned original record. A mismatch, unavailable readback or failed process leaves the allocation failed or unknown without retry. Real native identity, listener ownership, cleanup and physical timing remain outside this preparation review. E02/T2 NOT_PASSED. T3, Owner and production remain closed.
