"""Offline WAV injection through the production 48k -> KWS -> ASR path."""

from __future__ import annotations

import importlib.util
import json
import sys
import wave
from pathlib import Path

import numpy as np


ROOT = Path(r"H:\UltimaAI\UltimaAgent")
sys.path.insert(0, str(ROOT))

from src.brain.voice._resample import mix_to_mono, resample_audio, resample_to_16k
from src.brain.voice.asr import asr_transcribe


SOURCE = ROOT / "data" / "voice" / "mic-regress" / "hp-mic-test.wav"
INJECTED = ROOT / "docs" / "reports" / "evidence" / "input-channel" / "t4-e2e-injected-48k.wav"
STARTUP = ROOT / "docs" / "reports" / "evidence" / "input-channel" / "t3-daemon-startup.txt"
DAEMON_PATH = ROOT / "data" / "logs" / "voice-listen-daemon.py"


def load_pcm16(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        if wav.getsampwidth() != 2:
            raise ValueError("expected PCM16")
        pcm = np.frombuffer(wav.readframes(wav.getnframes()), dtype=np.int16)
    return mix_to_mono(pcm.reshape(-1, channels).astype(np.float32)) / 32768.0, rate


def write_pcm16(path: Path, samples: np.ndarray, rate: int) -> None:
    pcm = np.clip(np.rint(samples * 32768.0), -32768, 32767).astype(np.int16)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())


def load_daemon_module():
    spec = importlib.util.spec_from_file_location("voice_listen_daemon_e2e", DAEMON_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load daemon module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_live_kws(daemon, samples_48k: np.ndarray) -> list[str]:
    spotter = daemon.make_spotter()
    stream = spotter.create_stream()
    hits: list[str] = []
    padded = np.concatenate((samples_48k, np.zeros(48000 * 3, dtype=np.float32)))
    for start in range(0, len(padded), 9600):
        block_48k = padded[start : start + 9600]
        block_16k = resample_to_16k(block_48k, 48000)
        stream.accept_waveform(16000, block_16k)
        while spotter.is_ready(stream):
            spotter.decode_stream(stream)
            result = spotter.get_result(stream)
            if result:
                hits.append(result)
                spotter.reset_stream(stream)
    return hits


def main() -> int:
    startup = STARTUP.read_text(encoding="utf-8")
    selected_48k = "来源: auto" in startup and "sr=48000 input_ch=2 output_ch=1" in startup
    source, source_rate = load_pcm16(SOURCE)
    simulated_capture = resample_audio(source, source_rate, 48000)
    write_pcm16(INJECTED, simulated_capture, 48000)

    daemon = load_daemon_module()
    hits = run_live_kws(daemon, simulated_capture)
    asr = asr_transcribe(INJECTED)
    result = {
        "privacy": "local-only; no network/cloud",
        "startup_selected_48k": selected_48k,
        "startup_evidence": str(STARTUP),
        "source": str(SOURCE),
        "injected_wav": str(INJECTED),
        "capture_rate": 48000,
        "capture_channels": 1,
        "shared_downsample": "resample_to_16k(48000 -> 16000, 3:1)",
        "kws_hits": hits,
        "asr_ok": bool(asr.get("ok")),
        "asr_text": asr.get("text"),
        "asr_engine": asr.get("engine"),
    }
    passed = selected_48k and bool(hits) and bool(asr.get("ok")) and bool(str(asr.get("text") or "").strip())
    result["conclusion"] = "PASS" if passed else "FAIL"
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
