from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_status_list", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_legacy_status_membership_reproduces_unhashable_list() -> None:
    with pytest.raises(TypeError, match="unhashable type: 'list'"):
        _ = ["ok"] in {"READY_FOR_REVIEW", "READY_FOR_DEEPSEEK_AUDIT"}


def test_list_status_is_explicitly_invalid(tmp_path: Path) -> None:
    dispatch = _load_dispatch()
    receipt = tmp_path / "final-message.json"
    receipt.write_text(
        json.dumps({"work_order": "wo-list", "status": ["ok"]}),
        encoding="utf-8",
    )

    decision = dispatch.classify_dispatch_receipt(
        receipt, work_order="wo-list", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False
    assert decision.format == "unknown"


def test_classifier_exception_is_fail_closed(monkeypatch, tmp_path: Path) -> None:
    dispatch = _load_dispatch()
    receipt = tmp_path / "final-message.json"
    receipt.write_text("{}", encoding="utf-8")

    def explode(*args, **kwargs):
        raise TypeError("unhashable type: 'list'")

    monkeypatch.setattr(dispatch, "classify_receipt_path", explode)
    decision = dispatch.classify_dispatch_receipt(
        receipt, work_order="wo-list", exit_code=0
    )

    assert decision.state == "blocked"
    assert decision.valid is False
    assert decision.format == "unknown"
