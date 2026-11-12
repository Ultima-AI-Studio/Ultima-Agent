"""Shared contract for main-brain chat protocol adapters."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


class ProviderConfigError(RuntimeError):
    """The effective S-MAIN settings do not identify a supported provider."""


@dataclass(frozen=True)
class ChatResult:
    content: str
    raw: dict[str, Any]
    usage: dict[str, Any]


class ChatProvider(ABC):
    """Minimal provider interface consumed by the main-brain service."""

    @abstractmethod
    def chat(
        self,
        *,
        system_prompt: str,
        messages: list[dict[str, Any]],
        temperature: float | None,
        max_tokens: int | None,
        json_schema: dict[str, Any] | None = None,
        disable_thinking: bool = False,
        timeout: float,
    ) -> ChatResult:
        """Send one provider-specific chat request and normalize its result."""


def messages_with_system(
    system_prompt: str, messages: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    if not system_prompt:
        return list(messages)
    return [{"role": "system", "content": system_prompt}, *messages]
