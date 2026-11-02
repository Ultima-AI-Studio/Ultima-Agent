# Task4C fix1 scoped independent re-review

SPEC FAIL. QUALITY NEEDS_FIXES. Caller b05bbe5dca2acf9952c5d0fc36155ff5ab1099656ed0b1d0b3da6ded6786aafe, from 83a55d081afd4ca945b18284097885041737bdbf9ad40d0674f1b0394ec58dfd. Original order wo-ultimaagent-20261101-0021. Seven original findings addressed as specified. Two issues in the changed paths require a ROOT disposition before any release.

## Original finding dispositions

- **RC-01 ADDRESSED** · root-inert-invocation.py:86–89, 183–198, 207–210, 303. pinned_json hashes and decodes one buffer. Module digests, review-2 verdict fields and the historical identities come from those buffers. Approval and caller manifest already retain their input bytes. Tests at test_root_inert_invocation.py:428–440.
- **RC-02 ADDRESSED** · root-inert-invocation.py:272–278, 299–312, 338–339, 349–352. fresh checks the current release and dispatch pins and samples expiry after those reads, immediately before caller-level P4/native admission, original admission, and delegation. The original cleanup path retains its deadlines once admitted. Tests at test_root_inert_invocation.py:443–463, 645–656.
- **RC-03 ADDRESSED** · root-inert-invocation.py:3, 14–17, 130–133, 146–179, 251–255, 280–287, 395–406. Actual entry and UUID4 bind HELLO, release and the consumed dispatch. The exact GO hash identifies the dispatch. Memory consumption precedes fallible claim creation. Missing/unknown dispatch closure remains a ROOT-side denial. The caller cannot issue a replacement grant. Tests at test_root_inert_invocation.py:466–483, 567–600.
- **RC-04 ADDRESSED** · root-inert-invocation.py:289–290. Any existing inert namespace blocks before P4. Prior UUID, empty namespace and unreadable namespace are covered, as is a prior pending result. Tests at test_root_inert_invocation.py:486–500.
- **RC-05 ADDRESSED** · root-inert-invocation.py:313–327, 332–354. Original admission returns to the private wrapper before headless mkdir or Owned. Issued decoded authority and baseline, effective fixed port/folder, budget admission and raw pins are compared. The two mutation cases cannot reach the launch boundary. The original is restored in finally. The pre-return native query problem is separately identified in RC-08. Tests at test_root_inert_invocation.py:503–535, 603–613, 659–670.
- **RC-06 ADDRESSED** · root-inert-invocation.py:355–368, 378. Original returned failure is latched before supplemental checks. The later exception occupies later_veto; the underlying result/witness is preserved. Tests at test_root_inert_invocation.py:538–550.
- **RC-07 ADDRESSED** · root-inert-invocation.py:107–117, 385–389. The writer flushes/fsyncs and exits the pending file context before os.link publishes to the no-replacement destination. A write, fsync or close exception skips the link. A destination collision preserves the existing canonical bytes. RC-09 concerns what source is linked after successful close. Tests at test_root_inert_invocation.py:553–564, 616–642.

## New findings in the fix

### RC-08 · P1 · root-inert-invocation.py:338-345

The new wrapper detects changed authority only after original_admit has already used its unverified target fields. With port replaced by 8756, adapter.py:1086,1092 allows the value and calls p4.listener_owner(8756), which runs Get-NetTCPConnection on that port (P4 controller.py:248-250). Replacing only parent_identity.pid while retaining run/origin also causes p4.identity(unissued_pid) at adapter.py:1081-1082,358-363 before any wrapper rejection. No off-scope launch is needed for these off-scope native reads. The existing replacement test records only simulated launches in its assertion at test_root_inert_invocation.py:528-535, despite its mock recording listener query targets at line 103.

Required fix. Bind the actual input consumed by original admission to the issued bytes before any target-directed lookup, while retaining the effective-state checks after original admission. A separate path prehash leaves a reopen gap. Have ROOT rule on a narrowly scoped private read binding if needed. In pure tests record every native PID/port lookup and assert that substituted targets are never observed.

### RC-09 · P2 · root-inert-invocation.py:385-392

The successful close belongs to the file created at line 388. The hardlink at line 389 resolves its source by pathname again. Replacing the closed pending path with a different ordinary file during that interval makes os.link publish the replacement successfully. no_reparse permits ordinary files. The caller still returns its in-memory record and may exit 0, although the canonical bytes can differ from the witness it durably closed. The close-failure and destination-collision tests do not substitute the source. ROOT independent readback can catch the mismatch; the publisher itself does not.

Required fix. Bind publication success to the originally serialized result bytes and closed object. At minimum compare canonical bytes against the exact expected bytes before returning an eligible process outcome, require identical ROOT readback and preserve failure evidence without overwrite. If canonical presence itself must certify closed-source identity, use an identity-bound publication mechanism or a ROOT-owned enforced exclusion across close/link. Cover a regular-file source substitution after close in a mock.

## Evidence and limits

Verified all named input and caller-five SHA-256 values, companion input hash, immutable prior review, ROOT ruling, report appendix and contextual diff.

Reopened raw argv, stdout, stderr, JUnit and rehashed the 646 raw source copies. Stages 13/13 failures, 19 pass and 1 fixture failure, 31 pass, 77 pass. Final unselected with 0 failures/errors/skips, empty stderr. ROOT readback retains all 50 old IDs and reports 81 current pins.

Traced only the changed private admission wrapper into original inert_admit/bind_parent and the targeted P4 listener query. Examined HELLO/grant and pending publication by data/code inspection. No suite rerun or runtime invocation.

Read the complete fix appendix after the preserved 14,779-byte prefix. The earlier FAIL report and machine verdict remain immutable. The changed driver counts the additional protocol ruling, the template stays unreleased, and no code approval or execution authority is implied by the test count. Reviewed hashes appear in verdict.json. All runtime, native, model, profile, T3, Owner and production gates remain closed. E02/T2 NOT_PASSED.
