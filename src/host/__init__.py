"""宿主抽象层（S13 · M25 前置）。"""

from .abstraction import (
    CompositeHost,
    HostAbstractionError,
    HostEvents,
    HostIO,
    HostRenderer,
    RENDER_KIND_ORB,
)

__all__ = [
    "CompositeHost", "HostAbstractionError", "HostEvents", "HostIO",
    "HostRenderer", "RENDER_KIND_ORB",
]
