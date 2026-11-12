from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-pipeline.py"


def _load_pipeline():
    spec = importlib.util.spec_from_file_location("run_pipeline_0048", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _base_argv(run_dir: Path) -> list[str]:
    return [
        "--requirement",
        "requirements/req.md",
        "--run-dir",
        str(run_dir),
        "--work-order",
        "wo-ultimaagent-20261112-0048",
        "--card",
        "tasks/queue/wo-ultimaagent-20261112-0048--gorch-pipeline-once-command.md",
        "--prompt",
        "tasks/queue/prompts/prompt-wo-ultimaagent-20261112-0048.md",
        "--evidence",
        "evidence-one.json",
        "evidence-two.md",
    ]


def test_dry_run_prints_six_stage_argv_and_writes_nothing(tmp_path: Path) -> None:
    run_dir = tmp_path / "must-not-be-created"

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *_base_argv(run_dir), "--dry-run", "--push"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0, proc.stderr
    rows = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert [row["step"] for row in rows] == [
        "plan",
        "dispatch-dor",
        "dispatch",
        "verify",
        "audit",
        "freeze",
    ]
    assert all(isinstance(row["argv"], list) and row["argv"] for row in rows)
    assert "--dry-run-dor" in rows[1]["argv"]
    assert "--execute" in rows[2]["argv"]
    assert "--push" in rows[-1]["argv"]
    assert not run_dir.exists()


def test_dry_run_honours_all_three_skip_switches(tmp_path: Path) -> None:
    run_dir = tmp_path / "must-not-be-created"
    argv = [
        "--run-dir",
        str(run_dir),
        "--work-order",
        "wo-ultimaagent-20261112-0047",
        "--card",
        "tasks/queue/wo-ultimaagent-20261112-0047--mainbrain-teaching-phase35.md",
        "--evidence",
        "done.json",
        "--dry-run",
        "--skip-plan",
        "--skip-dispatch",
        "--skip-freeze",
    ]

    proc = subprocess.run(
        [sys.executable, str(SCRIPT), *argv],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert proc.returncode == 0, proc.stderr
    rows = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    assert [row["step"] for row in rows] == ["verify", "audit"]
    assert not run_dir.exists()


def test_invalid_receipt_block_is_a_real_failure() -> None:
    pipeline = _load_pipeline()

    assert pipeline._blocked_dispatch_outcome(
        {"receipt_valid": False, "state": "blocked"}
    ) == ("blocked-for-invalid-receipt", 2)


def test_valid_receipt_waiting_for_audit_slot_is_a_pause() -> None:
    pipeline = _load_pipeline()

    assert pipeline._blocked_dispatch_outcome(
        {"receipt_valid": True, "state": "blocked", "audit_slot_busy": True}
    ) == ("paused-for-audit-slot", 0)


def test_other_valid_receipt_block_is_not_misreported_as_slot_wait() -> None:
    pipeline = _load_pipeline()

    assert pipeline._blocked_dispatch_outcome(
        {"receipt_valid": True, "state": "blocked", "audit_slot_busy": False}
    ) == ("blocked", 2)


def test_verify_failure_stops_before_audit_and_freeze(tmp_path: Path, monkeypatch) -> None:
    pipeline = _load_pipeline()
    called: list[str] = []

    def fake_call(script: str, argv: list[str]):
        called.append(script)
        return subprocess.CompletedProcess([script, *argv], 2, "verify no", "")

    monkeypatch.setattr(pipeline, "_call", fake_call)
    rc = pipeline.main(
        [
            "--run-dir",
            str(tmp_path),
            "--work-order",
            "wo-ultimaagent-20261112-0047",
            "--card",
            "card.md",
            "--evidence",
            "done.json",
            "--skip-plan",
            "--skip-dispatch",
        ]
    )

    assert rc == 2
    assert called == ["verify-order.py"]
    payload = json.loads((tmp_path / "pipeline.json").read_text(encoding="utf-8"))
    assert payload["outcome"] == "verify-failed"


def test_audit_failure_stops_before_freeze(tmp_path: Path, monkeypatch) -> None:
    pipeline = _load_pipeline()
    called: list[str] = []

    def fake_call(script: str, argv: list[str]):
        called.append(script)
        code = 2 if script == "audit-work-order.py" else 0
        return subprocess.CompletedProcess([script, *argv], code, "", "audit no" if code else "")

    monkeypatch.setattr(pipeline, "_call", fake_call)
    rc = pipeline.main(
        [
            "--run-dir",
            str(tmp_path),
            "--work-order",
            "wo-ultimaagent-20261112-0047",
            "--card",
            "card.md",
            "--evidence",
            "done.json",
            "--skip-plan",
            "--skip-dispatch",
        ]
    )

    assert rc == 2
    assert called == ["verify-order.py", "audit-work-order.py"]
    payload = json.loads((tmp_path / "pipeline.json").read_text(encoding="utf-8"))
    assert payload["outcome"] == "audit-failed"


def test_skip_freeze_finishes_as_audited(tmp_path: Path, monkeypatch) -> None:
    pipeline = _load_pipeline()
    called: list[str] = []

    def fake_call(script: str, argv: list[str]):
        called.append(script)
        return subprocess.CompletedProcess([script, *argv], 0, "ok", "")

    monkeypatch.setattr(pipeline, "_call", fake_call)
    rc = pipeline.main(
        [
            "--run-dir",
            str(tmp_path),
            "--work-order",
            "wo-ultimaagent-20261112-0047",
            "--card",
            "card.md",
            "--evidence",
            "done.json",
            "--skip-plan",
            "--skip-dispatch",
            "--skip-freeze",
        ]
    )

    assert rc == 0
    assert called == ["verify-order.py", "audit-work-order.py"]
    payload = json.loads((tmp_path / "pipeline.json").read_text(encoding="utf-8"))
    assert payload["outcome"] == "audited"
    assert [step["step"] for step in payload["steps"]] == [
        "plan",
        "dispatch-dor",
        "dispatch",
        "verify",
        "audit",
        "freeze",
    ]
    assert all("exit_code" in step and "stdout" in step and "stderr" in step for step in payload["steps"])
    skipped_steps = [payload["steps"][0], *payload["steps"][1:3], payload["steps"][-1]]
    assert all(step.get("skipped") for step in skipped_steps)
