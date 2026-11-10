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
    # 自检通过的证据不止「自检 PASS」一种写法：执行端更常写「14 passed」、
    # 「PYTEST_EXIT_CODE=0」。只认那一条字面文案，会把干完活、只是换了说法的
    # 回执一律判成 invalid——2026-11-10 核对 ORB-W6/W7 就是这么被误判成 blocked 的。
    selfcheck_pass = (
        re.search(r"自检\s*[：:]?\s*(?:PASS|通过)", text, re.IGNORECASE)
        or re.search(r"PYTEST_EXIT_CODE\s*[=:]\s*0\b", text, re.IGNORECASE)
        or re.search(r"\b\d+\s+passed\b", text, re.IGNORECASE)
    )
    # 出现失败计数时，前面的 passed 数字不能当作通过证据。
    # 注意：不能因为文本里出现 "failed" 就否决——真实回执里既有「修复前 3 failed」
    # 这种复现记录，也有「28 项历史债」这种沿用结论（ORB-W7 就是这样被二次误伤）。
    # 本次是否通过由 exit_code 和执行端 READY 声明共同决定，历史失败只在正文里叙述。
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
