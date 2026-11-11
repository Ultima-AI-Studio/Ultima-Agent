from __future__ import annotations

from datetime import UTC, datetime
import json

import pytest

from tasks.queue_engine.auto_relay_poc import (
    AutoRelayPoc,
    BoundedLoopExceeded,
    IdempotencyConflict,
)
from tasks.queue_engine.state_machine import QueueState


def task(
    task_id: str,
    *,
    state: QueueState = QueueState.QUEUED,
    priority: int = 50,
    dependencies: list[str] | None = None,
    created_at: str = "2026-11-11T00:00:00+00:00",
) -> dict:
    return {
        "task_id": task_id,
        "state": state.value,
        "priority": priority,
        "dependsOn": list(dependencies or []),
        "created_at": created_at,
    }


def test_normal_relay_completes_first_then_automatically_dispatches_dependent_next(tmp_path):
    poc = AutoRelayPoc(
        [
            task("first", priority=90),
            task("second", priority=80, dependencies=["first"]),
        ],
        state_path=tmp_path / "relay.json",
    )

    result = poc.run_until_wait()

    assert result == {
        "stop_reason": "NO_ELIGIBLE_TASK",
        "dispatch_order": ["first", "second"],
        "states": {"first": "COMPLETED", "second": "COMPLETED"},
        "receipt_count": 2,
    }
    persisted = json.loads((tmp_path / "relay.json").read_text(encoding="utf-8"))
    assert persisted["dispatch_order"] == ["first", "second"]


def test_unmet_head_dependency_does_not_skip_to_lower_priority_task(tmp_path):
    poc = AutoRelayPoc(
        [
            task("dependency", state=QueueState.EXECUTING, priority=10),
            task("head", priority=90, dependencies=["dependency"]),
            task("lower-independent", priority=80),
        ],
        state_path=tmp_path / "relay.json",
    )

    result = poc.run_until_wait()

    assert result["stop_reason"] == "DEPENDENCY_BLOCKED"
    assert result["dispatch_order"] == []
    assert result["states"]["lower-independent"] == QueueState.QUEUED.value


def test_dispatch_failure_retries_twice_then_blocks(tmp_path):
    poc = AutoRelayPoc(
        [task("flaky")],
        state_path=tmp_path / "relay.json",
        outcomes={"flaky": ["fail", "fail", "fail"]},
        max_retries=2,
    )

    result = poc.run_until_wait()

    assert result["stop_reason"] == "BLOCKED"
    assert result["dispatch_order"] == ["flaky", "flaky", "flaky"]
    assert result["states"] == {"flaky": QueueState.BLOCKED.value}
    assert poc.snapshot()["retry_counts"] == {"flaky": 2}


def test_audit_without_run_has_duration_or_is_invalid_and_never_permanent_holder():
    now = datetime(2026, 11, 11, 5, 0, tzinfo=UTC)

    measurable = AutoRelayPoc.audit_hold(
        {
            "state": QueueState.AUDIT.value,
            "audit_run": None,
            "audit_started_at": "2026-11-11T04:00:00+00:00",
        },
        now=now,
    )
    unmeasurable = AutoRelayPoc.audit_hold(
        {"state": QueueState.AUDIT.value, "audit_run": None},
        now=now,
    )

    assert measurable == {
        "valid": True,
        "counted": True,
        "wait_seconds": 3600,
        "reason": None,
    }
    assert unmeasurable == {
        "valid": False,
        "counted": False,
        "wait_seconds": None,
        "reason": "missing_time_evidence",
    }
    assert (measurable["wait_seconds"] is not None) != unmeasurable["valid"]


def test_duplicate_receipt_is_counted_once_and_conflicting_digest_fails_closed(tmp_path):
    poc = AutoRelayPoc([task("one")], state_path=tmp_path / "relay.json")
    poc.run_until_wait()
    receipt_id = "one:attempt:1"
    digest = poc.snapshot()["receipts"][receipt_id]
    before = poc.snapshot()

    assert poc.accept_receipt(receipt_id=receipt_id, digest=digest, task_id="one") is False
    assert poc.snapshot() == before
    assert len(poc.snapshot()["receipts"]) == 1
    with pytest.raises(IdempotencyConflict):
        poc.accept_receipt(receipt_id=receipt_id, digest="different", task_id="one")
    assert poc.snapshot() == before


def test_step_limit_raises_instead_of_running_unbounded(tmp_path):
    poc = AutoRelayPoc(
        [task("one", priority=30), task("two", priority=20), task("three", priority=10)],
        state_path=tmp_path / "relay.json",
    )

    with pytest.raises(BoundedLoopExceeded, match="max_steps=2"):
        poc.run_until_wait(max_steps=2)

    assert poc.dispatch_order == ["one", "two"]
    assert next(item for item in poc.tasks if item["task_id"] == "three")["state"] == "QUEUED"
