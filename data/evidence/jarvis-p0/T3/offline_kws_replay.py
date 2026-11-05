"""Isolated saved-WAV replay for work order 0023; never opens audio devices."""

from __future__ import annotations

import hashlib
import json
import sys
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.brain.voice._resample import mix_to_mono, resample_to_16k
from src.brain.voice.wake_matching import WakePhraseMatcher

SAMPLES = ROOT / "data" / "voice" / "mic-regress"
KEYWORDS = ROOT / "models" / "sherpa" / "kws" / "keywords.txt"
MODEL = ROOT / "models" / "sherpa" / "kws" / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
OUTPUT = Path(__file__).with_name("offline-kws-replay.json")

POSITIVE = (
    "hp-mic-test.wav",
    "jarvis-three-words.wav",
    "listen-1793004909.wav",
    "listen-1793270775.wav",
    "listen-1793270820.wav",
    "listen-1793271306.wav",
    "listen-1793271706.wav",
    "listen-1793273795.wav",
)
NEGATIVE = (
    "listen-1793007945.wav",
    "listen-1793235389.wav",
    "listen-1793235399.wav",
    "listen-1793235409.wav",
    "listen-1793243229.wav",
    "listen-1793272213.wav",
    "listen-1793274652.wav",
    "listen-1793290022.wav",
)


def _load(path: Path) -> np.ndarray:
    with wave.open(str(path), "rb") as source:
        if source.getsampwidth() != 2:
            raise ValueError(f"{path.name}: expected PCM16")
        rate = source.getframerate()
        channels = source.getnchannels()
        raw = source.readframes(source.getnframes())
    samples = np.frombuffer(raw, dtype=np.int16).reshape(-1, channels).astype(np.float32) / 32768.0
    return resample_to_16k(mix_to_mono(samples), rate)


def _spotter():
    import sherpa_onnx

    return sherpa_onnx.KeywordSpotter(
        tokens=str(MODEL / "tokens.txt"),
        encoder=str(MODEL / "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        decoder=str(MODEL / "decoder-epoch-13-avg-2-chunk-8-left-64.onnx"),
        joiner=str(MODEL / "joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        keywords_file=str(KEYWORDS),
        num_threads=2,
        sample_rate=16000,
        max_active_paths=8,
        keywords_score=2.0,
        keywords_threshold=0.08,
        num_trailing_blanks=8,
        provider="cpu",
    )


def _run(spotter, samples: np.ndarray) -> list[str]:
    stream = spotter.create_stream()
    hits: list[str] = []
    for start in range(0, len(samples), 3200):
        block = samples[start : start + 3200]
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


def main() -> int:
    matcher = WakePhraseMatcher.from_keyword_lines(KEYWORDS.read_text(encoding="utf-8").splitlines())
    spotter = _spotter()
    rows = []
    for sample_class, names in (("positive", POSITIVE), ("negative", NEGATIVE)):
        for name in names:
            path = SAMPLES / name
            hits = _run(spotter, _load(path))
            accepted = [hit for hit in hits if matcher.matches(hit)]
            rows.append(
                {
                    "class": sample_class,
                    "sample": name,
                    "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    "raw_hits": hits,
                    "accepted_hits": accepted,
                }
            )
    positive_hits = sum(bool(row["accepted_hits"]) for row in rows if row["class"] == "positive")
    negative_hits = sum(bool(row["accepted_hits"]) for row in rows if row["class"] == "negative")
    result = {
        "work_order": "wo-ultimaagent-20261103-0023",
        "mode": "saved_wav_offline_no_microphone_no_playback",
        "parameters": {
            "keywords_threshold": 0.08,
            "keywords_score": 2.0,
            "num_trailing_blanks": 8,
            "max_active_paths": 8,
            "fuzzy_ratio": "<0.35",
        },
        "historical_baseline": {"positive_hits": 7, "positive_total": 8, "false_wakes": 0, "negative_total": 8},
        "current": {"positive_hits": positive_hits, "positive_total": 8, "false_wakes": negative_hits, "negative_total": 8},
        "not_worse": positive_hits >= 7 and negative_hits <= 0,
        "rows": rows,
    }
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result["current"], ensure_ascii=False))
    return 0 if result["not_worse"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
