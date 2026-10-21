"""Eight-state queue lifecycle with fail-closed transition validation."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .storage import QueueStorage


class QueueState(StrEnum):
    QUEUED = "QUEUED"
    EXECUTING = "EXECUTING"
    SELF_CHECK = "SELF-CHECK"
    AUDIT = "AUDIT"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    BLOCKED = "BLOCKED"
    CANCELLED = "CANCELLED"


class InvalidTransition(ValueError):
    """Raised before persistence when a requested transition is forbidden."""


_ALLOWED: dict[QueueState, frozenset[QueueState]] = {
    QueueState.QUEUED: frozenset({QueueState.EXECUTING, QueueState.CANCELLED}),
    QueueState.EXECUTING: frozenset({QueueState.SELF_CHECK, QueueState.FAILED}),
    QueueState.SELF_CHECK: frozenset({QueueState.AUDIT, QueueState.FAILED}),
    QueueState.AUDIT: frozenset({QueueState.COMPLETED, QueueState.FAILED}),
    QueueState.COMPLETED: frozenset(),
    QueueState.FAILED: frozenset({QueueState.QUEUED, QueueState.BLOCKED}),
    QueueState.BLOCKED: frozenset({QueueState.QUEUED, QueueState.CANCELLED}),
    QueueState.CANCELLED: frozenset(),
}
_HUMAN_ACTORS = frozenset({"human", "brain"})


class StateMachine:
    def __init__(self, storage: QueueStorage | None = None) -> None:
        self.storage = storage

    def transition(
        self,
        task: dict[str, Any],
        target: QueueState | str,
        *,
        actor: str,
        reason: str,
        audit_passed: bool = False,
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Return an updated copy and append its event only after all guards pass."""
        source = self._state(task.get("state"))
        destination = self._state(target)
        if destination not in _ALLOWED[source]:
            raise InvalidTransition(f"illegal transition: {source.value} -> {destination.value}")
        if destination is QueueState.COMPLETED and not audit_passed:
            raise InvalidTransition("AUDIT -> COMPLETED requires an explicit audit PASS")
        if source is QueueState.BLOCKED and actor not in _HUMAN_ACTORS:
            raise InvalidTransition("BLOCKED may be released only by human or brain")

        retry_count = self._retry_count(task)
        if source is QueueState.FAILED and destination is QueueState.QUEUED:
            if retry_count >= 2:
                raise InvalidTransition("retry limit reached; FAILED must transition to BLOCKED")
            retry_count += 1
        if source is QueueState.FAILED and destination is QueueState.BLOCKED and retry_count < 2:
            raise InvalidTransition("FAILED may transition to BLOCKED only after retryCount >= 2")

        updated = dict(task)
        updated["state"] = destination.value
        if "retryCount" in task:
            updated["retryCount"] = retry_count
        updated["updated_at"] = datetime.now(UTC).isoformat()
        updated["terminal_reason"] = reason if destination in {
            QueueState.COMPLETED,
            QueueState.FAILED,
            QueueState.BLOCKED,
            QueueState.CANCELLED,
        } else None
        event = self._event(source, destination, reason, actor)
        self._append(task["task_id"], event)
        return updated, event

    def retry_or_block(
        self, task: dict[str, Any], *, actor: str, reason: str
    ) -> tuple[dict[str, Any], dict[str, str]]:
        destination = QueueState.BLOCKED if self._retry_count(task) >= 2 else QueueState.QUEUED
        return self.transition(task, destination, actor=actor, reason=reason)

    def block_failed_dependents(
        self, tasks: list[dict[str, Any]], *, actor: str = "queue-engine"
    ) -> list[tuple[str, dict[str, str]]]:
        """Block queued dependents whose prerequisite is currently failed or blocked."""
        states = {task["task_id"]: self._state(task["state"]) for task in tasks}
        changes: list[tuple[str, dict[str, str]]] = []
        for task in tasks:
            if self._state(task["state"]) is not QueueState.QUEUED:
                continue
            failed_dependencies = [
                dependency
                for dependency in task.get("dependsOn", [])
                if states.get(dependency) in {QueueState.FAILED, QueueState.BLOCKED}
            ]
            if not failed_dependencies:
                continue
            dependency = failed_dependencies[0]
            source = QueueState.QUEUED
            destination = QueueState.BLOCKED
            reason = f"依赖 {dependency} 未完成"
            task["state"] = destination.value
            task["updated_at"] = datetime.now(UTC).isoformat()
            task["terminal_reason"] = reason
            event = self._event(source, destination, reason, actor)
            self._append(task["task_id"], event)
            changes.append((task["task_id"], event))
        return changes

    def block_for_unclear_audit(
        self, task: dict[str, Any], *, actor: str, reason: str
    ) -> tuple[dict[str, Any], dict[str, str]]:
        """Fail closed when an audit/watchdog cannot establish completion evidence."""
        source = self._state(task.get("state"))
        if source in {QueueState.COMPLETED, QueueState.CANCELLED}:
            raise InvalidTransition(f"terminal task cannot be audit-blocked: {source.value}")
        if actor not in {"auditor", "brain"}:
            raise InvalidTransition("unclear audit may be blocked only by auditor or brain")
        destination = QueueState.BLOCKED
        updated = dict(task)
        updated["state"] = destination.value
        updated["updated_at"] = datetime.now(UTC).isoformat()
        updated["terminal_reason"] = reason
        event = self._event(source, destination, reason, actor)
        self._append(task["task_id"], event)
        return updated, event

    def _append(self, task_id: str, event: dict[str, str]) -> None:
        if self.storage is not None:
            self.storage.append_event(task_id, event)

    @staticmethod
    def _state(value: QueueState | str | None) -> QueueState:
        try:
            return value if isinstance(value, QueueState) else QueueState(value)
        except (TypeError, ValueError) as exc:
            raise InvalidTransition(f"unknown queue state: {value!r}") from exc

    def _retry_count(self, task: dict[str, Any]) -> int:
        value = task.get("retryCount")
        if value is None:
            return self._retry_count_from_events(task["task_id"])
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise InvalidTransition(f"invalid retryCount: {value!r}")
        return value

    def _retry_count_from_events(self, task_id: str) -> int:
        if self.storage is None:
            return 0
        path = self.storage.events_dir / f"{task_id}.jsonl"
        if not path.exists():
            return 0
        count = 0
        try:
            for line in path.read_text(encoding="utf-8").splitlines():
                event = json.loads(line)
                if event.get("from") == QueueState.FAILED.value and event.get("to") == QueueState.QUEUED.value:
                    count += 1
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise InvalidTransition(f"cannot recover retry count for {task_id}: {exc}") from exc
        return count

    @staticmethod
    def _event(
        source: QueueState, destination: QueueState, reason: str, actor: str
    ) -> dict[str, str]:
        if not actor or not reason:
            raise InvalidTransition("actor and reason are required for every transition")
        return {
            "ts": datetime.now(UTC).isoformat(),
            "from": source.value,
            "to": destination.value,
            "reason": reason,
            "actor": actor,
        }
