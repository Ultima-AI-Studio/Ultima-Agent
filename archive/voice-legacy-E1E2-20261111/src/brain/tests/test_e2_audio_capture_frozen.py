"""E2 采集行为冻结副本（随 archive/voice-legacy-E1E2-20261111 一起归档）。

原位置：src/brain/tests/test_audio_resample.py::test_audio_capture_opens_wasapi_stereo_and_reads_mono
原判据一句未改，仅把被测文件路径从 `data/logs/voice-listen-daemon.py` 改到本归档内同路径。

本文件不在 pytest 默认收集范围内（archive 目录不被扫），不会进入 CI；
保留它是为了回滚 E2 时仍有一份可执行的行为基线，而不是为让测试变绿而删除判据。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np


def test_audio_capture_opens_wasapi_stereo_and_reads_mono() -> None:
    daemon_path = Path(__file__).resolve().parents[3] / "data" / "logs" / "voice-listen-daemon.py"
    spec = importlib.util.spec_from_file_location("voice_listen_daemon_for_test", daemon_path)
    assert spec is not None and spec.loader is not None
    daemon = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(daemon)

    class FakeStream:
        def __init__(self, **kwargs) -> None:
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, *args) -> None:
            return None

        def read(self, frames: int):
            assert frames == 2
            return np.array([[1000, 3000], [-1000, 1000]], dtype=np.int16), False

    class FakeSoundDevice:
        def __init__(self) -> None:
            self.stream = None

        def query_devices(self, index: int) -> dict:
            assert index == 42
            return {"max_input_channels": 2, "default_samplerate": 48000.0}

        def InputStream(self, **kwargs):
            self.stream = FakeStream(**kwargs)
            return self.stream

    fake_sd = FakeSoundDevice()
    with daemon.AudioCapture(fake_sd).open(42, "Windows WASAPI", 48000) as capture:
        mono, overflowed = capture.read(2)

    assert fake_sd.stream.kwargs == {
        "device": 42,
        "samplerate": 48000,
        "channels": 2,
        "dtype": "int16",
    }
    assert capture.hostapi == "Windows WASAPI"
    assert capture.samplerate == 48000
    assert capture.channels == 2
    assert overflowed is False
    np.testing.assert_array_equal(mono, np.array([[2000], [0]], dtype=np.int16))
