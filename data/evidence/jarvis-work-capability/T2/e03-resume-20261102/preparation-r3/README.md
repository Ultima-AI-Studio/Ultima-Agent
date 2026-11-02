# Preparation r3 — fix round 2/5

READY_FOR_INDEPENDENT_REREVIEW; actual_release=false. This correction is limited to the two open R2 groups, SPEC3/B2 and QUALITY2/B1 including nested unknown descendants. Five previously addressed groups retain their behavior. No actual UI/model/product acceptance is claimed. P1/P2 are immutable and preserved; product HEAD/source21/helper/fixture/query/SDK/defaults/model/protected identities remain unchanged.

## B1: lossless OS argv and nested descendants

The new controller owns its process_snapshot implementation. A child PowerShell CIM query converts CommandLine to base64 UTF16LE before serialization. The JSON pipe then contains ASCII only; Python strictly decodes ASCII, validates base64, and strictly decodes UTF16LE. It never guesses the host GB2312 codepage or uses errors=replace. This change affects only the new controller's child query; P1, OS and global encoding stay untouched. Full system snapshots remain transient; raw evidence is persisted only for explicit already-owned PID-scoped queries.

Owned discovery uses this transport for exact Unicode/multiline argv matching. It also inspects descendants beneath each validated interpreter identity, detects nested unknown children/grandchildren, records ambiguity and forces cleanup/overall FAIL. Unknown identities never enter the termination set merely because of a parent PID. Existing creation ordering, exact exe/argv/root, stale-parent rejection, observation-only conhost, retained launcher handle, exited-launcher and listener ownership rules remain.

Actual headless proof uses the revised Owned.launch/discover/assert_listener/cleanup with pinned Python and a harmless prep-owned socket listener. The original Chinese E03 query and original multiline E01 request+three facts are passed verbatim as inert --query arguments. This is not the product CLI and invokes no model. Each final case records original raw scoped OS JSON bytes, decoded commandline, base64 source, exact roundtrip, launcher/basechild/listener identities, absent Python/conhost identities, closed port and protected5 before/after. No impossible live orphan is claimed; prior R2 actual/simulated distinction remains.

## B2: reconcile every observed final state

inventory_map validates each recorded bytes_hex against its actual SHA256 and rejects missing/duplicate records. mechanical now compares the first external artifact bytes/hash with the later inventory bytes/hash and exact expected set, in addition to existing service/write/replace/SDK/capture/caret/run identity checks.

Before cleanup, all entered cases still preserve available logs/product/events/windows/output bytes. reconcile_effects compares the last trusted output map against the accepted observations, including raw bytes, hash, missing/additional outputs, and exact final required owned window dictionaries (identity/text/selection/caret). Any conflict or unknown required effects adds terminal error before teardown and forces overall FAIL/nonzero after cleanup. E03/negative require windows; E01 has no fixture, so its explicit no-required-window reason does not make an otherwise consistent E01 fail. Negative text/no-files state uses the same final comparison. No conflicting data is deleted or rewritten to manufacture success.

Original product-result.json is retained. A later raw CLI parse is separately recorded in pre-cleanup-product-observed.json; a different parsed observation cannot overwrite the original and fails consistency. Service success stays visible even when the harness/final consistency fails. Semantic/no-additions review stays independent, and interrupted native starts stay null/unknown under the accepted ruling.

## Scope, protocol and commands

Canonical future preparation review binding is now R/review-preparation-3/review.md. All other canonical schema2 root authority/ledger/native-preflight/approval paths, <=60s native freshness, <=120s admission expiry, ordered seven-case sequence/six positive CLI cap, exact sibling state, hash-bound independent predecessor acceptance, model/source proof before owned UI, policy-dependent server/listener health before CLI, and original CLI300/SDK1800/maxturn10/work2048/controller315 budgets remain as documented in immutable P2 README. Root alone creates/consumes real authority; no authority/ledger/actual directory is supplied.

New review files: controller.py, test_controller.py, run_checks.py, headless_owned.py, headless_proof.py, README.md, inputs.json. p2-to-r3.diff is the exact complete P2 controller-to-R3 controller diff; full-new.diff contains complete new source/test/driver/docs files. manifest.json binds these and final verification/preservation evidence.

Final targeted check command:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r3/run_checks.py final-retained
```

Result103 passed, exit0, zero socket connections. All original80 purposes remain; additions target only B1/B2, nested unknowns, raw/last effects contradictions, unchanged success, immutable product results and relevant E01 window applicability. final-retained-receipt.json records actual driver_argv, equivalent pytest argv/API args, owned environment, imports, exit. final-retained.log and final-retained.xml preserve output/JUnit. Production8756/11434 and external socket connections remain blocked by the prep test audit hook. Product82/research293 were not rerun.

Actual headless command:

```powershell
& H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e03-resume-20261102/preparation-r3/headless_proof.py
```

Two final cases passed. headless-final-retained-proof.json binds final controller SHA564207fc29158b1a1e6de78158eae16339456f5ad9498e63afd8cc732e3da60b. Exact final case folders are e03-query-final4 and e01-query-final4, containing scoped lossless-commandline-proof.json/.raw, owned tree, pre-cleanup proof, stdout/stderr and cleanup. Earlier successful final/final2 proof folders remain; adapter.log/XML/receipt retain the prior100-check run. Final101 evidence uses a separate final prefix. Initial R3 development run had79 passes and one malformed-inventory fixture raising KeyError rather than ValueError; the new inventory record shape check corrected this. The failed run's log was superseded during development, so no immutable failed-log claim is made; this account preserves the failure honestly. All previous P1/P2 and review failures remain untouched.

No product/native/production/external requests, UI/audio, model changes, product/SDK/default/query edits, dependency installation, source10, queue/git work, authority or child agent. Same reviewer must perform scoped independent re-review before root admission. actual_release=false.

Final B2 retention completion: external-readback-attempts.json saves each trusted first-read raw byte/hash or failure reason, including partial success before a later missing file or invalid UTF8. external-artifacts.json and mechanical-inputs.json persist first artifacts, baseline, windows and later inventory before mechanical rejection. Final103 checks and final4 headless cases correspond to controller564207fc; earlier101 final.log/XML/receipt and final3 scoped proofs remain historical. headless-203030-historical-proof.json exactly matches the previous manifest hash, restored byte-for-byte from preserved final3 case packets; it is not evidence for the new controller. No code changes follow these final checks.
