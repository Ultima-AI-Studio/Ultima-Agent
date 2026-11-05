"""Saved-WAV local-first transcription smoke; opens no audio device."""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.brain.voice.asr import asr_transcribe

WAV = ROOT / "data" / "voice" / "mic-regress" / "listen-1793319736.wav"
OUTPUT = Path(__file__).with_name("local-asr-smoke.json")


def main() -> int:
    result = asr_transcribe(WAV)
    receipt = {
        "work_order": "wo-ultimaagent-20261103-0023",
        "mode": "saved_wav_offline_no_microphone_no_playback",
        "wav": str(WAV.relative_to(ROOT)).replace("\\", "/"),
        "wav_sha256": hashlib.sha256(WAV.read_bytes()).hexdigest(),
        "result": result,
        "pass": bool(result.get("ok") and result.get("text") and result.get("backend") == "sherpa-onnx"),
    }
    OUTPUT.write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"backend": result.get("backend"), "text": result.get("text"), "pass": receipt["pass"]}, ensure_ascii=False))
    return 0 if receipt["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
