# T2 cumulative repair 4 independent code review

**Specification REVISE. Code REVISE.** Reviewed net diff from `c6bcc3ca84d9fb46567b0895d8d12d5c78181e36` to `30b6b145c607adaf39f46e3764d356c94a698600` against the exact approved design and fixture ruling. No Critical findings. Three Important findings block this code gate.

## I1 — A JS method declaration passes as an executed call

`src/brain/work_research.py:267-281`

For class Queue {\n  dispatch(item)\n  { return item; }\n}, citing only line 2 with symbol dispatch and claim Calls dispatch is accepted by the exact candidate. The previous token is {, and validation stops at ) without checking the following method body. The special-case exclusion at line 267 covers only .ts. The same gap affects .js/.mjs/.cjs. This violates the requirement to reject signatures even before independent semantic review.

Use adjacent full-source token context to rule out a declaration or statement continuation. Fail closed on ambiguous spans. Add the class-method regression while retaining supported return/assignment/await witnesses.

## I2 — Projection and syntax coordinates can bind a claim to a different line

`src/brain/work_research.py:173,205-206,232`

The projector uses splitlines(), the JS witness counts only LF, and Python AST positions follow Python's physical line rules. One no-I/O probe on candidate code accepted a JS source containing '// heading' + U+2028 + '// note' + LF + 'const x = queue.dispatch(item);'. Citing only L2 returned the evidence text '// note' for the claim Calls queue.dispatch. The analogous legal Python source '# head' + form-feed + '# note' + LF + 'x = queue.dispatch(item)' accepted L2 with evidence '# note'. This links a different source span to the claim and survives deterministic re-render.

Use one language-correct coordinate mapping for displayed lines, token/AST boundaries and receipt excerpts, or fail closed on ambiguous separators. Keep the original decoded body hash and verify selected visible text contains the whole eligible statement. Add both regressions.

## I3 — Returned terminal records and effect observations can come from different instants

`src/brain/work_service.py:94-98,128-136`

The runner return freezes terminal records with ledger.snapshot() and appends them to tool_results, then a compose error takes a second outcome_snapshot(). Once tool_results is populated, terminal records from this second read are discarded but its effects are returned. A timed-out worker reaching intent and completing between those reads yields a snapshot that includes its newer file intent yet omits its terminal result already present at that same observation. On success the completed effect is omitted altogether, as the retained offline success receipt confirms. This misses the approved single detached snapshot including effects.

Capture terminal records and effects together under the ledger lock at a single response cutoff, use the same pair for status and output on both paths, and keep SDK-returned results separate when assembling the response. Add a deterministic between-snapshots worker completion regression.

## Verified scope and evidence

The 70,682-byte review package covers eight files. The copy borrows the secured/instrumented engine inside the existing ask lock, preserves NativeReAct/tool construction and restores bus subscriptions in finally. The wire checks reject invalid envelopes before tool consumption. Caller-thread/binding filtering, the pre-generation latch and the separate pending/intent/error transitions support the tested one-failure stop and conservative timeout classification. The delimiter edit preserves canonical/explicit input handling. The harness changes only manifest metadata. Fixture migrations preserve existing intentions. The 24,000-character numbered pack and retained 21,229-character donor pack were reviewed. No syntax gate establishes semantic entailment.

All 20 input hashes matched the current checkout and before/after covering manifests. Design, protocol, source-candidate and candidate-readback digests matched the review order. Independently parsed raw JUnit and exit receipts. A/B first collection errors exited 2 and were excluded. Substantive RED runs gave 9 and 11 failures, B also passed 10. GREEN gave 9 and 21 passes. Intermediate combined run had 1 failure among 86, corrected run passed 86. Symbol red/green exited 1/0. Final covering and isolated compatibility passed 187 and 8 respectively, with zero skipped/errors/failures and all 151 prior and all 60 T1 identities included. Original voice-reference and anyio warnings are retained.

Offline candidate probe outputs matched physical file presence and SHA-256 under the isolated task roots. Success used two generations with CLI 0. Unsupported used one with CLI 2 and absent file. Postcommit and partial used two and one respectively, both needs_attention/CLI 2 with retained bytes. Existing late-worker tests hold the SDK worker at controlled barriers across a separate request. Their barriers release after return, so they do not cover I3. Protected identity receipts matched 492/37880/32856/18068. One focused read-only validator probe reproduced I1/I2. No suite rerun or external/model/UI/audio action.

Current real 8B E02 has not run on this candidate. Historical E02 failure remains. No T2 acceptance, 14B, production or Owner/freeze release.
