# E02 output-structure controlled entry implementation plan

> **For agentic workers:** Use superpowers:executing-plans; root implements inline, with one independent plan review and one final preparation review. No implementer delegation.

**Goal:** Bind the already frozen output-structure diagnostic candidate to the existing controlled entry, proving bounded diagnostic export before requesting any actual case.

**Architecture:** Reuse the previous entry, bindings and adapter without changing any function/class AST. Update only immutable candidate/path/hash bindings, version-dependent export tests and preparation evidence. The existing product still owns source binding, rendering research.md, write/readback and ACK.

**Tech Stack:** Existing Windows Python, stdlib test runners, guarded offline pytest, local Git.

**Spec:** `H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md`; frozen product report `H:\UltimaAI\UltimaAgent\docs\reports\jarvis-work-t2-e02-output-structure-diagnostics-preparation-20261108-r2.md`; original work order `wo-ultimaagent-20261101-0021` / T2.

## Global Constraints

- Current candidate `bf7f7a9cf0e4ba559c29daa388c00379d12d345a`, root `C:\Users\Administrator\.codex\worktrees\jarvis-e02-output-structure-r2\UltimaAgent`; product source remains frozen. No new writer design or delivery behavior change.
- Use only `qwen3-8b-uncensored`, digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`. No 14B, downloads, model calls, UI, audio, service operations or actual profile execution in this plan.
- Original question, four sources and corpus SHA `9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002` unchanged. Full fact, citation, coverage, artifact, timing and independent acceptance requirements remain.
- Original budgets: CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8; service260/client300/rootwork275/cleanup310/seal315 seconds; context16384, messages32768/entity49152/native65536/private diagnostic16384 bytes; read/ACK256, writer2048 tokens; retry0. Exact inherited budgets dictionary must compare equal, with integer types.
- Actual case allocation0 and independent result-review allocation0. Preparation authority never grants execution. Old releases, controller authorities, actual receipts or grants must not be copied. New actual case requires explicit user allocation after this preparation is reviewable.
- Seven existing protected identities, all old failures/results, 15 unrelated tracked edits, source/credit boundaries and T2/T3-T5/Owner gates remain. Old E01/E03 results do not count for this candidate.
- New evidence root N=`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-output-structure-controlled-preparation-20261108-r1`; old entry O=`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-output-budget-controlled-preparation-20261107-r1`; product prep B=`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-output-structure-diagnostics-20261108-r2`.
- Write only N, this plan, its report, original work-order/stage/current-run/global registration and matching UltimaDocs mirrors; ignored per-plan skill ledger is allowed. No deletion, deployment or remote push; prior automatic push/cleanup rejections remain, no alternate channel.
- WIP: root is the only project implementer; original worker scan and at most one independent reviewer at a time. Offline shards at most2. Reuse existing isolated product checkout; no product edits or integration.

## Review Focus

1. Incomplete source inventory or helper paths mistaken for product paths: require all77 product source pins from B, all under the frozen root and byte-equal.
2. Reused old release or a preparation answer accidentally granting execution: record a truthful content-derived preparation decision with allocations0 and show original missing-grant refusal without calling run_once.
3. v5 safe content and bounded excerpts cannot cross original export path: verify actual exported bytes, hashes and original16384 cap, including FULL/EXCERPTS/OMITTED_POLICY.
4. Contradictory v5 content/JSON/retention states: original exporter must reject invalid packet without creating raw evidence, preserve failure-only/zero-credit semantics.
5. Historical failed test expectations or borrowed acceptance passing as fresh evidence: count current JUnit identities, preserve the two expected obsolete-v4 failures, verify same final source bytes and preserve prior actual result separately.

### Task 1: Rebind and verify the frozen entry

**Files:** N/code/{entry,bindings}.py; N/harness/{adapter,test_adapter,run_checks,headless_proof}.py, README.md, manifest.json; N/tests/test_{bindings,entry,live_boundary,plumbing_replay}.py; N/inputs/*.json; N/verification/*.py; N/plan.md; N/review/independent-plan-review.{json,md}.

**Interfaces:** Consumes B manifest/review/publication, B/inputs/current-inputs.json (77 source_files), O input manifest and original core AST. Produces closed input-manifest.json, candidate-runtime-manifest.json and fresh preparation receipts. `verify_preparation.verify() -> dict` reports computed fresh unique test totals, all allocations0.

- [ ] Register plan, DoR five fields and current WIP in original work order/stage/global/current-run before implementation; independently review exact plan. Expected: PASS_PLAN_ONLY bound to this plan hash, no actual authority.
- [ ] Copy only named source/test/helper files from O into N. Record copy provenance; do not recursively copy O. Use B's complete source_files, filtering any supplemental freeze helpers out of product inventory. Set CANDIDATE and exact path/manifest/decision digests; require core function/class AST equality with O. Expected: 77 frozen sources and unchanged model/corpus/budgets.
- [ ] Run copied export-native-refusal cases through `harness/run_checks.py export-red`. Expected: precisely two v4-vs-v5 assertion failures; retain this receipt and all hashes. This is an obsolete-test compatibility failure, not a new product defect.
- [ ] Update that exact version assertion to v5; add export tests for FULL, large EXCERPTS, OMITTED_POLICY and a contradictory retention state using existing native_refusal test transport. Assert exported bytes/hash/cap, zero acceptance credit and no runtime END; invalid packet cannot create raw evidence. Product and adapter functions stay unchanged.
- [ ] Replace obsolete preparation verification assumptions about O's own initial KeyError with checks of this N's actual receipts. Freeze the harness manifest, then run original eight guarded groups with max2 shards: base-a, base-b, recovery, export-green, failure-export-green, bindings, entry and boundary. Expected: all final groups PASS, zero denied external/model/service activity, same final source bytes. Record any unexpected failure honestly; no unbounded retries.
- [ ] Run original read_runtime.py once for fresh protected identities, isolated port availability, /api/version and /api/tags only. Run preservation before/after against B and O plus previous failures and unrelated edits. Expected: all7 identities match, exact8B digest, no model/service operation.
- [ ] Write execution-proposal.md retaining original prompt/four sources, budgets and complete acceptance; v5 is failure evidence only, with bounded v4 fallback. Prepare final manifest/review/closeout/readback scripts before sealing. Expected: actual/review allocations0; missing-grant gate proof remains pending final preparation review.
- [ ] Commit only after final preparation review in Task2, keeping source/test receipts bound to the final manifest. Task1 evidence check: `python -I -B -X utf8 N/verification/verify_preparation.py` must PASS. Product979 checks are frozen evidence, not rerun or added to fresh entry total.

### Task 2: Independent preparation review and local closeout

**Files:** N/manifest.json, N/preparation-report.md, N/execution-proposal.md; N/review/independent-preparation-review.{json,md}; N/verification/{ready-readback,publication-readback,final-readback}.json; project report and exact UltimaDocs plan/report mirrors; original registration controls.

**Interfaces:** Consumes Task1 exact sources and fresh receipts. Independent reviewer returns literal reviewer=`root-independent`, verdict=`PASS_PREPARATION_ONLY`, matching manifest_sha256/candidate and actual_run_authorized=false. Harness approval is a preparation record, not actual authority.

- [ ] Seal all plan/input/source/checker/proposal/preparation evidence; dispatch one read-only final reviewer. Expected: explicit PASS bound to exact candidate/manifest. A blocking finding allows one evidence-led offline fix pass, retained failure and required closure review; it does not allocate research.
- [ ] After PASS only, record harness approval using original entry.read_ready contract. Prove `read_release` rejects missing release; do not call run_once, create release/actual/native-preflight/controller authority or call model. Expected: ready package accepted, missing grant rejected, actual0.
- [ ] Update current control pointers truthfully, preserving last_actual_result, E02 0/3, T2/Owner not passed, goal active. Mirror plan/report locally; commit scoped files and tag project/mirror. Expected: exact local Git readback, all manifest/published hashes and unrelated files intact. No remote retry.
- [ ] Archive ledger by copying only; keep ignored scratch if cleanup remains blocked. Run final readback once after publication. Expected: fresh final PASS for preparation only, exact heads/tag, source/inputs/manifests verified and allocations0.
- [ ] Present concrete execution proposal and request one explicit current8B original-question/four-source case plus one independent result review; failure no retry. Until answer, no actual execution. The goal remains active and E02 has no new acceptance credit.

## Plan self-review

Spec coverage: output evidence only; original delivery contract and all budgets remain. Shared interface: Task2 consumes final Task1 manifest/checker bytes, so publication receipts are created after sealing and do not retroactively change manifest members. Product B is immutable. Preparation decision uses a content-derived id clearly marked non-platform, has allocations0 and cannot serve as actual release. Old publication/actual outputs are evidence references, not copied authorization. Verification is restricted to original guarded suites; broad pytest could cross explicit no-model/no-service scope and is excluded.
