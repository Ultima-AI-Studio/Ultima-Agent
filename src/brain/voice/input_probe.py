"""Local microphone discovery and bounded signal probing.

The probe is deliberately independent of KWS gain/noise-gate settings.  Its
``peak``/``rms`` thresholds only decide whether an endpoint receives real
audio, using the frozen input-channel work-order values.
"""

from __future__ import annotations

import copy
import logging
import time
from collections.abc import Callable
from typing import Any


LOGGER = logging.getLogger(__name__)

PROBE_PEAK_THRESHOLD = 0.01
PROBE_RMS_THRESHOLD = 0.002
MAX_DEVICE_PROBE_SECONDS = 2.0
MAX_TOTAL_PROBE_SECONDS = 15.0

_SYSTEM_FOLLOWING_NAMES = (
    "主声音捕获",
    "声音映射器",
    "primary sound capture",
    "microsoft sound mapper",
)
_LAST_SELECTION: dict[str, Any] | None = None


def _sounddevice():
    import sounddevice as sd

    return sd


def _emit(log_fn: Callable[[str], None] | None, message: str, *, warning: bool = False) -> None:
    (LOGGER.warning if warning else LOGGER.info)(message)
    if log_fn is not None:
        log_fn(message)


def _is_system_following(name: str) -> bool:
    normalized = name.casefold()
    return any(fragment.casefold() in normalized for fragment in _SYSTEM_FOLLOWING_NAMES)


def enumerate_inputs() -> list[dict[str, Any]]:
    """Return physical input endpoints with host API and native rate metadata."""
    sd = _sounddevice()
    hostapis = sd.query_hostapis()
    inputs: list[dict[str, Any]] = []
    for index, raw in enumerate(sd.query_devices()):
        channels = int(raw.get("max_input_channels", 0))
        name = str(raw.get("name") or "")
        if channels <= 0 or not name:
            continue
        if _is_system_following(name):
            LOGGER.info("输入探测跳过 idx=%s name=%s reason=system-following", index, name)
            continue
        hostapi_index = int(raw.get("hostapi", -1))
        try:
            hostapi = str(hostapis[hostapi_index]["name"])
        except (IndexError, KeyError, TypeError):
            hostapi = f"hostapi-{hostapi_index}"
        inputs.append(
            {
                "index": index,
                "name": name,
                "hostapi": hostapi,
                "hostapi_index": hostapi_index,
                "max_input_channels": channels,
                "default_samplerate": float(raw.get("default_samplerate") or 0.0),
            }
        )
    return inputs


def describe_input(index: int) -> dict[str, Any]:
    """Return current metadata for one explicit endpoint.

    Unlike :func:`enumerate_inputs`, this does not apply the automatic-selection
    filter: an L2 override is an explicit operator choice, and the built-in
    fallback must remain usable even when enumeration/probing fails.
    """
    sd = _sounddevice()
    raw = sd.query_devices(int(index))
    hostapi_index = int(raw.get("hostapi", -1))
    try:
        hostapi = str(sd.query_hostapis()[hostapi_index]["name"])
    except (IndexError, KeyError, TypeError):
        hostapi = f"hostapi-{hostapi_index}"
    return {
        "index": int(index),
        "name": str(raw.get("name") or f"device-{index}"),
        "hostapi": hostapi,
        "hostapi_index": hostapi_index,
        "max_input_channels": int(raw.get("max_input_channels", 0)),
        "default_samplerate": float(raw.get("default_samplerate") or 0.0),
    }


def probe_device(index: int, seconds: float = MAX_DEVICE_PROBE_SECONDS) -> dict[str, Any]:
    """Record briefly from *index* and return bounded local signal metrics."""
    result: dict[str, Any] = {"ok": False, "peak": 0.0, "rms": 0.0, "voiced_sec": 0.0}
    try:
        import numpy as np

        sd = _sounddevice()
        raw = sd.query_devices(index)
        samplerate = int(round(float(raw.get("default_samplerate") or 0.0)))
        max_channels = int(raw.get("max_input_channels", 0))
        duration = min(max(float(seconds), 0.0), MAX_DEVICE_PROBE_SECONDS)
        if samplerate <= 0 or max_channels <= 0 or duration <= 0:
            raise ValueError("device has no usable input format")
        channels = min(max_channels, 2)
        frames = max(1, int(round(samplerate * duration)))
        audio = sd.rec(
            frames,
            samplerate=samplerate,
            channels=channels,
            dtype="float32",
            device=index,
            blocking=True,
        )
        samples = np.asarray(audio, dtype=np.float32)
        mono = samples.mean(axis=1) if samples.ndim > 1 else samples.reshape(-1)
        if mono.size == 0:
            raise ValueError("device returned no samples")
        peak = float(np.abs(mono).max())
        rms = float(np.sqrt(np.mean(mono * mono)))
        block_size = max(1, int(round(samplerate * 0.1)))
        voiced_samples = sum(
            len(block)
            for start in range(0, len(mono), block_size)
            if (block := mono[start : start + block_size]).size
            and float(np.abs(block).max()) > PROBE_PEAK_THRESHOLD
        )
        voiced_sec = voiced_samples / samplerate
        result.update(
            ok=peak > PROBE_PEAK_THRESHOLD and rms > PROBE_RMS_THRESHOLD,
            peak=peak,
            rms=rms,
            voiced_sec=voiced_sec,
            samplerate=samplerate,
            channels=channels,
        )
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def _prefer_wasapi_48k(device: dict[str, Any]) -> bool:
    return "wasapi" in str(device.get("hostapi", "")).casefold() and int(
        round(float(device.get("default_samplerate") or 0.0))
    ) == 48000


def auto_select(
    profile_input: dict[str, Any] | None,
    log_fn: Callable[[str], None] | None = None,
) -> int | None:
    """Select the first endpoint that proves it receives audio, bounded to 15s."""
    global _LAST_SELECTION

    profile = profile_input if isinstance(profile_input, dict) else {}
    manual = profile.get("device_index")
    if isinstance(manual, int) and not isinstance(manual, bool) and manual >= 0:
        _LAST_SELECTION = {"index": manual, "source": "l2"}
        _emit(log_fn, f"输入探测跳过: idx={manual} source=l2")
        return manual

    try:
        devices = enumerate_inputs()
    except Exception as exc:
        _LAST_SELECTION = None
        _emit(log_fn, f"输入设备枚举失败: {type(exc).__name__}: {exc}", warning=True)
        return None

    if profile.get("prefer_wasapi48k", True):
        devices = sorted(devices, key=lambda item: 0 if _prefer_wasapi_48k(item) else 1)

    deadline = time.monotonic() + MAX_TOTAL_PROBE_SECONDS
    for device in devices:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            _emit(log_fn, "输入探测停止: total-budget=15s", warning=True)
            break
        duration = min(MAX_DEVICE_PROBE_SECONDS, remaining)
        index = int(device["index"])
        metrics = probe_device(index, seconds=duration)
        if metrics.get("ok"):
            _LAST_SELECTION = {**device, "source": "auto", "probe": metrics}
            _emit(
                log_fn,
                f"输入探测选中: idx={index} hostapi={device['hostapi']} "
                f"sr={int(round(device['default_samplerate']))} peak={metrics['peak']:.4f} "
                f"rms={metrics['rms']:.4f}",
            )
            return index
        reason = metrics.get("error") or (
            f"silent peak={metrics.get('peak', 0.0):.4f} rms={metrics.get('rms', 0.0):.4f}"
        )
        _emit(log_fn, f"输入探测未选中: idx={index} reason={reason}", warning=True)

    _LAST_SELECTION = None
    _emit(log_fn, "输入探测无可用设备: fallback required", warning=True)
    return None


def get_cached_selection() -> dict[str, Any] | None:
    """Return a defensive copy of the current process-local selection."""
    return copy.deepcopy(_LAST_SELECTION)


def resolve_input(
    profile_input: dict[str, Any] | None,
    fallback_index: int,
    log_fn: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    """Resolve auto/L2/fallback selection to one capture descriptor.

    Probe failures are fail-closed to the caller's built-in fallback and never
    prevent the voice loop from starting.  The returned ``source`` is stable
    evidence for startup diagnostics.
    """
    selected_index = auto_select(profile_input, log_fn=log_fn)
    cached = get_cached_selection() or {}
    source = str(cached.get("source") or "auto") if selected_index is not None else "fallback"
    index = int(selected_index if selected_index is not None else fallback_index)
    try:
        selected = describe_input(index)
    except Exception as exc:
        _emit(
            log_fn,
            f"输入设备元数据读取失败: idx={index} {type(exc).__name__}: {exc}",
            warning=True,
        )
        selected = {
            "index": index,
            "name": f"device-{index}",
            "hostapi": "unknown",
            "hostapi_index": -1,
            "max_input_channels": 1,
            "default_samplerate": 44100.0,
        }
    selected["source"] = source
    rate = int(round(float(selected.get("default_samplerate") or 44100.0)))
    _emit(
        log_fn,
        f"探测选中: idx={index} hostapi={selected['hostapi']} sr={rate}（来源: {source}）",
    )
    return selected


__all__ = [
    "MAX_DEVICE_PROBE_SECONDS",
    "MAX_TOTAL_PROBE_SECONDS",
    "PROBE_PEAK_THRESHOLD",
    "PROBE_RMS_THRESHOLD",
    "auto_select",
    "describe_input",
    "enumerate_inputs",
    "get_cached_selection",
    "probe_device",
    "resolve_input",
]
