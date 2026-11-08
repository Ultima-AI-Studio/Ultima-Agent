from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from src.brain import orchestrator


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "orchestrate-order.py"


def _load_cli():
    spec = importlib.util.spec_from_file_location("orchestrate_order_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_default_run_executes_three_stages_in_order_and_uses_run_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    requirement = tmp_path / "requirement.txt"
    requirement.write_text("approved requirement", encoding="utf-8")
    run_dir = tmp_path / "run"
    calls: list[tuple[str, str, Path]] = []

    def fake_run_stage(stage: str, prompt: str, destination: Path):
        destination = Path(destination)
        calls.append((stage, prompt, destination))
        artifact = {"stage": stage, "prompt": prompt}
        stages_dir = destination / "stages"
        stages_dir.mkdir(parents=True, exist_ok=True)
        (stages_dir / f"{stage}.json").write_text(
            json.dumps(artifact), encoding="utf-8"
        )
        return artifact

    monkeypatch.setenv("DEEPSEEK_API_KEY", "mock-only-key")
    monkeypatch.setattr(cli, "run_stage", fake_run_stage)

    result = cli.main(
        ["--requirement", str(requirement), "--run-dir", str(run_dir)]
    )

    assert result == 0
    assert [stage for stage, _, _ in calls] == [
        "decompose",
        "work_order",
        "schedule",
    ]
    assert all(prompt == "approved requirement" for _, prompt, _ in calls)
    assert all(destination == run_dir for _, _, destination in calls)
    assert sorted(path.name for path in (run_dir / "stages").iterdir()) == [
        "decompose.json",
        "schedule.json",
        "work_order.json",
    ]


def test_stage_failure_writes_failure_artifact_and_stops_later_stages(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    calls: list[str] = []

    def fake_call_deepseek(_system: str, _prompt: str, **_kwargs):
        stage = ("decompose", "work_order", "schedule")[len(calls)]
        calls.append(stage)
        if stage == "work_order":
            raise orchestrator.OrchestratorError("mock stage failure")
        return {
            "model": "mock-model",
            "response": "ok",
            "tokens": {"in": 1, "out": 1},
        }

    monkeypatch.setenv("DEEPSEEK_API_KEY", "mock-only-key")
    monkeypatch.setattr(orchestrator, "call_deepseek", fake_call_deepseek)

    result = cli.main(
        ["--requirement", "literal requirement", "--run-dir", str(tmp_path)]
    )

    assert result != 0
    assert calls == ["decompose", "work_order"]
    assert (tmp_path / "stages" / "decompose.json").is_file()
    failed = json.loads(
        (tmp_path / "stages" / "work_order-failed.json").read_text(encoding="utf-8")
    )
    assert failed["stage"] == "work_order"
    assert "mock stage failure" in failed["error"]
    assert not (tmp_path / "stages" / "schedule.json").exists()


def test_dry_run_never_calls_stage_or_changes_stage_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cli = _load_cli()
    run_dir = tmp_path / "run"
    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True)
    marker = stages_dir / "existing.json"
    marker.write_text('{"kept": true}\n', encoding="utf-8")
    before = marker.read_bytes()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
    monkeypatch.setattr(
        cli,
        "run_stage",
        lambda *_args, **_kwargs: pytest.fail("dry-run called run_stage"),
    )

    result = cli.main(
        [
            "--requirement",
            "literal requirement",
            "--run-dir",
            str(run_dir),
            "--dry-run",
        ]
    )

    assert result == 0
    assert list(stages_dir.iterdir()) == [marker]
    assert marker.read_bytes() == before


def test_missing_api_key_exits_nonzero_without_success_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    cli = _load_cli()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    result = cli.main(
        ["--requirement", "literal requirement", "--run-dir", str(tmp_path)]
    )

    captured = capsys.readouterr()
    assert result != 0
    assert "DEEPSEEK_API_KEY" in captured.err
    assert not any((tmp_path / "stages").glob("*.json"))
