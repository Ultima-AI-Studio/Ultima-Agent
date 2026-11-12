"""Ollama native ``/api/chat`` adapter."""

from __future__ import annotations

from json import dumps, loads
from typing import Any
from urllib.request import Request, urlopen

from .base import ChatProvider, ChatResult, messages_with_system


class OllamaNativeProvider(ChatProvider):
    def __init__(self, settings: dict[str, Any]) -> None:
        self.endpoint = str(settings.get("endpoint") or "").rstrip("/")
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
        body: dict[str, Any] = {
            "model": self.model,
            "messages": messages_with_system(system_prompt, messages),
            "stream": False,
        }
        if temperature is not None or max_tokens is not None:
            body["options"] = {}
            if temperature is not None:
                body["options"]["temperature"] = temperature
            if max_tokens is not None:
                body["options"]["num_predict"] = max_tokens
        if disable_thinking:
            body["think"] = False
        if json_schema is not None:
            body["format"] = json_schema

        url = self.endpoint if self.endpoint.endswith("/api/chat") else self.endpoint + "/api/chat"
        request = Request(
            url,
            data=dumps(body, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=timeout) as response:
            raw = loads(response.read().decode("utf-8"))

        content = (raw.get("message") or {}).get("content", "")
        if not isinstance(content, str):
            raise TypeError("Ollama message content must be a string")
        usage = raw.get("usage")
        if not isinstance(usage, dict):
            prompt_tokens = int(raw.get("prompt_eval_count") or 0)
            completion_tokens = int(raw.get("eval_count") or 0)
            usage = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            }
        return ChatResult(content=content, raw=raw, usage=usage)
