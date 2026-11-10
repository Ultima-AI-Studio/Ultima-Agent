from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "run-gorch.py"


def _load():
    spec = importlib.util.spec_from_file_location("run_gorch", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _proc(code: int) -> subprocess.CompletedProcess:
    return subprocess.CompletedProcess(args=[], returncode=code, stdout="", stderr="")


def _write_stages(run_dir: Path, verdicts: dict[str, str]) -> None:
    stages_dir = run_dir / "stages"
    stages_dir.mkdir(parents=True, exist_ok=True)
    for name, verdict in verdicts.items():
        (stages_dir / f"{name}.json").write_text(json.dumps({"verdict": verdict}), encoding="utf-8")


def _pipeline(tmp_path: Path) -> dict:
    return json.loads((tmp_path / "run" / "pipeline.json").read_text(encoding="utf-8"))


def test_no_evidence_blocks_before_audit(monkeypatch, tmp_path):
    """An audit with nothing to read can only FAIL; refuse instead of burning it."""

    calls: list[str] = []
    cli = _load()
    monkeypatch.setattr(cli, "_call", lambda s, a: (calls.append(s), _proc(0))[1])
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run")])
    assert code == 2
    assert calls == []
    assert "no evidence" in _pipeline(tmp_path)["reason"]


def test_plan_not_completed_blocks(monkeypatch, tmp_path):
    calls: list[str] = []
    cli = _load()
    monkeypatch.setattr(cli, "_call", lambda s, a: (calls.append(s), _proc(0))[1])
    _write_stages(tmp_path / "run", {"decompose": "completed", "work_order": "blocked", "schedule": "completed"})
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--plan", "需求", "--evidence", "a.md"])
    assert code == 2
    assert calls == ["orchestrate-order.py"]
    assert "not all COMPLETED" in _pipeline(tmp_path)["reason"]


def test_audit_failure_never_freezes(monkeypatch, tmp_path):
    calls: list[str] = []
    cli = _load()
    codes = [0, 2, 0]

    def fake_call(script, argv):
        calls.append(script)
        return _proc(codes[len(calls) - 1])

    monkeypatch.setattr(cli, "_call", fake_call)
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--evidence", "a.md"])
    assert code == 2
    assert calls == ["verify-order.py", "audit-work-order.py"]
    assert _pipeline(tmp_path)["outcome"] == "audit-failed"


def test_verify_failure_blocks_audit(monkeypatch, tmp_path):
    """Facts decide entry. A stale receipt is not something a reviewer can rescue."""

    calls: list[str] = []
    cli = _load()

    def fake_call(script, argv):
        calls.append(script)
        return _proc(2)

    monkeypatch.setattr(cli, "_call", fake_call)
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--evidence", "a.md"])
    assert code == 2
    assert calls == ["verify-order.py"]
    assert _pipeline(tmp_path)["outcome"] == "verify-failed"


def test_audit_pass_then_freeze(monkeypatch, tmp_path):
    calls: list[str] = []
    cli = _load()
    monkeypatch.setattr(cli, "_call", lambda s, a: (calls.append(s), _proc(0))[1])
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--evidence", "a.md"])
    assert code == 0
    assert calls == ["verify-order.py", "audit-work-order.py", "freeze-work-order.py"]
    assert _pipeline(tmp_path)["outcome"] == "frozen"


def test_skip_freeze_stops_after_audit(monkeypatch, tmp_path):
    calls: list[str] = []
    cli = _load()
    monkeypatch.setattr(cli, "_call", lambda s, a: (calls.append(s), _proc(0))[1])
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--evidence", "a.md", "--skip-freeze"])
    assert code == 0
    assert calls == ["verify-order.py", "audit-work-order.py"]


def test_plan_output_is_not_passed_to_the_audit(monkeypatch, tmp_path):
    """The plan artifacts must never become the audited evidence."""

    seen: dict[str, list[str]] = {}

    def fake_call(script, argv):
        seen[script] = argv
        return _proc(0)

    cli = _load()
    monkeypatch.setattr(cli, "_call", fake_call)
    _write_stages(tmp_path / "run", {"decompose": "completed", "work_order": "completed", "schedule": "completed"})
    code = cli.main(["--work-order", "wo-x", "--card", str(tmp_path / "c.md"),
                     "--run-dir", str(tmp_path / "run"), "--plan", "需求", "--evidence", "a.md"])
    assert code == 0
    audit_argv = seen["audit-work-order.py"]
    assert "--evidence" in audit_argv
    evidence = audit_argv[audit_argv.index("--evidence") + 1:]
    assert evidence == ["a.md"]
