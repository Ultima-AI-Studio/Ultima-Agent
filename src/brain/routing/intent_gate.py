"""Three-state local intent gate used before text can enter the Agent."""

from __future__ import annotations

import json
import logging
import math
import re
import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, Sequence
from urllib.request import Request, urlopen

from .config import (
    ALLOW_PATTERNS,
    ALLOW_PROTOTYPES,
    ASR_CORRECTION_MARKERS,
    DEFAULT_ROUTING_CONFIG,
    DENY_PATTERNS,
    DENY_PROTOTYPES,
    UNTRUSTED_ASR_FRAGMENTS,
    RoutingConfig,
)

LOGGER = logging.getLogger(__name__)


class RouteState(StrEnum):
    ALLOW = "ALLOW"
    DENY = "DENY"
    ABSTAIN = "ABSTAIN"


@dataclass(frozen=True, slots=True)
class IntentDecision:
    state: RouteState
    confidence: float
    reason: str
    reply: str = ""
    allow_similarity: float | None = None
    deny_similarity: float | None = None


class EmbeddingChannel(Protocol):
    def embed(self, texts: Sequence[str]) -> list[list[float]]: ...


class OllamaEmbeddingChannel:
    """Small standard-library client for memory/backend.py's Ollama channel."""

    def __init__(self, config: RoutingConfig = DEFAULT_ROUTING_CONFIG) -> None:
        self._config = config

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        payload = json.dumps(
            {"model": self._config.embedding_model, "input": list(texts)},
            ensure_ascii=False,
        ).encode("utf-8")
        request = Request(
            self._config.ollama_embed_url,
            data=payload,
            headers={"Content-Type": "application/json; charset=utf-8"},
            method="POST",
        )
        with urlopen(request, timeout=30) as response:
            body = json.load(response)
        vectors = body.get("embeddings", []) if isinstance(body, dict) else []
        if len(vectors) != len(texts):
            raise ValueError("Ollama embedding response count mismatch")
        return [[float(value) for value in vector] for vector in vectors]


def cosine_similarity(left: Sequence[float], right: Sequence[float]) -> float:
    if len(left) != len(right) or not left:
        return 0.0
    denominator = math.sqrt(sum(value * value for value in left)) * math.sqrt(
        sum(value * value for value in right)
    )
    if denominator == 0:
        return 0.0
    return sum(a * b for a, b in zip(left, right, strict=True)) / denominator


class IntentGate:
    """Rules first, then local embedding similarity, with fail-closed abstention."""

    def __init__(
        self,
        config: RoutingConfig = DEFAULT_ROUTING_CONFIG,
        *,
        embedding_channel: EmbeddingChannel | None = None,
    ) -> None:
        self.config = config
        self._embedding_channel = embedding_channel or OllamaEmbeddingChannel(config)
        self._allow_rules = tuple(re.compile(pattern, re.IGNORECASE) for pattern in ALLOW_PATTERNS)
        self._deny_rules = tuple(re.compile(pattern, re.IGNORECASE) for pattern in DENY_PATTERNS)
        self._prototype_vectors: tuple[list[list[float]], list[list[float]]] | None = None
        self._embedding_lock = threading.Lock()

    def route(
        self,
        text: str | None,
        *,
        asr_confidence: float | None = None,
        asr_corrected: bool = False,
    ) -> IntentDecision:
        value = text.strip() if isinstance(text, str) else ""
        if not value:
            return self._decision(RouteState.ABSTAIN, 1.0, "empty_input")
        if asr_corrected or any(marker.lower() in value.lower() for marker in ASR_CORRECTION_MARKERS):
            return self._decision(RouteState.ABSTAIN, 1.0, "asr_corrected")
        if asr_confidence is not None and asr_confidence < self.config.low_asr_confidence:
            return self._decision(RouteState.ABSTAIN, 1.0 - max(0.0, asr_confidence), "low_asr_confidence")
        if any(fragment in value for fragment in UNTRUSTED_ASR_FRAGMENTS):
            return self._decision(RouteState.ABSTAIN, 0.99, "untrusted_asr_fragment")
        if any(rule.search(value) for rule in self._deny_rules):
            return self._decision(RouteState.DENY, 0.99, "deny_rule")
        if any(rule.search(value) for rule in self._allow_rules):
            return self._decision(RouteState.ALLOW, 0.98, "allow_rule")

        try:
            allow_score, deny_score = self._similarity_scores(value)
        except (OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
            LOGGER.warning("routing embedding unavailable; abstaining: %s", type(exc).__name__)
            return self._decision(RouteState.ABSTAIN, 0.0, "embedding_unavailable")

        if (
            deny_score >= self.config.deny_similarity_threshold
            and deny_score >= allow_score + self.config.similarity_margin
        ):
            return self._decision(
                RouteState.DENY,
                deny_score,
                "deny_similarity",
                allow_similarity=allow_score,
                deny_similarity=deny_score,
            )
        if (
            allow_score >= self.config.allow_similarity_threshold
            and allow_score >= deny_score
        ):
            return self._decision(
                RouteState.ALLOW,
                allow_score,
                "allow_similarity",
                allow_similarity=allow_score,
                deny_similarity=deny_score,
            )
        confidence = max(0.0, 1.0 - max(allow_score, deny_score))
        return self._decision(
            RouteState.ABSTAIN,
            confidence,
            "low_similarity",
            allow_similarity=allow_score,
            deny_similarity=deny_score,
        )

    def _similarity_scores(self, text: str) -> tuple[float, float]:
        with self._embedding_lock:
            if self._prototype_vectors is None:
                prototypes = self._embedding_channel.embed((*ALLOW_PROTOTYPES, *DENY_PROTOTYPES))
                split = len(ALLOW_PROTOTYPES)
                self._prototype_vectors = (prototypes[:split], prototypes[split:])
            vector = self._embedding_channel.embed((text,))[0]
            allow_vectors, deny_vectors = self._prototype_vectors
        allow_score = max(cosine_similarity(vector, candidate) for candidate in allow_vectors)
        deny_score = max(cosine_similarity(vector, candidate) for candidate in deny_vectors)
        return allow_score, deny_score

    def _decision(
        self,
        state: RouteState,
        confidence: float,
        reason: str,
        *,
        allow_similarity: float | None = None,
        deny_similarity: float | None = None,
    ) -> IntentDecision:
        reply = ""
        if state is RouteState.DENY:
            reply = self.config.deny_reply
        elif state is RouteState.ABSTAIN:
            reply = self.config.abstain_reply
        decision = IntentDecision(
            state=state,
            confidence=round(max(0.0, min(1.0, confidence)), 4),
            reason=reason,
            reply=reply,
            allow_similarity=allow_similarity,
            deny_similarity=deny_similarity,
        )
        LOGGER.info(
            "routing decision=%s confidence=%.4f reason=%s",
            decision.state,
            decision.confidence,
            decision.reason,
        )
        return decision


_DEFAULT_GATE: IntentGate | None = None
_DEFAULT_GATE_LOCK = threading.Lock()


def get_intent_gate() -> IntentGate:
    global _DEFAULT_GATE
    if _DEFAULT_GATE is None:
        with _DEFAULT_GATE_LOCK:
            if _DEFAULT_GATE is None:
                _DEFAULT_GATE = IntentGate()
    return _DEFAULT_GATE


__all__ = [
    "EmbeddingChannel",
    "IntentDecision",
    "IntentGate",
    "OllamaEmbeddingChannel",
    "RouteState",
    "cosine_similarity",
    "get_intent_gate",
]
