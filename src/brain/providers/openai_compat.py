"""OpenAI-compatible ``/chat/completions`` adapter."""

from __future__ import annotations

from json import dumps, loads
from typing import Any
from urllib.request import Request, urlopen

from ..slot_adapter import main_chat_url
from .base import ChatProvider, ChatResult, messages_with_system


class OpenAICompatProvider(ChatProvider):
    def __init__(self, settings: dict[str, Any]) -> None:
        self.settings = dict(settings)
        self.model = str(settings.get("model") or "")

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
        del disable_thinking  # This protocol has no native thinking switch.
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages_with_system(system_prompt, messages),
        }
        if temperature is not None:
            body["temperature"] = temperature
        if max_tokens is not None:
            body["max_tokens"] = max_tokens
        if json_schema is not None:
            body["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema,
            }

        headers = {"Content-Type": "application/json; charset=utf-8"}
        api_key = str(self.settings.get("api_key") or "").strip()
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        request = Request(
            main_chat_url(self.settings),
            data=dumps(body, ensure_ascii=False).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            raw = loads(response.read().decode("utf-8"))

        choices = raw.get("choices") or []
        content = ((choices[0].get("message") or {}).get("content", "")) if choices else ""
        if not isinstance(content, str):
            raise TypeError("OpenAI-compatible message content must be a string")
        usage = raw.get("usage")
        return ChatResult(
            content=content,
            raw=raw,
            usage=usage if isinstance(usage, dict) else {},
        )
