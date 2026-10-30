from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.brain.interaction import InteractionLoop
from src.brain.voice import voice_profile


@pytest.fixture()
def persona_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[Path, Path]:
    profile = tmp_path / "voice-profile.json"
    jarvis = tmp_path / "jarvis.md"
    jarvis.write_text("JARVIS L1 FACTS ONLY", encoding="utf-8")
    monkeypatch.setattr(voice_profile, "PROFILE_PATH", profile)
    monkeypatch.setattr(voice_profile, "JARVIS_PERSONA_PATH", jarvis)
    return profile, jarvis


def test_normal_jarvis_persona_loads(persona_paths: tuple[Path, Path]) -> None:
    assert voice_profile.load_persona() == "JARVIS L1 FACTS ONLY"


def test_existing_override_takes_priority(
    persona_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    profile_path, _ = persona_paths
    override = tmp_path / "custom.md"
    override.write_text("CUSTOM PERSONA", encoding="utf-8")
    profile_path.write_text(
        json.dumps({"persona": {"override": str(override)}}), encoding="utf-8"
    )
    assert voice_profile.load_persona() == "CUSTOM PERSONA"


def test_missing_override_falls_back_to_jarvis(
    persona_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    profile_path, _ = persona_paths
    profile_path.write_text(
        json.dumps({"persona": {"override": str(tmp_path / "missing.md")}}), encoding="utf-8"
    )
    assert voice_profile.load_persona() == "JARVIS L1 FACTS ONLY"


def test_missing_jarvis_file_uses_built_in_template(
    persona_paths: tuple[Path, Path]
) -> None:
    _, jarvis = persona_paths
    jarvis.unlink()
    content = voice_profile.load_persona()
    assert "Jarvis" in content
    assert "Never invent" in content


def test_agent_fallback_sends_persona_and_filters_marketing(
    persona_paths: tuple[Path, Path], tmp_path: Path
) -> None:
    loop = InteractionLoop(tmp_path / "queue")
    with patch("src.brain.agent_client.agent_healthy", return_value=True), patch(
        "src.brain.agent_client.ask_agent", return_value="天气晴朗。请点赞关注我们。"
    ) as ask:
        reply = loop._try_agent_fallback("查天气")
    assert reply is not None
    assert reply.text == "收到。"
    sent = ask.call_args.args[0]
    assert "JARVIS L1 FACTS ONLY" in sent
    assert "查天气" in sent
