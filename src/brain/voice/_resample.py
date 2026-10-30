"""Single-source audio channel mixing and high-quality resampling to 16 kHz."""

from __future__ import annotations

import math

import numpy as np


TARGET_SAMPLE_RATE = 16000
_FILTER_HALF = 32


def mix_to_mono(samples: np.ndarray) -> np.ndarray:
    """Return float32 mono samples; multi-channel input is averaged by frame."""
    audio = np.asarray(samples, dtype=np.float32)
    if audio.ndim == 1:
        return audio
    if audio.ndim == 2:
        return audio.mean(axis=1, dtype=np.float32)
    raise ValueError(f"audio must be 1-D or 2-D, got shape={audio.shape}")


def resample_audio(samples: np.ndarray, sr_in: int, sr_out: int) -> np.ndarray:
    """Resample mono float32 audio with the frozen Blackman-windowed sinc filter.

    The rational rate is derived from ``gcd(sr_in, sr_out)``.  Filter
    half-width and downsampling cutoff match the frozen 2026-10-29
    implementation; upsampling is band-limited to the source Nyquist rate.
    """
    if any(isinstance(rate, bool) or not isinstance(rate, int) or rate <= 0 for rate in (sr_in, sr_out)):
        raise ValueError("sample rates must be positive integers")
    mono = mix_to_mono(samples)
    if mono.size == 0:
        return np.array([], dtype=np.float32)
    if sr_in == sr_out:
        return mono.astype(np.float32, copy=False)

    divisor = math.gcd(sr_in, sr_out)
    down = sr_in // divisor
    up = sr_out // divisor
    n_out = int(round(len(mono) * up / down))
    taps = np.arange(-_FILTER_HALF, _FILTER_HALF + 1, dtype=np.int64)
    cutoff = (min(sr_in, sr_out) / 2.0) / sr_in
    output: list[np.ndarray] = []
    for start in range(0, n_out, 32768):
        stop = min(start + 32768, n_out)
        positions = np.arange(start, stop, dtype=np.float64) * (down / up)
        base = np.floor(positions)[:, None].astype(np.int64) + taps[None, :]
        indices = np.clip(base, 0, len(mono) - 1)
        distance = positions[:, None] - base.astype(np.float64)
        scaled = distance * cutoff
        sinc = np.divide(
            np.sin(np.pi * scaled),
            np.pi * scaled,
            out=np.ones_like(scaled),
            where=np.abs(scaled) >= 1e-9,
        )
        window_position = distance + _FILTER_HALF
        window = (
            0.42
            - 0.5 * np.cos(2 * np.pi * window_position / (2 * _FILTER_HALF))
            + 0.08 * np.cos(4 * np.pi * window_position / (2 * _FILTER_HALF))
        )
        output.append((mono[indices] * sinc * window).sum(axis=1).astype(np.float32))
    return np.concatenate(output)


def resample_to_16k(samples: np.ndarray, sr_in: int) -> np.ndarray:
    """Shared 16 kHz exit: 48k uses 3:1 and 44.1k uses 441:160."""
    return resample_audio(samples, sr_in, TARGET_SAMPLE_RATE)


__all__ = ["TARGET_SAMPLE_RATE", "mix_to_mono", "resample_audio", "resample_to_16k"]
