"""Strict JSON schema and parser for replies exposed by the Agent server."""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass
from typing import Any


REPLY_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply_text": {"type": "string", "minLength": 1},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "grounded": {"type": "boolean"},
    },
    "required": ["reply_text", "confidence", "grounded"],
    "additionalProperties": False,
}
_REQUIRED_FIELDS = frozenset(REPLY_JSON_SCHEMA["required"])


class StructuredReplyError(ValueError):
    """Raised when model output is not exactly the approved reply object."""


@dataclass(frozen=True, slots=True)
class StructuredReply:
    reply_text: str
    confidence: float
    grounded: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise StructuredReplyError(f"duplicate field: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise StructuredReplyError(f"non-JSON numeric constant: {value}")


def parse_structured_reply(content: str) -> StructuredReply:
    """Parse one complete object; reject wrappers, coercions, and extra fields."""
    try:
        value = json.loads(
            content,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise StructuredReplyError(f"invalid JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise StructuredReplyError("reply must be a JSON object")
    fields = set(value)
    if fields != _REQUIRED_FIELDS:
        missing = sorted(_REQUIRED_FIELDS - fields)
        extra = sorted(fields - _REQUIRED_FIELDS)
        raise StructuredReplyError(f"field mismatch: missing={missing}, extra={extra}")
    reply_text = value["reply_text"]
    confidence = value["confidence"]
    grounded = value["grounded"]
    if not isinstance(reply_text, str) or not reply_text.strip():
        raise StructuredReplyError("reply_text must be a non-empty string")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)):
        raise StructuredReplyError("confidence must be a number")
    confidence_value = float(confidence)
    if not math.isfinite(confidence_value) or not 0 <= confidence_value <= 1:
        raise StructuredReplyError("confidence must be between 0 and 1")
    if not isinstance(grounded, bool):
        raise StructuredReplyError("grounded must be a boolean")
    return StructuredReply(reply_text.strip(), confidence_value, grounded)
