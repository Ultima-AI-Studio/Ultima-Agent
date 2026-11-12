from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_wo_boundary", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _classify(tmp_path: Path, text: str):
    receipt = tmp_path / "final-message.txt"
    receipt.write_text(text, encoding="utf-8")
    return _load_dispatch().classify_dispatch_receipt(
        receipt, work_order="wo-orb-w7", exit_code=0
    )


def test_work_order_does_not_match_longer_identifier(tmp_path: Path) -> None:
    decision = _classify(
        tmp_path,
        "工单 wo-orb-w7x\n自检 PASS\nREADY_FOR_DEEPSEEK_AUDIT",
    )
    assert decision.valid is False
    assert decision.state == "blocked"


def test_work_order_matches_complete_identifier(tmp_path: Path) -> None:
    decision = _classify(
        tmp_path,
        "工单 wo-orb-w7。\n自检 PASS\nREADY_FOR_DEEPSEEK_AUDIT",
    )
    assert decision.valid is True
    assert decision.state == "audit"
