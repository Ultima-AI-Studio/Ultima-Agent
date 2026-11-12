"""Resolve effective S-MAIN settings to a protocol adapter."""

from __future__ import annotations

from typing import Any

from .base import ChatProvider, ProviderConfigError
from .ollama_native import OllamaNativeProvider
from .openai_compat import OpenAICompatProvider

_OLLAMA_IMPLS = frozenset({"ollama", "ollama-8b"})
_OPENAI_COMPAT_IMPLS = frozenset({"openai", "openai-compatible", "lmstudio", "vllm"})


def provider_for(settings: dict[str, Any]) -> ChatProvider:
    impl = str(settings.get("impl") or "").strip().lower()
    if impl in _OLLAMA_IMPLS:
        return OllamaNativeProvider(settings)
    if impl in _OPENAI_COMPAT_IMPLS:
        return OpenAICompatProvider(settings)
    raise ProviderConfigError(f"不支持的 S-MAIN provider impl: {impl or '<empty>'}")


__all__ = ["provider_for"]
