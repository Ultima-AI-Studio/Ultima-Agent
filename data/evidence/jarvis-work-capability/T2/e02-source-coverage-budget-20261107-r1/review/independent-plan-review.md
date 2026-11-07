# Independent exact plan review

Verdict: **PASS_PLAN_ONLY**. No blocking plan finding.

Plan: `docs/plans/jarvis-work-e02-source-coverage-budget-plan-20261107.md`
SHA256: `1f5e5776f7db9b5c406bc85c6670af50d1a4ba43ce145718067fb6e48a4de5ab`.
The evidence-root `plan.md` has the same independently read hash.
Candidate HEAD: `ee1bef61f04169c64978538dbc4ba799ef7be6c0`; worktree clean at review.

The plan addresses both reported failures while preserving delivery gates. Plan lines 20-33 and 46 derive availability from the trusted catalogue, count confirmed card-bearing visible sources, and restrict only the inspect source enum. Baseline `agent_server.py:564-577` already distinguishes pending confirmed pages from issued pages; implementation must include the pending page once and preserve the unconfirmed-observation rejection. Baseline `work_navigation.py:432-452` projects only nonempty cards, so the new helper must separately validate every visible source ID against availability, including empty-card pages. Repeated source pages count once; empty pages contribute no coverage. Replay inputs must satisfy the trusted reconstruction requirement at `work_navigation.py:560-595`, not acquire authority from prompt text or a recorded schema.

The budget rule in plan line 31 is feasible: four reads of one source leave two reads and two missing sources; the fifth must use an uncovered available source. Once that page supplies cards, the sixth preserves opportunity for a third source. Empty-card pages can still make the goal infeasible, correctly leaving refusal available. This is an opportunity constraint, not a guarantee of relevant facts. Six reads, one write and one ACK remain eight native POSTs. Source order, page selection and prose remain model decisions.

Plan lines 23 and 37-39 correctly distinguish prewrite refusal from postwrite ACK. Baseline `agent_server.py:570-583` currently accepts arbitrary final text in both phases; the fixed prewrite enum removes that misleading path. `work_service.py:191-215` already distinguishes effects and enforces proof/artifact acceptance. The proposed public failure text must preserve that distinction and must not state the file is absent when effects exist. `work_research.py:788-808,832-833` must reconstruct the same schema without weakening terminal proof checks.

The validation plan is meaningful: lines 29, 33 and 46 require real SDK execution over MockTransport, an actual temporary artifact, write/ACK, and independent replay, not a mocked success result. Existing fixtures support that path (`test_work_research.py:365-423`; `test_work_navigation_transport.py:26-51,90-103`). The old fifth same-source action must fail validation before dispatch; the valid adaptive mock must exercise all six reads and eight POSTs. Replay mutation tests should coherently preserve surrounding links/hashes so rejection targets the authority/schema invariant.

The parent-supplied fixture adaptation is compatible with plan lines 24 and 38-39: move the valid 1000-character private final diagnostic case (`test_work_failure_diagnostics.py:186-191`) to authorized ACK followed by synthetic independent-artifact validation failure. Preserve maximum-size/private assertions and sensitive, overlong, forged and late-change negatives. Add arbitrary-prewrite refusal/false-saved rejection rather than deleting existing diagnostic coverage.

Implementation review must verify deep-copy narrowing preserves the original SDK spec and all non-source constraints; trusted snapshot/canonical authority validation; no empty-page authority loophole; exact live/replay phase equality; and fresh complete bounded offline checks. None of these are claimed executed here.

Scope: read-only source/plan/hash inspection; writes limited to these two review files. No tests, network, inference, runtime/process/service/UI/audio actions or delegation. Frozen N13 factual outcome is taken from the proposal/task, not rerun. This is neither implementation approval nor live research acceptance. No new case authority; actual/model calls zero. E02 remains 0/3 and T2/Owner unpassed. Original write-phase HTTP500 remains unconfirmed.
