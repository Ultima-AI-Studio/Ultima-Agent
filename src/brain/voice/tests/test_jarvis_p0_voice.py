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


def test_kws_listener_refreshes_only_its_stream_and_fuzzy_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import numpy as np

    fake_sounddevice = types.ModuleType("sounddevice")
    fake_sherpa = types.ModuleType("sherpa_onnx")

    class FakeStream:
        def accept_waveform(self, _sample_rate, _samples) -> None:
            return None

    class FakeSpotter:
        def __init__(self, **kwargs) -> None:
            self.created = 0
            self.kwargs = kwargs

        def create_stream(self):
            self.created += 1
            return FakeStream()

        def is_ready(self, _stream) -> bool:
            return False

    fake_sherpa.KeywordSpotter = FakeSpotter
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)
    monkeypatch.setitem(sys.modules, "sherpa_onnx", fake_sherpa)
    sys.modules.pop("src.brain.voice.kws_listener", None)
    import src.brain.voice as voice_package

    monkeypatch.delattr(voice_package, "kws_listener", raising=False)
    kws_listener = importlib.import_module("src.brain.voice.kws_listener")

    keywords = tmp_path / "keywords.txt"
    keywords.write_text("j iǎ w éi s ī @贾维斯\n", encoding="utf-8")
    monkeypatch.setitem(kws_listener._KWS_ARGS, "keywords_file", str(keywords))
    listener = kws_listener.KwsListener()
    assert listener.kws.kwargs["keywords_threshold"] == pytest.approx(0.08)
    assert listener.kws.kwargs["keywords_score"] == pytest.approx(2.0)
    assert listener.kws.kwargs["num_trailing_blanks"] == 8
    original_stream = listener._stream

    class RestartNow:
        @staticmethod
        def should_restart(*, active_audio: bool) -> bool:
            assert not active_audio
            return True

    listener._restart_guard = RestartNow()
    monkeypatch.setattr(listener, "_detect", lambda _block: "贾维丝")
    assert listener.feed(np.zeros(3200, dtype=np.float32)) == "贾维丝"
    assert listener._stream is not original_stream
    assert listener.session_restart_count == 1
