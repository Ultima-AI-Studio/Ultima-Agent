from __future__ import annotations

import importlib
import json
import os
import time
from pathlib import Path

import pytest

from tasks.queue_engine.dispatcher import DispatchLock


def _sentinel_module():
    return importlib.import_module("src.brain.sentinel")


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
