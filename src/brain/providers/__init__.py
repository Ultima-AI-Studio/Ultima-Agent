"""Main-brain protocol adapters.

Configuration is supplied by ``slot_adapter`` callers; this package only
translates effective settings into provider-specific HTTP requests.
"""

from .base import ChatProvider, ChatResult, ProviderConfigError
from .probe import ProbeResult, probe
from .resolve import provider_for

__all__ = [
    "ChatProvider",
    "ChatResult",
    "ProbeResult",
    "ProviderConfigError",
    "probe",
    "provider_for",
]
