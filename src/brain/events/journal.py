"""Thread-safe bounded event journal."""

from __future__ import annotations

import json
import threading
from typing import Any


L1_EVENT_TYPES = frozenset(
    {
        "message_in",
        "message_received",
        "message",
        "response",
        "stream_start",
        "stream_chunk",
        "stream_end",
        "injector_result",
        "memories_written",
        "agent_name_updated",
        "tts_reply",
        "audio_created",
    }
)
L2_EVENT_TYPES = frozenset(
    {
        "tool_preparing",
        "tool_executing",
        "tool_call",
        "command_run",
        "command_output",
        "focus_frame",
        "focus_compressed",
    }
)
L3_EVENT_TYPES = frozenset(
    {
        "tick",
        "heartbeat_settings_updated",
        "social_status",
        "key_configured",
        "browser_preview",
        "error",
        "scheduled_task",
        "scheduled_task_completed",
        "scheduled_task_retry",
        "scheduled_task_failed",
        "processing_preempted",
        "llm_retry",
        "message_requeued",
        "message_dropped",
        "protocol_violation",
        "task_advance",
        "audit_record",
    }
)
VALID_PATHS = frozenset({"all", "l1", "l2", "l3"})


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


def event_path(event_type: str) -> str:
    if event_type in L1_EVENT_TYPES:
        return "l1"
    if event_type in L2_EVENT_TYPES:
        return "l2"
    return "l3"


class EventJournal:
    """Keep the latest events in insertion order with cursor lookup."""

    def __init__(self, limit: int = 240) -> None:
        if limit <= 0:
            raise ValueError("journal limit must be positive")
        self._limit = limit
        self._events: list[dict[str, Any]] = []
        self._lock = threading.RLock()

    def append(self, event: dict[str, Any]) -> None:
        with self._lock:
            self._events.append(_clone(event))
            overflow = len(self._events) - self._limit
            if overflow > 0:
                del self._events[:overflow]

    def history(self, *, path: str = "all", limit: int | None = None) -> list[dict[str, Any]]:
        if path not in VALID_PATHS:
            raise ValueError(f"unsupported event path: {path}")
        with self._lock:
            events = [
                event
                for event in self._events
                if path == "all" or event_path(str(event.get("type", ""))) == path
            ]
            if limit is not None:
                if limit < 0:
                    raise ValueError("history limit must not be negative")
                events = events[-min(limit, self._limit) :] if limit else []
            return _clone(events)

    def get_after(self, last_event_id: str) -> list[dict[str, Any]]:
        with self._lock:
            for index, event in enumerate(self._events):
                if event["id"] == str(last_event_id):
                    return _clone(self._events[index + 1 :])
            return _clone(self._events)
