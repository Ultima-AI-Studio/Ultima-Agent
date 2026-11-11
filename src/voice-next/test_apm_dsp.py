import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).parent))
import apm_dsp


def tone(samples, rate=16000, freq=440):
    t = np.arange(samples) / rate
    return (0.3 * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def test_reference_is_silent_before_start_and_after_end():
    ref = apm_dsp.PlaybackReference(160)
    assert not ref.active
    assert np.abs(ref.frame_at(0.0)).sum() == 0
    pcm = np.ones(1600, dtype=np.int16)
    ref.start(pcm, 100.0)
    assert ref.active
    assert np.abs(ref.frame_at(99.0)).sum() == 0          # before playback
    assert np.all(ref.frame_at(100.0) == 1)               # first frame
    assert np.all(ref.frame_at(100.05) == 1)              # middle
    assert np.abs(ref.frame_at(100.2)).sum() == 0         # past the end
    ref.stop()
    assert not ref.active
    assert np.abs(ref.frame_at(100.05)).sum() == 0


def test_reference_pads_the_tail_frame():
    ref = apm_dsp.PlaybackReference(160)
    ref.start(np.ones(170, dtype=np.int16), 0.0)
    tail = ref.frame_at(0.01)                             # second frame, 10 samples left
    assert tail.shape == (160,)
    assert np.all(tail[:10] == 1) and np.all(tail[10:] == 0)


def test_reference_lead_shifts_the_time_axis():
    ref = apm_dsp.PlaybackReference(160)
    ref.start(np.ones(1600, dtype=np.int16), 0.0)
    ref.lead_seconds = 0.02
    assert np.abs(ref.frame_at(0.01)).sum() == 0          # still inside the lead
    assert np.all(ref.frame_at(0.02) == 1)                # now audible


def test_chain_carries_the_remainder_without_dropping_audio():
    chain = apm_dsp.ApmChain(rate=16000, noise_suppression=False, auto_gain_control=False, echo_cancellation=False)
    out = chain.process(tone(100), 0.0)
    assert out.size == 0
    assert chain._pending.size == 100
    out = chain.process(tone(200), 100 / 16000)
    assert out.size == 160
    assert chain._pending.size == 140


def test_chain_processes_a_full_frame():
    chain = apm_dsp.ApmChain(rate=16000, noise_suppression=True, auto_gain_control=True, echo_cancellation=False)
    out = chain.process(tone(160), 0.0)
    assert out.shape == (160,)
    assert np.all(np.isfinite(out))
    assert chain.frames_processed == 1


def test_chain_accepts_aec_with_padded_reference():
    chain = apm_dsp.ApmChain(rate=16000, echo_cancellation=True)
    near = tone(160)
    reference = (tone(160) * 10000).astype(np.int16)
    chain.reference.start(reference, 0.0)
    out = chain.process(near, 0.0)
    assert out.shape == (160,)
    assert np.all(np.isfinite(out))


def test_chain_aec_without_reference_plays_silence_instead_of_raising():
    chain = apm_dsp.ApmChain(rate=16000, echo_cancellation=True)
    out = chain.process(tone(160), 0.0)
    assert out.shape == (160,)
    assert np.all(np.isfinite(out))


def test_chain_reset_clears_pending_and_reference():
    chain = apm_dsp.ApmChain(rate=16000, echo_cancellation=True)
    chain.process(tone(100), 0.0)
    chain.reference.start(np.ones(160, dtype=np.int16), 0.0)
    chain.reset()
    assert chain._pending.size == 0
    assert not chain.reference.active
    assert chain.frames_processed == 0


def test_chain_reads_gain_and_speech_probability():
    chain = apm_dsp.ApmChain(rate=16000)
    chain.process(tone(1600), 0.0)
    assert isinstance(chain.gain_db, float)
    assert 0.0 <= chain.speech_probability <= 1.0


def test_chain_rejects_a_bad_rate():
    with pytest.raises(ValueError):
        apm_dsp.ApmChain(rate=16001)
