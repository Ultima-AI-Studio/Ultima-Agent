from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate_work_order.py"
CARD = ROOT / "tasks" / "queue" / "wo-ultimaagent-20261108-0031--m2-workorder-contract.md"


def load_validator():
    if not SCRIPT.is_file():
        pytest.fail(f"validator script is missing: {SCRIPT}")
    spec = importlib.util.spec_from_file_location("validate_work_order", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def changed_card(tmp_path: Path, old: str, new: str) -> Path:
    text = CARD.read_text(encoding="utf-8")
    assert old in text
    path = tmp_path / "wo-negative.md"
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    return path


def error(report, code: str) -> dict:
    matches = [item for item in report.errors if item["code"] == code]
    assert matches, report.errors
    assert matches[0]["line"] is not None
    return matches[0]


def test_current_card_passes_structured_contract():
    validator = load_validator()
    report = validator.validate(CARD)

    assert report.status == "PASS"
    assert report.order == "wo-ultimaagent-20261108-0031"
    assert report.errors == []


def test_every_existing_queue_card_passes_default_compatibility():
    validator = load_validator()
    cards = sorted((ROOT / "tasks" / "queue").glob("wo-*.md"))
    assert len(cards) >= 6

    failures = {card.name: validator.validate(card).errors for card in cards if validator.validate(card).status != "PASS"}

    assert failures == {}


def test_missing_non_goals_fails_with_source_line(tmp_path: Path):
    validator = load_validator()
    path = changed_card(tmp_path, "**本阶段不做（Non-goals）**", "**范围补充**")

    item = error(validator.validate(path), validator.E_NO_FORBIDDEN)

    assert "不做" in item["message"]


def test_task_table_and_details_mismatch_names_task_and_line(tmp_path: Path):
    validator = load_validator()
    path = changed_card(tmp_path, "| T4 | 总验收 |", "| T9 | 总验收 |")

    item = error(validator.validate(path), validator.E_T_SET_MISMATCH)

    assert "T9" in item["message"]


def test_missing_forbidden_block_names_task_and_line(tmp_path: Path):
    validator = load_validator()
    path = changed_card(
        tmp_path,
        "**禁止**：\n- 不得把 DoR 检查做成\"警告继续跑\"。",
        "**边界补充**：\n- 不得把 DoR 检查做成\"警告继续跑\"。",
    )

    item = error(validator.validate(path), validator.E_MISSING_DETAIL_FIELD)

    assert "T2" in item["message"]
    assert "forbidden" in item["message"]


def test_unknown_status_fails_as_not_dispatchable_at_header_line(tmp_path: Path):
    validator = load_validator()
    path = changed_card(tmp_path, "状态：可开工", "状态：执行中")

    item = error(validator.validate(path), validator.E_STATUS_NOT_DISPATCHABLE)

    assert item["line"] == 3


def test_completed_status_can_be_validated_outside_dispatch_context(tmp_path: Path):
    validator = load_validator()
    path = changed_card(tmp_path, "状态：可开工", "状态：已完成")

    assert validator.validate(path).status == "FAIL"
    assert validator.validate(path, dispatch_status=False).status == "PASS"


def test_revision_format_error_has_header_line(tmp_path: Path):
    validator = load_validator()
    path = changed_card(tmp_path, "163df2c0b044945b01ebd395cb2743bb3676eda9", "not-a-revision")

    item = error(validator.validate(path), validator.E_REVISION_FORMAT)

    assert "revision" in item["message"]


def test_weak_gate_names_affected_task(tmp_path: Path):
    validator = load_validator()
    path = changed_card(
        tmp_path,
        "1. `pytest tests\\test_dor_gate.py -o addopts= -q` 全绿，用例数 ≥5。",
        "1. 代码质量良好。",
    )

    item = error(validator.validate(path), validator.E_GATE_WEAK)

    assert "T2" in item["message"]


def test_json_cli_stdout_is_parseable_and_matches_exit_code():
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), str(CARD), "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )

    payload = json.loads(completed.stdout)
    assert completed.returncode == 0
    assert payload["status"] == "PASS"
    assert payload["errors"] == []


def test_strict_promotes_legacy_warning_to_failure():
    validator = load_validator()
    legacy = ROOT / "tasks" / "queue" / "wo-s1-engineering-packaging.md"

    normal = validator.validate(legacy)
    strict = validator.validate(legacy, strict=True)

    assert normal.status == "PASS"
    assert any(item["code"] == validator.W_LEGACY_PROFILE for item in normal.warnings)
    assert strict.status == "FAIL"
