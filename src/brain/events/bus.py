"""Thread-safe event bus used by the agent server and source modules."""

from __future__ import annotations

import json
import threading
import time
from collections.abc import Callable
from typing import Any

from .journal import EventJournal

EventHandler = Callable[[dict[str, Any]], None]


def _clone(value: Any) -> Any:
    return json.loads(json.dumps(value, ensure_ascii=False))


class EventBus:
    """Publish immutable JSON events to subscribers and a bounded journal."""

    def __init__(self) -> None:
        self._journal = EventJournal(limit=240)
        self._lock = threading.RLock()
        self._next_id = 1
        self._subscribers: dict[int, EventHandler] = {}
        self._next_subscriber_id = 1
        self._sticky: dict[str, dict[str, Any]] = {}

    def emit_event(
        self,
        event_type: str,
        data: dict[str, Any],
        *,
        sticky: bool = False,
    ) -> dict[str, Any]:
        if not isinstance(event_type, str) or not event_type.strip():
            raise ValueError("event type must be a non-empty string")
        if not isinstance(data, dict):
            raise TypeError("event data must be a dict")
        isolated_data = _clone(data)
        with self._lock:
            event = {
                "id": str(self._next_id),
                "type": event_type,
                "data": isolated_data,
                "ts": time.time(),
            }
            self._next_id += 1
            self._journal.append(event)
            if sticky:
                self._sticky[event_type] = _clone(event)
            subscribers = list(self._subscribers.values())
        for handler in subscribers:
            try:
                handler(_clone(event))
            except Exception:
                continue
        return _clone(event)

    def subscribe(self, handler: EventHandler) -> Callable[[], None]:
        if not callable(handler):
            raise TypeError("event handler must be callable")
        with self._lock:
            subscriber_id = self._next_subscriber_id
            self._next_subscriber_id += 1
            self._subscribers[subscriber_id] = handler

        def unsubscribe() -> None:
            with self._lock:
                self._subscribers.pop(subscriber_id, None)

        return unsubscribe

    def get_after(self, last_event_id: str) -> list[dict[str, Any]]:
        return self._journal.get_after(str(last_event_id))

    def history(self, *, path: str = "all", limit: int | None = None) -> list[dict[str, Any]]:
        return self._journal.history(path=path, limit=limit)

    def set_sticky(self, event_type: str, data: dict[str, Any]) -> dict[str, Any]:
        return self.emit_event(event_type, data, sticky=True)

    def clear_sticky(self, event_type: str) -> None:
        with self._lock:
            self._sticky.pop(event_type, None)

    def get_sticky(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return _clone(self._sticky)


_EVENT_BUS = EventBus()


def get_event_bus() -> EventBus:
    return _EVENT_BUS


def emit_event(event_type: str, data: dict[str, Any], *, sticky: bool = False) -> dict[str, Any]:
    return _EVENT_BUS.emit_event(event_type, data, sticky=sticky)
