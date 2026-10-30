from __future__ import annotations

import json
import wave
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.brain.voice import daemon, tts, voice_profile


@pytest.fixture
def profile_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config" / "voice-profile.json"
    monkeypatch.setattr(voice_profile, "PROFILE_PATH", path)
    return path


def _write_profile(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def _write_wav(path: Path, frames: int = 160) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as writer:
        writer.setnchannels(1)
        writer.setsampwidth(2)
        writer.setframerate(16000)
        writer.writeframes(b"\x00\x01" * frames)


def test_default_voice_profile_uses_existing_jarvis_reference(profile_path: Path) -> None:
    voice = voice_profile.load_profile()["voice"]

    assert voice == {
        "engine": "cv3",
        "ref_audio": "data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav",
        "prompt_text": None,
    }
    assert (voice_profile.ROOT / voice["ref_audio"]).is_file()


def test_l2_voice_override_is_applied(profile_path: Path, tmp_path: Path) -> None:
    reference = tmp_path / "custom-reference.wav"
    _write_wav(reference)
    _write_profile(
        profile_path,
        {
            "voice": {
                "engine": "edge",
                "ref_audio": str(reference),
                "prompt_text": "Custom prompt.<|endofprompt|>",
            }
        },
    )

    assert voice_profile.load_profile()["voice"] == {
        "engine": "edge",
        "ref_audio": str(reference),
        "prompt_text": "Custom prompt.<|endofprompt|>",
    }


def test_missing_l2_reference_falls_back_to_l1_jarvis(
    profile_path: Path, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    _write_profile(profile_path, {"voice": {"ref_audio": str(tmp_path / "missing.wav")}})

    voice = voice_profile.load_profile()["voice"]

    assert voice["ref_audio"] == voice_profile.DEFAULT_PROFILE["voice"]["ref_audio"]
    assert "reference audio unavailable" in caplog.text


def test_l3_voice_override_wins_over_l2(profile_path: Path, tmp_path: Path) -> None:
    l2_reference = tmp_path / "l2.wav"
    l3_reference = tmp_path / "l3.wav"
    _write_wav(l2_reference)
    _write_wav(l3_reference)
    _write_profile(
        profile_path,
        {"voice": {"engine": "edge", "ref_audio": str(l2_reference)}},
    )

    voice = voice_profile.load_profile(
        {"voice": {"engine": "cv3", "ref_audio": str(l3_reference)}}
    )["voice"]

    assert voice["engine"] == "cv3"
    assert voice["ref_audio"] == str(l3_reference)


def test_corrupt_l2_json_restores_builtin_voice(profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True, exist_ok=True)
    profile_path.write_text("{broken", encoding="utf-8")

    assert voice_profile.load_profile()["voice"] == voice_profile.DEFAULT_PROFILE["voice"]


def test_invalid_voice_fields_fall_back_individually(profile_path: Path) -> None:
    _write_profile(
        profile_path,
        {"voice": {"engine": "cloud", "ref_audio": "", "prompt_text": "  "}},
    )

    assert voice_profile.load_profile()["voice"] == voice_profile.DEFAULT_PROFILE["voice"]


@pytest.mark.parametrize("malformed", [None, [], "voice"])
def test_malformed_l2_voice_section_falls_back(
    profile_path: Path, malformed: object
) -> None:
    _write_profile(profile_path, {"voice": malformed})

    assert voice_profile.load_profile()["voice"] == voice_profile.DEFAULT_PROFILE["voice"]


@pytest.mark.parametrize("malformed", [None, [], "voice"])
def test_malformed_l3_voice_section_falls_back(
    profile_path: Path, malformed: object
) -> None:
    assert voice_profile.load_profile({"voice": malformed})["voice"] == (
        voice_profile.DEFAULT_PROFILE["voice"]
    )


@pytest.mark.parametrize("malformed", [[], {}, 7, True])
def test_malformed_voice_engine_falls_back(
    profile_path: Path, malformed: object
) -> None:
    _write_profile(profile_path, {"voice": {"engine": malformed}})

    assert voice_profile.load_profile()["voice"]["engine"] == "cv3"


@pytest.mark.parametrize("contents", [b"", b"not a wave", b"RIFF"])
def test_corrupt_l2_reference_falls_back_to_l1_jarvis(
    profile_path: Path, tmp_path: Path, contents: bytes
) -> None:
    reference = tmp_path / "corrupt.wav"
    reference.write_bytes(contents)
    _write_profile(profile_path, {"voice": {"ref_audio": str(reference)}})

    assert voice_profile.load_profile()["voice"]["ref_audio"] == (
        voice_profile.DEFAULT_PROFILE["voice"]["ref_audio"]
    )


def test_default_prompt_resolution_uses_jarvis_reference(profile_path: Path) -> None:
    expected = voice_profile.ROOT / voice_profile.DEFAULT_PROFILE["voice"]["ref_audio"]

    assert tts.resolve_prompt_wav() == expected


def test_missing_prompt_reference_uses_cosyvoice_asset(tmp_path: Path) -> None:
    profile = {"voice": {"ref_audio": str(tmp_path / "missing.wav")}}

    assert tts.resolve_prompt_wav(profile) == (
        tts.COSYVOICE_SOURCE / "asset" / "zero_shot_prompt.wav"
    )


def test_absolute_prompt_reference_is_used(tmp_path: Path) -> None:
    reference = tmp_path / "absolute.wav"
    _write_wav(reference)

    assert tts.resolve_prompt_wav({"voice": {"ref_audio": str(reference)}}) == reference


def test_default_jarvis_reference_uses_matching_builtin_transcript(
    profile_path: Path,
) -> None:
    assert tts.resolve_prompt_text() == (
        "Hello, Mr. Stark. I am Jarvis. And may I say, your suit is on fire."
        "<|endofprompt|>"
    )


@pytest.mark.parametrize(
    "reference",
    [
        "data/voice/jarvis-ref/../jarvis-ref/jarvis_voice_ref_pcm16.wav",
        str(
            voice_profile.ROOT
            / "data/voice/jarvis-ref/../jarvis-ref/jarvis_voice_ref_pcm16.wav"
        ),
    ],
)
def test_equivalent_jarvis_paths_use_matching_builtin_transcript(
    reference: str,
) -> None:
    profile = {"voice": {"ref_audio": reference, "prompt_text": None}}

    assert tts.resolve_prompt_text(profile) == (
        "Hello, Mr. Stark. I am Jarvis. And may I say, your suit is on fire."
        "<|endofprompt|>"
    )


def test_corrupt_prompt_reference_uses_cosyvoice_pair(tmp_path: Path) -> None:
    reference = tmp_path / "corrupt.wav"
    reference.write_bytes(b"not a wave")
    profile = {"voice": {"ref_audio": str(reference), "prompt_text": None}}

    assert tts.resolve_prompt_wav(profile) == (
        tts.COSYVOICE_SOURCE / "asset" / "zero_shot_prompt.wav"
    )
    assert tts.resolve_prompt_text(profile) == tts.DEFAULT_PROMPT_TEXT


@pytest.mark.parametrize(
    ("configured", "expected"),
    [
        (None, "希望你以后能够做的比我还好呦。<|endofprompt|>"),
        ("Jarvis custom prompt.<|endofprompt|>", "Jarvis custom prompt.<|endofprompt|>"),
    ],
)
def test_prompt_text_null_and_override_are_resolved(
    configured: str | None, expected: str
) -> None:
    profile = {"voice": {"prompt_text": configured}}

    assert tts.resolve_prompt_text(profile) == expected


def test_daemon_request_refreshes_resolved_prompt_pair(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first_reference = tmp_path / "first.wav"
    second_reference = tmp_path / "second.wav"
    _write_wav(first_reference)
    _write_wav(second_reference)
    requests: list[dict] = []

    class FakeDaemon:
        def ensure_started(self) -> bool:
            return True

        def request(self, request: dict, timeout: float) -> dict:
            requests.append(request)
            return {"ok": True, "engine": "cv3"}

    monkeypatch.setattr(daemon, "_tts_daemon", lambda: FakeDaemon())
    first = {
        "voice": {
            "ref_audio": str(first_reference),
            "prompt_text": "First prompt.<|endofprompt|>",
        }
    }
    second = {
        "voice": {
            "ref_audio": str(second_reference),
            "prompt_text": "Second prompt.<|endofprompt|>",
        }
    }

    daemon.daemon_tts_synthesize("first", tmp_path / "first-out.wav", profile=first)
    daemon.daemon_tts_synthesize("second", tmp_path / "second-out.wav", profile=second)

    assert [(item["prompt_wav"], item["prompt_text"]) for item in requests] == [
        (str(first_reference), "First prompt.<|endofprompt|>"),
        (str(second_reference), "Second prompt.<|endofprompt|>"),
    ]


def _profile_with_engine(engine: str) -> dict:
    return {
        "voice": {
            "engine": engine,
            "ref_audio": voice_profile.DEFAULT_PROFILE["voice"]["ref_audio"],
            "prompt_text": None,
        }
    }


def test_cv3_ready_uses_daemon_before_cold_or_edge(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "daemon.wav"
    calls: list[str] = []
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("cv3"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: True)
    monkeypatch.setattr(
        daemon,
        "daemon_tts_synthesize",
        lambda text, path, timeout, profile: calls.append("daemon")
        or {"ok": True, "wav": str(path), "engine": "cv3"},
    )
    monkeypatch.setattr(
        tts,
        "_synthesize_cv3_cold",
        lambda *args, **kwargs: calls.append("cold") or {"ok": True},
    )
    monkeypatch.setattr(
        tts,
        "_synthesize_edge",
        lambda *args, **kwargs: calls.append("edge") or {"ok": True},
    )

    result = tts._synthesize_once("hello", out, 10)

    assert result["engine"] == "cv3"
    assert calls == ["daemon"]


def test_daemon_unavailable_uses_cold_cv3_before_other_engines(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "cold.wav"
    calls: list[str] = []
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("cv3"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: True)
    monkeypatch.setattr(
        daemon,
        "daemon_tts_synthesize",
        lambda *args, **kwargs: calls.append("daemon") or None,
    )
    monkeypatch.setattr(
        tts,
        "_synthesize_cv3_cold",
        lambda *args, **kwargs: calls.append("cold")
        or {"ok": True, "wav": str(out), "engine": "cv3"},
    )
    monkeypatch.setattr(tts, "_piper_available", lambda: calls.append("piper") or True)

    result = tts._synthesize_once("hello", out, 10)

    assert result["engine"] == "cv3"
    assert calls == ["daemon", "cold"]


def test_cold_cv3_uses_the_profile_resolved_by_synthesize_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    profile = _profile_with_engine("cv3")
    reference = tmp_path / "profile-reference.wav"
    _write_wav(reference)
    rendered = tmp_path / "rendered.py"
    rendered.write_text("# rendered", encoding="utf-8")
    calls: list[tuple[str, dict]] = []
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: True)
    monkeypatch.setattr(
        tts,
        "resolve_prompt_wav",
        lambda supplied: calls.append(("resolve", supplied)) or reference,
    )
    monkeypatch.setattr(
        tts,
        "_render_script",
        lambda supplied: calls.append(("render", supplied)) or rendered,
    )
    monkeypatch.setattr(
        tts.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout='{"ok": true, "engine": "cv3"}\n', stderr="", returncode=0
        ),
    )

    result = tts._synthesize_cv3_cold("hello", tmp_path / "out.wav", 10, profile)

    assert result["engine"] == "cv3"
    assert calls == [("resolve", profile), ("render", profile)]


def test_cv3_unavailable_falls_back_to_local_piper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "piper.wav"
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("cv3"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: False)
    monkeypatch.setattr(tts, "_piper_available", lambda: True)

    def synthesize_piper(text: str, path: Path) -> dict:
        path.write_bytes(b"wav")
        return {"ok": True, "wav": str(path), "engine": "sherpa-piper-tts"}

    monkeypatch.setattr(tts, "_synthesize_piper", synthesize_piper)
    monkeypatch.setattr(
        tts, "_synthesize_edge", lambda *args, **kwargs: pytest.fail("edge called")
    )

    assert tts._synthesize_once("hello", out, 10)["engine"] == "sherpa-piper-tts"


def test_piper_unavailable_falls_back_to_local_melo(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "melo.wav"
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("cv3"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: False)
    monkeypatch.setattr(tts, "_piper_available", lambda: False)
    monkeypatch.setattr(tts, "_sherpa_tts_available", lambda: True)

    def synthesize_melo(text: str, path: Path) -> dict:
        path.write_bytes(b"wav")
        return {"ok": True, "wav": str(path), "engine": "sherpa-melo-tts"}

    monkeypatch.setattr(tts, "_synthesize_sherpa", synthesize_melo)
    monkeypatch.setattr(
        tts, "_synthesize_edge", lambda *args, **kwargs: pytest.fail("edge called")
    )

    assert tts._synthesize_once("hello", out, 10)["engine"] == "sherpa-melo-tts"


def test_edge_engine_explicitly_allows_edge_after_local_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "edge.wav"
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("edge"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: False)
    monkeypatch.setattr(tts, "_piper_available", lambda: False)
    monkeypatch.setattr(tts, "_sherpa_tts_available", lambda: False)

    def synthesize_edge(text: str, path: Path) -> dict:
        path.write_bytes(b"wav")
        return {"ok": True, "wav": str(path), "engine": "edge-tts"}

    monkeypatch.setattr(tts, "_synthesize_edge", synthesize_edge)

    assert tts._synthesize_once("hello", out, 10)["engine"] == "edge-tts"


def test_cv3_engine_disables_edge_when_all_local_engines_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(tts, "load_profile", lambda: _profile_with_engine("cv3"))
    monkeypatch.setattr(tts, "all_cv3_resources_ready", lambda: False)
    monkeypatch.setattr(tts, "_piper_available", lambda: False)
    monkeypatch.setattr(tts, "_sherpa_tts_available", lambda: False)
    monkeypatch.setattr(
        tts, "_synthesize_edge", lambda *args, **kwargs: pytest.fail("edge called")
    )

    with pytest.raises(RuntimeError, match="本地 TTS 链路不可用"):
        tts._synthesize_once("hello", tmp_path / "missing.wav", 10)


def test_tts_synthesize_result_has_no_circular_attempt_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "serializable.wav"

    def synthesize_once(text: str, path: Path, timeout: int) -> dict:
        path.write_bytes(b"wav")
        return {"ok": True, "wav": str(path), "engine": "cv3"}

    monkeypatch.setattr(tts, "_synthesize_once", synthesize_once)
    monkeypatch.setattr(tts, "tts_output_is_near_silent", lambda path: False)

    result = tts.tts_synthesize("hello", out)

    assert json.loads(json.dumps(result))["engine"] == "cv3"
    assert result["attempts"][0] is not result
