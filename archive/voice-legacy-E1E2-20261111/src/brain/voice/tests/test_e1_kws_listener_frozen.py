"""E1 唤醒入口冻结用例（随 archive/voice-legacy-E1E2-20261111 一起归档）。

原位置：src/brain/voice/tests/test_jarvis_p0_voice.py::test_kws_listener_refreshes_only_its_stream_and_fuzzy_matches
断言一句未改 —— 阈值 0.08 / score 2.0 / trailing 8、模糊命中"贾维丝"、命中后只换 stream 不重建实例。
唯一改动是被测模块的加载方式：从 `import src.brain.voice.kws_listener` 改为按归档路径 spec 加载。

本文件不在 pytest 默认收集范围内（archive 不被扫），不进入 CI；
保留它是为回滚 E1 时仍有一份可执行的行为基线，而不是为让测试变绿而删除判据。
"""

from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import numpy as np
import pytest

ARCHIVE_ROOT = Path(__file__).resolve().parents[4]


def _load_archived_kws_listener():
    path = ARCHIVE_ROOT / "src" / "brain" / "voice" / "kws_listener.py"
    assert path.exists(), f"归档文件缺失：{path}"
    spec = importlib.util.spec_from_file_location("ua_archive_kws_listener", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules["ua_archive_kws_listener"] = module
    spec.loader.exec_module(module)
    return module


def test_kws_listener_refreshes_only_its_stream_and_fuzzy_matches(
    tmp_path: Path,
    monkeypatch,
) -> None:
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

    kws_listener = _load_archived_kws_listener()

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
