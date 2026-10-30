"""Play an existing local WAV during the bounded real-device probe.

Evidence-only helper: no synthesis, microphone access, network, or product
configuration changes.  It exists solely to make the auto-probe signal gate
observable on an otherwise silent test machine.
"""

import time
import wave
from pathlib import Path

import numpy as np
import sounddevice as sd


ROOT = Path(r"H:\UltimaAI\UltimaAgent")
WAV = ROOT / "data" / "voice" / "mic-regress" / "wake-prompt.wav"

time.sleep(0.5)
with wave.open(str(WAV), "rb") as wf:
    rate = wf.getframerate()
    channels = wf.getnchannels()
    samples = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16).astype(np.float32)
if channels > 1:
    samples = samples.reshape(-1, channels).mean(axis=1)
samples = np.clip(samples / 32768.0 * 2.0, -1.0, 1.0)
for _ in range(3):
    sd.play(samples, rate)
    sd.wait()
    time.sleep(0.2)
