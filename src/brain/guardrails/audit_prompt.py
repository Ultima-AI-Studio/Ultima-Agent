"""Strict loader and adapter for the independent LLM audit role.

The LLM audit is evidence triage for the existing deterministic reviewer.  It
does not introduce another severity scale or delivery gate: validated model
output is converted into :class:`ReviewResult` through
:class:`IndependentReviewer`.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .reviewer import AUDIT_ROLES, SEVERITIES, IndependentReviewer, ReviewResult


DEFAULT_AUDIT_PROMPT_PATH = Path(__file__).with_name("prompts") / "independent-auditor.md"

AUDIT_OUTPUT_JSON_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "severity": {"type": "string", "enum": list(SEVERITIES)},
                    "item": {"type": "string", "minLength": 1},
                    "detail": {"type": "string"},
                },
                "required": ["severity", "item", "detail"],
                "additionalProperties": False,
            },
        },
        "gate": {"type": "string", "enum": ["PASS", "FAIL"]},
    },
    "required": ["findings", "gate"],
    "additionalProperties": False,
}


class AuditPromptError(ValueError):
    """Raised when the audit role, prompt source, or LLM output is unsafe."""


def _validate_role(role: str) -> None:
    if role not in AUDIT_ROLES:
        raise AuditPromptError(f"independent audit is limited to {AUDIT_ROLES}; got {role!r}")


def load_audit_prompt(
    role: str,
    *,
    path: str | Path = DEFAULT_AUDIT_PROMPT_PATH,
) -> str:
    """Load the independent audit prompt, failing closed on role or I/O errors."""
    _validate_role(role)
    prompt_path = Path(path)
    try:
        content = prompt_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise AuditPromptError(f"audit prompt source unavailable: {prompt_path}") from exc
    if not content:
        raise AuditPromptError(f"audit prompt source is empty: {prompt_path}")
    return content


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise AuditPromptError(f"duplicate field: {key}")
        value[key] = item
    return value


def _reject_constant(value: str) -> Any:
    raise AuditPromptError(f"non-JSON numeric constant: {value}")


def _expect_exact_fields(value: dict[str, Any], required: set[str], label: str) -> None:
    fields = set(value)
    if fields != required:
        missing = sorted(required - fields)
        extra = sorted(fields - required)
        raise AuditPromptError(f"{label} field mismatch: missing={missing}, extra={extra}")


def parse_audit_output(content: str, *, role: str) -> ReviewResult:
    """Validate strict audit JSON and adapt it to the deterministic gate model."""
    _validate_role(role)
    try:
        value = json.loads(
            content,
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except json.JSONDecodeError as exc:
        raise AuditPromptError(f"invalid audit JSON: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise AuditPromptError("audit output must be a JSON object")
    _expect_exact_fields(value, {"findings", "gate"}, "audit output")

    findings = value["findings"]
    supplied_gate = value["gate"]
    if not isinstance(findings, list):
        raise AuditPromptError("findings must be an array")
    if supplied_gate not in ("PASS", "FAIL"):
        raise AuditPromptError("gate must be PASS or FAIL")

    reviewer = IndependentReviewer(role)
    for index, finding in enumerate(findings):
        if not isinstance(finding, dict):
            raise AuditPromptError(f"findings[{index}] must be an object")
        _expect_exact_fields(finding, {"severity", "item", "detail"}, f"findings[{index}]")
        severity = finding["severity"]
        item = finding["item"]
        detail = finding["detail"]
        if severity not in SEVERITIES:
            raise AuditPromptError(f"findings[{index}].severity must be one of {SEVERITIES}")
        if not isinstance(item, str) or not item.strip():
            raise AuditPromptError(f"findings[{index}].item must be non-empty text")
        if not isinstance(detail, str):
            raise AuditPromptError(f"findings[{index}].detail must be text")
        reviewer.add_finding(severity, item.strip(), detail.strip())

    reviewer.checked.append("llm-audit-output")
    result = reviewer.gate()
    expected_gate = "PASS" if result.ok else "FAIL"
    if supplied_gate != expected_gate:
        raise AuditPromptError(
            f"gate conflicts with deterministic reviewer: expected {expected_gate}, got {supplied_gate}"
        )
    return result


__all__ = [
    "AUDIT_OUTPUT_JSON_SCHEMA",
    "AuditPromptError",
    "DEFAULT_AUDIT_PROMPT_PATH",
    "load_audit_prompt",
    "parse_audit_output",
]
