# SDD ledger — plan: docs/plans/jarvis-work-capability-delivery-plan-20261101.md

T0: technical preparation complete; independent r2 review PASS. BASE=6b70aa6.
T1: technical PASS at source 2e0682c, checkpoint c600c5c. T2: BLOCKED after completed single compatibility exception (cumulative3=default2+exception1), source610005e. CODE PASS/151 tests; actual sole E02 FAIL malformed JSON and unsupported OpenAI implementation claim. Same current8B, no14B/production switch. T3-T5 not started.

Ruling: standard task-brief helper expects Task N, but approved plan uses T0-T5. Extract exact T1 plus Global Constraints/Review Focus/interfaces without altering approved plan.
Ruling: CLI adapter reports effective read-only sandbox despite workspace-write request; all shell calls denied and no code written. Keep FAILED receipt. Use existing authorized Codex API developer session in the same worktree, with queue/evidence/audit gates unchanged; do not change sandbox or security settings.
Ruling: stage task IDs hang from original wo-ultimaagent-20261101-0021. They do not create new original work orders or reset budget/history. Original stays open until E01-E08 and Owner gate.

| Pair/task | Shared interface or self-check | Finding/ruling |
|---|---|---|
| T0/T1 | exact r2 plan/spec/cases, runtime input snapshot | PASS digests fixed, isolated source hydrated, baseline 14 passed |
| T1 | tests vs code/file scope | trusted startup root, alias constructor capture, SDK ledger, real CLI; no known open blocker |
| T2 | context capture vs target validation | implement at T2, validate before writes |
| T3 | session IDs vs SDK SessionStore | explicit mapping required; do not assume user_id equals session_id |
| T4 | task states vs cancelled/recovery | T1 cannot claim T4 behavior; API fixed before T4 |
| T5 | actual text/voice vs common service | keep IDs and artifacts; Owner voice acceptance remains |
| T1/T2 | WorkService context field | data only; never authorization |
| T1/T3 | request/session/task/artifact fields | stable response contract |
| T1/T4 | state and ledger | stage T1 mechanical verification only, recovery later |
| T1/T5 | ask_work/CLI and response | common work mode, legacy stays compatible |
| T2/T3 | selected object vs session state | preserve provenance and identity |
| T2/T4 | stale context vs retry | re-observe before mutations |
| T2/T5 | context to host | source/time/target validation retained |
| T3/T4 | persistent task associations vs crash | avoid replay side effects |
| T3/T5 | continuous session IDs | propagate in all host calls |
| T4/T5 | cancellation/recovery API | fixed evidence and runtime status before host acceptance |

2026-11-02: T1 fresh candidate regression 60 passed. Strict live group uses three independent processes/runtime/output roots; all CLI exits 0 and product states succeeded. Controller reopened all three files and confirmed byte hashes and the three fixed facts without additions. Preserve initial proxy failures, warm group, strict cleanup-script failure, and the exact-line oracle false negatives; semantic acceptance permits headings/lists under frozen r2. No T1 gate PASS or Owner acceptance yet.

2026-11-02: T1 independent review PASS/Approved, Critical0 Important0 Minor3. Source checkpoint c600c5c and matching T1 technical tag pushed/peeled-verified; UltimaDocs mirror2646fa6 same stage tag also verified. T1 stage COMPLETED; original order remains open. T2 stage registered and Manager read back, fresh sole implementer preflights precise context/target/source interfaces before code. Three Minor items are assigned to related T2 changes with regression, not silently rewritten in T1.

Ruling: approve T2 adapter design with task-2-interface-ruling.md — strict trusted target manifests/request binding, readonly SDK search/GET, truthful uncertain UI outcomes and real dedicated-window readback satisfy E02/E03. A native focus switch cannot be OS-transactional; direct captured handles prevent redirection and any detected post-check drift is needs_attention, never rollback/success. Companion file preserves T1 artifacts. Named CLI/server/harness additions are necessary integration scope. No new dependency/core, default permissions remain closed. Cost if wrong: repair T2 and repeat its gate before any T3 work. T2 TDD implementation now authorized.

Task T2: independent review1 NEEDS FIXES; Important I1 companion A/B mismatch reproduced with actual file. Fix round1/2 dispatched to original implementer; no stage PASS. Prior e673 E02 group failed2/3; f2e harness-format E02 succeeded mechanically but independent semantic review pending; its E03 group failed1/3 on stale target. Preserve every attempt. Ruling: improve generic research default organization rather than require a harness-specific long recipe; keep fixed topic and semantic/citation requirements. Supplement eight missing T1 agent-tools compatibility cases. Source repairs require scoped re-review before new final live groups.

Task T2: minor (deferred): M1 dense safety-critical statements, triage in final branch review; M2 baseline voice-reference startup warning retained/reported, no voice repair in this task.

Historical correction: the eight legacy agent-tools tests hardcode H ROOT and bare-module path insertion; original T1 run can use H/data synthetic TemporaryDirectory, so full evidence-root isolation was overstated for that subset. T0/H/C test and tool-module bytes all match. Immutable T1 logs/tag retained; unchanged test bodies will rerun with C module preload and evidence-root ROOT, actual paths/testcase identities recorded. This is a compatibility supplement, not new real memory/queue permission.

Task T2: fix round1/2 complete (1 addressed,0 open — I1 companion payload mismatch; commits e673e1f..ad1621e). Scoped independent re-review PASS, no new Critical/Important. Fresh covering tests88 plus isolated legacy8 pass; all8 exact identities/import paths verified independently. Baseline voice-reference and anyio assert-rewrite warning retained as Minor. Ruling: release frozen ad1621e final E01/E02/E03 live groups; code repair does not itself mean T2 PASS. Original runtime remains untouched.

Task T2: ad1621e gate stopped after E01 PASS3 and E02 FAIL1 (CLI2, zero GET, model saved search snippets). Controller physically reopened E01 files and recomputed13source hashes; all3facts intact. E03 not started. No retry/cherry-pick. Own workers exited and isolated locks cleaned after dead-owner identity proof; protected4processes unchanged.

Ruling: start final bounded repair round2/2, design first — required source search/GET must be run as explicit prerequisites via the existing SDK executor, rather than entrusted to model tool selection. Same NativeReAct then drafts from actual bodies; optional structured report tool may render bound source references through SDK FileWriteTool. No new Agent/retrieval engine/vendor/dependency. Context source candidates are data, not authorization. Need≥3actually cited verified sources, not every fetched candidate. Fixed topic/semantic gate and all failures remain. Precise design/interface supplement required before code; no new live groups until reviewed candidate release. T3-T5 remain pending.

Ruling: approve fix2 design per task-2-fix-round-2-ruling.md — real SDK prerequisite collection, frozen catalogue and model-fact structured writer remove optional GET/citation-copy planning failures. Exact optional probe failures stay recorded and can be nonfatal only by collector call association with≥3cited good sources; mandatory/timeout/write failures remain fatal. Standard file/selection modes and original permission gates stay. Mixed research+replacement explicitly unsupported. Final scoped review and live gate still required; this uses final project repair round2/2.

Task T2: fix round2/2 code review complete (I2 addressed,0 open — mandatory reads and bound source report; ad1621e..10fec03). Fresh independent reviewer found no new Critical/Important. Current tests141+8=149 unique, all60T1 cases covered and15source hashes recomputed. Final frozen10fec03 live gate released; T2 itself still pending.

Task T2: minor (deferred, final review triage): work_research.py27-34 greedy URL extraction consumes adjacent Chinese punctuation/prose, including a known candidate in natural E02 request. Preserve raw input and resulting candidate failures; do not silently modify frozen case or claim all4sources succeeded. Only approved exact optional-probe classification with≥3actually cited successful sources can pass. No third repair/title reset authorized.

Final T2 stop: 10fec03 E01 PASS3; E02 FAIL1 after SDK search1/GET4 (3success+1retained optional404). Model first sent facts:string and was rejected, then wrote a file with array but unsupported OpenAI/incorrect-source claims. Physical file retained SHA744796ff9991b9694499de09ba2d377c069c3357bf7f3d4364ed5fca82864cca. E03 not started; no later stages. Controller independently reopened files/source body, recomputed15hashes and current protected4process identities; fresh reviewer independently agrees FAIL/BLOCKED. No third repair.

Disposition: parent and T2 queue records FAILED/non-runnable, global blocked, Manager independently read back; no fabricated queue re-entry history. Original code/services/KWS untouched. Save blocked checkpoint and mirror, retain this recovery workspace. Model-comparison proposal for already-registered qwen2.5:14b is prepared but NOT EXECUTED; Owner strategy/scope decision required before additional inference/repair. No production default change or overall completion.

Ruling: one controller-manual compatibility exception within the existing authorized goal, not automatic retry or Owner approval. Fresh actual SDK rendering proves nested sections.items.facts and source_id constraints never reach NativeReAct. Apply only the prehashed two-file patch (633aa638), with actual first-inference prompt RED/GREEN tests. Cumulative repair3=default2+one explicit exception; all prior FAIL/blocked evidence and original work-order identity stay. Model/permissions/semantic gates remain unchanged. Cost if wrong: stop this exception, retain failed output, do not extend it into further prompts or model comparisons. Basis: H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/schema-prompt-diagnosis/controller-compatibility-ruling.md.

Task T2: original implementer /root/implement_work_capability_t2 is executing this exact two-file exception. Prior live gate remains FAIL; new live gate is not released before fresh scoped review. Model-comparison proposal is deferred and unexecuted; the user clarified Qwen3 8B, did not approve 14B.

Task T2: compatibility exception cumulative3 source610005e (parent afbbe3e) submitted. Exactly37 added lines in2authorized files; RED2 failures/GREEN2 pass, covering143+isolated8=151 distinct tests, all60T1 identities covered, other13 inputs unchanged. Controller read report commands/logs/candidate manifest. Fresh scoped reviewer /root/review_work_schema_exception dispatched on generated afbbe3e..610005e diff. Live E02 remains unreleased; no14B/default/runtime change.

Task T2: cumulative repair3 scoped review CODE PASS, I3 ADDRESSED, no new Critical/Important; raw review outputs independently hashed. Ruling: release ONE same-current8B E02 round1 through unchanged round_case natural query, count it as first of3 if accepted; any mechanical/semantic failure stops this exception. E01/E03/further E02 and T3-T5 remain unreleased pending independent result readback. No14B.

Task T2: cumulative repair3 exception CLOSED. Actual sole610005e E02 round1 mechanical+semantic FAIL, raw JSON missing facts array close bracket (not old facts:string), same-run later real file retained SHAcd54c3471bbbe50caa3ca72708332e9321db36feb35f2b598a9fc74e7a5f50bf; unsupported S2OpenAI claim. Controller and fresh reviewer independently reopened bytes and source bodies; no extra round/model/network/UI. Four protected identities unchanged, own0processes, one own dead-owner runtime lock removed with receipt. T2EXECUTING->FAILED/nonrunnable, globalblocked/Manager readback, other45records unchanged; actual queue reentry1, no fabricated BLOCKED history. No later-stage release. Save explicit blocked checkpoint and mirror, keep this recovery workspace.
