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
