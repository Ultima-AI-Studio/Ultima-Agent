from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

from tasks.queue_engine.receipt_contract import _classify_text


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_work_order_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_contract_block_does_not_spell_out_the_markers():
    """The block is handed to the executor; a literal marker would leak it."""

    block = _load_dispatch().receipt_contract_block("wo-orb-w8")
    assert "READY_FOR_DEEPSEEK_AUDIT" not in block
    assert "READY_FOR_REVIEW" not in block
    assert not any(
        line.strip().startswith("自检：PASS") for line in block.splitlines()
    )
    decision = _classify_text(block, work_order="wo-orb-w8", exit_code=0)
    assert decision.valid is False


def test_receipt_with_markers_is_accepted():
    block = _load_dispatch().receipt_contract_block("wo-orb-w8")
    receipt = (
        "## 改动文件清单\n- scripts/x.py\n\n自检：PASS\n\n"
        "READY_FOR_DEEPSEEK_AUDIT\n" + block
    )
    decision = _classify_text(receipt, work_order="wo-orb-w8", exit_code=0)
    assert decision.state == "audit"
    assert decision.valid is True


def test_receipt_without_markers_is_still_rejected():
    block = _load_dispatch().receipt_contract_block("wo-orb-w8")
    receipt = "已完成全部改动，ACC-1~ACC-6 全绿。\n" + block
    decision = _classify_text(receipt, work_order="wo-orb-w8", exit_code=0)
    assert decision.valid is False


def test_blocked_receipt_stays_blocked():
    block = _load_dispatch().receipt_contract_block("wo-orb-w8")
    receipt = block + "\n完成状态：BLOCKED（等待授权）\n"
    decision = _classify_text(receipt, work_order="wo-orb-w8", exit_code=0)
    assert decision.state == "blocked"
    assert decision.valid is True


@pytest.mark.parametrize("order", ["wo-orb-w8", "wo-s1-abc-def"])
def test_contract_block_carries_the_order_id(order: str):
    block = _load_dispatch().receipt_contract_block(order)
    assert order in block
    assert _classify_text(block, work_order=order, exit_code=0).valid is False
