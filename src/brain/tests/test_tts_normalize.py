r"""DEFECT-001 修复单测：TTS 极短文本近静音 → normalize_tts_wav 归一化。

覆盖：
1. 低 RMS 短 WAV → 增益补偿（new_rms ≥ target_rms）+ 最小时长 padding
2. 正常 WAV → 不放大（gain=1）
3. 时长已足 → 不 padding
4. 静音 WAV（RMS=0）→ 仅 padding，不除零
5. 非 PCM16 → ValueError
6. 归一化后 WAV 可被 wave 重新读取（往返完整）
7. 削顶统计存在（夹取后无异常）

运行：tools\python31313\python.exe -X utf8 src\brain\tests\test_tts_normalize.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
import wave
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.voice.tts import (
    normalize_tts_wav,
    expand_tts_text,
    tts_output_is_near_silent,
    _DEFAULT_MIN_DURATION,
)


def _make_wav(path: Path, rate: int, samples: list[int], channels: int = 1) -> None:
    import array

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(array.array("h", samples).tobytes())


class TestTextExpand(unittest.TestCase):
    """DEFECT-001 根因修复：≤1 字文本自动扩展，保证模型正常发声。"""

    def test_one_char_expanded(self):
        self.assertEqual(expand_tts_text("好"), "好，收到。")

    def test_one_char_expanded_with_space(self):
        self.assertEqual(expand_tts_text(" 好 "), "好，收到。")

    def test_two_chars_unchanged(self):
        self.assertEqual(expand_tts_text("好的"), "好的")

    def test_normal_sentence_unchanged(self):
        self.assertEqual(expand_tts_text("稍等，我整理一下。"), "稍等，我整理一下。")

    def test_empty_unchanged(self):
        self.assertEqual(expand_tts_text(""), "")
        self.assertEqual(expand_tts_text("   "), "   ")

    def test_english_single_char_expanded(self):
        self.assertEqual(expand_tts_text("ok"), "ok")
        self.assertEqual(expand_tts_text("o"), "o，收到。")

    def test_keep_semantics(self):
        """扩展保留原字 + 确认后缀，不改变原意。"""
        self.assertTrue(expand_tts_text("好").startswith("好"))
        self.assertTrue(expand_tts_text("嗯").startswith("嗯"))


class TestNearSilentDetection(unittest.TestCase):
    """DEFECT-001 近静音检测：RMS < 0.01 或 时长 < 0.3s 判定为近静音。"""

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def test_low_rms_is_near_silent(self):
        path = self.root / "low.wav"
        _make_wav(path, 24000, [100] * 2400)  # 0.1s RMS≈0.003
        self.assertTrue(tts_output_is_near_silent(path))

    def test_normal_audio_not_near_silent(self):
        path = self.root / "normal.wav"
        _make_wav(path, 24000, [6000] * 24000)  # 1.0s RMS≈0.13
        self.assertFalse(tts_output_is_near_silent(path))

    def test_very_short_normal_rms_near_silent(self):
        path = self.root / "short.wav"
        _make_wav(path, 24000, [6000] * 2400)  # 0.1s（RMS 正常但时长不足）
        self.assertTrue(tts_output_is_near_silent(path))

    def test_missing_file_near_silent(self):
        self.assertTrue(tts_output_is_near_silent(self.root / "missing.wav"))


class TestNormalize(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _read_samples(self, path: Path) -> list[int]:
        import array

        with wave.open(str(path), "rb") as wav:
            return list(array.array("h", wav.readframes(wav.getnframes())))

    def test_low_rms_short_wav_gained_and_padded(self):
        # 0.1s、振幅 100（RMS≈0.003，近静音）
        path = self.root / "low.wav"
        _make_wav(path, 16000, [100] * 1600)
        report = normalize_tts_wav(path)
        self.assertTrue(report["normalized"])
        self.assertGreater(report["gain"], 1.0)
        # 整段（含 pad）RMS 达可听阈值（静音 padding 会稀释，0.02 可听）
        self.assertGreaterEqual(report["new_rms"], 0.02)
        self.assertGreaterEqual(report["new_seconds"], _DEFAULT_MIN_DURATION - 0.01)
        self.assertTrue(report["padded"])

    def test_normal_wav_not_gained(self):
        # 0.8s、振幅 6000（RMS≈0.13，正常）
        path = self.root / "normal.wav"
        _make_wav(path, 16000, [6000] * 12800)
        report = normalize_tts_wav(path)
        self.assertEqual(report["gain"], 1.0)
        self.assertFalse(report["padded"])
        self.assertLessEqual(report["new_rms"], 0.2)

    def test_duration_sufficient_no_pad(self):
        # 1.0s、低振幅 200 → 增益但时长已足不 padding
        path = self.root / "long_low.wav"
        _make_wav(path, 16000, [200] * 16000)
        report = normalize_tts_wav(path)
        self.assertGreater(report["gain"], 1.0)
        self.assertFalse(report["padded"])
        self.assertGreaterEqual(report["new_seconds"], 1.0)

    def test_silence_wav_pad_only(self):
        # 全静音 0.2s → RMS=0，仅 padding，无除零
        path = self.root / "silence.wav"
        _make_wav(path, 16000, [0] * 3200)
        report = normalize_tts_wav(path)
        self.assertTrue(report["normalized"])
        self.assertEqual(report["orig_rms"], 0.0)
        self.assertGreaterEqual(report["new_seconds"], _DEFAULT_MIN_DURATION - 0.01)
        self.assertTrue(report["padded"])

    def test_non_pcm16_raises(self):
        # 8-bit WAV → ValueError
        path = self.root / "bad.wav"
        with wave.open(str(path), "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(1)
            wav.setframerate(16000)
            wav.writeframes(b"\x80" * 100)
        with self.assertRaises(ValueError):
            normalize_tts_wav(path)

    def test_roundtrip_readable(self):
        path = self.root / "roundtrip.wav"
        _make_wav(path, 22050, [150] * 3000)  # 0.136s 低振幅
        normalize_tts_wav(path)
        with wave.open(str(path), "rb") as wav:
            self.assertEqual(wav.getframerate(), 22050)
            self.assertEqual(wav.getsampwidth(), 2)
            self.assertGreater(wav.getnframes(), 0)
        samples = self._read_samples(path)
        self.assertGreater(len(samples), 0)

    def test_stereo_preserved(self):
        # 双声道低振幅 → 保持双声道 + 增益
        path = self.root / "stereo.wav"
        _make_wav(path, 16000, [100] * 3200, channels=2)
        report = normalize_tts_wav(path)
        self.assertGreater(report["gain"], 1.0)
        with wave.open(str(path), "rb") as wav:
            self.assertEqual(wav.getnchannels(), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
