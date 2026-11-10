# Work Order Naming Unification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make one Python module the sole authority for work-order IDs and queue-card resolution, with every dynamic consumer importing it.

**Architecture:** `scripts/order_naming.py` owns the compiled grammar, validation, and exact/slugged card lookup. Dispatcher, verifier, auditor, freezer, and the orchestration format test consume those interfaces; no other location keeps a competing naming expression or constructs a dynamic queue-card filename.

**Tech Stack:** Python 3.13 standard library, pytest 9, Markdown.

**Spec:** `docs/specs/work-order-naming-contract.md`

## Global Constraints

- Do not modify or rename anything under `tasks/queue`, queue state, prohibited tracker files, or untracked evidence.
- Do not add a third-party dependency.
- Keep the work-order grammar in exactly one compiled pattern in `scripts/order_naming.py`.
- Resolve only `<order>.md` and `<order>--<slug>.md`; zero or multiple hits are errors that name the hits.

## Review Focus

- A neighboring order with the same prefix must not count as a card match.
- Direct and slugged cards for one order must be reported as ambiguous.
- Invalid IDs must be rejected before filesystem glob interpretation.
- A slugged card must flow through dispatch, verification, audit, and freeze consumers.
- Existing unrelated pytest baseline failures must remain distinguished from regressions.

---

### Task 1: Centralize naming and card lookup

**Files:**
- Create: `scripts/order_naming.py`
- Create: `scripts/tests/test_order_naming.py`
- Modify: `scripts/dispatch-work-order.py`
- Modify: `scripts/verify-order.py`
- Modify: `scripts/audit-work-order.py`
- Modify: `scripts/freeze-work-order.py`
- Modify: `tasks/queue_engine/audit.py`
- Modify: `tasks/tests/test_audit_e2e.py`
- Modify: `src/brain/orchestration/tests/test_register_control_m29.py`
- Verify: `docs/specs/work-order-naming-contract.md`

**Interfaces:**
- Produces: `ORDER_ID_PATTERN`, `is_valid_order(order: str) -> bool`, and `resolve_card_path(order: str, queue_dir: Path) -> Path`.
- Consumes: queue-card filenames already present in `tasks/queue`; callers supply their actual queue directory.

- [ ] **Step 1: Write focused tests for valid and invalid IDs, exact and slugged paths, zero hits, multiple hits, and prefix isolation.**
- [ ] **Step 2: Run the focused test and verify RED because the authority module does not exist.**
- [ ] **Step 3: Implement the minimal authority module and run the focused test to GREEN.**
- [ ] **Step 4: Replace each dynamic consumer and the orchestration assertion with imports from the authority.**
- [ ] **Step 5: Run focused tests, `scripts/tests`, the related orchestration test, stock/negative/path acceptance probes, and the single-source search.**
- [ ] **Step 6: Inspect the diff and prohibited paths, then commit the coherent change for independent review.**
