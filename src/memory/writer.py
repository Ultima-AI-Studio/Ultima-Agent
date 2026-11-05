"""Storage-neutral memory writer guarded by :mod:`poison_guard`."""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from .poison_guard import MemoryPoisonGuard, PoisonDecision

T = TypeVar("T")


class MemoryWriteRejected(ValueError):
    def __init__(self, decision: PoisonDecision) -> None:
        self.decision = decision
        super().__init__(f"memory write rejected ({decision.category}): {decision.reason}")


class GuardedMemoryWriter:
    """Validate first, then delegate the unchanged text to existing storage."""

    def __init__(
        self,
        write: Callable[[str], T],
        *,
        guard: MemoryPoisonGuard | None = None,
    ) -> None:
        self._write = write
        self._guard = guard or MemoryPoisonGuard()

    def write(self, content: str) -> T:
        decision = self._guard.evaluate(content)
        if not decision.allowed:
            raise MemoryWriteRejected(decision)
        return self._write(content)


__all__ = ["GuardedMemoryWriter", "MemoryWriteRejected"]
