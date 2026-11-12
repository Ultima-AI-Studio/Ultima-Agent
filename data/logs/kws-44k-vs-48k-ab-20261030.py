# -*- coding: utf-8 -*-
"""Offline KWS A/B: native 44.1k downsampling vs simulated 48k capture path."""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np


ROOT = Path(r"H:\UltimaAI\UltimaAgent")
sys.path.insert(0, str(ROOT))

from src.brain.voice._resample import mix_to_mono, resample_audio, resample_to_16k


SAMPLE_DIR = ROOT / "data" / "voice" / "mic-regress"
OUTPUT_PATH = ROOT / "data" / "logs" / "kws-44k-vs-48k-ab-20261030.txt"
EVIDENCE_OUTPUT_PATH = (
    ROOT / "docs" / "reports" / "evidence" / "input-channel" / "t2-kws-44k-vs-48k-ab.txt"
)
KEYWORDS_PATH = ROOT / "models" / "sherpa" / "kws" / "keywords.txt"
KWS_MODEL = (
    ROOT
    / "models"
    / "sherpa"
    / "kws"
    / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
)
RANDOM_SEED = 20261030
KWS_THRESHOLD = 0.08
KWS_SCORE = 2.0

# Seven files are independently confirmed KWS hits in the existing corpus.
# listen-1793270820 is the weak positive independently labelled by local ASR as
# “小维思，今天天气怎么样”, so it stays a positive even when KWS misses it.
POSITIVE_SAMPLES = (
    "hp-mic-test.wav",
    "jarvis-three-words.wav",
    "listen-1793004909.wav",
    "listen-1793270775.wav",
    "listen-1793270820.wav",
    "listen-1793271306.wav",
    "listen-1793271706.wav",
    "listen-1793273795.wav",
)

# Existing A/B corpus samples, all independently transcribed without a wakeword.
# Two contaminated historical negatives (0105 “乔一斯”, 0820 “小维思”) are
# excluded rather than allowing false ground truth to manufacture a PASS.
NEGATIVE_SAMPLES = (
    "listen-1793007945.wav",
    "listen-1793235389.wav",
    "listen-1793235399.wav",
    "listen-1793235409.wav",
    "listen-1793243229.wav",
    "listen-1793272213.wav",
    "listen-1793274652.wav",
    "listen-1793290022.wav",
)


def load_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wav:
        samplerate = wav.getframerate()
        channels = wav.getnchannels()
        if wav.getsampwidth() != 2:
            raise ValueError(f"{path.name}: expected PCM16 WAV")
        raw = wav.readframes(wav.getnframes())
    pcm = np.frombuffer(raw, dtype=np.int16)
    if pcm.size % channels:
        raise ValueError(f"{path.name}: incomplete interleaved frame")
    frames = pcm.reshape(-1, channels).astype(np.float32) / 32768.0
    return mix_to_mono(frames), samplerate


def build_channel_inputs(samples: np.ndarray, samplerate: int) -> tuple[np.ndarray, np.ndarray]:
    """Return baseline 44.1→16k and simulated 44.1→48→16k inputs."""
    baseline = resample_to_16k(samples, samplerate)
    simulated_48k = resample_audio(samples, samplerate, 48000)
    return baseline, resample_to_16k(simulated_48k, 48000)


def make_spotter():
    import sherpa_onnx

    return sherpa_onnx.KeywordSpotter(
        tokens=str(KWS_MODEL / "tokens.txt"),
        encoder=str(KWS_MODEL / "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        decoder=str(KWS_MODEL / "decoder-epoch-13-avg-2-chunk-8-left-64.onnx"),
        joiner=str(KWS_MODEL / "joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        keywords_file=str(KEYWORDS_PATH),
        num_threads=2,
        sample_rate=16000,
        max_active_paths=8,
        keywords_score=KWS_SCORE,
        keywords_threshold=KWS_THRESHOLD,
        num_trailing_blanks=0,
        provider="cpu",
    )


def run_kws(spotter, samples_16k: np.ndarray) -> list[str]:
    stream = spotter.create_stream()
    hits: list[str] = []
    for start in range(0, len(samples_16k), 3200):
        block = samples_16k[start : start + 3200]
        if len(block) < 3200:
            block = np.pad(block, (0, 3200 - len(block)))
        stream.accept_waveform(16000, block)
        while spotter.is_ready(stream):
            spotter.decode_stream(stream)
            result = spotter.get_result(stream)
            if result:
                hits.append(result)
                spotter.reset_stream(stream)
    return hits


def _validate_inputs() -> None:
    if len(POSITIVE_SAMPLES) < 8 or len(NEGATIVE_SAMPLES) < 8:
        raise RuntimeError("A/B requires at least 8 positive and 8 negative samples")
    if set(POSITIVE_SAMPLES) & set(NEGATIVE_SAMPLES):
        raise RuntimeError("positive and negative sample sets overlap")
    missing = [name for name in (*POSITIVE_SAMPLES, *NEGATIVE_SAMPLES) if not (SAMPLE_DIR / name).is_file()]
    if missing:
        raise FileNotFoundError(f"missing samples: {missing}")
    keyword_lines = KEYWORDS_PATH.read_text(encoding="utf-8").splitlines()
    if sum("@贾维斯" in line for line in keyword_lines) != 6:
        raise RuntimeError("keywords.txt must contain exactly 6 Jarvis variants")


def main() -> int:
    np.random.seed(RANDOM_SEED)
    _validate_inputs()
    spotter = make_spotter()
    rows: list[dict[str, object]] = []
    for sample_class, names in (("positive", POSITIVE_SAMPLES), ("negative", NEGATIVE_SAMPLES)):
        for name in names:
            samples, samplerate = load_wav(SAMPLE_DIR / name)
            if samplerate != 44100:
                raise RuntimeError(f"{name}: expected 44100 Hz source, got {samplerate}")
            baseline, simulated = build_channel_inputs(samples, samplerate)
            hit_44 = run_kws(spotter, baseline)
            hit_48 = run_kws(spotter, simulated)
            rows.append(
                {
                    "class": sample_class,
                    "sample": name,
                    "source_sr": samplerate,
                    "peak": float(np.abs(samples).max()),
                    "44k_to_16k": hit_44,
                    "44k_to_48k_to_16k": hit_48,
                }
            )

    positive = [row for row in rows if row["class"] == "positive"]
    negative = [row for row in rows if row["class"] == "negative"]
    pos_hit_44 = sum(bool(row["44k_to_16k"]) for row in positive)
    pos_hit_48 = sum(bool(row["44k_to_48k_to_16k"]) for row in positive)
    neg_hit_44 = sum(bool(row["44k_to_16k"]) for row in negative)
    neg_hit_48 = sum(bool(row["44k_to_48k_to_16k"]) for row in negative)
    new_false_wakes = [
        str(row["sample"])
        for row in negative
        if row["44k_to_48k_to_16k"] and not row["44k_to_16k"]
    ]
    passed = pos_hit_48 >= pos_hit_44 and neg_hit_48 == 0 and not new_false_wakes

    lines = [
        "KWS 44.1k vs simulated 48k channel A/B — 2026-10-30",
        f"seed={RANDOM_SEED} threshold={KWS_THRESHOLD} score={KWS_SCORE} variants=6 trailing_blanks=0",
        f"positive={len(positive)} negative={len(negative)}",
        "",
        "class | sample | source_sr | peak | 44.1k→16k | 44.1k→48k→16k",
        "--- | --- | ---: | ---: | --- | ---",
    ]
    for row in rows:
        lines.append(
            f"{row['class']} | {row['sample']} | {row['source_sr']} | {row['peak']:.6f} | "
            f"{json.dumps(row['44k_to_16k'], ensure_ascii=False)} | "
            f"{json.dumps(row['44k_to_48k_to_16k'], ensure_ascii=False)}"
        )
    lines.extend(
        [
            "",
            f"POSITIVE 44.1k: {pos_hit_44}/{len(positive)} = {pos_hit_44 / len(positive):.1%}",
            f"POSITIVE 48k: {pos_hit_48}/{len(positive)} = {pos_hit_48 / len(positive):.1%}",
            f"NEGATIVE false wakes 44.1k: {neg_hit_44}/{len(negative)}",
            f"NEGATIVE false wakes 48k: {neg_hit_48}/{len(negative)}",
            f"NEW_FALSE_WAKES_48K: {json.dumps(new_false_wakes, ensure_ascii=False)}",
            "CONCLUSION: "
            + ("PASS — 48k recall >= 44.1k and negative set has zero false wakes" if passed else "FAIL — keep 44.1k default"),
        ]
    )
    report = "\n".join(lines) + "\n"
    OUTPUT_PATH.write_text(report, encoding="utf-8")
    EVIDENCE_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    EVIDENCE_OUTPUT_PATH.write_text(report, encoding="utf-8")
    print(report, end="")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
