"""In-process KP-003/004/006 event dispatcher."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable
from threading import RLock
from typing import Any


EventHandler = Callable[[dict[str, Any]], None]


class EventBus:
    def __init__(self) -> None:
        self._subscriptions: dict[str, dict[str, EventHandler]] = defaultdict(dict)
        self._lock = RLock()

    def subscribe(self, module_id: str, event_name: str, handler: EventHandler) -> None:
        with self._lock:
            self._subscriptions[event_name][module_id] = handler

    def unsubscribe_module(self, module_id: str) -> None:
        with self._lock:
            for handlers in self._subscriptions.values():
                handlers.pop(module_id, None)

    def publish(self, event: dict[str, Any]) -> int:
        with self._lock:
            handlers = list(self._subscriptions.get(event["payload"]["event"], {}).values())
            handlers += list(self._subscriptions.get("*", {}).values())
        delivered = 0
        for handler in handlers:
            try:
                handler(event)
                delivered += 1
            except Exception:
                # Subscriber failure never takes down the event bus.
                continue
        return delivered
