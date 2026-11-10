# Card Form Unification Implementation Plan

> **For agentic workers:** Execute inline in this session. The work order forbids writes outside the listed scripts, `scripts/tests/`, and this report, so no auxiliary worktree or `.superpowers` ledger will be created.

**Goal:** Make the audit and freeze entry points accept the uniquely resolved `tasks/queue/*.md` work-order card while preserving the existing `tasks/cards/<id>/task.md` contract.

**Architecture:** `gorch_contract.stage_gates()` is the single fallback parser for queue-stage acceptance sections. Audit uses ACC rows first and stage rows second; freeze resolves the order card once, binds either the legacy dispatched card set or the queue card itself, and validates the same gate set that audit judged.

**Tech Stack:** Python 3.13.16, pytest, stdlib only.

**Spec:** `tasks/queue/wo-ultimaagent-20261110-0033--card-form-unify.md`

## Global Constraints

- Only modify `scripts/gorch_contract.py`, `scripts/audit-work-order.py`, `scripts/freeze-work-order.py`, `scripts/tests/`, and `docs/reports/`.
- Do not modify `scripts/dispatch-work-order.py`, `scripts/order_naming.py`, 0030 commit `dc651d6f` or its T0-T2 frozen artifacts, existing `tasks/cards/`, or the global queue index.
- Use `tools/venv-openjarvis/Scripts/python.exe` for every Python command.
- Stop after T0-T4 and the receipt; do not enter 0030 T4-T7.
- Preserve `passed = pass1 and pass2 and visible` and the freeze requirement `audit_passed is True`.

## Review Focus

- A queue card with no ACC table must expose every `Gate Tn` section in numeric order; T0 owns the real-0030 parser test.
- A stage criterion must contain only the bullets belonging to its acceptance block; T0 owns the block-boundary test.
- A queue card larger than 4000 characters and evidence larger than 6000 characters must remain complete below the new limits; T1 owns the audit integration test.
- An arbitrary file outside both canonical card forms must remain rejected; T2 owns the queue-path mismatch test and legacy root tests retain the card-form checks.
- An empty dispatched-card list is valid only when the audited card is the uniquely resolved queue work-order card; T2 owns empty, canonical-record, and mismatch tests.

---

### Task T0: Stage gate parser

**Files:**
- Modify: `scripts/gorch_contract.py`
- Test: `scripts/tests/test_card_form_unify.py`

**Interfaces:**
- Produces: `stage_gates(card_text: str) -> list[dict]` with `id`, `criterion`, and `how`.
- Consumed by: T1 audit fallback and T2 freeze gate conservation.

- [x] Add real-0030 and focused block-boundary tests; run them and confirm failure because `stage_gates` is absent.
- [x] Implement strict stage-heading parsing, bullet merging, duplicate refusal, and numeric ordering without changing `acc_rows`.
- [x] Re-run focused tests and confirm T0 passes.

### Task T1: Queue-card audit compatibility

**Files:**
- Modify: `scripts/audit-work-order.py`
- Test: `scripts/tests/test_card_form_unify.py`

**Interfaces:**
- Consumes: `stage_gates()` from T0.
- Produces: queue-aware `_card_id()`, ACC-first gate fallback, 16000-character card window, 12000-character evidence window, and stage-id verdict parsing.

- [x] Add queue `_card_id`, gate fallback, stage verdict, and raised-window audit tests; run them and confirm the pre-change failures.
- [x] Implement the minimal audit changes while preserving waiver, authority, JSON structure, DeepSeek transport, and the two-round pass formula.
- [x] Re-run focused tests and confirm T1 passes.

### Task T2: Queue-card freeze binding

**Files:**
- Modify: `scripts/freeze-work-order.py`
- Test: `scripts/tests/test_card_form_unify.py`

**Interfaces:**
- Consumes: `stage_gates()` and `order_naming.resolve_card_path()`.
- Produces: one binding result for either legacy card records or the queue work-order card record.

- [x] Add tests for empty receipt cards, an explicit canonical queue-card receipt, and a mismatched path; run them and confirm failure.
- [x] Implement queue binding by resolved path plus SHA-256, retain legacy canonical-card checks, and use stage gates only when ACC rows are absent.
- [x] Re-run focused and existing audit/freeze contract tests.

### Task T3: Live 0030 audit

**Files:**
- Runtime output only: `tasks/queue/runs/wo-ultimaagent-20261108-0030-20261110T101704476104Z/audit.json`

- [x] Run the exact user-supplied DeepSeek command with the fixed interpreter.
- [x] Read back `audit.json`; require non-blocked output, `Gate T3`, and `model` plus `response` in both rounds.
- [x] Record the actual `audit_passed` value without changing the verdict logic.

### Task T4: Regression and receipt

**Files:**
- Modify: `docs/reports/wo-ultimaagent-20261110-0033-t0-t4-execution.md`

- [x] Run the exact `scripts/tests` regression command and require no more than the fresh baseline of 6 failures.
- [x] Review the scoped diff and verify forbidden files and 0030 T0-T2 artifacts are untouched.
- [x] Append the literal JSON receipt and stop.

## Execution Ledger

- Pre-flight: T0 produces `stage_gates`; T1 and T2 consume the same function. The ACC-first fallback order is identical in both consumers.
- Ruling: work in the current checkout because the user fixed this repository and run directory and prohibited auxiliary writes outside the allowlist; cost if wrong: local target edits coexist with unrelated dirty work and therefore require path-scoped diff verification.
- Baseline: `tools/venv-openjarvis/Scripts/python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q` -> 6 failed, 32 passed.
- T0 RED: 3 failed because `stage_gates` was absent; GREEN: 3 passed.
- T1 RED: 3 failed on empty gate fallback, queue `_card_id`, and blocked raised-window audit; GREEN: focused suite 6 passed.
- T2 RED: 4 failed because the queue binding entry did not exist; GREEN: focused suite 10 passed.
- Legacy regression: `tests/test_order_contract.py`, `tests/test_audit_checklist.py`, `tests/test_gate_waiver_contract.py`, and `tests/test_freeze_binding.py` -> 77 passed.
- T3: live DeepSeek audit wrote `audit.json` and was not blocked. Both `deepseek-flash` rounds supplied `model` and `response`; gates contain `Gate T0` through `Gate T7`; all inputs were complete. DeepSeek passed only T3 and failed the unexecuted stages. Its response used `Tn`/`Overall` rather than the required `Gate Tn`/`AUDIT` literals, so the unchanged parser recorded `MISSING` and `audit_passed` is false.
- T4: exact regression command -> 6 failed, 42 passed; the failure count equals the fresh baseline and all 10 new tests passed.
- Final review: self-review because this session forbids spawning review agents. `git diff --check` and `py_compile` passed; scoped audit/freeze tests passed; no Critical, Important, or Minor findings.
- Boundary readback: `scripts/dispatch-work-order.py` and `scripts/order_naming.py` have no scoped diff. The 0030 external worktree has no diff from `a4d968af` under `src/brain/orchestration/ledger` or `src/brain/orchestration/queue.py`; `dc651d6f` remains a commit object. Pre-existing untracked `tasks/cards/` content was not modified.

## Receipt

```json
{
  "work_order": "wo-ultimaagent-20261110-0033",
  "status": "READY_FOR_REVIEW",
  "gates": {
    "T0": "PASS",
    "T1": "PASS",
    "T2": "PASS",
    "T3": "PASS",
    "T4": "PASS"
  },
  "audit_json_path": "H:\\UltimaAI\\UltimaAgent\\tasks\\queue\\runs\\wo-ultimaagent-20261108-0030-20261110T101704476104Z\\audit.json",
  "audit_passed": false,
  "changed_files": [
    "scripts/gorch_contract.py",
    "scripts/audit-work-order.py",
    "scripts/freeze-work-order.py",
    "scripts/tests/test_card_form_unify.py",
    "docs/reports/wo-ultimaagent-20261110-0033-t0-t4-execution.md",
    "tasks/queue/runs/wo-ultimaagent-20261108-0030-20261110T101704476104Z/audit.json"
  ],
  "boundary_declaration": "未改动 dispatch-work-order.py、order_naming.py、0030 的 dc651d6f 与 T0–T2 产物",
  "regression": {
    "pytest_failed": 6,
    "baseline_failed": 6
  }
}
```
