from __future__ import annotations

import inspect
import importlib
import sys
import types
from pathlib import Path

import pytest

from src.brain.voice import asr
from src.brain.voice.session_restart import SessionRestartGuard
from src.brain.voice.transcription_backends import (
    BackendUnavailable,
    TranscriptionRouter,
)
from src.brain.voice.wake_matching import WakePhraseMatcher, levenshtein_ratio


def test_levenshtein_threshold_is_strictly_below_point_35() -> None:
    matcher = WakePhraseMatcher(("jarvis",), threshold=0.35)
    assert matcher.matches("jarvix")
    assert levenshtein_ratio("jarvix", "jarvis") == pytest.approx(1 / 6)
    assert matcher.matches("jxxvis")
    assert levenshtein_ratio("jxxvis", "jarvis") == pytest.approx(2 / 6)
    boundary_matcher = WakePhraseMatcher(("a" * 20,), threshold=0.35)
    boundary_value = "a" * 13 + "b" * 7
    assert levenshtein_ratio(boundary_value, "a" * 20) == pytest.approx(0.35)
    assert not boundary_matcher.matches(boundary_value)


def test_fuzzy_matching_uses_word_windows_and_unicode_normalization() -> None:
    matcher = WakePhraseMatcher(("hey jarvis", "贾维斯", "ULTIMA"))
    assert matcher.matches("please hey jarvix now")
    assert matcher.matches("贾维丝")
    assert matcher.matches("ｕｌｔｉｍａ")
    assert not matcher.matches("ordinary background conversation")


def test_keyword_file_labels_are_extracted_without_phoneme_tokens() -> None:
    matcher = WakePhraseMatcher.from_keyword_lines(
        ("j iǎ w éi s ī @贾维斯", "AH1 L T IH0 M AH0 @ULTIMA")
    )
    assert matcher.targets == ("贾维斯", "ultima")


def test_session_restart_fires_once_at_50_seconds_and_defers_during_audio() -> None:
    now = [100.0]
    guard = SessionRestartGuard(interval_seconds=50.0, clock=lambda: now[0])
    assert not guard.should_restart(active_audio=False)
    now[0] = 150.0
    assert not guard.should_restart(active_audio=True)
    now[0] = 151.0
    assert guard.should_restart(active_audio=False)
    assert not guard.should_restart(active_audio=False)
    now[0] = 201.0
    assert guard.should_restart(active_audio=False)


def test_transcription_router_is_local_first_and_switches_without_call_site_change(
    tmp_path: Path,
) -> None:
    wav = tmp_path / "sample.wav"
    wav.write_bytes(b"RIFF")
    calls: list[str] = []
    router = TranscriptionRouter()
    router.register(
        "sherpa-onnx",
        lambda path: calls.append("sherpa-onnx") or {"ok": True, "text": "本地"},
    )
    router.register(
        "optional-cloud",
        lambda path: calls.append("optional-cloud") or {"ok": True, "text": "云端"},
        is_cloud=True,
    )

    assert router.names == ("sherpa-onnx", "optional-cloud")
    assert router.transcribe(wav)["text"] == "本地"
    assert calls == ["sherpa-onnx"]
    assert router.transcribe(wav, preferred="optional-cloud")["text"] == "云端"


def test_transcription_router_falls_back_to_optional_cloud() -> None:
    router = TranscriptionRouter()

    def unavailable(_path: Path) -> dict:
        raise BackendUnavailable("local model unavailable")

    router.register("sherpa-onnx", unavailable)
    router.register("optional-cloud", lambda _path: {"ok": True, "text": "fallback"}, is_cloud=True)
    result = router.transcribe(Path("fixture.wav"))
    assert result["text"] == "fallback"
    assert result["backend"] == "optional-cloud"


def test_asr_public_signature_and_call_site_stay_stable(tmp_path: Path, monkeypatch) -> None:
    wav = tmp_path / "sample.wav"
    wav.write_bytes(b"RIFF")

    class FakeRouter:
        def transcribe(self, path: Path, *, preferred: str | None = None) -> dict:
            assert path == wav
            assert preferred is None
            return {"ok": True, "text": "router-result", "backend": "fake"}

    monkeypatch.setattr(asr, "_build_transcription_router", lambda timeout: FakeRouter())
    assert tuple(inspect.signature(asr.asr_transcribe).parameters) == (
        "wav_path",
        "model",
        "timeout",
    )
    assert asr.asr_transcribe(wav)["text"] == "router-result"


# 旧唤醒入口（src/brain/voice/kws_listener.py）已冻结归档到
# archive/voice-legacy-E1E2-20261111/，其专属用例随文件一并移出，不在此处保留。
