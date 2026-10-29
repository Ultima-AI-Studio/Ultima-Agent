"""UltimaAgent in-process event stream."""

from .bus import EventBus, emit_event, get_event_bus

__all__ = ["EventBus", "emit_event", "get_event_bus"]
