"""Bounded recognition-session restart policy.

Adapted from the 50-second proactive restart in DockWright's
``WakeWordDetector.swift`` at commit
``d6d3f3f71fc83afc9df3f74f9376413084777b90``.
MIT License, Copyright (c) 2026 Adel Elo.
"""

from __future__ import annotations

import time
from collections.abc import Callable


class SessionRestartGuard:
    """Request a stream refresh every interval, never during active audio."""

    def __init__(
        self,
        *,
        interval_seconds: float = 50.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be positive")
        self.interval_seconds = interval_seconds
        self._clock = clock
        self._deadline = clock() + interval_seconds

    def should_restart(self, *, active_audio: bool) -> bool:
        now = self._clock()
        if now < self._deadline or active_audio:
            return False
        self._deadline = now + self.interval_seconds
        return True


__all__ = ["SessionRestartGuard"]
