from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"
VALID_CARD = ROOT / "tasks" / "queue" / "wo-ultimaagent-20261108-0031--m2-workorder-contract.md"


def load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_work_order", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def prompt(tmp_path: Path, order: str) -> Path:
    path = tmp_path / "prompt.txt"
    path.write_text(f"Read docs/INDEX.md and execute {order}", encoding="utf-8")
    return path


def invalid_card(tmp_path: Path, order: str = "wo-negative-dor") -> Path:
    text = VALID_CARD.read_text(encoding="utf-8").replace("状态：可开工", "状态：执行中", 1)
    path = tmp_path / f"{order}.md"
    path.write_text(text, encoding="utf-8")
    return path


def run_dispatch(tmp_path: Path, order: str, card: Path, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--order",
            order,
            "--prompt",
            str(prompt(tmp_path, order)),
            "--card",
            str(card),
            "--dry-run-dor",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def test_card_resolution_prefers_unique_order_prefix(tmp_path: Path):
    dispatch = load_dispatch()
    root = tmp_path / "repo"
    queue = root / "tasks" / "queue"
    queue.mkdir(parents=True)
    matched = queue / "wo-demo--matched.md"
    matched.write_text("matched", encoding="utf-8")
    explicit = tmp_path / "explicit.md"
    explicit.write_text("explicit", encoding="utf-8")

    assert dispatch.resolve_work_order_card("wo-demo", explicit, root=root) == matched


def test_card_resolution_rejects_multiple_prefix_matches(tmp_path: Path):
    dispatch = load_dispatch()
    root = tmp_path / "repo"
    queue = root / "tasks" / "queue"
    queue.mkdir(parents=True)
    (queue / "wo-demo--one.md").write_text("one", encoding="utf-8")
    (queue / "wo-demo--two.md").write_text("two", encoding="utf-8")

    with pytest.raises(ValueError, match="多张"):
        dispatch.resolve_work_order_card("wo-demo", None, root=root)


def test_failed_dor_exits_two_without_record_or_run_directory(tmp_path: Path):
    order = "wo-negative-dor"
    record = tmp_path / "dispatch-record.json"
    runs = ROOT / "tasks" / "queue" / "runs"
    before = set(runs.glob(f"{order}-*")) if runs.exists() else set()

    completed = run_dispatch(tmp_path, order, invalid_card(tmp_path, order), "--dor-record", str(record))

    after = set(runs.glob(f"{order}-*")) if runs.exists() else set()
    payload = json.loads(completed.stdout)
    assert completed.returncode == 2
    assert payload["dor_status"] == "FAIL"
    assert payload["errors"]
    assert {"code", "line", "message"} <= payload["errors"][0].keys()
    assert not record.exists()
    assert after == before


def test_passing_dry_run_writes_auditable_pass_record(tmp_path: Path):
    order = "wo-ultimaagent-20261108-0031"
    record = tmp_path / "dispatch-record.json"

    completed = run_dispatch(tmp_path, order, VALID_CARD, "--dor-record", str(record))

    payload = json.loads(completed.stdout)
    saved = json.loads(record.read_text(encoding="utf-8"))
    assert completed.returncode == 0
    assert payload["ready"] is True
    assert saved["dor_status"] == "PASS"
    assert "dor_skipped" not in saved


def test_skip_dor_records_original_errors(tmp_path: Path):
    order = "wo-negative-skip"
    record = tmp_path / "dispatch-record.json"
    card = invalid_card(tmp_path, order)

    completed = run_dispatch(
        tmp_path,
        order,
        card,
        "--skip-dor",
        "--dor-record",
        str(record),
    )

    saved = json.loads(record.read_text(encoding="utf-8"))
    assert completed.returncode == 0
    assert saved["dor_skipped"] is True
    assert saved["dor_errors"]
    assert any(item["code"] == "E_STATUS_NOT_DISPATCHABLE" for item in saved["dor_errors"])


def test_dor_record_builder_preserves_error_objects():
    dispatch = load_dispatch()
    errors = [{"code": "E_SAMPLE", "line": 7, "message": "sample"}]

    record = dispatch.dor_record("wo-demo", "FAIL", errors, skipped=True)

    assert record == {"order": "wo-demo", "dor_skipped": True, "dor_errors": errors}
