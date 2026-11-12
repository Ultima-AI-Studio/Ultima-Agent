from __future__ import annotations

import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_selfcheck_colon", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _classify(tmp_path: Path, selfcheck_line: str):
    receipt = tmp_path / "final-message.txt"
    receipt.write_text(
        "工单 wo-colon\nREADY_FOR_DEEPSEEK_AUDIT\n" + selfcheck_line,
        encoding="utf-8",
    )
    return _load_dispatch().classify_dispatch_receipt(
        receipt, work_order="wo-colon", exit_code=0
    )


def test_selfcheck_accepts_fullwidth_colon(tmp_path: Path) -> None:
    decision = _classify(tmp_path, "- 自检：PASS")
    assert decision.valid is True
    assert decision.state == "audit"


def test_unrelated_pass_is_not_a_selfcheck(tmp_path: Path) -> None:
    decision = _classify(tmp_path, "说明：前置门 PASS")
    assert decision.valid is False
    assert decision.state == "blocked"
