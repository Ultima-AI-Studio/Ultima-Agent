"""Read-only task status projection over the frozen queue engine storage."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from tasks.queue_engine import QueueState, QueueStorage, StorageError


QUEUE_STATES = tuple(state.value for state in QueueState)
STATE_ZH = {
    "QUEUED": "排队中",
    "EXECUTING": "执行中",
    "SELF-CHECK": "自检中",
    "AUDIT": "审计中",
    "COMPLETED": "已完成（通过）",
    "FAILED": "失败",
    "BLOCKED": "冻结",
    "CANCELLED": "已取消",
}
ANOMALY_STATES = frozenset({"FAILED", "BLOCKED"})
_TERMINAL_STATES = frozenset({"COMPLETED", "FAILED", "BLOCKED", "CANCELLED"})
_TITLE = re.compile(r"^\s*-\s*\*\*标题\*\*\s*[：:]\s*(.+?)\s*$", re.M)


class QueueReadError(ValueError):
    """A persisted queue cannot be represented safely."""


class _ReadOnlyQueueStorage(QueueStorage):
    """Reuse frozen index parsing without its layout-creation side effect."""

    def ensure_layout(self) -> None:
        if not self.index_path.is_file():
            raise StorageError("task index does not exist")


@dataclass(frozen=True, slots=True)
class TaskStatus:
    task_id: str
    title_zh: str
    state: str
    state_zh: str
    priority: int
    duration: str
    terminal_reason: str | None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class QueueSnapshot:
    ok: bool
    status: str
    message: str
    total: int | None
    counts: dict[str, int]
    tasks: tuple[TaskStatus, ...]
    anomalies: tuple[TaskStatus, ...]

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["tasks"] = [item.to_dict() for item in self.tasks]
        value["anomalies"] = [item.to_dict() for item in self.anomalies]
        return value


def read_queue_status(root: str | Path, *, now: datetime | None = None) -> QueueSnapshot:
    """Load current task values through ``QueueStorage`` without reading events."""
    storage = _ReadOnlyQueueStorage(root)
    if not storage.index_path.is_file():
        return _failure("tasks.json 不存在")
    try:
        records = storage.load_tasks()
        current = now or datetime.now(UTC)
        if current.tzinfo is None:
            raise QueueReadError("当前时间缺少时区")
        tasks = tuple(_project(storage, record, current) for record in records)
        if len({item.task_id for item in tasks}) != len(tasks):
            raise QueueReadError("task_id 重复")
        counts = {state: 0 for state in QUEUE_STATES}
        for item in tasks:
            counts[item.state] += 1
        anomalies = tuple(item for item in tasks if item.state in ANOMALY_STATES)
        return QueueSnapshot(True, "读取成功", "任务状态读取成功", len(tasks), counts, tasks, anomalies)
    except (OSError, StorageError, QueueReadError, TypeError, ValueError) as exc:
        return _failure(str(exc))


def _project(storage: QueueStorage, record: dict[str, Any], now: datetime) -> TaskStatus:
    state = record["state"]
    if state not in STATE_ZH:
        raise QueueReadError(f"非法任务状态：{state!r}")
    priority = record["priority"]
    if not isinstance(priority, int) or isinstance(priority, bool) or not 0 <= priority <= 100:
        raise QueueReadError(f"非法优先级：{priority!r}")
    terminal_reason = record["terminal_reason"]
    if terminal_reason is not None and not isinstance(terminal_reason, str):
        raise QueueReadError("terminal_reason 必须为文字或空值")
    created = _timestamp(record["created_at"], "created_at")
    updated = _timestamp(record["updated_at"], "updated_at")
    if updated < created:
        raise QueueReadError("updated_at 早于 created_at")
    end = updated if state in _TERMINAL_STATES else now.astimezone(UTC)
    if end < created:
        raise QueueReadError("任务耗时为负数")
    title = _read_title(storage, record)
    return TaskStatus(
        task_id=record["task_id"],
        title_zh=title,
        state=state,
        state_zh=STATE_ZH[state],
        priority=priority,
        duration=_duration(end - created),
        terminal_reason=terminal_reason,
    )


def _read_title(storage: QueueStorage, record: dict[str, Any]) -> str:
    raw_path = record["card_path"]
    if not isinstance(raw_path, str) or not raw_path:
        raise QueueReadError("card_path 非法")
    path = Path(raw_path)
    path = path if path.is_absolute() else storage.root / path
    path = path.resolve()
    cards_root = storage.cards_dir.resolve()
    if not path.is_relative_to(cards_root) or path.parent.name != record["task_id"]:
        raise QueueReadError("card_path 越出任务卡目录")
    try:
        text = path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise QueueReadError(f"任务卡读取失败：{record['task_id']}") from exc
    match = _TITLE.search(text)
    if not match or not match.group(1).strip():
        raise QueueReadError(f"任务卡缺少中文标题：{record['task_id']}")
    return match.group(1).strip()


def _timestamp(value: Any, name: str) -> datetime:
    if not isinstance(value, str):
        raise QueueReadError(f"{name} 不是时间文字")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise QueueReadError(f"{name} 格式非法") from exc
    if parsed.tzinfo is None:
        raise QueueReadError(f"{name} 缺少时区")
    return parsed.astimezone(UTC)


def _duration(delta: Any) -> str:
    seconds = int(delta.total_seconds())
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def _failure(detail: str) -> QueueSnapshot:
    return QueueSnapshot(
        False,
        "状态读取失败",
        f"状态读取失败：{detail}",
        None,
        {},
        (),
        (),
    )
