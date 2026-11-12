from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit-work-order.py"


def _load_audit():
    spec = importlib.util.spec_from_file_location("audit_passed_0048", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _round(passed: bool) -> dict:
    return {
        "passed": passed,
        "per_gate": {f"T{i}": "PASS" for i in range(5)},
    }


def test_two_all_pass_rounds_are_a_pass_even_when_input_is_marked_incomplete() -> None:
    audit = _load_audit()
    assert audit._audit_passed(
        _round(True), _round(True), ["large evidence object"], []
    ) is True


def test_one_failed_round_is_not_a_pass() -> None:
    audit = _load_audit()
    assert audit._audit_passed(_round(True), _round(False), [], []) is False


def test_integrity_error_still_blocks_an_all_pass_audit() -> None:
    audit = _load_audit()
    assert audit._audit_passed(
        _round(True), _round(True), [], ["evidence hash mismatch"]
    ) is False
