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
from typing import Any, Iterable
from uuid import uuid4

from .state_machine import QueueState


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
        max_retries: int = 2,
    ) -> None:
        if not isinstance(max_retries, int) or isinstance(max_retries, bool) or max_retries < 0:
            raise PocContractError("max_retries must be a non-negative integer")
        records = [dict(task) for task in tasks]
        identities = [task.get("task_id") for task in records]
        if any(not isinstance(task_id, str) or not task_id for task_id in identities):
            raise PocContractError("every task needs a non-empty task_id")
        if len(set(identities)) != len(identities):
            raise PocContractError("task_id values must be unique")
        for task in records:
            try:
                task["state"] = QueueState(task["state"]).value
            except (KeyError, TypeError, ValueError) as exc:
                raise PocContractError(f"invalid state for {task.get('task_id')!r}") from exc
            task.setdefault("priority", 50)
            task.setdefault("dependsOn", [])
            task.setdefault("created_at", "")
            if not isinstance(task["dependsOn"], list):
                raise PocContractError("dependsOn must be a list")

        self.tasks = records
        self.state_path = Path(state_path)
        self.outcomes = {task_id: list(values) for task_id, values in (outcomes or {}).items()}
        if any(value not in {"success", "fail"} for values in self.outcomes.values() for value in values):
            raise PocContractError("fixture outcomes must be success or fail")
        self.max_retries = max_retries
        self.attempts = {task_id: 0 for task_id in identities}
        self.retry_counts = {task_id: 0 for task_id in identities}
        self.receipts: dict[str, str] = {}
        self.dispatch_order: list[str] = []
        self.events: list[dict[str, Any]] = []
        self._save()

    def run_until_wait(self, *, max_steps: int = 100) -> dict[str, Any]:
        """Relay successes until a bounded wait, block, or explicit step limit."""
        if not isinstance(max_steps, int) or isinstance(max_steps, bool) or max_steps < 1:
            raise PocContractError("max_steps must be a positive integer")
        for _ in range(max_steps):
            queued = self._ordered_queued()
            if not queued:
                return self._result("NO_ELIGIBLE_TASK")
            task = queued[0]
            ready, reason = self._dependency_gate(task)
            if not ready:
                return self._result("DEPENDENCY_BLOCKED", reason=reason)
            outcome = self._dispatch_once(task)
            if outcome == "BLOCKED":
                return self._result("BLOCKED")
        if self._ordered_queued():
            raise BoundedLoopExceeded(f"relay stopped after max_steps={max_steps}")
        return self._result("NO_ELIGIBLE_TASK")

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
        self.receipts[receipt_id] = digest
        self._transition(task, QueueState.COMPLETED, f"accepted {receipt_id}")
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
            "retry_counts": dict(self.retry_counts),
            "receipts": dict(self.receipts),
            "dispatch_order": list(self.dispatch_order),
            "events": [dict(event) for event in self.events],
        }

    def _dispatch_once(self, task: dict[str, Any]) -> str:
        task_id = task["task_id"]
        self.attempts[task_id] += 1
        attempt = self.attempts[task_id]
        self.dispatch_order.append(task_id)
        self._transition(task, QueueState.EXECUTING, f"fixture dispatch attempt {attempt}")
        configured = self.outcomes.get(task_id, [])
        outcome = configured[attempt - 1] if attempt <= len(configured) else "success"
        if outcome == "success":
            self._transition(task, QueueState.SELF_CHECK, "fixture execution completed")
            self._transition(task, QueueState.AUDIT, "fixture self-check passed")
            receipt_id = f"{task_id}:attempt:{attempt}"
            digest = sha256(f"success:{task_id}:{attempt}".encode("utf-8")).hexdigest()
            self.accept_receipt(receipt_id=receipt_id, digest=digest, task_id=task_id)
            return "COMPLETED"

        self._transition(task, QueueState.FAILED, "fixture dispatch failed")
        if self.retry_counts[task_id] < self.max_retries:
            self.retry_counts[task_id] += 1
            self._transition(task, QueueState.QUEUED, "bounded fixture retry")
            self._save()
            return "RETRY_SCHEDULED"
        self._transition(task, QueueState.BLOCKED, "fixture retry limit reached")
        self._save()
        return "BLOCKED"

    def _ordered_queued(self) -> list[dict[str, Any]]:
        return sorted(
            (task for task in self.tasks if task["state"] == QueueState.QUEUED.value),
            key=lambda task: (
                -int(task["priority"]),
                str(task["created_at"]),
                task["task_id"],
            ),
        )

    def _dependency_gate(self, task: dict[str, Any]) -> tuple[bool, str]:
        by_id = {item["task_id"]: item for item in self.tasks}
        for dependency in task["dependsOn"]:
            if dependency not in by_id:
                return False, f"missing dependency: {dependency}"
            if by_id[dependency]["state"] != QueueState.COMPLETED.value:
                return False, f"dependency not completed: {dependency}"
        return True, "dependencies completed"

    def _transition(self, task: dict[str, Any], target: QueueState, reason: str) -> None:
        source = task["state"]
        task["state"] = target.value
        self.events.append(
            {"task_id": task["task_id"], "from": source, "to": target.value, "reason": reason}
        )

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


__all__ = [
    "AutoRelayPoc",
    "BoundedLoopExceeded",
    "IdempotencyConflict",
    "PocContractError",
]
