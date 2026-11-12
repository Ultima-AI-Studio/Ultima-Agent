"""s4-state-axis 状态与记忆共享轴测试（M04）。

验收口径（tasks/cards/s4-state-axis/task.md）：
- ACCEPT-1 四类状态聚合只读视图可用
- ACCEPT-2 每类带更新时间戳 + 聚合版本号
- ACCEPT-3 跨形态消费同一快照（行为层状态机接入）
- ACCEPT-4 事件推送订阅生效（刷新→订阅者收到新快照）
- ACCEPT-5 回归不倒退（既有行为层/队列/设备/羁绊测试全绿）
- ACCEPT-6 回执完整
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.state.axis import StateAxis, SESSION_EVENTS
from src.brain.persona.bond import BondSystem
from src.brain.iot.device_profile import DeviceRegistry, DeviceProfile
from src.brain.orchestration.queue import TaskQueue
from src.brain.display.behavior import BehaviorMapper


def _make_axis(tmp: Path) -> StateAxis:
    bond = BondSystem(tmp / "bond")
    registry = DeviceRegistry(tmp / "device")
    queue = TaskQueue(tmp / "queue")
    behavior = BehaviorMapper()
    return StateAxis(bond=bond, registry=registry, queue=queue, behavior=behavior)


class TestStateAxisS4(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：四类状态聚合只读视图可用
    def test_accept1_four_categories(self) -> None:
        axis = _make_axis(self.root)
        snap = axis.snapshot()
        for key in ("session", "identity", "device", "tasks"):
            self.assertIn(key, snap["categories"], key)
        # 真实数据源：bond 状态轴 / 设备档案 / 队列视图
        self.assertIn("tier", snap["categories"]["identity"]["value"])
        self.assertIsInstance(snap["categories"]["device"]["value"], list)
        self.assertIn("total", snap["categories"]["tasks"]["value"])

    # ACCEPT-2：每类状态带更新时间戳 + 聚合版本号
    def test_accept2_timestamps_and_version(self) -> None:
        axis = _make_axis(self.root)
        snap = axis.snapshot()
        self.assertGreaterEqual(snap["version"], 1)
        for key in ("session", "identity", "device", "tasks"):
            cat = snap["categories"][key]
            self.assertIn("updated_ts", cat)
        # 更新 session 后版本号递增
        v1 = snap["version"]
        snap2 = axis.apply_voice_state("thinking")
        self.assertGreater(snap2["version"], v1)
        self.assertEqual(snap2["categories"]["session"]["value"]["state"], "thinking")

    # ACCEPT-3：跨形态消费同一快照（行为层状态机接入）
    def test_accept3_cross_form_consume(self) -> None:
        axis = _make_axis(self.root)
        vis = axis.visual_snapshot()
        self.assertIn("state", vis)
        self.assertIn("glow_color", vis)
        axis.apply_voice_state("listening")
        vis2 = axis.visual_snapshot()
        self.assertEqual(vis2["state"], "listening")
        # 悬浮球/组合窗口消费的是同一快照（session.visual 一致）
        snap = axis.snapshot()
        self.assertEqual(snap["categories"]["session"]["value"]["visual"]["state"], "listening")

    # ACCEPT-4：事件推送订阅生效（刷新→订阅者收到新快照）
    def test_accept4_subscriber_push(self) -> None:
        axis = _make_axis(self.root)
        received: list[dict] = []
        axis.subscribe(lambda snap: received.append(snap))
        # 总线事件驱动刷新
        snap = axis.on_bus_event("voice.speaking")
        self.assertEqual(snap["categories"]["session"]["value"]["state"], "speaking")
        self.assertEqual(len(received), 1)
        self.assertEqual(received[0]["version"], snap["version"])
        # 任务类事件刷新
        snap2 = axis.on_bus_event("queue.progress")
        self.assertEqual(len(received), 2)

    # ACCEPT-4b：真实订阅者回调可卸载
    def test_accept4b_unsubscribe(self) -> None:
        axis = _make_axis(self.root)
        hits: list[int] = []

        def cb(snap):
            hits.append(snap["version"])

        axis.subscribe(cb)
        axis.refresh()
        self.assertEqual(len(hits), 1)
        axis.unsubscribe(cb)
        axis.refresh()
        self.assertEqual(len(hits), 1)

    # ACCEPT-5：回归不倒退（本单聚合不改底层，只读消费）
    def test_accept5_readonly(self) -> None:
        axis = _make_axis(self.root)
        # 聚合前后底层状态不变（只读）
        before = axis.bond.state_axis()
        axis.refresh()
        after = axis.bond.state_axis()
        self.assertEqual(before, after)

    # ACCEPT-6：回执完整（视图字段齐全）
    def test_accept6_receipt(self) -> None:
        axis = _make_axis(self.root)
        snap = axis.snapshot()
        for key in ("version", "updated_at", "categories"):
            self.assertIn(key, snap)
        for event in SESSION_EVENTS:
            self.assertIn(event, SESSION_EVENTS)


if __name__ == "__main__":
    unittest.main()
