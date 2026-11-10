# Independent preparation review — NEEDS_FIXES

Candidate `47ac3a464ca15e01311d5739eda53b2a32d8783c`, parent `0421a54cab572be013c3f7ad562e86406bfe8e52`.
Frozen manifest SHA256: `05b21259b4ebdf52b987b8a49a3063cc4c6cb642b726d204744c358bcf6f7bf8` (1383 members).

## Strengths

The rejection branch preserves the original exception, v4 fallback and public metadata-only summary. Full canonical packet sizing preserves the 16384-byte cap and original pages. Raw response hashes bind to the native receipt; FULL evidence is remeasured and reparsed. Write-before-ACK refusal remains an actual committed write with zero acceptance credit. Legacy v3/v4 remain closed.

Independent readback verified 969 distinct JUnit cases (965 product + 4 compatibility), 20 identical-source groups, 131 native and 41 structure cases, no green failures/errors/skips. Initial 27 RED and supplemental 6 RED assertions remain, with no collection errors. The scanner correction matches the existing password_assignment regex; it does not expand scanner coverage. Maximum recorded group duration was 73.138739 seconds, peak overlap 2, configured timeout 90 seconds. All 1567 dependency pins, 15 unrelated files, 77 current source files, parent/candidate identities, N19/N21 manifest/result/seal members and last_actual_result were independently checked. Seven protected identities match only at recorded checkpoints.

## Issues

### Important — PREP-STATE-01 (P2)

`src/brain/work_research_diagnostics.py:450-453,481-505` does not close the relationships between content type, JSON status and retention mode.

For a valid snapshot with content=123/null, the builder produces NON_STRING, null length/hash metadata and UNAVAILABLE evidence with no fragments and omitted_chars=null. A change of JSON status to UNAVAILABLE still passes the non-COMPLETE branch: only NON_STRING implies non-string, with no converse. Independently changing retention mode to OMITTED_POLICY or OMITTED_BUDGET still passes: null omitted_chars matches the expected null count and the final mode branch only checks for empty fragments. An unencodable string also permits either omitted mode despite no scan/budget operation being possible. This follows directly from the current branches; the reviewer did not execute product code.

These contradictions misrepresent whether text existed and why it was withheld, undermining diagnostic evidence. They do not demonstrate a write/ACK acceptance bypass.

Require NON_STRING iff content is not a string, and UNAVAILABLE evidence iff content is non-string or its UTF-8 measurement is unavailable. OMITTED_POLICY/BUDGET must refer to an encodable measured string and have no fragments. Keep JSON UNAVAILABLE available for actual parsing failure on string content, including safely retained encodable text. Add negative state-mutation cases and preserve legitimate parser-unavailable positives. A new candidate and fresh evidence/review are required; this review cannot approve changed bytes.

Critical: none identified. Minor: none identified.

## Declined to judge

- Actual E02 model behavior, improvement, T2/Owner acceptance and result review: No actual/model/result-review allocation; no new actual response body exists.
- Publication/closeout scripts and final local documentation/mirror readback: closeout.py, publish.py and closeout-static-readback.json are outside frozen manifest and not executed; final publication readback remains the main session responsibility after fixes and a fresh review.
- Continuous process liveness and operating-system packet absence: Only recorded before/after identities and Python offline audit were available; no process operations or OS network measurement authorized.
- Dynamic reproduction or rerunning product checks: Explicit read-only review prohibits product imports and test/profile/entry execution; assertions above are static, recorded test results were independently parsed.

## Assessment

Ready to merge: No. Verdict: NEEDS_FIXES. The frozen package is well preserved and its recorded offline checks are internally consistent, but v5 state consistency must be fixed before preparation approval. Actual run authorization is false; actual/model/result-review allocations and acceptance credit remain zero. No E02 improvement, T2/Owner pass or old E01/E03 credit transfer is granted.
