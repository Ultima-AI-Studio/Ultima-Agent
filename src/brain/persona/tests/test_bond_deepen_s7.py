"""s7-bond-deepen 验收测试：羁绊深化（关系记忆/档位回退/跨形态快照）。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.persona.bond import BondSystem, BondError, SoulProfile, TIERS


class TestBondDeepen(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.bond = BondSystem(self.data_dir, SoulProfile(name="Ultima"))

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：add_note 沉淀偏好/互动史（kind=note，字段齐全）
    def test_add_note_persists_fields(self) -> None:
        self.bond.add_note("用户偏好：凌晨后不再主动播报", scope="preference")
        self.bond.add_note("互动史：今天完成了任务状态联调", scope="interaction")
        notes = self.bond.get_notes(kind="note")
        self.assertEqual(len(notes), 2)
        for n in notes:
            self.assertEqual(n["kind"], "note")
            self.assertIn("ts", n)
            self.assertIn("detail", n)
            self.assertIn("scope", n)
        self.assertEqual(notes[0]["scope"], "preference")
        self.assertEqual(notes[1]["scope"], "interaction")

    # ACCEPT-2：get_notes 可查询（全量 + 按 kind 过滤）
    def test_get_notes_filter(self) -> None:
        self.bond.add_note("偏好A", scope="preference")
        self.bond.add_note("互动B", scope="interaction")
        self.assertEqual(len(self.bond.get_notes()), 2)
        self.assertEqual(len(self.bond.get_notes(kind="note", scope="preference")), 1)
        self.assertEqual(len(self.bond.get_notes(kind="note", scope="interaction")), 1)
        self.assertEqual(len(self.bond.get_notes(kind="tier_open")), 0)

    def test_add_note_rejects_bad_input(self) -> None:
        with self.assertRaises(BondError):
            self.bond.add_note("", scope="preference")
        with self.assertRaises(BondError):
            self.bond.add_note("x", scope="unknown")

    # ACCEPT-3：close_intimate_tier 档位回退生效且留痕
    def test_close_intimate_tier(self) -> None:
        self.bond.open_intimate_tier()
        self.bond.set_address_and_tone("老伙计", "朋友式口吻")
        self.assertEqual(self.bond.state_axis()["tier"], "亲密")
        self.bond.close_intimate_tier()
        axis = self.bond.state_axis()
        self.assertEqual(axis["tier"], "专业距离")
        self.assertEqual(axis["address"], "用户")
        self.assertEqual(axis["tone"], self.bond.soul.tone_default)
        # 留痕：tier_open 历史含回退记录
        opens = [f for f in self.bond.history() if f["kind"] == "tier_open"]
        self.assertGreaterEqual(len(opens), 1)
        self.assertIn("回退", opens[-1]["detail"])

    def test_close_intimate_tier_without_open(self) -> None:
        with self.assertRaises(BondError):
            self.bond.close_intimate_tier()

    # ACCEPT-4：state_axis 含关系记忆快照（跨形态读取一致）
    def test_state_axis_memory_snapshot(self) -> None:
        self.bond.add_note("偏好A", scope="preference")
        self.bond.add_note("互动B", scope="interaction")
        axis = self.bond.state_axis()
        mem = axis["relation_memory"]
        self.assertEqual(mem["notes_count"], 2)
        self.assertEqual(mem["preferences_count"], 1)
        self.assertEqual(mem["interactions_count"], 1)
        self.assertEqual(mem["facts_total"], 2)
        # 持久化后重建：跨形态读取一致
        bond2 = BondSystem(self.data_dir, SoulProfile(name="Ultima"))
        self.assertEqual(bond2.state_axis()["tier"], axis["tier"])
        self.assertEqual(bond2.state_axis()["relation_memory"]["notes_count"], 2)


if __name__ == "__main__":
    unittest.main()
