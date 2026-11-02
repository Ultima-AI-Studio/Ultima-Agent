## Independent review of preparation-r4, fix 3/5

**SPEC3/B2 ADDRESSED. QUALITY2/B1 ADDRESSED. SPEC PASS. QUALITY PASS.** All seven original preparation findings are addressed. No fix-induced breakage identified. This verdict applies to the reviewed preparation bytes only. actual_release=false; T2 product exit NOT_PASSED.

**QUALITY2/B1.** The nested discovery traversal now starts from each retained verified parent even when it has exited. A possible surviving child with a later creation time is recorded with its identity, parent and unknown upper bound. It is excluded from the kill set and its ambiguity fails cleanup. The two new synthetic variants exercise the actual cleanup method and distinguish a possible survivor (FAIL) from one that predates the parent (excluded). Both assert zero terminate calls. The Unicode and multiline transport remains intact in two real, bounded headless process proofs with listener ownership, owned identities absent, closed ports and unchanged protected identities.

**SPEC3/B2.** Case.negative now stores the baseline and initial output inventory before validation, and requires an empty initial and per-scenario output set. It persists the observed command, capture, window, foreground, refusal, send witness and output state before the corresponding assertions. Capture, readback, provider or release exceptions record the failure or unavailable observation. Both completed scenarios must carry an empty output set into final reconciliation. Eight targeted regression cases cover the two former false/lost-evidence paths, capture/refusal/send and observation failures, and the successful empty case. The transient-output case confirms that path, bytes and hash remain in the evidence even after subsequent observation returns empty. The existing positive consistency checks were untouched.

**Independent verification.** Reviewed the complete P3-to-P4 controller diff, compared it to the bound source files and examined the ten added regressions. Rehashed all 28 manifest bindings. Read back the final 113-test JUnit (zero failures, errors or skips) and both current-controller headless proofs. No additional execution was needed. No real orphan scenario was inferred from simulation. Model inference, real window behavior, factual correctness and case acceptance remain unverified. This review issued no authority and consumed no case budget.

- controller_sha256 8b8fb6fdf4868b3bb8cea61daaf402e5336f86167d0be84e04c455586d98706f
- manifest_sha256 d3d49198d8e544ac5335f404163b98fb3b92333cb85ee81d3508a7b22eda47b1
- diff_sha256 fe837578f4987b2ecd83909457b413b2b870bfcd3240c7bf06e662f949fcad6e
- author_report_sha256 f882d13729750a85b0bfd12f4ffbd320d691fcaa7aa9062a6aa8cb9166dd5f14
