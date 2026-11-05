"""Fail-closed validation for content proposed for long-term memory.

Adapted from ``AdelElo13/DockWright-MacOS-Agent``
``Dockwright/Core/Memory/MemoryPoisonGuard.swift`` at commit
``d6d3f3f71fc83afc9df3f74f9376413084777b90``.
MIT License, Copyright (c) 2026 Adel Elo.
See ``docs/research/sources/dockwright/LICENSE``.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PoisonDecision:
    allowed: bool
    category: str | None = None
    reason: str | None = None


class MemoryPoisonGuard:
    """Evaluate a proposed memory before any storage side effect occurs."""

    _INJECTION_PHRASES = (
        "always remember",
        "never forget",
        "from now on",
        "your instructions are",
        "you must always",
        "you must never",
        "ignore previous",
        "ignore all previous",
        "disregard your",
        "override your",
        "your new instruction",
        "system prompt",
        "jailbreak",
        "developer mode",
        "永远记住",
        "忽略之前",
        "无视以上",
        "从现在开始",
        "你的新指令",
        "系统提示词",
        "隐藏指令",
        "altijd onthouden",
        "nooit vergeten",
        "vanaf nu",
        "je instructies zijn",
        "negeer vorige",
        "a partir de ahora",
        "ignora las instrucciones anteriores",
        "これまでの指示を無視",
        "システムプロンプト",
    )

    _SECRET_PATTERNS = tuple(
        re.compile(pattern)
        for pattern in (
            r"(?i)(?:api[_\s-]?key|access[_\s-]?token|secret[_\s-]?key)\s*(?:is|=|:)\s*\S+",
            r"(?i)(?:password|wachtwoord|passcode)\s*(?:is|=|:)\s*\S+",
            r"\bsk-ant-[A-Za-z0-9_-]{20,}\b",
            r"\bsk-[A-Za-z0-9_-]{20,}\b",
            r"\bAIza[A-Za-z0-9_-]{20,}\b",
            r"(?i)\bbearer\s+[A-Za-z0-9._~+/=-]{20,}\b",
            r"\b\d{13,19}\b",
            r"(?i)(?:credit.?card|bank.?account|routing.?number|cvv|pin.?code|银行卡号)\s*(?:is|是|=|:)",
            r"(?i)(?:ssn|social.?security)\s*(?:number\s*)?(?:is\s*)?(?:=|:)?\s*\d{3}-?\d{2}-?\d{4}",
        )
    )

    _INSTRUCTION_PATTERNS = tuple(
        re.compile(pattern, re.IGNORECASE)
        for pattern in (
            r"^(?:you should|you must|you need to|you have to|always|never)\s",
            r"^(?:do not|don't|dont)\s+(?:ever|tell|share|reveal|mention)",
            r"^(?:when asked|if someone|if anyone|if they)\s",
            r"(?:respond with|reply with|answer with|say that)\s",
        )
    )

    def evaluate(self, content: str) -> PoisonDecision:
        if not isinstance(content, str):
            return PoisonDecision(False, "type", "memory content must be text")

        normalized = unicodedata.normalize("NFKC", content)
        lowered = normalized.casefold()
        for phrase in self._INJECTION_PHRASES:
            if phrase.casefold() in lowered:
                return PoisonDecision(False, "injection", f"contains injection phrase: {phrase}")

        for pattern in self._SECRET_PATTERNS:
            if pattern.search(normalized):
                return PoisonDecision(False, "secret", "contains credential or sensitive identifier")

        for pattern in self._INSTRUCTION_PATTERNS:
            if pattern.search(normalized):
                return PoisonDecision(False, "instruction", "looks like an instruction rather than a fact")

        trimmed = normalized.strip()
        if len(trimmed) < 5:
            return PoisonDecision(False, "length", "memory is shorter than 5 characters")
        if len(trimmed) > 500:
            return PoisonDecision(False, "length", "memory is longer than 500 characters")

        cased = [char for char in trimmed if char.isalpha() and char.lower() != char.upper()]
        if len(trimmed) > 10 and cased:
            uppercase_ratio = sum(char.isupper() for char in cased) / len(cased)
            if uppercase_ratio > 0.7:
                return PoisonDecision(False, "uppercase", "excessive uppercase content")

        return PoisonDecision(True)


__all__ = ["MemoryPoisonGuard", "PoisonDecision"]
