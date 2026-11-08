"""Fail-closed classification for Codex final-message receipts."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
import re
from typing import Any


@dataclass(frozen=True)
class ReceiptDecision:
    state: str
    valid: bool
    format: str


INVALID_RECEIPT = ReceiptDecision(state="blocked", valid=False, format="unknown")


def _classify_structured(
    receipt: Any, *, work_order: str, exit_code: int
) -> ReceiptDecision:
    if not isinstance(receipt, dict) or receipt.get("work_order") != work_order:
        return INVALID_RECEIPT
    status = receipt.get("status")
    if not isinstance(status, str):
        return INVALID_RECEIPT
    if status == "BLOCKED":
        return ReceiptDecision(state="blocked", valid=True, format="json")
    evidence = receipt.get("evidence")
    landed_files = receipt.get("landed_files")
    valid_payload = (
        isinstance(evidence, list)
        and bool(evidence)
        and all(isinstance(path, str) and Path(path).is_file() for path in evidence)
        and isinstance(landed_files, list)
    )
    if (
        exit_code == 0
        and valid_payload
        and status in {"READY_FOR_REVIEW", "READY_FOR_DEEPSEEK_AUDIT"}
    ):
        return ReceiptDecision(state="audit", valid=True, format="json")
    return INVALID_RECEIPT


def _classify_text(text: str, *, work_order: str, exit_code: int) -> ReceiptDecision:
    if not re.search(rf"(?<![\w-]){re.escape(work_order)}(?![\w-])", text):
        return INVALID_RECEIPT
    blocked = re.search(
        r"(?:当前状态|完成状态)\s*[：:]?[^\r\n]{0,120}\bBLOCKED\b",
        text,
        re.IGNORECASE,
    )
    if blocked:
        return ReceiptDecision(state="blocked", valid=True, format="text")
    audit_marker = re.search(
        r"\b(?:READY_FOR_DEEPSEEK_AUDIT|READY_FOR_REVIEW)\b", text
    )
    selfcheck_pass = re.search(
        r"自检\s*[：:]?\s*(?:PASS|通过)", text, re.IGNORECASE
    )
    if exit_code == 0 and audit_marker and selfcheck_pass:
        return ReceiptDecision(state="audit", valid=True, format="text")
    return INVALID_RECEIPT


def classify_receipt_path(
    path: str | Path, *, work_order: str, exit_code: int
) -> ReceiptDecision:
    receipt_path = Path(path)
    try:
        text = receipt_path.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError):
        return INVALID_RECEIPT
    if not text.strip():
        return INVALID_RECEIPT
    try:
        structured = json.loads(text)
    except (TypeError, ValueError):
        return _classify_text(text, work_order=work_order, exit_code=exit_code)
    return _classify_structured(
        structured, work_order=work_order, exit_code=exit_code
    )


__all__ = ["ReceiptDecision", "classify_receipt_path"]
