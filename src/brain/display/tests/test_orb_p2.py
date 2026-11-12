"""L0/L6 悬浮球状态机（P2 #64，Claw 路线 + emotionId）测试。

覆盖：
1. 初始态合法 / 非法拒绝
2. 合法迁移 + 事件记录（含 payload）
3. 非法迁移拒绝（failed → processing 不允许、未知状态拒绝）
4. 幂等迁移（同状态不产生事件）
5. 语音状态绑定（tts/asr/error → talking/listening/thinking/failed）
6. 渲染指令（emotionId / 视觉参数 / Claw 令牌齐全）
7. emotion_params 与 snapshot
8. on_transition 回调

运行：<venv-py> -X utf8 -W ignore -m unittest discover -s src\\brain\\display\\tests -p "test_*.py"
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.display.orb import OrbStateMachine, VALID_STATES  # noqa: E402


class TestOrbStateMachine(unittest.TestCase):
    # -- 初始态 ---------------------------------------------------------

    def test_initial_idle(self):
        m = OrbStateMachine()
        self.assertEqual(m.state, "idle")

    def test_invalid_initial_rejected(self):
        with self.assertRaises(ValueError):
            OrbStateMachine("nope")

    # -- 合法迁移 --------------------------------------------------------

    def test_transition_and_event(self):
        m = OrbStateMachine()
        self.assertTrue(m.transition("listening"))
        self.assertEqual(m.state, "listening")
        self.assertEqual(len(m.events()), 1)
        ev = m.events()[0]
        self.assertEqual(ev.from_state, "idle")
        self.assertEqual(ev.to_state, "listening")

    def test_transition_with_payload(self):
        m = OrbStateMachine()
        m.transition("thinking", payload={"why": "query"})
        self.assertEqual(m.events()[-1].payload["why"], "query")

    def test_transition_callback(self):
        seen = []
        m = OrbStateMachine(on_transition=lambda ev: seen.append(ev.to_state))
        m.transition("listening")
        m.transition("thinking")
        self.assertEqual(seen, ["listening", "thinking"])

    # -- 非法迁移 --------------------------------------------------------

    def test_failed_cannot_go_processing(self):
        m = OrbStateMachine("failed")
        self.assertFalse(m.transition("processing"))
        self.assertEqual(m.state, "failed")

    def test_unknown_target_rejected(self):
        m = OrbStateMachine()
        self.assertFalse(m.transition("nope"))

    def test_invalid_event_recorded(self):
        m = OrbStateMachine("failed")
        m.transition("processing")
        self.assertEqual(len(m.events()), 1)
        self.assertTrue(m.events()[-1].payload.get("invalid"))

    # -- 幂等 ------------------------------------------------------------

    def test_idempotent_same_state_no_event(self):
        m = OrbStateMachine()
        m.transition("idle")
        self.assertEqual(len(m.events()), 0)

    # -- 语音绑定 --------------------------------------------------------

    def test_voice_tts_mapping(self):
        m = OrbStateMachine()
        m.bind_voice_status({"kind": "tts_started"})
        self.assertEqual(m.state, "talking")
        m.bind_voice_status({"kind": "tts_done"})
        self.assertEqual(m.state, "idle")

    def test_voice_asr_mapping(self):
        m = OrbStateMachine()
        m.bind_voice_status({"kind": "asr_started"})
        self.assertEqual(m.state, "listening")
        m.bind_voice_status({"kind": "asr_done"})
        self.assertEqual(m.state, "thinking")

    def test_voice_error_mapping(self):
        m = OrbStateMachine()
        m.bind_voice_status({"kind": "error"})
        self.assertEqual(m.state, "failed")

    def test_voice_unknown_kind_ignored(self):
        m = OrbStateMachine()
        self.assertFalse(m.bind_voice_status({"kind": "???"}))
        self.assertEqual(m.state, "idle")

    # -- 渲染指令 --------------------------------------------------------

    def test_render_command_contract(self):
        m = OrbStateMachine()
        cmd = m.render_command()
        self.assertEqual(cmd["kind"], "orb.render")
        self.assertEqual(cmd["state"], "idle")
        self.assertEqual(cmd["emotionId"], "calm")
        visual = cmd["visual"]
        for k in ("color", "glass_opacity", "fluid_strength", "animation", "active_band"):
            self.assertIn(k, visual)

    def test_render_command_talking(self):
        m = OrbStateMachine("talking")
        cmd = m.render_command()
        self.assertEqual(cmd["emotionId"], "speaking")
        self.assertEqual(cmd["visual"]["fluid_strength"], 1.0)
        self.assertEqual(cmd["visual"]["animation"], "audio-wave")

    # -- 参数 / 快照 -----------------------------------------------------

    def test_emotion_params_unknown_falls_back_idle(self):
        m = OrbStateMachine()
        p = m.emotion_params("nope")
        self.assertEqual(p["emotionId"], "calm")

    def test_snapshot(self):
        m = OrbStateMachine("thinking")
        snap = m.snapshot()
        self.assertEqual(snap["state"], "thinking")
        self.assertEqual(snap["emotionId"], "thinking")
        self.assertEqual(snap["event_count"], 0)


if __name__ == "__main__":
    unittest.main()
