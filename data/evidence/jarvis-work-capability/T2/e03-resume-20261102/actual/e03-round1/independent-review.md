# E03 round1 actual independent review

Verdict: **PASS for this one controlled actual E03 sample.** Mechanical/SPEC, facts, target, file, scope, cleanup and boundaries each PASS on the evidence below. This does not release another case or pass E02/T2/T3/Owner.

Reviewer: `root-independent`; schema2. Candidate `244d2120abcd6b8d7744f74a05bd22de46a2d3a5` / source9 `7c201a3aa00c4cfccb170f6ee5102a282174f329`. Selected model `qwen3-8b-uncensored`, digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`.

Root packet SHA256: `be622cf2eb5515e0d825059c5923775fa1db779a9de969b91048268d6690fbd4`.
Terminal SHA256: `7476db06b402710ca4d0c5b08f9fe8f97126d0080f30b29eeeedc5eb53af9e52`.
Independent JSON SHA256: `e84dfc5f9d2a266eaa5940a11da82c0bf79641228228b52aad3458092ccc39ec`.

All47 packet files were independently rehashed and length checked:47/47 match, zero mismatches. Runner, admitted preparation manifest/review and authority file hashes match separately; current frozen21 files and installed SDK6 also match. No suite was rerun. The initial attempt to reconstruct authority bytes from its embedded JSON object was not used as hash proof; the actual authority file SHA was read and matches the packet.

The actual request/session is `e03-round1`; task `8879e805-227e-4b20-ad29-63ad9c30bdbe`. Actual work CLI count1; observed completed inference count3 from `trace.type=inference_end`, all selected8B; native starts remain null. Exactly2 real SDK tool calls start and complete successfully: replace `1283fac9-b851-49b1-ae50-f3b79d5a576e` then write `b8091080-e511-4ab2-8353-38f3a4c5496f`. There is one `mutation.send` pre-send witness with success=false followed by the same call's completed success=true receipt. Source `work_tools.py`/`work_context.py` confirms this witness is intent accounting, not a failed completed tool or separate invocation. No timeout, retry or alternate-model inference appears. Raw CLI JSON equals product result and the later observed product result.

Facts independently PASS. Actual replacement and raw file contain:

```text
1. 项目代号为松林。
2. 交付物为Markdown文档。
3. 截止日期为2026年11月8日。
```

Each numbered point preserves one original fact, including Markdown as the deliverable format and the exact deadline. No added or conflicting factual claim appears. This conclusion comes from the actual content, not a fixed canned oracle, terminal PASS, verified flag or model completion claim.

Target PASS: A HWND10488212/control6949014, PID35200 creation134380908876360286, Edit, approved title, is consistent across policy, capture `95b77e14-c71d-4255-b30a-e58da601c9a5`, real replace metadata and separate external observers. Initial and dispatch baselines agree (selection0..41 UTF16). Dispatch baseline ends11:01:34.210730Z, capture11:01:35.717159Z; final observer ends11:01:50.175830Z, pre-cleanup observer11:01:50.622420Z. Both later snapshots have the exact50-unit replacement and caret50..50. Other HWND16713994/control4196880, same owned PID, retains its exact original text and selection. The original selection covers the whole text, so prefix/suffix preservation is vacuous.

File PASS: the sole output is `outputs/8879e805-227e-4b20-ad29-63ad9c30bdbe/rewrite.md` under the fixed trusted output root. Its98 UTF-8 raw bytes hash to `980174edf18f42e76ca6b06938cc1da66d13180d53c42f06cc404a6e2cb7f2bf`. The write call, absolute artifact path, service readback, external attempts/raw hex, final/pre-cleanup inventories, root independent readback, and reviewer fresh file read agree. File equals real replacement and final observed window text exactly; CRLF/LF normalization is unnecessary. No extra output file is present.

Mechanical/runtime PASS: `admission.json`, native dispatch/after receipts show daemon0.32.15 with fixed8.2B registration and manifest digest. `listener.json` ties port49164 to actual serving PID27984 creation134380908889102764 (launcher32176), exact isolated runtime/output/policy argv. CLI launcher19116/basechild5512 are one normal CLI process tree, not2 work invocations. Hashed runner source confirms no controller retry/model replacement and unchanged allowance10 turns/2048 tokens, CLI300s/SDK1800s defaults. Health alone was not treated as proof of generation; actual trace/tool/effect correlation supplies that proof.

Cleanup PASS: all10 exact known Python process identities and3 observation-only System32 console auxiliaries from `owned-tree.json` are recorded absent in `cleanup.json`; port closed, errors empty, no stale/unknown descendants. Hashed teardown code proves only owned identity-checked Python termination, stopfile preference and natural auxiliary disappearance. Boundaries PASS: protected5 identities remain12796/492/37880/32856/18068 with retained creation/exe; source/native/SDK checks precede and follow execution. Current frozen21/SDK6 read-only hashes independently match. The isolated server log contains expected health/ask traffic; the voice reference warning records configuration fallback only and supplies no evidence of audio use.

Limits: this is one fixed controlled sample, not a success-rate estimate or deployment. Starts/incomplete native inferences remain null and disconnect-generation remains unknown; no zero is invented. The normal completed response and identical final/pre-cleanup effects show no contradictory observed late effect within that observation interval. Historical preparation PASS only binds the admitted package, not this case's result. Process/window protection and cleanup are assessed from preserved actual receipts and hashed implementation, with no new UI/native/model/process/network/git/queue action. No broader filesystem/process absence is claimed. HEAD remains an admission claim rather than a fresh git query; all21 current relevant files match. The root packet excludes itself/runtime cache scratch by design. Original terminal pending-facts and all packet artifacts are unchanged.
