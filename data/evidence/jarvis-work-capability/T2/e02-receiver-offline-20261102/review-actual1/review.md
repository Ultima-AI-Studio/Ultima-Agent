# First offline receiver attempt: independent evidence review

SPEC: PASS. QUALITY: PASS. Scope: truthfulness of the first failed attempt, preservation, cleanup accounting and closed budget only. This is not an execution-success or product-acceptance certificate. No blocking findings within that scope. E02/T2 remain NOT_PASSED; the original goal remains INCOMPLETE.

## Verification and provenance

Read-only review of root-actual-r1-packet.json and its 11 bound raw files; all 11 SHA256 values and byte lengths independently match. The missing controller-r1/terminal.json is still absent. All 775 preparation-r3 manifest bindings independently match current bytes and the 775 recorded bound-hashes-after values. Both boundary files are byte-identical (SHA256 9f267343551298cb31a462421d026d6019f9f728d245dae792b30309110bd4d4). Source21 has 21 unchanged bindings; recorded C/H heads remain 244d2120abcd6b8d7744f74a05bd22de46a2d3a5 / 0a31d84169ba8e151ec2f9a2c6fea958804daa5b. Review-readiness-2's nine bindings independently match; its earlier preparation-only PASS does not imply this attempt passed. Readiness-1 REVISE remains historical and unreplaced.

Only ordinary file reads, SHA256 hashing, JSON parsing, integer/date formatting and static source inspection were performed. No Python, SDK, lexer, probe, controller, product, model, network or process experiment; no runtime repair, process inspection/action, subagent or old-artifact edit. PowerShell JSON parsing for precision checks explicitly used DateKind String to preserve the seventh digit rather than its automatic DateTime conversion.

## Findings

1. **Mechanical preflight INCOMPLETE; no representation observation.** The unchanged 411-byte result.json (SHA256 93ae2ce6d585bad2acf739a9ddb718ebc1b87a24ff1267d1a784e165da4ea5ca) records ValueError('Protected5 unverifiable or changed'), elapsed 0.2999388000171166 seconds, boundary_unchanged=true, all_bound_hashes_unchanged=true and prohibited_attempts=[]. run_probe.py lines 567-572 save/check the boundary and require every protected identity before calling run(manifest). Lines 576-600 preserve INCOMPLETE and write after-boundary/hash evidence. No lexer/receiver/S3/S4 comparisons were entered; comparison count is 0. The generic boundary_error does not establish actual drift. This result establishes neither a representation defect nor a model failure, and does not satisfy E02/T2.

2. **Deterministic timestamp-precision incompatibility explains this specific preflight rejection.** process_identity (lines 147-151) formats the native FILETIME with all seven fractional digits and compares that string exactly with a baseline whose seventh digit is zero. Independently converting the five saved integer FILETIMEs gives precisely each boundary-before/after actual timestamp and matching executable; truncating only to common microseconds gives exactly the legacy runtime-before baseline, root runtime-before and recorded CIM values. All five exact-string verified flags therefore correctly remain false under the implemented predicate. This diagnosis does not rewrite the baseline, flags or result. No observed process change is needed to explain the rejection. The old baseline cannot establish historical submicrosecond equality beyond its recorded precision; continuous liveness is not independently certified here.

| PID | Native FILETIME | Full native UTC | Legacy common microsecond UTC | Discarded 100ns ticks |
| --- | --- | --- | --- | --- |
| 12796 | 134378998103213233 | 2026-10-31T05:56:50.3213233Z | 2026-10-31T05:56:50.3213230Z | 3 |
| 492 | 134380046658027655 | 2026-11-01T11:04:25.8027655Z | 2026-11-01T11:04:25.8027650Z | 5 |
| 37880 | 134380046658262507 | 2026-11-01T11:04:25.8262507Z | 2026-11-01T11:04:25.8262500Z | 7 |
| 32856 | 134380102909908255 | 2026-11-01T12:38:10.9908255Z | 2026-11-01T12:38:10.9908250Z | 5 |
| 18068 | 134380102942151021 | 2026-11-01T12:38:14.2151021Z | 2026-11-01T12:38:14.2151020Z | 1 |

3. **Controller cleanup was scoped; controller normal completion is unproven.** identities.jsonl has one initial retained-handle identity: redirector PID6268, parent28316, creation_filetime134381003428540356, terminated=false, absent=false. It is not a terminal receipt. The historical actual base-Python identity was never captured. Empty stdout/stderr and absent terminal do not prove a normal Python or outer exit. Root's contemporaneous resolution records no matching live probe CLI before stopping, exact controller exe/command/parent5656 plus native creation_filetime134381003409629751, successful termination of its retained handle and that exact handle signaled. This supports the recorded stop of the verified own outer controller only; the review did not rerun any process query or termination. The subsequent empty known_remaining/probe_matches rows support observed follow-up absence, not retrospective exact identity/exit proof for the uncaptured base child. Python/protected/unknown termination count remains 0; own outer stop count is 1. Protected5 preservation is supported by unchanged native observations and matching common-precision before/after readbacks, with the historical precision limitation above.

4. **Exact outer stall cause remains UNKNOWN.** Static controller code includes discovery/capture, native waits, watchdog and stream-copy phases, but no terminal/phase trace establishes which phase stalled in this attempt. No unique cause, successful watchdog cleanup or normal controller exit is inferred. Precision-label caveat: raw controller FILETIME134381003409629751 converts to 2026-11-02T13:39:00.9629751Z; the resolution's created_utc=2026-11-02T13:39:00.9629750Z is its CIM-common value, also explicitly present as cim_common_microsecond_utc. Treat the raw integer as native identity; do not describe that created_utc string as full-native precision. This is a nonblocking documentation distinction because raw identity and exact-handle signaling are retained.

5. **First-attempt budget and acceptance accounting are honest and closed.** Actual batch attempts1/cap1 CLOSED; comparisons0; new model/POST0; product/source10/SDK/default/queue/frozen edits0 as recorded and consistent with the early code path and preserved bound bytes. This review makes no independent exhaustive audit of unbound system state. root-one-batch-authority retains old source9 count9/cap9 CLOSED and oldprefix posts3/cap4 CLOSED. Four inert guard invocations are prior infrastructure evidence, not actual representation comparisons. Existing E01/E03 source9 acceptance is retained in scope, not retested or enlarged. Product integration/source10, T3, another actual attempt, model retry and 14B/larger remain unreleased; current8B-only restriction is retained. The original first-result bytes, false verified flags, missing terminal and incomplete historical child identity remain visible.

## Smallest future engineering step (UNEXECUTED)

If root separately authorizes a future correction and its budget, first specify an immutable native-FILETIME/executable baseline and exact identity comparison semantics with a pure saved-data check that distinguishes legacy microseconds from native100ns. Do not mutate the old baseline or accept its missing native digit by assumption. This recommendation releases no actual run, model call, process action, product change or acceptance relaxation. Root may also close this tooling branch; that decision is outside this review.

## Key bindings (SHA256)

- root-actual-r1-packet.json: 9ec5ae272ea1d200abfa274aa3e37dd42c8a5b6a092017eb972141759f080659
- root-first-attempt-resolution.json: a44e5f7a4e6bd5663abc4206f98bdff11037ae74d8c027af60e75a79ee59ff97
- root-runtime-after-actual-r1.json: 6ec32088465ff0a3ea32718fd02262cecc2b9b3ee7688256024488a689d18dd6
- actual-r1-closed.json: 783b0b1c04d1abee6789d863b8c710d4114b860d90f7f80f59b893348c601957
- preparation-r3/manifest.json: 0795df4c9e0c173395c8a8ce7e425313f9deb8f4393faa7ec03999474ba05111
- preparation-r3/run_probe.py: b4e30f7f1c91d03024b5bd1005429c0328164a059b365211c05baf0d857f52b5
- preparation-r3/outer_controller.ps1: b8c1046e445a72360b685acce596e6b82c72ddd0451257d734b8ec47c0ffde89
- review-readiness-2/verdict.json: 1b6dc782b2b93a7e8adb6434da77c716bc95968b57748c73fb12276f893face3
