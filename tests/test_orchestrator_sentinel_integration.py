from __future__ import annotations

import json
import os
import time
from pathlib import Path

import pytest

from src.brain import orchestrator, sentinel


class _DeepSeekResponse:
    status_code = 200

    @staticmethod
    def json() -> dict[str, object]:
        return {
            "choices": [{"message": {"content": "decomposition complete"}}],
            "usage": {"prompt_tokens": 9, "completion_tokens": 3},
        }


def test_mock_stage_and_three_tick_exit_anomaly_share_one_run_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DEEPSEEK_API_KEY", "integration-test-key")
    monkeypatch.setattr(
        orchestrator.requests,
        "post",
        lambda *_args, **_kwargs: _DeepSeekResponse(),
    )
    monkeypatch.setattr(sentinel, "process_identity", lambda _pid: None)
    log_path = tmp_path / "worker.err"
    log_path.write_text("stale worker output\n", encoding="utf-8")
    old = time.time() - 120
    os.utime(log_path, (old, old))

    stage = orchestrator.run_stage("decompose", "approved plan", tmp_path)
    watcher = sentinel.Sentinel("wo-orb-w6", tmp_path, 4242, "expected-identity", missed=3)
    for _ in range(3):
        watcher.tick()

    assert stage["response"] == "decomposition complete"
    assert (tmp_path / "stages" / "decompose.json").exists()
    heartbeat_lines = (tmp_path / "heartbeat.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(heartbeat_lines) == 3
    assert all(json.loads(line)["pid_alive"] is False for line in heartbeat_lines)
    anomaly = json.loads((tmp_path / "anomaly.json").read_text(encoding="utf-8"))
    assert anomaly["order"] == "wo-orb-w6"
    assert anomaly["kind"] == "exit-anomaly"
    assert anomaly["consecutive"] == 3
