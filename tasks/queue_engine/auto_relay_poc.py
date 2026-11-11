"""Isolated fixture-only proof for bounded automatic work-order relay.

This module is intentionally not imported by queue_engine's public package, CLI,
dispatcher, watchdog, or any startup path.  It never launches a process, opens a
network connection, or reads the production queue.  Tests provide every task,
outcome, clock value, and persistence path.
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
import json
import os
from pathlib import Path
from time import monotonic
from typing import Any, Callable, Iterable
from uuid import uuid4

from .priority_deps import QueuePlanner
from .state_machine import QueueState, StateMachine


class PocContractError(ValueError):
    """Raised when a fixture violates the PoC contract."""


class IdempotencyConflict(PocContractError):
    """Raised when one receipt identity is reused with different content."""


class BoundedLoopExceeded(PocContractError):
    """Raised instead of allowing a relay call to process unbounded work."""


class AutoRelayPoc:
    """Run a deterministic, bounded relay against caller-owned fixture data."""

    def __init__(
        self,
        tasks: Iterable[dict[str, Any]],
        *,
        state_path: str | Path,
        outcomes: dict[str, list[str]] | None = None,
    ) -> None:
        records = [dict(task) for task in tasks]
        identities = [task.get("task_id") for task in records]
        if any(not isinstance(task_id, str) or not task_id for task_id in identities):
            raise PocContractError("every task needs a non-empty task_id")
        if len(set(identities)) != len(identities):
            raise PocContractError("task_id values must be unique")
        for index, task in enumerate(records):
            try:
                state = QueueState(task["state"]).value
            except (KeyError, TypeError, ValueError) as exc:
                raise PocContractError(f"invalid state for {task.get('task_id')!r}") from exc
            task.setdefault("priority", 50)
            task.setdefault("dependsOn", [])
            task.setdefault("created_at", "")
            if not isinstance(task["dependsOn"], list):
                raise PocContractError("dependsOn must be a list")
            records[index] = {**task, "state": state, "retryCount": 0}

        self.tasks = records
        self.machine = StateMachine(storage=None)
        self.state_path = Path(state_path)
        self.outcomes = {task_id: list(values) for task_id, values in (outcomes or {}).items()}
        if any(value not in {"success", "fail"} for values in self.outcomes.values() for value in values):
            raise PocContractError("fixture outcomes must be success or fail")
        self.attempts = {task_id: 0 for task_id in identities}
        self.receipts: dict[str, str] = {}
        self.dispatch_order: list[str] = []
        self.events: list[dict[str, Any]] = []
        self._save()

    def run_until_wait(self, *, max_steps: int = 100) -> dict[str, Any]:
        """Relay successes until a bounded wait, block, or explicit step limit."""
        if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
            raise PocContractError("max_steps must be a positive integer")
        result = RelayPump(self).pump_once(max_actions=max_steps)
        if result["stop_reason"] == "ACTION_LIMIT_REACHED":
            raise BoundedLoopExceeded(f"relay stopped after max_steps={max_steps}")
        result.pop("action_count")
        return result

    def accept_receipt(
        self,
        *,
        receipt_id: str,
        digest: str,
        task_id: str,
    ) -> bool:
        """Persist one completion receipt; exact duplicates are idempotent."""
        previous = self.receipts.get(receipt_id)
        if previous is not None:
            if previous != digest:
                raise IdempotencyConflict(f"receipt digest changed: {receipt_id}")
            return False
        task = self._task(task_id)
        if task["state"] != QueueState.AUDIT.value:
            raise PocContractError("completion receipt requires AUDIT state")
        self._transition(
            task,
            QueueState.COMPLETED,
            f"accepted {receipt_id}",
            audit_passed=True,
        )
        self.receipts[receipt_id] = digest
        self._save()
        return True

    @staticmethod
    def audit_hold(record: dict[str, Any], *, now: datetime) -> dict[str, Any]:
        """Classify a no-run AUDIT holder without guessing a missing duration."""
        if record.get("state") != QueueState.AUDIT.value:
            raise PocContractError("audit_hold requires AUDIT state")
        raw = (
            record.get("audit_started_at")
            or record.get("dispatched_at")
            or record.get("updated_at")
        )
        if not raw:
            return {
                "valid": False,
                "counted": False,
                "wait_seconds": None,
                "reason": "missing_time_evidence",
            }
        try:
            at = datetime.fromisoformat(str(raw).replace("Z", "+00:00"))
            if at.tzinfo is None or now.tzinfo is None:
                raise ValueError("timezone required")
            seconds = int((now - at).total_seconds())
            if seconds < 0:
                raise ValueError("future timestamp")
        except (TypeError, ValueError):
            return {
                "valid": False,
                "counted": False,
                "wait_seconds": None,
                "reason": "invalid_time_evidence",
            }
        return {
            "valid": True,
            "counted": True,
            "wait_seconds": seconds,
            "reason": None,
        }

    def snapshot(self) -> dict[str, Any]:
        return {
            "tasks": [dict(task) for task in self.tasks],
            "attempts": dict(self.attempts),
            "retry_counts": {
                task["task_id"]: task["retryCount"]
                for task in self.tasks
            },
            "receipts": dict(self.receipts),
            "dispatch_order": list(self.dispatch_order),
            "events": [dict(event) for event in self.events],
        }

    def _dispatch_once(self, task: dict[str, Any]) -> str:
        task_id = task["task_id"]
        self.attempts[task_id] += 1
        attempt = self.attempts[task_id]
        self.dispatch_order.append(task_id)
        task = self._transition(
            task,
            QueueState.EXECUTING,
            f"fixture dispatch attempt {attempt}",
        )
        configured = self.outcomes.get(task_id, [])
        outcome = configured[attempt - 1] if attempt <= len(configured) else "success"
        if outcome == "success":
            task = self._transition(task, QueueState.SELF_CHECK, "fixture execution completed")
            self._transition(task, QueueState.AUDIT, "fixture self-check passed")
            receipt_id = f"{task_id}:attempt:{attempt}"
            digest = sha256(f"success:{task_id}:{attempt}".encode("utf-8")).hexdigest()
            self.accept_receipt(receipt_id=receipt_id, digest=digest, task_id=task_id)
            return "COMPLETED"

        task = self._transition(task, QueueState.FAILED, "fixture dispatch failed")
        updated, event = self.machine.retry_or_block(
            task,
            actor="queue-engine",
            reason="formal retry policy",
        )
        self._replace_task(updated)
        self.events.append({"task_id": task_id, **event})
        self._save()
        return (
            "BLOCKED"
            if updated["state"] == QueueState.BLOCKED.value
            else "RETRY_SCHEDULED"
        )

    def _ordered_queued(self) -> list[dict[str, Any]]:
        return sorted(
            (task for task in self.tasks if QueueState(task["state"]) is QueueState.QUEUED),
            key=lambda task: (
                -int(task["priority"]),
                str(task["created_at"]),
                task["task_id"],
            ),
        )

    def _dependency_gate(self, task: dict[str, Any]) -> tuple[bool, str]:
        return QueuePlanner.dependency_gate(task, self.tasks, self.machine)

    def _transition(
        self,
        task: dict[str, Any],
        target: QueueState,
        reason: str,
        *,
        actor: str = "queue-engine",
        audit_passed: bool = False,
    ) -> dict[str, Any]:
        updated, event = self.machine.transition(
            task,
            target,
            actor=actor,
            reason=reason,
            audit_passed=audit_passed,
        )
        self._replace_task(updated)
        self.events.append({"task_id": updated["task_id"], **event})
        return updated

    def _replace_task(self, updated: dict[str, Any]) -> None:
        for index, task in enumerate(self.tasks):
            if task["task_id"] == updated["task_id"]:
                self.tasks[index] = updated
                return
        raise PocContractError(f"unknown task: {updated['task_id']}")

    def _task(self, task_id: str) -> dict[str, Any]:
        try:
            return next(task for task in self.tasks if task["task_id"] == task_id)
        except StopIteration as exc:
            raise PocContractError(f"unknown task: {task_id}") from exc

    def _result(self, stop_reason: str, *, reason: str | None = None) -> dict[str, Any]:
        result = {
            "stop_reason": stop_reason,
            "dispatch_order": list(self.dispatch_order),
            "states": {task["task_id"]: task["state"] for task in self.tasks},
            "receipt_count": len(self.receipts),
        }
        if reason is not None:
            result["reason"] = reason
        return result

    def _save(self) -> None:
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.state_path.with_name(f".{self.state_path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(self.snapshot(), stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.state_path)
        finally:
            if temporary.exists():
                temporary.unlink()


class RelayPump:
    """Bounded, stoppable host for the fixture-only relay."""

    def __init__(
        self,
        relay: AutoRelayPoc,
        *,
        max_actions: int = 1,
        sleep: Callable[[float], None] | None = None,
        clock: Callable[[], float] = monotonic,
    ) -> None:
        self.relay = relay
        self.max_actions = self._positive_int(max_actions, name="max_actions")
        self.sleep = sleep
        self.clock = clock

    def pump_once(self, max_actions: int) -> dict[str, Any]:
        """Process no more than ``max_actions`` fixture dispatch actions."""
        limit = self._positive_int(max_actions, name="max_actions")
        before = len(self.relay.dispatch_order)
        for _ in range(limit):
            queued = self.relay._ordered_queued()
            if not queued:
                return self._summary("NO_ELIGIBLE_TASK", before=before)
            task = queued[0]
            ready, reason = self.relay._dependency_gate(task)
            if not ready:
                self.relay._save()
                return self._summary(
                    "DEPENDENCY_BLOCKED",
                    before=before,
                    reason=reason,
                )
            outcome = self.relay._dispatch_once(task)
            if outcome == "BLOCKED":
                return self._summary("BLOCKED", before=before)
        stop_reason = (
            "ACTION_LIMIT_REACHED"
            if self.relay._ordered_queued()
            else "NO_ELIGIBLE_TASK"
        )
        return self._summary(stop_reason, before=before)

    def run(self, stop_event: Any, interval_s: float) -> dict[str, Any]:
        """Pump at a bounded cadence until the caller-owned stop event is set."""
        if (
            not isinstance(interval_s, (int, float))
            or isinstance(interval_s, bool)
            or interval_s <= 0
        ):
            raise PocContractError("interval_s must be a positive number")
        started = self.clock()
        pump_count = 0
        action_count = 0
        while not stop_event.wait(0):
            result = self.pump_once(self.max_actions)
            pump_count += 1
            action_count += result["action_count"]
            if self.sleep is None:
                if stop_event.wait(interval_s):
                    break
            else:
                self.sleep(interval_s)
                if stop_event.wait(0):
                    break
        elapsed_s = max(0.0, self.clock() - started)
        return {
            "stop_reason": "STOPPED",
            "pump_count": pump_count,
            "action_count": action_count,
            "dispatch_order": list(self.relay.dispatch_order),
            "elapsed_s": elapsed_s,
        }

    def _summary(
        self,
        stop_reason: str,
        *,
        before: int,
        reason: str | None = None,
    ) -> dict[str, Any]:
        result = self.relay._result(stop_reason, reason=reason)
        result["action_count"] = len(self.relay.dispatch_order) - before
        return result

    @staticmethod
    def _positive_int(value: Any, *, name: str) -> int:
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            raise PocContractError(f"{name} must be a positive integer")
        return value


__all__ = [
    "AutoRelayPoc",
    "BoundedLoopExceeded",
    "IdempotencyConflict",
    "PocContractError",
    "RelayPump",
]
