"""WebRTC APM front-end DSP for the live voice entry.

Adds noise suppression, automatic gain control and optional echo cancellation
to the 16 kHz capture path. Echo cancellation is a two-input algorithm: the
caller must keep a far-end reference of the audio currently being played
through the speaker, otherwise WebRTC refuses to process the near frame.

All maths stays in upstream WebRTC; this module only does 10 ms framing,
sample conversion and far-end time alignment.
"""
from __future__ import annotations

import numpy as np

import pywebrtc_audio

FULL_SCALE = 32767.0


class PlaybackReference:
    """What the speaker is audible-playing at a given monotonic time."""

    def __init__(self, frame_samples, rate=16000):
        self.frame_samples = int(frame_samples)
        self.rate = int(rate)
        self._pcm = np.zeros(0, dtype=np.int16)
        self._started_at = None
        # Extra delay between "playback requested" and "sound is in the room"
        # (sounddevice buffer + speaker latency). Tuned on real hardware.
        self.lead_seconds = 0.0

    def start(self, pcm16, started_at):
        self._pcm = np.ascontiguousarray(pcm16, dtype=np.int16)
        self._started_at = float(started_at)

    def stop(self):
        self._pcm = np.zeros(0, dtype=np.int16)
        self._started_at = None

    @property
    def active(self):
        return self._started_at is not None

    def frame_at(self, moment):
        """Return the far-end frame audible at monotonic `moment`, or silence."""
        silence = np.zeros(self.frame_samples, dtype=np.int16)
        if self._started_at is None:
            return silence
        offset = (float(moment) - self._started_at - self.lead_seconds) * self.rate
        start = int(offset)
        if start < 0 or start >= self._pcm.size:
            return silence
        chunk = self._pcm[start:start + self.frame_samples]
        if chunk.size == self.frame_samples:
            return chunk
        padded = silence.copy()
        padded[:chunk.size] = chunk
        return padded


class ApmChain:
    """10 ms framed APM over 16 kHz audio, with a far-end reference for AEC."""

    def __init__(self, rate=16000, noise_suppression=True, auto_gain_control=True,
                 echo_cancellation=False, stream_delay_ms=0):
        self.rate = int(rate)
        if self.rate <= 0 or self.rate % 100:
            raise ValueError('rate must be a positive multiple of 100')
        self.frame = self.rate // 100
        self.echo_cancellation = bool(echo_cancellation)
        self.auto_gain = bool(auto_gain_control)
        self.noise_suppression = bool(noise_suppression)
        self.processor = pywebrtc_audio.AudioProcessor(
            sample_rate=self.rate,
            noise_suppression=bool(noise_suppression),
            auto_gain_control=bool(auto_gain_control),
            echo_cancellation=self.echo_cancellation,
            stream_delay_ms=int(stream_delay_ms),
        )
        self.reference = PlaybackReference(self.frame, self.rate)
        self._pending = np.zeros(0, dtype=np.int16)
        self.gain_db = 0.0
        self.speech_probability = 0.0
        self.frames_processed = 0

    def reset(self):
        self.processor.reset()
        self.reference.stop()
        self._pending = np.zeros(0, dtype=np.int16)
        self.gain_db = 0.0
        self.speech_probability = 0.0
        self.frames_processed = 0

    def process(self, samples, started_at):
        """Feed 16 kHz float32 audio captured at `started_at`.

        Returns the processed full frames only. A short remainder is carried to
        the next call, so no audio is dropped and latency stays below one frame.
        """
        pcm16 = np.clip(np.asarray(samples, dtype=np.float32) * FULL_SCALE,
                        -FULL_SCALE - 1, FULL_SCALE).astype(np.int16)
        if pcm16.size:
            self._pending = np.concatenate([self._pending, pcm16])
        count = self._pending.size // self.frame
        if not count:
            return np.zeros(0, dtype=np.float32)
        out = np.empty(count * self.frame, dtype=np.int16)
        for index in range(count):
            start = index * self.frame
            chunk = self._pending[start:start + self.frame]
            far = self.reference.frame_at(started_at + start / self.rate) if self.echo_cancellation else None
            out[start:start + self.frame] = np.asarray(self.processor.process(chunk, far), dtype=np.int16)
            self.frames_processed += 1
        self._pending = self._pending[count * self.frame:]
        self._read_levels()
        return out.astype(np.float32) / FULL_SCALE

    def _read_levels(self):
        # Upstream raises RuntimeError (not just AttributeError) when the
        # matching sub-module is disabled, e.g. gain_db without AGC.
        try:
            value = self.processor.gain_db
            self.gain_db = float(value) if value is not None else 0.0
        except (AttributeError, TypeError, ValueError, RuntimeError):
            self.gain_db = 0.0
        try:
            self.speech_probability = float(self.processor.speech_probability)
        except (AttributeError, TypeError, ValueError, RuntimeError):
            self.speech_probability = 0.0
