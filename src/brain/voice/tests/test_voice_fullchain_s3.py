"""s3-voice-fullchain 验收测试（M05/M06 · ACCEPT-1~7）。"""

import math
import struct
import tempfile
import unittest
import wave
from pathlib import Path

from src.brain.voice.fullchain import (
    BargeInFlag,
    PipecatEvaluator,
    UnifiedIntentEntry,
    VadSegmenter,
    VoiceStateMachine,
)


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="voice_s3_"))


def make_wav(path: Path, *, rate: int = 16000, voiced_ms: int = 2000,
             silence_ms: int = 1500, tail_ms: int = 500) -> Path:
    """合成 wav：有声段 + 静音段 + 尾音段（验证断句）。"""
    frames = bytearray()
    n_voiced = int(rate * voiced_ms / 1000)
    n_sil = int(rate * silence_ms / 1000)
    n_tail = int(rate * tail_ms / 1000)
    for i in range(n_voiced):
        v = int(6000 * math.sin(2 * math.pi * 440 * i / rate))
        frames += struct.pack("<h", v)
    for _ in range(n_sil):
        frames += struct.pack("<h", 0)
    for i in range(n_tail):
        v = int(6000 * math.sin(2 * math.pi * 440 * i / rate))
        frames += struct.pack("<h", v)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(bytes(frames))
    return path


class TestVoiceFullchain(unittest.TestCase):
    def test_vad_segmentation(self):  # ACCEPT-1
        d = make_tmp()
        wav = make_wav(d / "t.wav")
        segs = VadSegmenter().segment(wav)
        self.assertEqual(len(segs), 2)  # 静音断为两句
        self.assertEqual(segs[0]["index"], 0)
        self.assertEqual(segs[1]["index"], 1)
        self.assertGreater(segs[1]["start_ms"], segs[0]["end_ms"])

    def test_barge_in(self):  # ACCEPT-2
        flag = BargeInFlag()
        self.assertFalse(flag.active)
        flag.raise_barge_in()
        self.assertTrue(flag.active)
        flag.clear()
        self.assertFalse(flag.active)

    def test_state_machine_and_subscribers(self):  # ACCEPT-3
        sm = VoiceStateMachine()
        events = []
        sm.subscribe(lambda e: events.append(e["to"]))
        self.assertEqual(sm.state, "idle")
        self.assertTrue(sm.transition("listening"))
        self.assertTrue(sm.transition("thinking"))
        self.assertTrue(sm.transition("speaking"))
        self.assertEqual(events, ["listening", "thinking", "speaking"])
        # 重复转移不重复触发
        self.assertFalse(sm.transition("speaking"))
        with self.assertRaises(ValueError):
            sm.transition("bogus")
        self.assertEqual(sm.snapshot()["state"], "speaking")

    def test_unified_entry(self):  # ACCEPT-4
        entry = UnifiedIntentEntry()
        r1 = entry.handle("查询任务状态", channel="voice")
        r2 = entry.handle("查询任务状态", channel="text")
        self.assertEqual(r1, r2)  # 语音/文字同入口结果一致
        self.assertEqual(r1["intent"], "task_query")
        self.assertEqual(len(entry.calls), 2)

    def test_pipecat_eval_persisted(self):  # ACCEPT-5
        d = make_tmp()
        ev = PipecatEvaluator(d)
        conclusion = ev.evaluate()
        self.assertIn(conclusion["decision"], ("采用", "降级"))
        self.assertTrue(conclusion["reason"])
        self.assertTrue((d / "pipecat-eval.json").exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
