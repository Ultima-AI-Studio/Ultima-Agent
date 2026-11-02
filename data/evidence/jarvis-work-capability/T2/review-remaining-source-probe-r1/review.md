# Remaining-source S3 proposal and isolated launcher, independent review r1

Disposition: SPEC REVISE · QUALITY REVISE. The research proposal is acceptable as a separate, preregistered question. Do not release the reviewed launcher until the Windows run-directory boundary is corrected and independently verified. No actual run is authorized by this review.

## One release blocker

At run_remaining_prefix.py lines 133–149, is_symlink() permits NTFS directory junctions. Both sides of the parent check resolve through the same junction. The path comparison can therefore succeed even when the canonical run directory is outside the controller’s permitted tree. At line 161 main creates that path, then writes an admission receipt, private run homes and later trial evidence there. This violates the exact-runroot and owned-write requirements on the target platform.

I reproduced it against the reviewed validate() with the actual installed Python 3.13.16, real frozen core and checked manifest. Only the actual namespace constant pointed to a review-owned fixture. An empty sibling directory served as the out-of-namespace target of mock-namespace/S3. A fresh valid fixture authority for S3 was accepted. The parent had is_junction() true and is_symlink() false. The resolved target was outside the mock namespace. Neither main nor network was called, the leaf was never created, and the test junction was removed. Evidence is in junction-fixture/result.txt.

Minimal correction: reject Windows reparse directories for the actual namespace, source and existing attempts; reject noncanonical output aliases and independently compare resolved output ownership to the fixed, trusted E-based root and literal source/attempt components. Apply the same ownership validation to prior packet locations. Add socket-denied regression cases for redirection at the namespace and source boundaries. Keep controller serialization and single-use authority; this finding requires no change to the frozen inference core.

## Other reviewed requirements

- The original r2 group remains FAIL. Original S2 spent 1 POST, had no generation and remains factually unassessed. The frozen query lists sources as optional references. S3 can test an accurately cited local code mechanism. It cannot fill the gap in manager initialization/provider selection from missing S2. Even positive results cannot retroactively pass r2, the whole task, E02 or the product. The candidate order S3→S1→S4 is fixed before viewing any new semantic output. All four attempts including S2 remain in the denominator.
- Under the specified serialized-controller trust boundary, admission enforces exact HEAD, source, digest, original packet, frozen manifest/core, one attempt per source, prior attempts and caps. Existing unlisted or partial attempt directories block later release. Later admission requires a distinct controller-bound independent PASS receipt with source, runroot and packet hash plus the actual confirmed mechanical packet. A pending mechanical packet alone cannot advance. Receipt authorship is a controller responsibility. Optimized interpreters are rejected before argument/authority handling.
- The launcher checks the bound resource/identity snapshot before admission and again before bootstrap. RAM ≥12 GiB, commit headroom ≥16 GiB, free GPU memory ≥8 GiB and age ≤30s are precautionary. The checks do not establish instantaneous allocation capacity. The controller must independently collect the evidence and serialize permissions.
- New-manifest 45 frozen files and four test artifacts independently rehashed with no mismatch. Confirmed launch/manifest/proposal hashes below. Frozen inputs, templates, prompt, schema, core, old S2 and accepted r2 technical review retain their recorded hashes. The launcher directly delegates SDK owner creation, socket guard, HTTP observation and run_prefix to the same verified core; the core retains the real caller END, one-turn/one-stage admission, real deadline, HTTP options and no writer. Checks are scoped to the new launcher and its frozen dependency identities.
- Author XML/exit/log record 26 passed, 0 failed. I reran the socket-denied actual SDK S3 MockTransport case in the review directory, 1 passed in 2.40 s. It exercises the real SDK/core and mock native transport, not an actual model and not the entire new CLI. The fixture’s simulated clock and artificial claim provide mechanical evidence only. Independently observed remaining-source-actual absent after review. Fresh factual review remains required per actual packet.

## Reviewed identities

Launcher 3bbf982c3d16c9509c4a287116389f84cc33be33c84804e3c859a128f3dc49a7  
Manifest a96b5e09a68fdb2dbb0fb2cf4f2c335b0af5ca9e54353a845c0bad9eb6e0a749  
Proposal 63bad29f553735f9d2cfdb39c6aeb2fcf7474e112f13dadc380d0d12d133f504  
Frozen core 4122c8d0c288689f31899fc59cebf7aabbcc546c46342071134af712d4a9863e  
Original S2 outcome 597467ca6cd98cf271eaa6a5a62181a614023c591b2a87d66c75eb4df42739aa
