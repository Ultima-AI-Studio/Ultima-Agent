r"""L4 A2 指令落盘 pusher 单测（HostOrbPusher）。

覆盖：
1. push 幂等覆盖 + seq 递增
2. 空/非法指令抛 ValueError
3. 写域文件 UTF-8 无 BOM + JSON 合法
4. 完整 orb.render 契约（kind/state/emotionId/label/prompt/visual/seq）
5. current() 读回
6. 缺 kind/state 拒绝

运行：tools\python31313\python.exe -X utf8 src\brain\tests\test_host_pusher.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.display.host_pusher import HostOrbPusher


def _render(state: str, **overrides) -> dict:
    cmd = {
        "kind": "orb.render",
        "state": state,
        "emotionId": "calm",
        "label": "待机",
        "ts": "2026-10-25T00:00:00.000+00:00",
        "visual": {
            "color": "#7cc6f4",
            "glass_opacity": 0.38,
            "fluid_strength": 0.25,
            "animation": "breathe-slow",
            "active_band": 0,
        },
    }
    cmd.update(overrides)
    return cmd


class TestHostOrbPusher(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.file = Path(self.tmp.name) / "orb_command.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_push_seq_increments(self):
        pusher = HostOrbPusher(self.file)
        first = pusher.push(_render("idle"))
        second = pusher.push(_render("talking", prompt="你觉得怎么样？"))
        self.assertEqual(first["seq"], 1)
        self.assertEqual(second["seq"], 2)

    def test_push_idempotent_overwrite(self):
        pusher = HostOrbPusher(self.file)
        pusher.push(_render("idle"))
        pusher.push(_render("talking", label="说话"))
        current = pusher.current()
        self.assertEqual(current["state"], "talking")
        self.assertEqual(current["label"], "说话")

    def test_prompt_preserved(self):
        pusher = HostOrbPusher(self.file)
        pusher.push(_render("talking", prompt="稍等，我整理一下。"))
        current = pusher.current()
        self.assertEqual(current["prompt"], "稍等，我整理一下。")

    def test_empty_command_rejected(self):
        pusher = HostOrbPusher(self.file)
        with self.assertRaises(ValueError):
            pusher.push({})
        with self.assertRaises(ValueError):
            pusher.push(None)

    def test_non_orb_kind_rejected(self):
        pusher = HostOrbPusher(self.file)
        with self.assertRaises(ValueError):
            pusher.push({"kind": "other", "state": "idle"})

    def test_missing_state_rejected(self):
        pusher = HostOrbPusher(self.file)
        with self.assertRaises(ValueError):
            pusher.push({"kind": "orb.render"})

    def test_file_utf8_no_bom_and_valid_json(self):
        pusher = HostOrbPusher(self.file)
        pusher.push(_render("thinking", emotionId="thinking", prompt="稍等，我整理一下。"))
        raw = self.file.read_bytes()
        self.assertFalse(raw.startswith(b"\xef\xbb\xbf"), "不应有 UTF-8 BOM")
        decoded = raw.decode("utf-8")
        data = json.loads(decoded)  # 合法 JSON
        self.assertEqual(data["state"], "thinking")
        self.assertEqual(data["emotionId"], "thinking")

    def test_contract_fields(self):
        pusher = HostOrbPusher(self.file)
        pusher.push(_render("processing", emotionId="working", label="处理中",
                            prompt="可以调整。请说明要调整的任务 ID…"))
        data = pusher.current()
        for key in ("seq", "kind", "state", "emotionId", "label", "visual", "ts"):
            self.assertIn(key, data)
        self.assertIn("prompt", data)
        self.assertEqual(data["visual"]["active_band"], 0)

    def test_current_empty_before_push(self):
        pusher = HostOrbPusher(self.file)
        self.assertEqual(pusher.current(), {})

    def test_current_after_corrupt_file(self):
        self.file.write_text("{broken", encoding="utf-8")
        pusher = HostOrbPusher(self.file)
        self.assertEqual(pusher.current(), {})
        # 损坏文件后 push 从 seq=0 重建（seq=1）
        first = pusher.push(_render("idle"))
        self.assertEqual(first["seq"], 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
