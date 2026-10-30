"""s3-bond-system 验收测试（M18 · ACCEPT-1~5）。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.persona.bond import BondSystem, BondError, SoulProfile


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="bond_s3_"))


class TestBondSystem(unittest.TestCase):
    def test_archives_and_facts(self):  # ACCEPT-1
        d = make_tmp()
        b = BondSystem(d, SoulProfile(name="Ultima"))
        self.assertEqual(b.soul.name, "Ultima")
        self.assertEqual(b.soul.persona, "贾维斯式管家：专业、克制、朋友般可靠")
        self.assertEqual(b.tier, "专业距离")

    def test_default_professional_and_explicit_open(self):  # ACCEPT-2
        d = make_tmp()
        b = BondSystem(d)
        self.assertEqual(b.tier, "专业距离")
        # 亲密档必须用户显式开放
        with self.assertRaises(BondError):
            b.open_intimate_tier(granted_by="system")
        b.open_intimate_tier(granted_by="user")
        self.assertEqual(b.tier, "亲密")
        self.assertTrue(any(f.kind == "tier_open" for f in b.facts))

    def test_address_tone_persist(self):  # ACCEPT-3
        d = make_tmp()
        b = BondSystem(d)
        with self.assertRaises(BondError):
            b.set_address_and_tone("阿凯", "轻松口吻")  # 未开放亲密档
        b.open_intimate_tier(granted_by="user")
        b.set_address_and_tone("阿凯", "轻松口吻")
        self.assertEqual(b.address, "阿凯")
        self.assertEqual(b.tone, "轻松口吻")
        # 持久化：重建实例读回
        b2 = BondSystem(d)
        self.assertEqual(b2.tier, "亲密")
        self.assertEqual(b2.address, "阿凯")
        self.assertEqual(b2.tone, "轻松口吻")
        self.assertEqual(len(b2.facts), 2)  # 关系事实可回溯

    def test_fatigue_boundary_fixed(self):  # ACCEPT-4
        d = make_tmp()
        b = BondSystem(d)
        hb = b.honesty_boundary()
        self.assertFalse(hb["simulate_fatigue"])
        self.assertFalse(hb["simulate_boredom"])
        self.assertIn("诚实边界", hb["reason"])

    def test_shared_state_axis(self):  # ACCEPT-5
        d = make_tmp()
        b = BondSystem(d)
        axis = b.state_axis()
        self.assertIn("tier", axis)
        self.assertIn("address", axis)
        self.assertIn("honesty", axis)
        # 跨形态共享同一状态轴（悬浮球/组合窗口/语音均消费此轴）


if __name__ == "__main__":
    unittest.main(verbosity=2)
