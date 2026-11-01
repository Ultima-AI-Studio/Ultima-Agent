# Independent offline-pair r3 rereview

**SPEC PASS. QUALITY PASS.** Scoped static review of the frozen proposal only.

Freeze SHA-256 `865211bb81a531d5b02952470c1f304aca4fa1eb1ab6e3eebda3cac927f9820e`.

## S1 — ADDRESSED

The full intended source and the submitted citation get independent judgments. Located is a location flag only. A reviewer must grade actual span support, account for scope and polarity, and must not move a reviewer-found range into the submitted-citation column. Missing, invalid and located are distinguished. Evidence: rubric.md and probe.py 211-246.

## S2 — ADDRESSED

Mechanical or envelope failure places the original secured content in the common fallback_text field. This preserves final_answer, malformed prose and noncanonical fields. Bare-string facts are also surfaced as claims. Valid reports preserve the ordered report fields and optional thought. The rubric requires deduplicated assertion scoring and forbids fallback coverage credit. It discloses the risk that malformed field style reveals a variant. Evidence: probe.py 183-254, rubric.md.

## Q1 — ADDRESSED

The guard calls the underlying HTTPTransport once, holds the returned original stream, and replaces it with a SyncByteStream that writes, hashes and yields the same chunks in order. HTTPX binds this stream, reads it for a nonstreaming POST and applies content decoding above iter_raw. Close is forwarded to the original transport stream. Completion is set only on iterator exhaustion. Both the wire options check before dispatch and the secured first-result boundary after dispatch remain intact. Partial/missing capture is inconclusive, and consumes the reservation. The receipt describes encoded entity bytes, not packet framing. Evidence: probe.py 89-116 and installed HTTPX source.

## Verification and limits

Exact r2 and r3 freeze hashes matched, all 39 entries matched in each, and each package contained eight files. Only probe.py, rubric.md, diagnostic-plan.md and freeze.json changed. AST parsing succeeded without module import.

Read installed HTTPX _transports/default.py (121-133, 230-259), _client.py (139-160, 918-928, 1013-1026) and _models.py (884-902, 935-972) as source. No probe, SDK, inference, UI, network or test entrypoint was run.

No new blocking regression identified within the r2-to-r3 delta. Runtime compatibility, real outputs and daemon attribution remain unverified. Proposal review grants no execution authorization. Existing one-shot stop and product/source/live gate boundaries still apply.
