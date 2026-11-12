"""s3-behavior-layer 验收测试（M07/M08 · ACCEPT-1~6）。"""

import unittest

from src.brain.display.behavior import (
    BehaviorMapper,
    MemoryVisualizer,
    SceneComposer,
    XRInterfaceReserve,
    THEME_TOKENS,
)


class TestBehaviorLayer(unittest.TestCase):
    def test_three_state_mapping(self):  # ACCEPT-1
        m = BehaviorMapper()
        self.assertEqual(m.map("voice.thinking").state, "thinking")
        self.assertEqual(m.map("voice.listening").state, "listening")
        self.assertEqual(m.map("voice.speaking").state, "speaking")
        self.assertEqual(m.map("task.running").state, "busy")
        # 未知事件兜底 idle
        self.assertEqual(m.map("unknown.event").state, "idle")
        # 状态事件全量映射覆盖（含任务/语音/编排）
        self.assertTrue(any(e.startswith("task.") for e in m.coverage))
        self.assertTrue(any(e.startswith("voice.") for e in m.coverage))
        self.assertTrue(any(e.startswith("queue.") for e in m.coverage))

    def test_memory_visualization(self):  # ACCEPT-2
        mv = MemoryVisualizer()
        mv.add("m1", "declarative", "用户偏好：路径一")
        mv.add("m2", "procedural", "工单验收流程")
        mv.add("m3", "declarative", "冻结基线")
        mv.link("m1", "m3")
        lit = mv.light(["m1", "m2"])
        self.assertEqual(set(lit), {"m1", "m2"})
        snap = mv.snapshot()
        self.assertEqual(snap["lit_count"], 2)
        self.assertEqual(len(snap["links"]), 1)
        # 重复点亮不重复计数
        self.assertEqual(mv.light(["m1"]), [])

    def test_scene_composer(self):  # ACCEPT-3
        sc = SceneComposer()
        comps = sc.assemble("对话", {"chat": {"items": 3}})
        self.assertEqual([c.kind for c in comps], ["header", "chat", "footer"])
        self.assertEqual(comps[1].payload["items"], 3)
        tree = sc.tree()
        self.assertIn("对话", tree["scenes"])
        # 既有场景回归不倒退
        self.assertTrue(sc.regression_ok())
        with self.assertRaises(ValueError):
            sc.assemble("未知场景")

    def test_theme_tokens_aligned(self):  # ACCEPT-4
        # 主题令牌全量存在；三态 glow 色与令牌一致
        self.assertIn("idle_glow", THEME_TOKENS)
        self.assertIn("thinking_glow", THEME_TOKENS)
        self.assertIn("listening_glow", THEME_TOKENS)
        self.assertIn("speaking_glow", THEME_TOKENS)
        m = BehaviorMapper()
        self.assertEqual(m.map("voice.thinking").glow_color, THEME_TOKENS["thinking_glow"])

    def test_xr_reserve(self):  # ACCEPT-5
        xr = XRInterfaceReserve()
        self.assertIn("xr.frame", xr.registered)
        xr.register("xr.haptic", "触觉反馈预留")
        self.assertIn("xr.haptic", xr.snapshot()["interfaces"])
        # 全部为预留态未实现
        self.assertTrue(all(not v["impl"] for v in xr.snapshot()["interfaces"].values()))


if __name__ == "__main__":
    unittest.main(verbosity=2)
