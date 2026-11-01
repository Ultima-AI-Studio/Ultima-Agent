"""Hard reply checks applied after an Agent answer and before playback."""

from __future__ import annotations

import json
import logging
import re
import threading
from dataclasses import dataclass
from typing import Sequence

from .config import DEFAULT_ROUTING_CONFIG, RoutingConfig
from .intent_gate import EmbeddingChannel, OllamaEmbeddingChannel, cosine_similarity

LOGGER = logging.getLogger(__name__)
DEFAULT_REPLY_CONFIDENCE_THRESHOLD = 0.6

_MARKETING_CONTEXT = re.compile(
    r"(?:请|记得|欢迎|别忘了|点击|点个|求|帮忙).{0,6}(?:关注|点赞|订阅)|"
    r"(?:关注|点赞|订阅).{0,6}(?:我|我们|账号|频道|主播|作者|支持)"
)
_SEMANTIC_BANNED_EXAMPLES = (
    "请关注我",
    "记得支持我的频道",
    "欢迎订阅我们的内容",
    "帮我点个赞",
)


@dataclass(frozen=True, slots=True)
class ReplySchema:
    """Work-order D compatible fields; grounded enforcement is disabled for C."""

    reply_text: str
    confidence: float | None = None
    grounded: bool | None = None


@dataclass(frozen=True, slots=True)
class VerificationResult:
    accepted: bool
    text: str
    issues: tuple[str, ...]
    grounded_checked: bool
    semantic_similarity: float | None = None


def split_sentences(text: str) -> list[str]:
    return [item.strip() for item in re.findall(r"[^。！？!?]+[。！？!?]?", text) if item.strip()]


class ReplyVerifier:
    def __init__(
        self,
        banned_phrases: Sequence[str],
        max_sentences: int,
        *,
        config: RoutingConfig = DEFAULT_ROUTING_CONFIG,
        embedding_channel: EmbeddingChannel | None = None,
        enforce_grounded: bool = False,
        enforce_confidence: bool = False,
        confidence_threshold: float = DEFAULT_REPLY_CONFIDENCE_THRESHOLD,
    ) -> None:
        self.banned_phrases = tuple(phrase.strip() for phrase in banned_phrases if phrase.strip())
        self.max_sentences = max(1, int(max_sentences))
        self.config = config
        self.enforce_grounded = enforce_grounded
        self.enforce_confidence = enforce_confidence
        self.confidence_threshold = float(confidence_threshold)
        self._embedding_channel = embedding_channel or OllamaEmbeddingChannel(config)
        self._prototype_vectors: list[list[float]] | None = None
        self._embedding_lock = threading.Lock()

    def verify(self, reply: ReplySchema | str) -> VerificationResult:
        schema = reply if isinstance(reply, ReplySchema) else ReplySchema(str(reply))
        text = schema.reply_text.strip()
        issues: list[str] = []
        similarity: float | None = None
        if not text:
            issues.append("empty_reply")
        if text and self._has_rule_banned(text):
            issues.append("banned_rule")
        elif text:
            try:
                similarity = self._banned_similarity(text)
                if similarity >= self.config.banned_similarity_threshold:
                    issues.append("banned_semantic")
            except (OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                LOGGER.warning("reply semantic check unavailable: %s", type(exc).__name__)

        if self.enforce_grounded and schema.grounded is not True:
            issues.append("grounded_required")
        if self.enforce_confidence:
            confidence = schema.confidence
            if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
                issues.append("confidence_required")
            elif not 0 <= float(confidence) <= 1:
                issues.append("confidence_invalid")
            elif float(confidence) < self.confidence_threshold:
                issues.append("confidence_below_threshold")

        sentences = split_sentences(text)
        if len(sentences) > self.max_sentences:
            text = "".join(sentences[: self.max_sentences]).strip()
            issues.append("sentence_limit_truncated")

        blocking = tuple(issue for issue in issues if issue != "sentence_limit_truncated")
        accepted = not blocking
        LOGGER.info(
            "reply_verifier accepted=%s issues=%s grounded_checked=%s",
            accepted,
            ",".join(issues) or "none",
            self.enforce_grounded,
        )
        return VerificationResult(
            accepted=accepted,
            text=text,
            issues=tuple(issues),
            grounded_checked=self.enforce_grounded,
            semantic_similarity=similarity,
        )

    def _has_rule_banned(self, text: str) -> bool:
        if _MARKETING_CONTEXT.search(text):
            return True
        return any(
            phrase in text and phrase not in {"关注", "点赞", "订阅"}
            for phrase in self.banned_phrases
        )

    def _banned_similarity(self, text: str) -> float:
        # Single-token vectors such as "关注" are overly broad for short Chinese
        # replies; exact/profile words are handled above, while embeddings use
        # complete marketing intents to avoid rejecting ordinary factual answers.
        prototypes = _SEMANTIC_BANNED_EXAMPLES
        with self._embedding_lock:
            if self._prototype_vectors is None:
                self._prototype_vectors = self._embedding_channel.embed(prototypes)
            segments = split_sentences(text) or [text]
            vectors = self._embedding_channel.embed(segments)
            candidates = tuple(self._prototype_vectors)
        return max(
            cosine_similarity(vector, prototype)
            for vector in vectors
            for prototype in candidates
        )


_VERIFIERS: dict[tuple[tuple[str, ...], int, bool, bool, float], ReplyVerifier] = {}
_VERIFIER_LOCK = threading.Lock()


def get_reply_verifier(
    banned_phrases: Sequence[str],
    max_sentences: int,
    *,
    enforce_grounded: bool = False,
    enforce_confidence: bool = False,
    confidence_threshold: float = DEFAULT_REPLY_CONFIDENCE_THRESHOLD,
) -> ReplyVerifier:
    key = (
        tuple(banned_phrases),
        int(max_sentences),
        bool(enforce_grounded),
        bool(enforce_confidence),
        float(confidence_threshold),
    )
    with _VERIFIER_LOCK:
        verifier = _VERIFIERS.get(key)
        if verifier is None:
            verifier = ReplyVerifier(
                key[0],
                key[1],
                enforce_grounded=key[2],
                enforce_confidence=key[3],
                confidence_threshold=key[4],
            )
            _VERIFIERS[key] = verifier
        return verifier


__all__ = [
    "DEFAULT_REPLY_CONFIDENCE_THRESHOLD",
    "ReplySchema",
    "ReplyVerifier",
    "VerificationResult",
    "get_reply_verifier",
    "split_sentences",
]
