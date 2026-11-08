from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest
import requests


def _orchestrator():
    return importlib.import_module("src.brain.orchestrator")


class FakeResponse:
    def __init__(self, status_code: int, payload: object = None, json_error: Exception | None = None):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error
        self.text = "fake-response"

    def json(self):
        if self._json_error is not None:
            raise self._json_error
        return self._payload


def _success_payload(content: str = "stage result") -> dict[str, object]:
    return {
        "choices": [{"message": {"content": content}}],
        "usage": {"prompt_tokens": 11, "completion_tokens": 7},
    }


def test_run_stage_writes_nine_field_artifacts_with_independent_systems(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    orchestrator = _orchestrator()
    secret = "test-only-deepseek-secret"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    calls: list[dict[str, object]] = []

    def fake_post(url, **kwargs):
        calls.append({"url": url, **kwargs})
        return FakeResponse(200, _success_payload())

    monkeypatch.setattr(orchestrator.requests, "post", fake_post)

    artifacts = [
        orchestrator.run_stage(stage, f"prompt for {stage}", tmp_path)
        for stage in ("decompose", "work_order", "schedule")
    ]

    expected_fields = {
        "stage",
        "model",
        "system_digest",
        "prompt",
        "response",
        "tokens",
        "elapsed_s",
        "verdict",
        "created_at",
    }
    assert all(set(artifact) == expected_fields for artifact in artifacts)
    assert all(artifact["tokens"] == {"in": 11, "out": 7} for artifact in artifacts)
    assert len({artifact["system_digest"] for artifact in artifacts}) == 3
    assert len({call["json"]["messages"][0]["content"] for call in calls}) == 3
    assert all(call["url"] == "https://api.deepseek.com/chat/completions" for call in calls)
    assert all(call["json"]["model"] == "deepseek-chat" for call in calls)

    for stage in ("decompose", "work_order", "schedule"):
        artifact_path = tmp_path / "stages" / f"{stage}.json"
        assert json.loads(artifact_path.read_text(encoding="utf-8"))["stage"] == stage
        assert secret not in artifact_path.read_text(encoding="utf-8")


def test_call_deepseek_fails_closed_when_key_is_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    orchestrator = _orchestrator()
    monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)

    with pytest.raises(orchestrator.OrchestratorError, match="DEEPSEEK_API_KEY"):
        orchestrator.call_deepseek("system", "prompt")


@pytest.mark.parametrize("retry_status", [429, 500])
def test_call_deepseek_retries_retryable_http_then_succeeds(
    retry_status: int, monkeypatch: pytest.MonkeyPatch
) -> None:
    orchestrator = _orchestrator()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(orchestrator, "sleep", lambda _seconds: None)
    responses = [
        FakeResponse(retry_status, {}),
        FakeResponse(retry_status, {}),
        FakeResponse(200, _success_payload("recovered")),
    ]
    calls = 0

    def fake_post(*_args, **_kwargs):
        nonlocal calls
        response = responses[calls]
        calls += 1
        return response

    monkeypatch.setattr(orchestrator.requests, "post", fake_post)

    result = orchestrator.call_deepseek("system", "prompt")

    assert result["response"] == "recovered"
    assert calls == 3


def test_call_deepseek_retries_timeout_three_times(monkeypatch: pytest.MonkeyPatch) -> None:
    orchestrator = _orchestrator()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(orchestrator, "sleep", lambda _seconds: None)
    calls = 0

    def fake_post(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        raise requests.Timeout("offline timeout")

    monkeypatch.setattr(orchestrator.requests, "post", fake_post)

    with pytest.raises(orchestrator.OrchestratorError, match="after 3 attempts"):
        orchestrator.call_deepseek("system", "prompt")

    assert calls == 3


def test_call_deepseek_does_not_retry_non_429_client_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    orchestrator = _orchestrator()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    calls = 0

    def fake_post(*_args, **_kwargs):
        nonlocal calls
        calls += 1
        return FakeResponse(401, {})

    monkeypatch.setattr(orchestrator.requests, "post", fake_post)

    with pytest.raises(orchestrator.OrchestratorError, match="HTTP 401"):
        orchestrator.call_deepseek("system", "prompt")

    assert calls == 1


def test_run_stage_writes_failed_artifact_for_invalid_json(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    orchestrator = _orchestrator()
    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    monkeypatch.setattr(
        orchestrator.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(200, json_error=ValueError("bad json")),
    )

    with pytest.raises(orchestrator.OrchestratorError, match="invalid JSON"):
        orchestrator.run_stage("decompose", "prompt", tmp_path)

    failed_path = tmp_path / "stages" / "decompose-failed.json"
    failed = json.loads(failed_path.read_text(encoding="utf-8"))
    assert failed["stage"] == "decompose"
    assert "invalid JSON" in failed["error"]
    assert not (tmp_path / "stages" / "decompose.json").exists()


def test_run_stage_writes_failed_artifact_for_empty_content(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    orchestrator = _orchestrator()
    secret = "must-not-be-persisted"
    monkeypatch.setenv("DEEPSEEK_API_KEY", secret)
    monkeypatch.setattr(
        orchestrator.requests,
        "post",
        lambda *_args, **_kwargs: FakeResponse(200, _success_payload("   ")),
    )

    with pytest.raises(orchestrator.OrchestratorError, match="empty content"):
        orchestrator.run_stage("work_order", "prompt", tmp_path)

    failed_path = tmp_path / "stages" / "work_order-failed.json"
    assert failed_path.exists()
    assert secret not in failed_path.read_text(encoding="utf-8")
