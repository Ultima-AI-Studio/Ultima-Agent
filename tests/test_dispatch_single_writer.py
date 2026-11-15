from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import subprocess
import sys
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
DISPATCH_SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"
WRITER_SCRIPT = ROOT / "scripts" / "queue-writer.py"
RENDER_SCRIPT = ROOT / "scripts" / "render-queue-views.py"


def _load_dispatch(name: str):
    spec = importlib.util.spec_from_file_location(name, DISPATCH_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _record(order: str, state: str = "pending", note: str = "fixture") -> dict:
    return {
        "project": "UltimaAgent",
        "work_order": order,
        "state": state,
        "audit_passed": False,
        "dispatched_at": None,
        "audit_run": None,
        "freeze_commit": None,
        "note": note,
    }


def _queue(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"schema_version": 1, "records": [record]}) + "\n",
        encoding="utf-8",
    )


def _isolate_state(dispatch, tmp_path: Path, record: dict) -> tuple[Path, Path]:
    queue = tmp_path / "queue-status.json"
    _queue(queue, record)
    renderer = tmp_path / "render.py"
    renderer.write_text("pass\n", encoding="utf-8")
    dispatch.QUEUE_STATUS = queue
    dispatch.QUEUE_WRITER = WRITER_SCRIPT
    dispatch.QUEUE_RENDERER = renderer
    run = tmp_path / "run"
    run.mkdir()
    return queue, run


def test_state_calls_writer_assigns_claim_and_preserves_other_records(tmp_path: Path):
    dispatch = _load_dispatch("dispatch_single_writer_state")
    order = "wo-ultimaagent-20261113-0061"
    queue, run = _isolate_state(dispatch, tmp_path, _record(order))
    document = json.loads(queue.read_text())
    document["records"].insert(0, _record("wo-other", note="exact other record"))
    queue.write_text(json.dumps(document) + "\n", encoding="utf-8")

    claim_id = dispatch.state(
        order,
        "executing",
        "run-one",
        run,
        expected="pending",
    )

    changed = json.loads(queue.read_text())
    target = next(item for item in changed["records"] if item["work_order"] == order)
    other = next(item for item in changed["records"] if item["work_order"] == "wo-other")
    assert claim_id == target["claim_id"]
    assert claim_id.strip()
    assert target["state"] == "executing"
    assert other == _record("wo-other", note="exact other record")


def test_redispatch_gets_new_claim_and_old_claim_cannot_transition(tmp_path: Path):
    dispatch = _load_dispatch("dispatch_single_writer_redispatch")
    order = "wo-ultimaagent-20261113-0061"
    queue, run = _isolate_state(dispatch, tmp_path, _record(order))
    first = dispatch.state(order, "executing", "run-one", run, expected="pending")
    dispatch.state(
        order,
        "blocked",
        "run-one blocked",
        run,
        expected="executing",
        expected_run="run-one",
        claim_id=first,
    )
    second = dispatch.state(order, "executing", "run-two", run, expected="blocked")
    before_stale = queue.read_bytes()

    with mock.patch.object(dispatch.subprocess, "run", wraps=subprocess.run):
        try:
            dispatch.state(
                order,
                "audit",
                "stale done",
                run,
                expected="executing",
                expected_run="run-two",
                claim_id=first,
            )
        except RuntimeError as exc:
            assert "queue writer failed" in str(exc)
        else:
            raise AssertionError("stale claim_id was accepted")

    assert first != second
    assert json.loads(queue.read_text())["records"][0]["claim_id"] == second
    assert queue.read_bytes() == before_stale


def test_initial_writer_failure_returns_two_before_worker_spawn(tmp_path: Path):
    dispatch = _load_dispatch("dispatch_single_writer_failure")
    order = "wo-ultimaagent-20261113-9999"
    root = tmp_path / "repo"
    queue_dir = root / "tasks" / "queue"
    queue_dir.mkdir(parents=True)
    card = queue_dir / f"{order}--fixture.md"
    card.write_text(f"# {order}\n\nfixture\n", encoding="utf-8")
    prompt = tmp_path / "prompt.txt"
    prompt.write_text(f"docs/INDEX.md {order}\n", encoding="utf-8")
    queue = queue_dir / "queue-status.json"
    _queue(queue, _record(order))
    before = queue.read_bytes()
    shared = tmp_path / "shared"
    shared.mkdir()
    dispatch.ROOT = root
    dispatch.SHARED = shared
    dispatch.QUEUE_STATUS = queue
    dispatch.QUEUE_WRITER = tmp_path / "missing-writer.py"
    dispatch.QUEUE_RENDERER = tmp_path / "unused-render.py"
    argv = ["dispatch", "--order", order, "--prompt", str(prompt), "--execute"]
    no_spawn = mock.Mock(side_effect=AssertionError("worker must not start"))
    report = SimpleNamespace(status="PASS", errors=[], warnings=[])

    with mock.patch.object(dispatch.validate_work_order, "validate", return_value=report), \
         mock.patch.object(dispatch, "contract_order_cards", return_value=[]), \
         mock.patch.object(dispatch.native, "codex_processes", return_value=[]), \
         mock.patch.object(dispatch, "resolve_codex_exe", return_value="fake-codex"), \
         mock.patch.object(dispatch, "process_identity", return_value="parent-identity"), \
         mock.patch.object(dispatch, "git_snapshot", return_value={"base_sha": "fixture"}), \
         mock.patch.object(dispatch.subprocess, "run", return_value=SimpleNamespace(
             returncode=2, stdout="", stderr="writer fixture failure"
         )), \
         mock.patch.object(dispatch.subprocess, "Popen", no_spawn), \
         mock.patch.object(sys, "argv", argv):
        assert dispatch.main() == 2

    assert no_spawn.call_count == 0
    assert queue.read_bytes() == before
    runs = list((queue_dir / "runs").iterdir())
    assert len(runs) == 1
    assert json.loads((runs[0] / "done.json").read_text())["launched"] is False
    assert (runs[0] / "dispatch-error.json").is_file()


def test_dispatch_help_is_identical_to_t0_snapshot():
    completed = subprocess.run(
        [sys.executable, str(DISPATCH_SCRIPT), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    expected = """usage: dispatch-work-order.py [-h] --order ORDER --prompt PROMPT [--card CARD]
                              [--skip-dor] [--dry-run-dor] [--execute]
                              [--repair]
                              [--max-runtime-seconds MAX_RUNTIME_SECONDS]
                              [--expected-run EXPECTED_RUN]
                              [--expected-state EXPECTED_STATE]
                              [--expected-reservation EXPECTED_RESERVATION]
                              [--reasoning-effort {high,ultra}]

options:
  -h, --help            show this help message and exit
  --order ORDER
  --prompt PROMPT
  --card CARD
  --skip-dor
  --dry-run-dor
  --execute
  --repair
  --max-runtime-seconds MAX_RUNTIME_SECONDS
  --expected-run EXPECTED_RUN
  --expected-state EXPECTED_STATE
  --expected-reservation EXPECTED_RESERVATION
  --reasoning-effort {high,ultra}
"""
    assert completed.returncode == 0
    assert completed.stdout.replace("\r\n", "\n") == expected
    assert "--claim-id" not in completed.stdout


def test_renderer_migrate_missing_authority_fails_closed(tmp_path: Path):
    isolated_script = tmp_path / "repo" / "scripts" / "render-queue-views.py"
    isolated_script.parent.mkdir(parents=True)
    isolated_script.write_bytes(RENDER_SCRIPT.read_bytes())
    authority = tmp_path / "repo" / "tasks" / "queue" / "queue-status.json"

    completed = subprocess.run(
        [sys.executable, str(isolated_script), "--migrate"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )

    assert completed.returncode != 0
    assert "queue-writer.py" in completed.stderr
    assert not authority.exists()

