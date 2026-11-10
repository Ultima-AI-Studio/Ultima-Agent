from __future__ import annotations

import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
RUNS = ROOT / "tasks" / "queue" / "runs"


def _classifier():
    from tasks.queue_engine.receipt_contract import classify_receipt_path

    return classify_receipt_path


@pytest.mark.parametrize(
    ("run_name", "expected_state"),
    [
        ("wo-orb-w6-20261108T125637445858Z", "blocked"),
        ("wo-orb-w6-20261108T133604629405Z", "audit"),
    ],
)
def test_real_w6_receipts_map_to_their_explicit_terminal_state(
    run_name: str, expected_state: str
) -> None:
    classify_receipt_path = _classifier()

    decision = classify_receipt_path(
        RUNS / run_name / "final.json", work_order="wo-orb-w6", exit_code=0
    )

    assert decision.state == expected_state
    assert decision.valid is True


@pytest.mark.parametrize("content", ["", "unrecognized completion words"])
def test_empty_or_unknown_receipt_remains_fail_closed(
    content: str, tmp_path: Path
) -> None:
    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(content, encoding="utf-8")

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False


def test_audit_words_without_explicit_selfcheck_pass_remain_blocked(
    tmp_path: Path,
) -> None:
    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        "工单 wo-orb-w7 READY_FOR_DEEPSEEK_AUDIT but no check result",
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False


def test_existing_structured_ready_for_review_contract_stays_supported(
    tmp_path: Path,
) -> None:
    classify_receipt_path = _classifier()
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("fresh proof", encoding="utf-8")
    receipt = tmp_path / "final.json"
    receipt.write_text(
        json.dumps(
            {
                "work_order": "wo-orb-w7",
                "status": "READY_FOR_REVIEW",
                "evidence": [str(evidence)],
                "landed_files": [],
            }
        ),
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "audit"
    assert decision.valid is True


@pytest.mark.parametrize("status", [[], {}])
def test_non_string_structured_status_remains_fail_closed(
    status: object, tmp_path: Path
) -> None:
    classify_receipt_path = _classifier()
    evidence = tmp_path / "evidence.txt"
    evidence.write_text("fresh proof", encoding="utf-8")
    receipt = tmp_path / "final.json"
    receipt.write_text(
        json.dumps(
            {
                "work_order": "wo-orb-w7",
                "status": status,
                "evidence": [str(evidence)],
                "landed_files": [],
            }
        ),
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False


@pytest.mark.parametrize("sep", ["", " ", "：", ":"])
def test_text_receipt_accepts_fullwidth_colon_in_selfcheck(
    sep: str, tmp_path: Path
) -> None:
    """回归：Codex 回执写「- 自检：PASS」（全角冒号），必须仍判 audit。

    修复前该写法被判 INVALID_RECEIPT，导致「待审计」被落成 blocked。
    """
    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        f"工单 wo-orb-w7\n完成状态：`READY_FOR_DEEPSEEK_AUDIT`\n- 自检{sep}PASS",
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "audit"
    assert decision.valid is True


def test_text_receipt_requires_complete_work_order_boundary(tmp_path: Path) -> None:
    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        "工单 wo-orb-w7x\n完成状态：READY_FOR_REVIEW\n自检 PASS",
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False


@pytest.mark.parametrize(
    "evidence_line",
    ["14 passed in 0.24s", "PYTEST_EXIT_CODE=0", "PYTEST_EXIT_CODE: 0"],
)
def test_text_receipt_accepts_pytest_evidence_as_selfcheck(
    evidence_line: str, tmp_path: Path
) -> None:
    """回归：执行端写「14 passed」而不是「自检 PASS」，也必须判 audit。

    2026-11-10 核对 ORB-W6/W7 时发现：两单实际都干完了、提交也在，
    但 final.json 写成中文 markdown 且只报 pytest 输出，没有「自检 PASS」
    这条字面文案，于是 receipt_valid=false、整单被判 blocked。
    """

    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        f"工单 wo-orb-w6\n当前状态：READY_FOR_DEEPSEEK_AUDIT\n{evidence_line}",
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w6", exit_code=0
    )

    assert decision.state == "audit"
    assert decision.valid is True


def test_text_receipt_mentions_history_failures_still_audits(tmp_path: Path) -> None:
    """回执里叙述历史失败（修复前复现、既有债）不得否决本次判 audit。

    回归 ORB-W7：真实回执写了「修复前定向回归：3 failed」与「28 项历史债」，
    按「出现 failed 就否决」的做法会被二次误伤成 blocked。
    """

    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        "工单 wo-orb-w7\n完成状态：READY_FOR_DEEPSEEK_AUDIT\n"
        "9 passed\n修复前定向回归：3 failed\n沿用上轮：28 failed 为既有历史债",
        encoding="utf-8",
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w7", exit_code=0
    )

    assert decision.state == "audit"
    assert decision.valid is True


def test_text_receipt_without_readiness_marker_stays_blocked(tmp_path: Path) -> None:
    """没有 READY 声明时，即使写了 passed 也不得判 audit。"""

    classify_receipt_path = _classifier()
    receipt = tmp_path / "final.json"
    receipt.write_text(
        "工单 wo-orb-w6\n14 passed, 3 failed 仍在修", encoding="utf-8"
    )

    decision = classify_receipt_path(
        receipt, work_order="wo-orb-w6", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False
