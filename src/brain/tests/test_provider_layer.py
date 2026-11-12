from __future__ import annotations

import importlib
import json
from pathlib import Path
import sys
import time
from types import SimpleNamespace
from typing import Any
from urllib.error import HTTPError

import pytest


class _Response:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def __enter__(self) -> "_Response":
        return self

    def __exit__(self, *_args: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def _provider_api():
    try:
        from src.brain.providers.base import ProviderConfigError
        from src.brain.providers.resolve import provider_for
    except ModuleNotFoundError as exc:
        pytest.fail(f"provider layer is not implemented: {exc}")
    return ProviderConfigError, provider_for


def _settings(impl: str) -> dict[str, Any]:
    return {
        "slot": "S-MAIN",
        "impl": impl,
        "endpoint": "http://provider.invalid",
        "model": "test-model",
        "enabled": True,
    }


def test_ollama_native_payload_preserves_native_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    _, provider_for = _provider_api()
    from src.brain.providers import ollama_native

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(
            {
                "message": {"content": '{"reply_text":"ok"}'},
                "prompt_eval_count": 4,
                "eval_count": 2,
            }
        )

    monkeypatch.setattr(ollama_native, "urlopen", fake_urlopen)
    schema = {"type": "object", "required": ["reply_text"]}

    result = provider_for(_settings("ollama")).chat(
        system_prompt="system",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.25,
        max_tokens=321,
        json_schema=schema,
        disable_thinking=True,
        timeout=7.5,
    )

    assert captured["url"] == "http://provider.invalid/api/chat"
    assert captured["timeout"] == 7.5
    assert captured["body"] == {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "hello"},
        ],
        "stream": False,
        "think": False,
        "format": schema,
        "options": {"temperature": 0.25, "num_predict": 321},
    }
    assert result.content == '{"reply_text":"ok"}'
    assert result.usage == {
        "prompt_tokens": 4,
        "completion_tokens": 2,
        "total_tokens": 6,
    }
    print("ollama_payload=" + json.dumps(captured["body"], ensure_ascii=False, sort_keys=True))


def test_openai_compat_payload_maps_schema_without_think(monkeypatch: pytest.MonkeyPatch) -> None:
    _, provider_for = _provider_api()
    from src.brain.providers import openai_compat

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(
            {
                "choices": [{"message": {"content": "ok"}}],
                "usage": {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4},
            }
        )

    monkeypatch.setattr(openai_compat, "urlopen", fake_urlopen)
    settings = _settings("openai-compatible")
    settings["endpoint"] = "http://provider.invalid/v1"
    schema = {"type": "object", "properties": {"answer": {"type": "string"}}}

    result = provider_for(settings).chat(
        system_prompt="system",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.1,
        max_tokens=222,
        json_schema=schema,
        disable_thinking=True,
        timeout=8.0,
    )

    assert captured["url"] == "http://provider.invalid/v1/chat/completions"
    assert captured["timeout"] == 8.0
    assert captured["body"] == {
        "model": "test-model",
        "messages": [
            {"role": "system", "content": "system"},
            {"role": "user", "content": "hello"},
        ],
        "temperature": 0.1,
        "max_tokens": 222,
        "response_format": {"type": "json_schema", "json_schema": schema},
    }
    assert "think" not in captured["body"]
    assert result.content == "ok"
    assert result.usage == {"prompt_tokens": 3, "completion_tokens": 1, "total_tokens": 4}
    print("openai_payload=" + json.dumps(captured["body"], ensure_ascii=False, sort_keys=True))


def test_existing_ollama_8b_default_uses_native_protocol() -> None:
    _, provider_for = _provider_api()

    provider = provider_for(_settings("ollama-8b"))

    assert provider.__class__.__name__ == "OllamaNativeProvider"


def test_unknown_impl_raises_provider_config_error() -> None:
    ProviderConfigError, provider_for = _provider_api()

    with pytest.raises(ProviderConfigError, match="weird"):
        provider_for(_settings("weird"))


def test_provider_sources_have_no_config_reads_or_hardcoded_defaults() -> None:
    providers_dir = Path(__file__).resolve().parents[1] / "providers"
    files = sorted(providers_dir.glob("*.py"))
    assert files, "provider source files must exist"

    banned = ("os.environ", "json.load", "11434", "qwen3-8b")
    matches = {
        token: [path.name for path in files if token in path.read_text(encoding="utf-8")]
        for token in banned
    }

    assert matches == {token: [] for token in banned}
    print(f"provider_scan files={len(files)} banned_matches={sum(map(len, matches.values()))}")


def _main_settings(impl: str = "ollama") -> dict[str, Any]:
    return {
        "slot": "S-MAIN",
        "impl": impl,
        "endpoint": "http://provider.invalid",
        "model": "configured-model",
        "enabled": True,
    }


def test_agent_server_structured_reply_preserves_locked_ollama_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server
    from src.brain.providers import ollama_native

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response(
            {
                "message": {
                    "content": '{"reply_text":"完成。","confidence":0.9,"grounded":true}'
                }
            }
        )

    monkeypatch.setattr(ollama_native, "urlopen", fake_urlopen)
    monkeypatch.setattr(agent_server, "_MAIN", _main_settings(), raising=False)

    reply = agent_server._request_structured_reply("状态？", "完成。", [])

    expected_user = json.dumps(
        {
            "user_query": "状态？",
            "agent_draft": "完成。",
            "tool_evidence": [],
            "retry_note": None,
        },
        ensure_ascii=False,
    )
    assert captured["body"] == {
        "model": "configured-model",
        "messages": [
            {"role": "system", "content": agent_server.STRUCTURED_REPLY_SYSTEM_PROMPT},
            {"role": "user", "content": expected_user},
        ],
        "stream": False,
        "think": False,
        "format": agent_server.REPLY_JSON_SCHEMA,
    }
    assert captured["timeout"] == agent_server.STRUCTURED_REPLY_TIMEOUT_SECONDS
    assert reply.reply_text == "完成。"
    print("structured_payload=" + json.dumps(captured["body"], ensure_ascii=False, sort_keys=True))


def test_agent_server_intent_classification_keeps_thinking_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server
    from src.brain.providers import ollama_native

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response({"message": {"content": "动手"}})

    monkeypatch.setattr(ollama_native, "urlopen", fake_urlopen)
    monkeypatch.setattr(agent_server, "_MAIN", _main_settings(), raising=False)

    assert agent_server._classify_intent("帮我制定并执行方案") == "task"
    assert captured["body"]["options"] == {"temperature": 0, "num_predict": 256}
    assert captured["body"].get("think") is not False
    assert captured["timeout"] == 15


def test_agent_server_get_jarvis_maps_ollama_alias_and_model(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server

    captured: dict[str, Any] = {}

    class FakeJarvis:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)
            self._config = SimpleNamespace(agent=SimpleNamespace(max_turns=10))

    monkeypatch.setattr(agent_server, "_MAIN", _main_settings("ollama-8b"), raising=False)
    monkeypatch.setattr(agent_server, "_jars", None)
    monkeypatch.setattr(agent_server, "_ensure_tools_registered", lambda: None)
    monkeypatch.setattr(agent_server, "Jarvis", FakeJarvis)

    jarvis = agent_server.get_jarvis()

    assert captured == {"engine_key": "ollama", "model": "configured-model"}
    assert jarvis._config.agent.max_turns == agent_server.ASK_MAX_TURNS


def test_mainbrain_proposal_uses_call_time_main_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import mainbrain_proposal
    from src.brain.providers import ollama_native

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["body"] = json.loads(request.data.decode("utf-8"))
        captured["timeout"] = timeout
        return _Response({"message": {"content": "建议派给策划部。"}})

    monkeypatch.setattr(ollama_native, "urlopen", fake_urlopen)
    monkeypatch.setattr(mainbrain_proposal, "main_settings", lambda: _main_settings(), raising=False)

    result = mainbrain_proposal.propose("请给出派发建议", timeout=9.0)

    assert captured["body"]["model"] == "configured-model"
    assert captured["body"]["stream"] is False
    assert captured["body"]["options"] == {
        "temperature": mainbrain_proposal.PROPOSE_TEMPERATURE,
        "num_predict": mainbrain_proposal.PROPOSE_NUM_PREDICT,
    }
    assert captured["timeout"] == 9.0
    assert result["model"] == "configured-model"
    print("proposal_payload=" + json.dumps(captured["body"], ensure_ascii=False, sort_keys=True))


def test_subagent_factory_uses_effective_main_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import openjarvis

    agent_tools_ultima = sys.modules.get("agent_tools_ultima")
    if agent_tools_ultima is None:
        from src.brain import agent_tools_ultima as packaged_agent_tools

        agent_tools_ultima = packaged_agent_tools

    captured: dict[str, Any] = {}

    class FakeJarvis:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)

    monkeypatch.setattr(agent_tools_ultima, "main_settings", lambda: _main_settings(), raising=False)
    monkeypatch.setattr(openjarvis, "Jarvis", FakeJarvis)

    child = agent_tools_ultima.UltimaSubagentTool._create_child()

    assert isinstance(child, FakeJarvis)
    assert captured == {"engine_key": "ollama", "model": "configured-model"}


def test_memory_backend_defaults_use_effective_main_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from src.brain.memory import backend

    monkeypatch.setattr(
        backend,
        "main_settings",
        lambda: {
            "model": "configured-memory-model",
            "endpoint": "http://configured-memory.invalid",
        },
        raising=False,
    )
    monkeypatch.setattr(backend.Mem0Backend, "_build_mem0", lambda self: object())

    memory = backend.Mem0Backend(data_dir=str(tmp_path), auto_registry=False)

    assert memory._memory_llm_model == "configured-memory-model"
    assert memory._ollama_base_url == "http://configured-memory.invalid"
    print(
        "memory_defaults="
        + json.dumps(
            {
                "model": memory._memory_llm_model,
                "endpoint": memory._ollama_base_url,
            },
            sort_keys=True,
        )
    )


def test_memory_backend_explicit_settings_override_main_settings(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    from src.brain.memory import backend

    def fail_if_called() -> dict[str, Any]:
        raise AssertionError("main_settings must not be read when both values are explicit")

    monkeypatch.setattr(backend, "main_settings", fail_if_called, raising=False)
    monkeypatch.setattr(backend.Mem0Backend, "_build_mem0", lambda self: object())

    memory = backend.Mem0Backend(
        data_dir=str(tmp_path),
        memory_llm_model="explicit-memory-model",
        ollama_base_url="http://explicit-memory.invalid",
        auto_registry=False,
    )

    assert memory._memory_llm_model == "explicit-memory-model"
    assert memory._ollama_base_url == "http://explicit-memory.invalid"
    print(
        "memory_explicit="
        + json.dumps(
            {
                "model": memory._memory_llm_model,
                "endpoint": memory._ollama_base_url,
            },
            sort_keys=True,
        )
    )


def test_orchestration_model_key_is_derived_from_effective_main_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from openjarvis.core.types import RoutingContext
    from src.brain.orchestration import engine

    monkeypatch.setattr(
        engine,
        "main_settings",
        lambda: {"model": "configured-route-model:latest"},
        raising=False,
    )
    machine = engine.LangGraphStateMachine(engine_key="provider-layer-route")

    selected = machine.select_model(RoutingContext(query="route", complexity_score=0.5))

    assert selected == "configured-route-model"
    print(f"orchestration_model_key={selected}")


def test_agent_server_health_payload_preserves_keys_and_exposes_provider(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server

    monkeypatch.setattr(agent_server, "_MAIN", _main_settings("ollama-8b"), raising=False)

    payload = agent_server._health_payload()

    assert {"ok", "model", "agent", "tools"} <= payload.keys()
    assert payload["ok"] is True
    assert payload["model"] == "configured-model"
    assert payload["provider"] == "ollama-8b"
    assert payload["provider_model"] == "configured-model"
    assert payload["provider_configured"] is True
    assert payload["provider_answerable"] is True
    assert "provider_note" not in payload
    print("health_configured=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


def test_agent_server_health_payload_marks_unusable_when_endpoint_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server

    settings = _main_settings("ollama-8b")
    settings.update({"endpoint": "", "enabled": False})
    monkeypatch.setattr(agent_server, "_MAIN", settings, raising=False)

    payload = agent_server._health_payload()

    assert payload["ok"] is True
    assert payload["provider_configured"] is False
    assert payload["provider_answerable"] is False
    assert payload["provider_note"] == "主脑配置缺失（endpoint），/ask 将无法作答"
    assert "无法作答" in payload["provider_note"]
    assert "endpoint" in payload["provider_note"]
    print("health_unusable=" + json.dumps(payload, ensure_ascii=False, sort_keys=True))


def test_agent_server_health_payload_reports_builtin_default_when_not_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from src.brain import agent_server

    settings = {
        "impl": "ollama-8b",
        "endpoint": "http://127.0.0.1:11434",
        "model": "qwen3-8b-uncensored:latest",
        "enabled": False,
    }
    monkeypatch.setattr(agent_server, "_MAIN", settings, raising=False)

    payload = agent_server._health_payload()

    assert payload["provider_answerable"] is True
    assert payload["provider_configured"] is False
    assert "provider_note" in payload
    assert "未显式配置" in payload["provider_note"]
    assert "内置默认" in payload["provider_note"]
    assert "ollama-8b" in payload["provider_note"]
    assert "qwen3-8b-uncensored:latest" in payload["provider_note"]
    assert "无法作答" not in payload["provider_note"]


@pytest.mark.parametrize("missing_key", ["impl", "model"])
def test_agent_server_health_payload_names_other_missing_provider_fields(
    monkeypatch: pytest.MonkeyPatch,
    missing_key: str,
) -> None:
    from src.brain import agent_server

    settings = _main_settings("ollama-8b")
    settings[missing_key] = ""
    monkeypatch.setattr(agent_server, "_MAIN", settings, raising=False)

    payload = agent_server._health_payload()

    assert payload["provider_configured"] is True
    assert payload["provider_answerable"] is False
    assert payload["provider_note"] == f"主脑配置缺失（{missing_key}），/ask 将无法作答"
    assert "无法作答" in payload["provider_note"]
    assert missing_key in payload["provider_note"]


def _probe_api():
    try:
        from src.brain.providers.probe import probe
    except ModuleNotFoundError as exc:
        pytest.fail(f"provider probe is not implemented: {exc}")
    return probe


def test_probe_not_configured_skips_network() -> None:
    probe = _probe_api()
    settings = _settings("ollama")
    settings["enabled"] = False

    result = probe(settings, timeout=0.2)

    assert result.state == "not-configured"
    assert result.latency_ms == 0
    print(f"probe_not_configured state={result.state} latency_ms={result.latency_ms}")


def test_probe_closed_port_returns_within_timeout() -> None:
    probe = _probe_api()
    settings = _settings("ollama")
    settings["endpoint"] = "http://127.0.0.1:1"
    timeout = 0.5

    started = time.perf_counter()
    result = probe(settings, timeout=timeout)
    elapsed_ms = round((time.perf_counter() - started) * 1000, 3)

    assert result.state == "unreachable"
    assert elapsed_ms <= timeout * 1000
    print(
        f"probe_unreachable state={result.state} "
        f"latency_ms={result.latency_ms} elapsed_ms={elapsed_ms} timeout_ms={timeout * 1000}"
    )


def test_probe_ok_uses_model_listing_endpoint(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _probe_api()
    probe_module = importlib.import_module("src.brain.providers.probe")

    captured: dict[str, Any] = {}

    def fake_urlopen(request, timeout: float):
        captured["url"] = request.full_url
        captured["timeout"] = timeout
        return _Response({"models": []})

    monkeypatch.setattr(probe_module, "urlopen", fake_urlopen)

    result = probe(_settings("ollama"), timeout=0.3)

    assert result.state == "ok"
    assert captured == {"url": "http://provider.invalid/api/tags", "timeout": 0.3}
    print(f"probe_ok state={result.state} latency_ms={result.latency_ms} url={captured['url']}")


def test_probe_unauthorized_is_a_state(monkeypatch: pytest.MonkeyPatch) -> None:
    probe = _probe_api()
    probe_module = importlib.import_module("src.brain.providers.probe")

    def fake_urlopen(request, timeout: float):
        del timeout
        raise HTTPError(request.full_url, 401, "Unauthorized", {}, None)

    monkeypatch.setattr(probe_module, "urlopen", fake_urlopen)

    result = probe(_settings("openai-compatible"), timeout=0.3)

    assert result.state == "unauthorized"
    print(f"probe_unauthorized state={result.state} latency_ms={result.latency_ms}")


def test_probe_local_ollama_when_available() -> None:
    probe = _probe_api()
    settings = _settings("ollama")
    settings["endpoint"] = "http://127.0.0.1:11434"

    result = probe(settings, timeout=2.0)

    if result.state != "ok":
        pytest.skip(f"local Ollama unavailable: {result.detail}")
    print(f"probe_local_ollama state={result.state} latency_ms={result.latency_ms}")
