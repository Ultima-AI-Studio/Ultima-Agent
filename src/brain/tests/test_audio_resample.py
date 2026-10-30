from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np

from src.brain.voice._resample import mix_to_mono, resample_audio, resample_to_16k


def _legacy_44100_to_16000(samples: np.ndarray) -> np.ndarray:
    n_out = int(round(len(samples) * 16000 / 44100))
    t = np.arange(n_out, dtype=np.float64) * (44100 / 16000)
    half = 32
    k = np.arange(-half, half + 1, dtype=np.int64)
    base = np.floor(t)[:, None].astype(np.int64) + k[None, :]
    idx = np.clip(base, 0, len(samples) - 1)
    dist = t[:, None] - base.astype(np.float64)
    cutoff = 8000 / 44100
    d = dist * cutoff
    sinc = np.divide(
        np.sin(np.pi * d),
        np.pi * d,
        out=np.ones_like(d),
        where=np.abs(d) >= 1e-9,
    )
    n = dist + half
    window = (
        0.42
        - 0.5 * np.cos(2 * np.pi * n / (2 * half))
        + 0.08 * np.cos(4 * np.pi * n / (2 * half))
    )
    return (samples[idx] * sinc * window).sum(axis=1).astype(np.float32)


def test_resample_44100_matches_frozen_legacy_output() -> None:
    t = np.arange(4410, dtype=np.float32) / 44100
    samples = (0.2 * np.sin(2 * np.pi * 440 * t) + 0.05 * np.sin(2 * np.pi * 1200 * t)).astype(
        np.float32
    )

    actual = resample_to_16k(samples, 44100)

    np.testing.assert_allclose(actual, _legacy_44100_to_16000(samples), rtol=0, atol=0)


def test_resample_48000_to_16000_uses_exact_three_to_one_length() -> None:
    samples = np.linspace(-0.5, 0.5, 48003, dtype=np.float32)

    actual = resample_to_16k(samples, 48000)

    assert actual.dtype == np.float32
    assert len(actual) == 16001


def test_resample_44100_to_48000_has_rational_length() -> None:
    samples = np.linspace(-0.5, 0.5, 44100, dtype=np.float32)

    actual = resample_audio(samples, 44100, 48000)

    assert actual.dtype == np.float32
    assert len(actual) == 48000


def test_mix_to_mono_averages_two_channels() -> None:
    stereo = np.array([[0.2, 0.6], [-0.4, 0.2], [0.0, 0.0]], dtype=np.float32)

    mono = mix_to_mono(stereo)

    np.testing.assert_allclose(mono, np.array([0.4, -0.1, 0.0], dtype=np.float32))


def test_resample_empty_input_is_empty() -> None:
    actual = resample_to_16k(np.array([], dtype=np.float32), 48000)

    assert actual.dtype == np.float32
    assert actual.size == 0


def test_resample_has_no_zero_division_warning() -> None:
    with np.errstate(divide="raise", invalid="raise"):
        actual = resample_to_16k(np.ones(441, dtype=np.float32), 44100)

    assert len(actual) == 160


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
