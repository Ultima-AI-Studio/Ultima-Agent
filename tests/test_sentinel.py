from __future__ import annotations

import importlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tasks.queue_engine.dispatcher import DispatchLock


ROOT = Path(__file__).resolve().parents[1]


def _sentinel_module():
    return importlib.import_module("src.brain.sentinel")


def _dispatch_module():
    path = ROOT / "scripts" / "dispatch-work-order.py"
    spec = importlib.util.spec_from_file_location("dispatch_work_order_test", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _write_log(run_dir: Path, *, age_s: float) -> Path:
    path = run_dir / "worker.log"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("worker output\n", encoding="utf-8")
    timestamp = time.time() - age_s
    os.utime(path, (timestamp, timestamp))
    return path


def _heartbeats(run_dir: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in (run_dir / "heartbeat.jsonl").read_text(encoding="utf-8").splitlines()
    ]


def test_tick_appends_utf8_heartbeat_for_normal_process(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=1)
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: "created-1")
    sentinel = sentinel_module.Sentinel("wo-normal", tmp_path, 42, "created-1")

    first = sentinel.tick()
    second = sentinel.tick()

    assert set(first) == {"ts", "pid_alive", "final_message", "log_age_s"}
    assert first["pid_alive"] is True
    assert first["final_message"] is False
    assert len(_heartbeats(tmp_path)) == 2
    assert _heartbeats(tmp_path)[1] == second
    assert not (tmp_path / "anomaly.json").exists()


def test_process_disappearance_alone_does_not_trigger_anomaly(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=1)
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: None)
    sentinel = sentinel_module.Sentinel("wo-fresh-log", tmp_path, 42, "created-1", missed=3)

    for _ in range(3):
        heartbeat = sentinel.tick()

    assert heartbeat["pid_alive"] is False
    assert heartbeat["log_age_s"] < 90
    assert len(_heartbeats(tmp_path)) == 3
    assert not (tmp_path / "anomaly.json").exists()


def test_three_anomaly_criteria_for_two_ticks_do_not_emit_event(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=120)
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: None)
    sentinel = sentinel_module.Sentinel("wo-two-ticks", tmp_path, 42, "created-1", missed=3)

    sentinel.tick()
    sentinel.tick()

    assert len(_heartbeats(tmp_path)) == 2
    assert not (tmp_path / "anomaly.json").exists()


def test_third_anomalous_tick_emits_event_and_recovery_keeps_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=120)
    identities = iter([None, None, None, "created-1"])
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: next(identities))
    sentinel = sentinel_module.Sentinel("wo-recover", tmp_path, 42, "created-1", missed=3)

    sentinel.tick()
    sentinel.tick()
    assert not (tmp_path / "anomaly.json").exists()
    sentinel.tick()

    anomaly_path = tmp_path / "anomaly.json"
    anomaly = json.loads(anomaly_path.read_text(encoding="utf-8"))
    assert anomaly["order"] == "wo-recover"
    assert anomaly["kind"] == "exit-anomaly"
    assert anomaly["consecutive"] == 3
    assert anomaly["evidence"]["pid_alive"] is False

    sentinel.tick()

    recovered = json.loads((tmp_path / "recovered.json").read_text(encoding="utf-8"))
    assert recovered["order"] == "wo-recover"
    assert recovered["kind"] == "recovered"
    assert anomaly_path.exists()
    assert json.loads(anomaly_path.read_text(encoding="utf-8")) == anomaly


def test_run_uses_dispatch_lock_and_returns_two_when_busy(tmp_path: Path) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=1)
    lock = DispatchLock(tmp_path / ".sentinel.lock")
    assert lock.acquire() is True
    try:
        sentinel = sentinel_module.Sentinel(
            "wo-lock", tmp_path, 42, "created-1", interval=0.05, missed=3
        )
        assert sentinel.run(max_ticks=1) == 2
    finally:
        lock.release()

    assert not (tmp_path / "heartbeat.jsonl").exists()


@pytest.mark.parametrize("final_name", ["final.json", "final-message.json"])
def test_either_final_receipt_stops_run_without_anomaly(
    final_name: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    (tmp_path / final_name).write_text("terminal receipt", encoding="utf-8")
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: None)
    sentinel = sentinel_module.Sentinel(
        "wo-final", tmp_path, 42, "created-1", interval=0.001, missed=3
    )

    assert sentinel.run() == 0

    heartbeats = _heartbeats(tmp_path)
    assert len(heartbeats) == 1
    assert heartbeats[0]["final_message"] is True
    assert not (tmp_path / "anomaly.json").exists()


def test_run_exits_after_third_anomalous_tick(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    sentinel_module = _sentinel_module()
    _write_log(tmp_path, age_s=120)
    monkeypatch.setattr(sentinel_module, "process_identity", lambda _pid: None)
    sentinel = sentinel_module.Sentinel(
        "wo-anomaly", tmp_path, 42, "created-1", interval=0.001, missed=3
    )

    assert sentinel.run() == 0

    assert len(_heartbeats(tmp_path)) == 3
    anomaly = json.loads((tmp_path / "anomaly.json").read_text(encoding="utf-8"))
    assert anomaly["kind"] == "exit-anomaly"
    assert anomaly["consecutive"] == 3


def test_dispatcher_starts_hidden_sentinel_with_worker_identity(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dispatch = _dispatch_module()
    captured: dict[str, object] = {}
    process = object()

    def fake_popen(command, **kwargs):
        captured["command"] = command
        captured.update(kwargs)
        return process

    monkeypatch.setattr(dispatch.subprocess, "Popen", fake_popen)

    result = dispatch.start_sentinel(
        "wo-orb-w7", tmp_path, 4242, "worker-created-1"
    )

    assert result is process
    assert captured["command"] == [
        sys.executable,
        "-m",
        "src.brain.sentinel",
        "wo-orb-w7",
        str(tmp_path),
        "4242",
        "worker-created-1",
    ]
    assert captured["cwd"] == ROOT
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["stdout"] is subprocess.DEVNULL
    assert captured["stderr"] is subprocess.DEVNULL
    assert captured["creationflags"] == 0x08000000


def test_dispatcher_waits_for_sentinel_self_exit() -> None:
    dispatch = _dispatch_module()

    class FakeSentinelProcess:
        def __init__(self) -> None:
            self.wait_calls: list[float] = []
            self.terminated = False

        def wait(self, timeout: float) -> int:
            self.wait_calls.append(timeout)
            return 0

        def terminate(self) -> None:
            self.terminated = True

    process = FakeSentinelProcess()

    dispatch.await_sentinel(process)

    assert process.wait_calls == [dispatch.SENTINEL_EXIT_TIMEOUT_S]
    assert process.terminated is False


def test_dispatcher_cli_and_ready_dry_run_contract_are_unchanged(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    dispatch = _dispatch_module()
    registration = "| UltimaAgent | wo-orb-w7 | pending | ready |"
    match = re.search(
        r"^\| UltimaAgent \| wo\-orb\-w7 \| (\w+) \| ([^\r\n]*)\|(?=\r?$)",
        registration,
        re.MULTILINE,
    )
    assert match is not None

    class FakeLock:
        def __init__(self, _path: Path) -> None:
            pass

        def __enter__(self):
            return self

        def __exit__(self, *_args) -> None:
            pass

        def release(self) -> None:
            pass

    monkeypatch.setattr(dispatch, "DispatchLock", FakeLock)
    monkeypatch.setattr(dispatch, "registered", lambda _order: (registration, match, ""))
    monkeypatch.setattr(dispatch, "check_version_gates", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(dispatch.shutil, "which", lambda _name: "C:/mock/codex.exe")
    monkeypatch.setattr(dispatch.native, "codex_processes", lambda: [])
    monkeypatch.setattr(
        sys,
        "argv",
        [
            str(ROOT / "scripts" / "dispatch-work-order.py"),
            "--order",
            "wo-orb-w7",
            "--prompt",
            str(ROOT / "tasks" / "queue" / "dispatch-wo-orb-w7-prompt.txt"),
        ],
    )

    assert dispatch.main() == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload == {"ready": True, "order": "wo-orb-w7", "codex_roles": []}
    help_result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "dispatch-work-order.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert help_result.returncode == 0
    for option in ("--order", "--prompt", "--execute", "--repair"):
        assert option in help_result.stdout
