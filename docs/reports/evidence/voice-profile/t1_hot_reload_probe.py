"""Isolated local KWS hot-reload probe; does not open the microphone."""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import tempfile
import time
import wave
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))


def load_daemon():
    path = ROOT / "data" / "logs" / "voice-listen-daemon.py"
    spec = importlib.util.spec_from_file_location("voice_listen_daemon_probe", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replay(daemon, spotter, wav_path: Path) -> str:
    with wave.open(str(wav_path), "rb") as source:
        rate = source.getframerate()
        channels = source.getnchannels()
        samples = np.frombuffer(source.readframes(source.getnframes()), dtype=np.int16)
    if channels > 1:
        samples = samples.reshape(-1, channels).mean(axis=1).astype(np.int16)
    audio = samples.astype(np.float32) / 32768.0
    if rate == daemon.SR:
        audio = daemon._resample_16k(audio)
    elif rate != daemon.SR_KWS:
        raise RuntimeError(f"unsupported probe sample rate: {rate}")
    audio = np.concatenate([audio, np.zeros(daemon.SR_KWS * 2, dtype=np.float32)])
    stream = spotter.create_stream()
    for start in range(0, len(audio), 3200):
        chunk = audio[start : start + 3200]
        stream.accept_waveform(daemon.SR_KWS, chunk)
        while spotter.is_ready(stream):
            spotter.decode_stream(stream)
            result = spotter.get_result(stream)
            if result:
                return result
    return ""


def main() -> None:
    from src.brain.voice import voice_profile

    daemon = load_daemon()
    custom_text = "查天气"
    custom_wav = ROOT / "data" / "voice" / "mic-regress" / "listen-1793321058.wav"
    baseline_wav = ROOT / "data" / "voice" / "mic-regress" / "jarvis-three-words.wav"

    with tempfile.TemporaryDirectory() as temporary:
        temp = Path(temporary)
        profile_path = temp / "voice-profile.json"
        keywords_path = temp / "keywords.txt"
        profile_path.write_text(
            json.dumps(voice_profile.DEFAULT_PROFILE, ensure_ascii=False), encoding="utf-8"
        )
        keywords_path.write_text(
            "\n".join(voice_profile.DEFAULT_WAKE_WORDS + ["AH1 L T IH0 M AH0 @ULTIMA"]) + "\n",
            encoding="utf-8",
        )

        voice_profile.PROFILE_PATH = profile_path
        voice_profile.KEYWORDS_PATH = keywords_path
        daemon.VOICE_PROFILE = profile_path
        daemon.KWS_KEYWORDS = keywords_path
        manager = daemon.HotReloadSpotter()
        pid_before = os.getpid()
        generation_before = id(manager.spotter)
        before_hit = replay(daemon, manager.spotter, custom_wav)
        baseline_hit_before = replay(daemon, manager.spotter, baseline_wav)

        time.sleep(0.02)
        updated = voice_profile.load_profile({"wakeword": {"custom": custom_text}})
        profile_path.write_text(
            json.dumps(updated, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        replacement = manager.maybe_reload()
        after_hit = replay(daemon, replacement, custom_wav)
        baseline_hit_after = replay(daemon, replacement, baseline_wav)

        result = {
            "ok": (
                after_hit == custom_text
                and baseline_hit_before == "贾维斯"
                and baseline_hit_after == "贾维斯"
                and id(replacement) != generation_before
            ),
            "privacy": "existing local saved-WAV injection; microphone not opened; no external request",
            "pid_before": pid_before,
            "pid_after": os.getpid(),
            "spotter_rebuilt": id(replacement) != generation_before,
            "before_custom_hit": before_hit,
            "after_custom_hit": after_hit,
            "baseline_hit_before": baseline_hit_before,
            "baseline_hit_after": baseline_hit_after,
            "keywords_contains_custom": f"@{custom_text}" in keywords_path.read_text(encoding="utf-8"),
            "wav": str(custom_wav),
            "wav_transcript_evidence": "data/logs/voice-listen.log:175 ASR=查天气。",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if not result["ok"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
