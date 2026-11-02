# T2 local-role preparation · independent scoped review 1

SPEC REVISE · QUALITY REVISE. Release false. Two important findings in the added proof path prevent authorizing the reviewed bytes.

## F1 · The new request hook runs after the last send-budget check and distorts the dispatch count

run_local_role_prefix.py lines 226 and 298–331 install an HTTPX request hook. On POST the hook reads the template twice, parses and deep-copies large structures and checks the request. run_local_role_core.py lines 283–293 already stamped admission, computed remaining timeout and incremented native_posts. The transparent observer creates its POST row before this hook. No check of the absolute deadline remains between completion of this added work and handing the request to the transport.

I exercised actual NativeLeaf.io, wire_gate and observe_http with the installed HTTPX MockTransport, a socket/DNS deny and a controlled clock. With d=36, time 35.99 on admission, advancing to 37 during the first template read, the valid request reached the transport at 37. A later response check raised. In a second test a one-character change to the secured user projection was correctly rejected in the hook. Transport calls were zero, while native_posts, observer POST rows and durable intent were all one. These are separate faults in the same placement. Evidence: reproduction.json and reproduce.py in this review directory.

Bounded correction: perform the exact raw/secured/typed request proof before final dispatch admission and before incrementing the actual send count, without altering any SDK messages or serialized request. Ensure the timeout is computed from the remaining absolute budget after proof and intent I/O. No additional template reads or expensive comparison after this boundary. Preserve consumed namespace/intent separately from transport admission and ambiguous network delivery. Require an expiry-during-proof case and a rejected-projection case showing zero mock transport calls and zero dispatch count, alongside strict positive wire equality and the existing slow-intent regression.

## F2 · Post-run proof rejection overwrites the primary packet

run_local_role_prefix.py lines 227–239: run_prefix saves and returns the detailed packet. If verify_messages on the raw projection subsequently raises, the outer handler replaces output with a new short dictionary, resets effects and derives native_posts from pre-hook observer rows. The finally block saves that replacement to the same outcome.json. This loses the real stage state, per-phase timing, SDK/END events, buffer/envelopes and consumed intent counts precisely when a discrepancy requires independent investigation. Confirmed work may already have occurred. This path was verified by inspection of both write sites; the independent transport reproduction above does not depend on it.

Keep the existing observed packet and append the proof failure as a distinct overall failure disposition (or preserve a hash-bound primary packet and separate verdict). Never infer unobserved effects from the exception. Test forced raw-proof mismatch with an existing detailed packet, reopen the resulting evidence and verify its timeline, real stage/intent/counters, envelopes and closure survive. Moving both proofs before send can eliminate the new late-error branch if equivalent diagnostics remain available on pre-send failures.

## Unaffected scope

Recomputed 397 historical preservation entries, all 414 manifest frozen-file entries and 21 top-level checksums. Author JUnit records 72 passes, zero failures/errors/skips. The three core diff hunks contain the approved generic local sufficiency text, projection key rename and direct CLI refusal. No semantic/stage/SDK rewrite in this diff. Freezer compares baseline/candidate raw and secured projections, original decoded query, schema, cards and views. Both templates were sealed. The new comparator normalizes copies and does not rewrite the HTTP entity. The gate's placement is the issue.

New admission distinguishes S4 then conditional S1, binds both historic failures/inventories and independent prior PASS, and retains reparse rejection and cumulative cap four including two already spent. Fresh cold snapshot with bound source/runroot, protected identities, source21, empty residency and conservative 12/16/8 GiB minima is checked twice. This review did not query live services. No local-role actual namespace exists. No actual model or network request was sent. S2/S3 stay permanently failed; even two future successful prefixes cannot prove >=3-source E02, file delivery or release source10.

Reviewed SHA256:
- manifest aa8d2be53f576092c9417ec08c06cb2c8beb7b3b93c26557157765c4dd5195d2
- helper 6d7c81000fd8f1854e031ce7ff645103f56b7373491f623a5dd80cffb7c57aa6
- launcher 0036b268ac5227681711c3766ecf31b83a492e468b71004ff060a053b2670a35
- S4 template 01f35b7d2d4feec8fba3dff43ad80d5b3fe57ddda5d7fc60c01b7734660f2547
- S1 template 0290e7912c86baa659173fa6513080f6aa3078ab222d767ddf23fcf1d2bd0dbe
