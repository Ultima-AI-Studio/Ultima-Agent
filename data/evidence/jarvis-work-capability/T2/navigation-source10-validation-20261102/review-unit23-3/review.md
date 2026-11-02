# U23 fix round 2 scoped re-review

**SPEC PASS. QUALITY PASS.**

BASE facd68d8f94b4adcfd136e489e9ff81580d2dc0d through HEAD 6b1e07c8318a334ee1f2218863eb84254e38f526. F3, F4 and N1 are addressed. No new Critical, Important or Minor finding in the two-file fix. F1/F2/F5/F6/F7 retain their prior dispositions. No out-of-scope observations.

## SPEC and QUALITY evidence

### F3 ADDRESSED

`src/brain/work_research.py:698-704,830-836; src/brain/tests/test_work_navigation_transport.py:161-174`

Writer START must equal the exact tool/agent/authored arguments from the writer generation. Writer END requires the correct tool, native_react and explicit True success, before its original receipt/metadata checks. The tests first verify a genuine complete file/runtime result. Changing only the END agent after the sealed prefix or the START agent at prewrite rejects at the corresponding identity gate.

### F4 ADDRESSED

`src/brain/work_research.py:781-786; src/brain/tests/test_work_navigation_transport.py:177-249`

After equality with raw and secured copies, the verifier recursively scans the decoded JSON envelope with the bound policy and rejects a string final_answer with empty strip(). Tests recompute real response bytes, hashes and counters, preserve the ACK prewrite and check the precise refusal. Empty/whitespace and escaped scanner-positive final answers are rejected, including a nested writer title in the action variant. Live decoded scanner tests distinguish refusal before the file from needs_attention after the file.

### N1 ADDRESSED

`src/brain/work_research.py:585-615; src/brain/tests/test_work_navigation_transport.py:55-157`

Replay recovers finite binary64 clock samples, subtracts deadline minus sample before subtracting the non-ACK reserve, checks monotonicity, and applies the same caps for metadata/chat and author/ACK. Timeout values must be real, finite, positive and within the cap. No epsilon is introduced. Six genuine fractional controls capture the same prepared request at build/send. Four nextafter overshoots are rejected at the intended replay gate; live GET/POST tests cover below/at/above author and ACK admission boundaries.

## Independent checks

Validated sealed base/head, 24967-byte package SHA, exact two changed source/test hashes against final receipts, and complete 68833-byte author report prefix against c43401ec. Read the fix brief, appended report and full diff. No git/index/source changes or test reruns.

Independently checked both final argv arrays against the root-sealed proof, all receipt file hashes (including logs/command/JUnit), zero exit, 31 before/after/current input hashes and JUnit counts. 475 passed in 86.93s; 8 passed with the existing anyio warning in 0.11s. Compatibility stderr retained the optional voice-reference fallback; no audio operation. Independently compared qualified JUnit identities: all earlier 449 retained, 26 added. Read and verified all 22 installed SDK hashes. Root additionally verified the 30 tracked input blobs; pre-existing untracked src/brain/browser/tests/test_browser_channel_s3.py is separately byte-bound.

F3 meaningful RED 2/2 missed raises. First F4 RED included fixture faults, then corrected f4-red-2 had 4 expected gate failures of 6 with live decode cases already denying. First N1 RED included Unlinked/failed END and StreamConsumed fixture failures; corrected n1-red-2 had 6 of 18 failures at Runtime final timeout admission drift. Final SDK/transport GREENs were 108, 114 and 132 respectively. The mistaken fixture stages remain preserved separately.

Reopened original four FIX2 files and reconstructed literal Markdown independently from stored GET bodies and fixture lines. Verified six manifest hashes per case, original path and bytes, source/binding/prompt, exact embedded prewrite and unchanged wires/events/timeline/receipt prefixes, version and digest metadata, consumed intent/file/effect identity. Text/permuted/HTML/mixed produced 337/337/370/341 bytes, 62 timeline nodes and 5 generations each.

Reopened all six FIX2 fractional proof sets with stdlib JSON/hash/Path reads, and checked original file content against the recorded SDK file adapter, plus the five exported input/runtime/snapshot/prefix/view hashes. Matched all 90 captured HTTPX request extensions to timeline sample, method, path, entity hash and receipt, then independently calculated all four timeout fields. The regular author/ACK limits were 5.100000000000023/20.100000000000136 seconds, and the last admissible binary64 samples produced 1.1368683772161603e-13/2.2737367544323206e-13 seconds. Test code verifies actual identity of each prepared request and its entity on entry to send. The corresponding rejection tests mutate a single read timeout to its next larger representable float.

These checks used the fixed H interpreter -B -X utf8 for stdlib-only static/readback work. The sealed test records and diff answer the three scoped questions. No product/SDK execution, harness, model or external request was performed for this review.

## Limits

Actual 8B inference, source10 semantic sufficiency on the original four-source task, live fetch and native timing, harness qualification, candidate-wide review, inert and production release remain unverified.

Real generated references that match the existing configured scanner still fail closed. Their availability rate is unmeasured. E02/T2 NOT_PASSED. Model/actual/harness/inert/T3/production release false.

## Inputs and commands

- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-fix2-review-inputs.json`  `444860ad72cce20735138f5306e3728e005c7f473109238a95fe0786f654ed13`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-fix2-rereview-brief.md`  `9d034527f5884e9f1b7b9b0bacd57e36c8c84f97b215ea55ffeb6a1a60892f00`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-unit23-fix2-brief.md`  `b3cb548a89b76168142ebbf2e7bfee269d8c08f82d3e21b244fa732edcda2c83`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\root-unit23-fix2-before-review.json`  `cfe4926ec7446d7a4fcdefa17efd149e533dab6182d147ce48d9820e64fc46c8`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit2-report.md`  `d0bb89d69d668f613fef7cc3d50b56185d5317b42f8ef262e0360c22b4edc7d0`
- `C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit23-fix2-review-package.txt`  `fc0bf03171729b0d49e7704ee036580335f49cbaf460e31103fb261a9afbfd32`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\review-unit23-2\verdict.json`  `e36019634549c3e1980d631f01499f0b0ee7b100c2a2a466227e228d139173a5`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-fix2-covering\receipt.json`  `5f28e13b4bd4fd43641f32ba65e7fbbea76627bf2bab62aac9562c73b5da3c81`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-fix2-compat\receipt.json`  `ec7cdc9b5d16f4d418296aa6fd4714cc0447eb3bb14d64e756326f308b5ba65b`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-fix2-readback\fractional-verification.json`  `3c083e5f3ec03c861242e0902103e24fae81ef9872cb7c050ba5dd2668f6a85a`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-fix2-readback\external-verification.json`  `1af1acfa11a0009d31d812432c834869f6fc1527fa6a1071f07bd83433bfe385`
- `H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\navigation-source10-validation-20261102\code\unit23-fix2-readback\sdk-sources.json`  `e0b0817c172a605193f76a640977bd815ae1cb45e297da29273d2ebe879ec691`

unit23-fix2-covering

```json
[
  "H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe",
  "-B",
  "-X",
  "utf8",
  "-m",
  "pytest",
  "src/brain/tests/test_work_research.py",
  "src/brain/tests/test_work_context.py",
  "src/brain/tests/test_work_delivery.py",
  "src/brain/tests/test_agent_server_sse.py",
  "src/brain/browser/tests/test_browser_channel_s3.py",
  "src/brain/tests/test_interaction.py",
  "src/brain/tests/test_work_navigation.py",
  "src/brain/tests/test_work_navigation_sdk.py",
  "src/brain/tests/test_work_navigation_transport.py",
  "-q",
  "-p",
  "no:cacheprovider",
  "-p",
  "ultima_nav_pathcheck",
  "--basetemp=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix2-covering\\temp",
  "--junitxml=H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix2-covering\\junit.xml"
]
```

unit23-fix2-compat

```json
[
  "H:\\UltimaAI\\UltimaAgent\\tools\\venv-openjarvis\\Scripts\\python.exe",
  "-B",
  "-X",
  "utf8",
  "H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\unit23-fix2-compat\\run_compat.py"
]
```

