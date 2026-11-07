# SDD ledger — plan: docs/plans/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md

User grant call_33506a697ec545c6b2a396ff83086672: source-reference schema alignment, necessary review, one conditional current8B case and result review, retry0.

Pre-flight: Task1 produces correlated schema and independent replay plus frozen candidate/readiness; Task2 consumes identical pinned bytes once.

Ruling: preserve frozen900b944 and previous evidence; native-created new worktree operation6ba6a53b-e91b-4c90-9ab6-388a82ea2ed9 completed with no registration error. Retain workspaces/ledgers per user evidence requirements. Cost: extra storage, no old evidence mutation.

Task1: initial RED28/28; implementation GREEN27/28. Remaining failure was test confusion: _research_budget enforces token estimate, strict32768 bytes is a separate native guard; corrected oversized token fixture to100000 chars without product-limit changes. Strengthened replay tests to repair all self-reported hashes and native entity, requiring rejection by independently rebuilt phase schema. Added malformed mixed-type mapping RED before input validation fix. All failed receipts retained.

Ruling: existing writer diagnostics now require valid incoming source/evidence pairs because malformed native envelopes are correctly rejected earlier. Preserve original diagnostic intent through test-only fault injection inside the real resolver boundary; duplicate-source fixture uses a correctly paired ref. Production responses are not rewritten. Cost if wrong: lost writer regression coverage; all17 original tests must still pass.

Ruling: original Ollama PID5708 was replaced by already-running11464 while the other six identities, parent, executable, command hash, version0.32.15 and8B digest match. User denies active restart/update; app log shows app startup/oldPID cleanup but initiator is unknown. Preserve the old baseline and add a new exact seven-identity baseline for this candidate only, pinned by path and SHA. Read-only reconciliation is within continued identity verification; no service operation or model call. Cost if wrong: preflight refuses any identity drift, and no continuity credit is inferred. Independent preparation review must inspect this.

Task1: bindings-red16 had2 positive-control errors caused by incomplete candidate rebinding; the14 apparent passes are not valid RED proof. Keep that receipt; run a new red-bound stage after complete candidate rebinding and before exact new-baseline enforcement. Expected14pass/2fail, then GREEN16.

Task1: product566 PASS under final bytes, candidate a0d21eb committed/tagged. Baseline RED14pass/2fail confirmed both obsolete-baseline and coherently replaced PID accepted. New baseline pinned by path/SHA. Initial binding script stopped at a whitespace-sensitive constant check after writing only input/bindings; resumed remaining adapter/manifest updates using the retained pre-edit hashes, no tests/authority issued in partial state. No shared P4/P1 edits.

Task1: entry-green25pass/1error was an ordering/setup error: prepare_review.py not generated yet. Preserve receipt; generate full package, bind producer source in runner, and run entry-final26 without changing any test or runtime entry behavior.

Task1: harness base-a11fail/68pass and recovery5fail/14pass, all traced to documents() fixture retaining the pre-baseline-update input-manifest SHA. Runtime correctly refused it before intended tests. Rebind that one fixture literal, keep every runtime function/assertion and all failed receipts, rerun all238 against final harness bytes; base-b earlier140pass is not counted under final hashes.

Task 1: independent preparation PASS, review 5b72c3b3252736defe0c71470e309d1b37730858ddd5698315200d0ca1b79fe8. Final: Ruling: live model output/facts, protected-state continuity and cleanup remain for the authorized case and result review; static preparation grants no acceptance credit. Cost if wrong: no E02 PASS without observed output. No unresolved findings.
