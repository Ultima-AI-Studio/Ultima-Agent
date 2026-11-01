# T2 cumulative repair 5 independent scoped code re-review

**Scoped CODE APPROVE.** I1, I2 and I3 are ADDRESSED. No new Critical or Important finding in this fix. This approves only the bounded repair from `30b6b145c607adaf39f46e3764d356c94a698600` to `b6ab85b54f638594ccd7adcd792362bd4ff0a8fe`. The prior source4 review continues to stand for unchanged code. This is not full-branch re-review, T2 acceptance, semantic/live PASS or Owner/freeze release.

## I1 — ADDRESSED

The Pygments full-source scan now retains the next significant token after the selected range. A witness ending at the closing call parenthesis without a terminator is accepted only at a conservative recognized boundary. A subsequent method body brace, member continuation or argument continuation is rejected; intervening comments and whitespace do not conceal it. The class/object method regressions span JS/MJS/CJS/TS; TS interface signatures remain rejected. Complete return/assignment/await witnesses remain covered. This fixes the reported method-header acceptance without introducing a lexer or general parser. This limited syntactic witness is not a proof of semantic entailment.

## I2 — ADDRESSED

Code and source-local limitation evidence now require displayed text to equal raw decoded body, reject HTML projection, and reject separators other than LF/CRLF before using AST/token coordinates. Both exact form-feed and U+2028 counterexamples are covered. Normal LF/CRLF tests check rejection of a truncated multiline statement and acceptance of the full visible span, preserving the original decoded-body digest. Documentation projection is unchanged. The repair fails closed rather than changing the retained source or silently translating its coordinates.

## I3 — ADDRESSED

WorkService obtains one outcome_snapshot pair after separately capturing SDK-returned results; an earlier exception obtains that pair only if no cutoff exists. The existing helper deep-copies records and report effects under the same ledger lock. Success verification, error classification and final response assembly use that detached pair; no later ledger read replaces one half. SDK results and terminal ledger records are assembled separately. Success now returns its completed effect and private report/file identities. The deterministic compose-error-read barrier permits the timed-out worker to finish after the fixed cutoff: later completion does not change the returned pair or turn timeout uncertainty into success. Prior before/after-intent, partial-write, two-request isolation and generation-stop cases remain retained.

## Independent evidence readback

Read the specified brief, verbatim r4 findings, latest repair5 report section and the generated 3-file diff once. Additional code context was limited to the complete JS witness function cut by that diff and the existing locked snapshot helper. No git command or suite rerun was used.

Independently hashed candidate-readback.json as `f7fed18834e32dc083e189e21b5fdd62e97fb45da1d5293fad83ee3d0ccb143f` and source-candidate.json as `b8e3f543b8fa7bc5dcac6e24fa3990a1e18afe26df736312227a4156da69b4a9`. All 20 manifest inputs match current files; before/after covering and candidate hashes agree. Source-before matches the prior candidate. Exactly the three permitted files differ between those input manifests. RED test digest equals the current test digest. The binding design SHA256 is `7fe32a4bff35683d66d7900ea35d285a111209247ae5aec4edee14d9d2fa81bd`; protocol remains `d641bd1a9e287b48d8a21413cb9c8574e9ca118ae38c17d50b8652b5a5e4f83c`. Commit/blob identity relies on the retained candidate readback; git was deliberately not rerun.

Parsed raw JUnit testcase identities and exit receipts: targeted RED 13 failed/9 passed, exit1; same targeted GREEN 22 passed, exit0; covering209 and isolated compatibility8 passed, exit0. Final XML has no failures/errors/skips, 217 unique identities, all195 prior and all60 T1 identities retained. The 22 new identities exactly equal each targeted XML set. Existing voice-reference fallback and anyio warning are retained. All9 key receipt hashes in candidate-readback match actual evidence files.

Reopened four offline probe artifacts beneath their recorded task roots and checked file presence and SHA256: success/succeeded/CLI0/two generations; unsupported/failed/CLI2/one/absent output; postcommit/needs_attention/CLI2/two; partial/needs_attention/CLI2/one. Successful effect is completed and references exactly one file and report terminal record. Independently checked the six donor witness texts against the hashed stored source bodies; retained donor pack is21,229 characters. Protected before/before-covering/after/postcommit receipts exactly match prior protected identities for PIDs492,37880,32856,18068 including executable and creation time. This is a retained-receipt check, not a fresh process health claim.

No additional focused test was needed. No model/network/UI/audio/microphone action, source/index/branch/queue/production mutation, restart, subagent or default change was performed. Only this review directory was written. Product model remains qwen3-8b-uncensored. Real current-candidate8B E02 remains unrun and unreleased; historical E02 failure is not overwritten. No14B or Owner/freeze approval is granted.
