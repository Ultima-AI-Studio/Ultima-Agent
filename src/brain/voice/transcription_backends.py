"""Storage-free transcription backend registry for UltimaAgent.

The interface/manager split is adapted from
``akshayaggarwal99/jarvis-ai-assistant`` ``src/transcription`` at commit
``bec50ef6e615707613c4fa22c8bd6afc3cc93152``.
MIT License, Copyright (c) 2025 Akshay Aggarwal.
See ``docs/research/sources/jarvis-ceo/LICENSE``.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

TranscriptionBackend = Callable[[Path], dict]


class BackendUnavailable(RuntimeError):
    pass


class TranscriptionUnavailable(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class _Registration:
    name: str
    transcribe: TranscriptionBackend
    is_cloud: bool


class TranscriptionRouter:
    """Try registered backends in order; callers keep one stable method."""

    def __init__(self) -> None:
        self._registrations: list[_Registration] = []

    @property
    def names(self) -> tuple[str, ...]:
        return tuple(item.name for item in self._registrations)

    def register(
        self,
        name: str,
        transcribe: TranscriptionBackend,
        *,
        is_cloud: bool = False,
    ) -> None:
        if not name or any(item.name == name for item in self._registrations):
            raise ValueError(f"invalid or duplicate backend name: {name!r}")
        self._registrations.append(_Registration(name, transcribe, is_cloud))

    def transcribe(self, wav: Path, *, preferred: str | None = None) -> dict:
        ordered = list(self._registrations)
        if preferred is not None:
            matches = [item for item in ordered if item.name == preferred]
            if not matches:
                raise ValueError(f"unknown transcription backend: {preferred}")
            ordered = matches + [item for item in ordered if item.name != preferred]

        failures: list[str] = []
        for item in ordered:
            try:
                result = item.transcribe(wav)
                if not result or not result.get("ok"):
                    failures.append(f"{item.name}: unsuccessful result")
                    continue
                enriched = dict(result)
                enriched.setdefault("backend", item.name)
                return enriched
            except Exception as exc:
                failures.append(f"{item.name}: {type(exc).__name__}: {exc}")
        raise TranscriptionUnavailable("; ".join(failures) or "no transcription backends registered")


__all__ = [
    "BackendUnavailable",
    "TranscriptionBackend",
    "TranscriptionRouter",
    "TranscriptionUnavailable",
]
