from __future__ import annotations

import importlib.util
import json
import sys
import time
import types
from pathlib import Path

import pytest

from src.brain.interaction import _WAKE_ECHO_ONLY
from src.brain.voice import voice_profile


def _load_daemon_module():
    path = voice_profile.ROOT / "data" / "logs" / "voice-listen-daemon.py"
    spec = importlib.util.spec_from_file_location("voice_listen_daemon_reload_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_custom_syncs_keywords_and_preserves_baseline(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    keywords = tmp_path / "keywords.txt"
    keywords.write_text("legacy @OLD\nAH1 L T IH0 M AH0 @ULTIMA\n", encoding="utf-8")
    monkeypatch.setattr(voice_profile, "KEYWORDS_PATH", keywords)
    profile = voice_profile.load_profile(
        {"wakeword": {"custom": "x īng q ī w ǔ @星期五"}}
    )
    assert voice_profile.apply_to_daemon(profile)
    lines = keywords.read_text(encoding="utf-8").splitlines()
    assert lines[:6] == voice_profile.DEFAULT_WAKE_WORDS
    assert "x īng q ī w ǔ @星期五" in lines
    assert lines[-1].endswith("@ULTIMA")


def test_plain_chinese_custom_uses_pinned_asr_phonemizer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    keywords = tmp_path / "keywords.txt"
    keywords.write_text("AH1 L T IH0 M AH0 @ULTIMA\n", encoding="utf-8")
    monkeypatch.setattr(voice_profile, "KEYWORDS_PATH", keywords)
    profile = voice_profile.load_profile({"wakeword": {"custom": "查天气"}})
    assert voice_profile.apply_to_daemon(profile)
    assert "ch á t iān q ì @查天气" in keywords.read_text(encoding="utf-8")


def test_daemon_mtime_rebuilds_spotter_without_pid_change(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = _load_daemon_module()
    keywords = tmp_path / "keywords.txt"
    profile = tmp_path / "voice-profile.json"
    keywords.write_text("old @OLD\n", encoding="utf-8")
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daemon, "KWS_KEYWORDS", keywords)
    monkeypatch.setattr(daemon, "VOICE_PROFILE", profile)

    class FakeSpotter:
        def __init__(self, generation: int):
            self.generation = generation

        def create_stream(self):
            return object()

    built = []

    def factory():
        spotter = FakeSpotter(len(built) + 1)
        built.append(spotter)
        return spotter

    manager = daemon.HotReloadSpotter(factory)
    pid_before = __import__("os").getpid()
    time.sleep(0.01)
    keywords.write_text("new @NEW\n", encoding="utf-8")
    replacement = manager.maybe_reload()
    assert replacement.generation == 2
    assert manager.spotter is replacement
    assert __import__("os").getpid() == pid_before


def test_daemon_reload_failure_keeps_old_instance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = _load_daemon_module()
    keywords = tmp_path / "keywords.txt"
    profile = tmp_path / "voice-profile.json"
    keywords.write_text("old @OLD\n", encoding="utf-8")
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daemon, "KWS_KEYWORDS", keywords)
    monkeypatch.setattr(daemon, "VOICE_PROFILE", profile)

    class FakeSpotter:
        def create_stream(self):
            return object()

    calls = 0

    def factory():
        nonlocal calls
        calls += 1
        if calls > 1:
            raise RuntimeError("broken model")
        return FakeSpotter()

    manager = daemon.HotReloadSpotter(factory)
    old = manager.spotter
    time.sleep(0.01)
    keywords.write_text("bad @BAD\n", encoding="utf-8")
    assert manager.maybe_reload() is old
    assert manager.spotter is old


def test_interaction_wake_echo_uses_custom_profile(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "voice-profile.json"
    path.write_text(
        json.dumps({"wakeword": {"custom": "x īng q ī w ǔ @星期五"}}, ensure_ascii=False),
        encoding="utf-8",
    )
    monkeypatch.setattr(voice_profile, "PROFILE_PATH", path)
    assert _WAKE_ECHO_ONLY.match("星期五。")


def test_kws_listener_reload_swaps_only_after_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_sounddevice = types.ModuleType("sounddevice")
    fake_sherpa = types.ModuleType("sherpa_onnx")

    class FakeSpotter:
        def __init__(self, **_kwargs):
            self.stream = object()

        def create_stream(self):
            return self.stream

    fake_sherpa.KeywordSpotter = FakeSpotter
    monkeypatch.setitem(sys.modules, "sounddevice", fake_sounddevice)
    monkeypatch.setitem(sys.modules, "sherpa_onnx", fake_sherpa)
    sys.modules.pop("src.brain.voice.kws_listener", None)
    from src.brain.voice import kws_listener

    keywords = tmp_path / "keywords.txt"
    keywords.write_text("old @OLD\n", encoding="utf-8")
    monkeypatch.setitem(kws_listener._KWS_ARGS, "keywords_file", str(keywords))
    listener = kws_listener.KwsListener()
    old = listener.kws
    time.sleep(0.01)
    keywords.write_text("new @NEW\n", encoding="utf-8")
    assert listener.maybe_reload_keywords()
    assert listener.kws is not old
    assert listener._keywords == ("new @NEW",)
