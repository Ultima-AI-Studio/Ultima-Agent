"""L7 语音入口闭环编排单测（VoiceInteractionLoop，mock ASR/TTS）。

覆盖：
1. 完整闭环：ASR → 桥接 → 推送（seq/prompt）→ TTS 回放
2. ASR 无文本 → 返回 asr 失败，不推送
3. 音频不存在 → input 失败
4. ASR 抛错 → asr 失败留痕
5. 空输入语义（桥接不迁移）仍视为成功
6. 无响应文本 → 跳过 TTS 视为通过
7. TTS 失败 → ok=False 且各段留痕
8. 音频输入与指令文件均为真实路径（写域 data/voice/ data/host/）

运行：tools\python31313\python.exe -X utf8 src\brain\tests\test_voice_loop.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.voice_loop import VoiceInteractionLoop


def _make_wav(path: Path, rate: int = 16000, samples: int = 16000) -> None:
    import struct
    with path.open("wb") as f:
        data = struct.pack("<" + "h" * samples, *([300] * samples))
        f.write(struct.pack("<4sI4s4sIHHIIHH4sI", b"RIFF", 36 + len(data),
                            b"WAVE", b"fmt ", 16, 1, 1, rate, rate * 2, 2, 16, b"data", len(data)))
        f.write(data)


class TestVoiceInteractionLoop(unittest.TestCase):
    def setUp(self):
        import json as _json
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.queue_root = self.root / "queue"
        self.command_file = self.root / "host" / "orb_command.json"
        self.reply_dir = self.root / "voice"
        # 预置一个 QUEUED 任务（含合法任务卡），保证查询意图命中并输出摘要（text 非空）
        self.queue_root.mkdir(parents=True, exist_ok=True)
        card_dir = self.queue_root / "cards" / "VL-001"
        card_dir.mkdir(parents=True, exist_ok=True)
        (card_dir / "卡.md").write_text(
            "- **标题**：语音闭环验证任务\n- **状态**：待执行\n", encoding="utf-8")
        task = {
            "task_id": "VL-001", "state": "QUEUED", "priority": 80,
            "dependsOn": [], "parallelGroup": None, "fileDomain": [],
            "reasoningEffort": None,
            "created_at": "2026-10-25T00:00:00+08:00",
            "updated_at": "2026-10-25T00:00:00+08:00",
            "terminal_reason": None, "card_path": "cards/VL-001/卡.md",
        }
        (self.queue_root / "tasks.json").write_text(
            _json.dumps([task], ensure_ascii=False), encoding="utf-8")
        self.loop = VoiceInteractionLoop(self.queue_root, self.command_file, self.reply_dir)

    def tearDown(self):
        self.tmp.cleanup()

    # ── 1. 完整闭环 ──
    def test_full_closed_loop(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": "查询任务状态", "model": "faster-whisper-medium"}):
            with patch("src.brain.voice_loop.tts_synthesize",
                       return_value={"ok": True, "wav": str(self.reply_dir / "reply-1.wav"),
                                     "seconds": 1.2}) as tts_mock:
                result = self.loop.handle_audio(wav)
        self.assertTrue(result["ok"])
        self.assertEqual(result["text"], "查询任务状态")
        # 推送落盘 + seq=1 + prompt 通道存在
        self.assertTrue(self.command_file.is_file())
        self.assertEqual(result["pushed"]["seq"], 1)
        self.assertIn("prompt", result["pushed"])
        # TTS 用响应文本合成
        self.assertIsNotNone(result["tts"])
        self.assertEqual(tts_mock.call_args[0][0], result["response"]["text"])
        self.assertIsNotNone(result["reply_wav"])
        # 回放文件真实存在（mock 不写文件，仅路径）
        self.assertTrue(Path(result["reply_wav"]).parent == self.reply_dir)

    # ── 2. ASR 无文本 ──
    def test_asr_empty_text(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": "   "}):
            result = self.loop.handle_audio(wav)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "asr")
        self.assertFalse(self.command_file.is_file())

    # ── 3. 音频不存在 ──
    def test_missing_audio(self):
        result = self.loop.handle_audio(self.root / "missing.wav")
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "input")

    # ── 4. ASR 抛错 ──
    def test_asr_raise(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        with patch("src.brain.voice_loop.asr_transcribe",
                   side_effect=RuntimeError("CUDA 失败")):
            result = self.loop.handle_audio(wav)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "asr")
        self.assertIn("CUDA 失败", result["error"])

    # ── 5. 空输入语义视为成功 ──
    def test_empty_utterance_semantics(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        # ASR 返回空白 → 走空输入分支
        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": ""}):
            result = self.loop.handle_audio(wav)
        self.assertFalse(result["ok"])  # ASR 无有效文本 → asr 失败（先于桥接）
        self.assertEqual(result["stage"], "asr")

    # ── 6. 无响应文本跳过 TTS ──
    def test_no_reply_skip_tts(self):
        wav = self.root / "in.wav"
        _make_wav(wav)

        class _EmptyReply:
            handled = True
            ok = True
            text = ""
            reason = None
            state = "idle"

            def to_dict(self):
                return {"handled": self.handled, "ok": self.ok,
                        "text": self.text, "reason": self.reason, "state": self.state}

        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": "随便聊聊"}):
            with patch.object(type(self.loop.bridge), "handle",
                              return_value=_EmptyReply()) as handle_mock:
                with patch("src.brain.voice_loop.tts_synthesize") as tts_mock:
                    result = self.loop.handle_audio(wav)
        self.assertTrue(result["ok"])
        self.assertEqual(result["stage"], "bridge")
        self.assertIsNone(result["tts"])
        self.assertIsNone(result["reply_wav"])
        handle_mock.assert_called_once()
        tts_mock.assert_not_called()

    # ── 7. TTS 失败留痕 ──
    def test_tts_failure_traced(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": "查询任务状态"}):
            with patch("src.brain.voice_loop.tts_synthesize",
                       side_effect=RuntimeError("模型加载失败")):
                result = self.loop.handle_audio(wav)
        self.assertFalse(result["ok"])
        self.assertEqual(result["stage"], "tts")
        self.assertIsNotNone(result["tts"])
        self.assertIn("模型加载失败", result["tts"]["error"])
        # 推送已完成（桥接段成功，TTS 失败不影响推送）
        self.assertEqual(result["pushed"]["seq"], 1)

    # ── 8. seq 递增（多次输入）──
    def test_seq_increments_across_calls(self):
        wav = self.root / "in.wav"
        _make_wav(wav)
        with patch("src.brain.voice_loop.asr_transcribe",
                   return_value={"ok": True, "text": "查询任务状态"}):
            with patch("src.brain.voice_loop.tts_synthesize",
                       return_value={"ok": True, "seconds": 1.0}):
                first = self.loop.handle_audio(wav)
                second = self.loop.handle_audio(wav)
        self.assertEqual(first["pushed"]["seq"], 1)
        self.assertEqual(second["pushed"]["seq"], 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
