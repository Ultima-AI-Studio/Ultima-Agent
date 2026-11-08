"""Tests for the checklist form of the audit.

The rule these protect: gates decide the verdict, not the closing summary line.
The previous version read only the final 'AUDIT: PASS', so a reviewer that
flagged a gate as failing halfway up but closed with PASS still passed the round.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "audit-work-order.py"

CARD = """
| 编号 | 判据 | 判定方式 |
|---|---|---|
| ACC-1 | 目标文件已落地 | 检查文件存在 |
| ACC-2 | 回归测试全绿 | 跑 pytest |
| ACC-3 | 未越界改动 | git status 核对 |
"""


def _load():
    spec = importlib.util.spec_from_file_location("audit_wo", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_gates_are_parsed_from_the_card():
    gates = _load().gates(CARD)
    assert [g["id"] for g in gates] == ["ACC-1", "ACC-2", "ACC-3"]
    assert gates[0]["criterion"] == "目标文件已落地"


def test_all_gates_pass_and_summary_agrees():
    text = "ACC-1: PASS - file exists\nACC-2: PASS - 12 passed\nACC-3: PASS - clean\nAUDIT: PASS"
    ok, per_gate = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is True
    assert per_gate == {"ACC-1": "PASS", "ACC-2": "PASS", "ACC-3": "PASS"}


def test_summary_pass_cannot_override_a_failed_gate():
    """The whole point: a confident closing line does not launder a failed gate."""

    text = "ACC-1: PASS - file exists\nACC-2: FAIL - no test output\nACC-3: PASS - clean\nAUDIT: PASS"
    ok, per_gate = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is False
    assert per_gate["ACC-2"] == "FAIL"


def test_a_skipped_gate_counts_as_missing_not_pass():
    """Silence is not a pass; an unreviewed gate blocks the round."""

    text = "ACC-1: PASS - file exists\nAUDIT: PASS"
    ok, per_gate = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is False
    assert per_gate["ACC-2"] == "MISSING"
    assert per_gate["ACC-3"] == "MISSING"


def test_summary_fail_blocks_even_if_gates_pass():
    text = "ACC-1: PASS\nACC-2: PASS\nACC-3: PASS\nAUDIT: FAIL"
    ok, _ = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is False


def test_gate_ids_are_case_insensitive_in_responses():
    text = "acc-1: pass - ok\nACC-2: PASS - ok\nACC-3: PASS - ok\nAUDIT: PASS"
    ok, _ = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is True


def test_a_later_pass_cannot_erase_an_earlier_fail():
    """The earlier version kept the last verdict, so FAIL-then-PASS read as pass.

    A reviewer who contradicts themselves has not established anything; the worst
    verdict for a gate stands.
    """

    text = ("ACC-1: PASS - file exists\n"
            "ACC-2: FAIL - no test output\n"
            "ACC-2: PASS - tests fine after all\n"
            "ACC-3: PASS - clean\nAUDIT: PASS")
    ok, per_gate = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is False
    assert per_gate["ACC-2"] == "FAIL"


def test_summary_substring_cannot_pass_a_failing_line():
    """'AUDIT: FAIL, NOT PASS' contains the word PASS; substring tests were fooled."""

    text = "ACC-1: PASS - exists\nAUDIT: FAIL, NOT PASS"
    ok, _ = _load()._round_passed(text, ["ACC-1"])
    assert ok is False


def test_a_pass_without_evidence_is_not_a_pass():
    """A bare verdict asserts a conclusion without saying what it saw."""

    text = "ACC-1: PASS\nACC-2: PASS - 12 passed\nACC-3: PASS - clean\nAUDIT: PASS"
    ok, per_gate = _load()._round_passed(text, ["ACC-1", "ACC-2", "ACC-3"])
    assert ok is False
    assert per_gate["ACC-1"] == "MISSING"


def test_two_verdicts_for_one_gate_are_ambiguous_not_pass():
    """Exactly one verdict per gate; two PASS lines leave no verdict to stand on."""

    text = ("ACC-1: PASS - first evidence\nACC-1: PASS - second evidence\n"
            "AUDIT: PASS")
    ok, per_gate = _load()._round_passed(text, ["ACC-1"])
    assert ok is False
    assert per_gate["ACC-1"] == "AMBIGUOUS"


def test_a_card_reusing_a_gate_id_is_rejected():
    """Two rows numbered ACC-2 let one verdict stand in for two criteria."""

    import pytest
    duplicated = CARD + "| ACC-2 | 另一个判据 | 另一种判定 |\n"
    with pytest.raises(ValueError):
        _load().gates(duplicated)
