from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from src.brain.voice import input_probe


def _device(
    index: int,
    name: str,
    *,
    hostapi: int = 0,
    channels: int = 1,
    samplerate: float = 44100.0,
) -> dict:
    return {
        "index": index,
        "name": name,
        "hostapi": hostapi,
        "max_input_channels": channels,
        "default_samplerate": samplerate,
    }


def test_enumerate_inputs_filters_system_following_endpoints(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = [
        _device(0, "Microsoft 声音映射器 - Input"),
        _device(1, "USBAudio2.0"),
        _device(12, "主声音捕获驱动程序"),
        _device(30, "USBAudio2.0", hostapi=1, channels=2, samplerate=48000.0),
        _device(31, "Output only", channels=0),
    ]
    fake_sd = SimpleNamespace(
        query_devices=lambda: devices,
        query_hostapis=lambda: [{"name": "MME"}, {"name": "Windows WASAPI"}],
    )
    monkeypatch.setattr(input_probe, "_sounddevice", lambda: fake_sd)

    result = input_probe.enumerate_inputs()

    assert [item["index"] for item in result] == [1, 3]
    assert result[1] == {
        "index": 3,
        "name": "USBAudio2.0",
        "hostapi": "Windows WASAPI",
        "hostapi_index": 1,
        "max_input_channels": 2,
        "default_samplerate": 48000.0,
    }


def test_probe_device_marks_silence_not_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_sd = SimpleNamespace(
        query_devices=lambda index: _device(index, "Silent mic"),
        rec=lambda frames, **kwargs: np.zeros((frames, kwargs["channels"]), dtype=np.float32),
    )
    monkeypatch.setattr(input_probe, "_sounddevice", lambda: fake_sd)

    result = input_probe.probe_device(4, seconds=0.2)

    assert result["ok"] is False
    assert result["peak"] == 0.0
    assert result["rms"] == 0.0
    assert result["voiced_sec"] == 0.0


def test_probe_device_marks_real_signal_ok_and_caps_duration(monkeypatch: pytest.MonkeyPatch) -> None:
    call: dict = {}

    def rec(frames: int, **kwargs):
        call.update(frames=frames, **kwargs)
        stereo = np.zeros((frames, kwargs["channels"]), dtype=np.float32)
        stereo[:, 0] = 0.03
        stereo[:, -1] = 0.01
        return stereo

    fake_sd = SimpleNamespace(
        query_devices=lambda index: _device(index, "WASAPI mic", channels=2, samplerate=48000.0),
        rec=rec,
    )
    monkeypatch.setattr(input_probe, "_sounddevice", lambda: fake_sd)

    result = input_probe.probe_device(30, seconds=9.0)

    assert call == {
        "frames": 96000,
        "samplerate": 48000,
        "channels": 2,
        "dtype": "float32",
        "device": 30,
        "blocking": True,
    }
    assert result["ok"] is True
    assert result["peak"] == pytest.approx(0.02)
    assert result["rms"] == pytest.approx(0.02)
    assert result["voiced_sec"] == pytest.approx(2.0)


def test_probe_device_failure_is_fail_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_sd = SimpleNamespace(query_devices=lambda index: (_ for _ in ()).throw(RuntimeError("busy")))
    monkeypatch.setattr(input_probe, "_sounddevice", lambda: fake_sd)

    result = input_probe.probe_device(9)

    assert result["ok"] is False
    assert result["peak"] == 0.0
    assert result["rms"] == 0.0
    assert result["voiced_sec"] == 0.0
    assert "busy" in result["error"]


def test_auto_select_l2_skips_enumeration_and_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        input_probe,
        "enumerate_inputs",
        lambda: (_ for _ in ()).throw(AssertionError("L2 must skip enumerate")),
    )
    monkeypatch.setattr(
        input_probe,
        "probe_device",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("L2 must skip probe")),
    )

    assert input_probe.auto_select({"mode": "auto", "device_index": 37}) == 37
    assert input_probe.get_cached_selection() == {"index": 37, "source": "l2"}


def test_auto_select_prefers_capable_wasapi_48k_without_hardcoded_index(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    devices = [
        {
            "index": 7,
            "name": "Physical mic",
            "hostapi": "MME",
            "hostapi_index": 0,
            "max_input_channels": 1,
            "default_samplerate": 44100.0,
        },
        {
            "index": 42,
            "name": "Physical mic",
            "hostapi": "Windows WASAPI",
            "hostapi_index": 1,
            "max_input_channels": 2,
            "default_samplerate": 48000.0,
        },
    ]
    attempted: list[tuple[int, float]] = []
    monkeypatch.setattr(input_probe, "enumerate_inputs", lambda: devices)

    def probe(index: int, seconds: float = 2.0) -> dict:
        attempted.append((index, seconds))
        return {"ok": True, "peak": 0.03, "rms": 0.01, "voiced_sec": 0.5}

    monkeypatch.setattr(input_probe, "probe_device", probe)

    assert input_probe.auto_select({"device_index": None, "prefer_wasapi48k": True}) == 42
    assert attempted == [(42, 2.0)]
    assert input_probe.get_cached_selection()["hostapi"] == "Windows WASAPI"


def test_auto_select_returns_none_when_every_probe_is_silent(monkeypatch: pytest.MonkeyPatch) -> None:
    devices = [
        {
            "index": 5,
            "name": "Mic A",
            "hostapi": "MME",
            "hostapi_index": 0,
            "max_input_channels": 1,
            "default_samplerate": 44100.0,
        },
        {
            "index": 8,
            "name": "Mic B",
            "hostapi": "Windows WDM-KS",
            "hostapi_index": 2,
            "max_input_channels": 1,
            "default_samplerate": 48000.0,
        },
    ]
    monkeypatch.setattr(input_probe, "enumerate_inputs", lambda: devices)
    monkeypatch.setattr(
        input_probe,
        "probe_device",
        lambda index, seconds=2.0: {"ok": False, "peak": 0.0, "rms": 0.0, "voiced_sec": 0.0},
    )

    assert input_probe.auto_select({"device_index": None}) is None
    assert input_probe.get_cached_selection() is None


def test_resolve_input_uses_fallback_metadata_and_source_log(monkeypatch: pytest.MonkeyPatch) -> None:
    logs: list[str] = []
    monkeypatch.setattr(input_probe, "auto_select", lambda profile, log_fn=None: None)
    monkeypatch.setattr(
        input_probe,
        "describe_input",
        lambda index: {
            "index": index,
            "name": "Fallback mic",
            "hostapi": "MME",
            "hostapi_index": 0,
            "max_input_channels": 1,
            "default_samplerate": 44100.0,
        },
    )

    selected = input_probe.resolve_input({"mode": "auto", "device_index": None}, 1, logs.append)

    assert selected["index"] == 1
    assert selected["source"] == "fallback"
    assert selected["hostapi"] == "MME"
    assert selected["default_samplerate"] == 44100.0
    assert logs[-1] == "探测选中: idx=1 hostapi=MME sr=44100（来源: fallback）"


def test_resolve_input_keeps_l2_source_and_describes_direct_device(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(input_probe, "auto_select", lambda profile, log_fn=None: 9)
    monkeypatch.setattr(input_probe, "get_cached_selection", lambda: {"index": 9, "source": "l2"})
    monkeypatch.setattr(
        input_probe,
        "describe_input",
        lambda index: {
            "index": index,
            "name": "Manual mic",
            "hostapi": "Windows WASAPI",
            "hostapi_index": 2,
            "max_input_channels": 2,
            "default_samplerate": 48000.0,
        },
    )

    selected = input_probe.resolve_input({"device_index": 9}, 1)

    assert selected["index"] == 9
    assert selected["source"] == "l2"
    assert selected["default_samplerate"] == 48000.0
