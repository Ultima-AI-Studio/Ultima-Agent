"""Persistent storage primitives for the task queue.

The production task library and tests are deliberately separated: callers
choose the root directory, and tests always use a temporary root.
"""

from __future__ import annotations

import json
import os
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4
from functools import wraps


def queue_transaction(method):
    """Serialize every high-level index read/modify/write with dispatch."""
    @wraps(method)
    def guarded(self, *args, **kwargs):
        from .dispatcher import DispatchLock
        with DispatchLock(self.storage.root / '.dispatch.lock'):
            return method(self, *args, **kwargs)
    return guarded


INDEX_FIELDS = (
    "task_id",
    "state",
    "priority",
    "dependsOn",
    "parallelGroup",
    "fileDomain",
    "reasoningEffort",
    "created_at",
    "updated_at",
    "terminal_reason",
    "card_path",
)
RUN_PARTS = ("before", "out", "err", "done", "session", "progress")
TERMINAL_ARCHIVE_STATES = frozenset({"COMPLETED", "CANCELLED"})
_TASK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*$")


class StorageError(ValueError):
    """Raised when persisted queue data violates the storage contract."""


class QueueStorage:
    """Own the queue index, append-only events, runs, and conservative archive."""

    def __init__(self, root: str | Path, *, max_index_items: int = 10_000) -> None:
        self.root = Path(root).resolve()
        self.max_index_items = max_index_items
        if max_index_items < 1:
            raise StorageError("max_index_items must be positive")
        self.index_path = self.root / "tasks.json"
        self.cards_dir = self.root / "cards"
        self.queue_dir = self.root / "queue"
        self.events_dir = self.root / "events"
        self.runs_dir = self.root / "runs"
        self.archive_dir = self.root / "archive"

    def ensure_layout(self) -> None:
        for directory in (
            self.cards_dir,
            self.queue_dir,
            self.events_dir,
            self.runs_dir,
            self.archive_dir,
        ):
            directory.mkdir(parents=True, exist_ok=True)
        if not self.index_path.exists():
            self._atomic_write_json(self.index_path, [])

    def load_tasks(self) -> list[dict[str, Any]]:
        self.ensure_layout()
        try:
            data = json.loads(self.index_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise StorageError(f"invalid task index: {exc}") from exc
        if not isinstance(data, list):
            raise StorageError("tasks.json must contain a JSON array")
        for task in data:
            self.validate_index_record(task)
        return data

    def save_tasks(self, tasks: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
        self.ensure_layout()
        records = [dict(task) for task in tasks]
        for task in records:
            self.validate_index_record(task)
        remaining = self._archive_excess_index_items(records)
        self._atomic_write_json(self.index_path, remaining)
        return remaining

    @staticmethod
    def validate_index_record(task: Any) -> None:
        if not isinstance(task, dict):
            raise StorageError("each task index item must be an object")
        actual = set(task)
        expected = set(INDEX_FIELDS)
        if actual != expected:
            missing = sorted(expected - actual)
            extra = sorted(actual - expected)
            raise StorageError(f"task index fields mismatch: missing={missing}, extra={extra}")
        QueueStorage._validate_task_id(task["task_id"])
        if not isinstance(task["dependsOn"], list) or not isinstance(task["fileDomain"], list):
            raise StorageError("dependsOn and fileDomain must be arrays")

    def append_event(self, task_id: str, event: dict[str, Any]) -> Path:
        self.ensure_layout()
        self._validate_task_id(task_id)
        event_path = self.events_dir / f"{task_id}.jsonl"
        encoded = json.dumps(event, ensure_ascii=False, separators=(",", ":")) + "\n"
        with event_path.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        return event_path

    def create_run_artifacts(
        self, task_id: str, *, timestamp: str | None = None, run_id: str | None = None
    ) -> dict[str, Path]:
        self.ensure_layout()
        self._validate_task_id(task_id)
        safe_timestamp = timestamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        safe_run_id = run_id or str(uuid4())
        if not re.fullmatch(r"[A-Za-z0-9_-]+", safe_timestamp):
            raise StorageError("timestamp contains unsafe characters")
        if not re.fullmatch(r"[A-Za-z0-9-]+", safe_run_id):
            raise StorageError("run_id contains unsafe characters")
        task_run_dir = self.runs_dir / task_id
        task_run_dir.mkdir(parents=True, exist_ok=True)
        artifacts: dict[str, Path] = {}
        for part in RUN_PARTS:
            path = task_run_dir / f"{task_id}.{safe_timestamp}.{safe_run_id}.{part}"
            path.touch(exist_ok=False)
            artifacts[part] = path
        return artifacts

    def _archive_excess_index_items(
        self, records: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        excess = len(records) - self.max_index_items
        if excess <= 0:
            return records
        eligible = sorted(
            (task for task in records if task["state"] in TERMINAL_ARCHIVE_STATES),
            key=lambda task: (task["updated_at"], task["created_at"], task["task_id"]),
        )
        if not eligible:
            return records
        selected_ids = {task["task_id"] for task in eligible[:excess]}
        archived = [task for task in records if task["task_id"] in selected_ids]
        if archived:
            archive_path = self.archive_dir / "index-items.jsonl"
            with archive_path.open("a", encoding="utf-8", newline="\n") as stream:
                for task in archived:
                    stream.write(json.dumps(task, ensure_ascii=False, separators=(",", ":")) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
        return [task for task in records if task["task_id"] not in selected_ids]

    @staticmethod
    def _validate_task_id(task_id: Any) -> None:
        if not isinstance(task_id, str) or not _TASK_ID_PATTERN.fullmatch(task_id):
            raise StorageError(f"invalid task_id: {task_id!r}")

    @staticmethod
    def _atomic_write_json(path: Path, value: Any) -> None:
        temporary = path.with_name(f".{path.name}.{uuid4().hex}.tmp")
        try:
            with temporary.open("x", encoding="utf-8", newline="\n") as stream:
                json.dump(value, stream, ensure_ascii=False, indent=2)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, path)
        finally:
            if temporary.exists():
                temporary.unlink()
