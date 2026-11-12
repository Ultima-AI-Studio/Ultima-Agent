"""s8-proactive-scenes 验收测试：主动提醒 + 异常巡检 + 与 Ticker 衔接。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.heartbeat.proactive_scenes import ProactiveSceneEngine, ProactiveError
from src.brain.heartbeat.ticker import HeartbeatTicker, MessagePreempt


class TestProactiveScenes(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.engine = ProactiveSceneEngine(self.data_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：注册/取消定时提醒（at/interval），持久化可恢复
    def test_register_cancel_reminder(self) -> None:
        self.engine.register_reminder("r1", "该休息了", at_ts=1000.0)
        self.engine.register_reminder("r2", "每 60 秒巡检", interval=60.0)
        snap = self.engine.snapshot()
        self.assertEqual(len(snap["reminders"]), 2)
        self.assertTrue(self.engine.cancel_reminder("r1"))
        self.assertFalse(self.engine.cancel_reminder("r1"))
        self.assertEqual(len(self.engine.snapshot()["reminders"]), 1)

    def test_register_reminder_invalid(self) -> None:
        with self.assertRaises(ProactiveError):
            self.engine.register_reminder("x", "")
        with self.assertRaises(ProactiveError):
            self.engine.register_reminder("x", "t", at_ts=None, interval=None)
        with self.assertRaises(ProactiveError):
            self.engine.register_reminder("x", "t", interval=-1)

    def test_reminder_persistence_reload(self) -> None:
        self.engine.register_reminder("r1", "持久化提醒", at_ts=1000.0)
        engine2 = ProactiveSceneEngine(self.data_dir)
        self.assertEqual(len(engine2.snapshot()["reminders"]), 1)
        self.assertEqual(engine2.snapshot()["reminders"][0]["text"], "持久化提醒")

    # ACCEPT-2：到期判定产出主动提醒提案
    def test_reminder_due_fires_once(self) -> None:
        self.engine.register_reminder("r1", "到点提醒", at_ts=500.0)
        out = self.engine.collect(now_ts=600.0)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["kind"], "reminder")
        self.assertEqual(out[0]["text"], "到点提醒")
        # 一次性到期只报一次
        self.assertEqual(len(self.engine.collect(now_ts=700.0)), 0)

    def test_interval_reminder_repeats(self) -> None:
        self.engine.register_reminder("r2", "周期提醒", interval=100.0, at_ts=0.0)
        out1 = self.engine.collect(now_ts=150.0)
        self.assertEqual(len(out1), 1)
        out2 = self.engine.collect(now_ts=300.0)
        self.assertEqual(len(out2), 1)  # 第二次周期到期

    # ACCEPT-3：异常巡检（单周期一次，不重复轰炸）
    def test_watch_fires_and_no_bombard(self) -> None:
        state = {"fail": True}
        def check() -> tuple[bool, str]:
            return (not state["fail"], "任务执行失败" if state["fail"] else "")
        self.engine.register_watch("w1", "任务失败监控", "发现任务异常", check)
        out1 = self.engine.collect(now_ts=100.0)
        self.assertEqual(len(out1), 1)
        self.assertEqual(out1[0]["kind"], "watch")
        self.assertIn("任务执行失败", out1[0]["text"])
        # 300s 窗口内不重复
        self.assertEqual(len(self.engine.collect(now_ts=350.0)), 0)
        # 超窗口再报
        self.assertEqual(len(self.engine.collect(now_ts=450.0)), 1)

    def test_watch_recovers_resets(self) -> None:
        state = {"fail": False}
        def check() -> tuple[bool, str]:
            return (not state["fail"], "异常" if state["fail"] else "")
        self.engine.register_watch("w1", "监控", "异常", check)
        self.assertEqual(len(self.engine.collect(now_ts=100.0)), 0)
        state["fail"] = True
        self.assertEqual(len(self.engine.collect(now_ts=200.0)), 1)
        state["fail"] = False
        self.engine.collect(now_ts=300.0)  # 恢复重置
        state["fail"] = True
        # 恢复后立即可再报（窗口已重置）
        self.assertEqual(len(self.engine.collect(now_ts=301.0)), 1)

    def test_watch_rejects_bad_check(self) -> None:
        with self.assertRaises(ProactiveError):
            self.engine.register_watch("w1", "n", "t", check="not-callable")

    # ACCEPT-4：与 HeartbeatTicker 衔接（空闲发声/抢占让位不受影响）
    def test_ticker_integration(self) -> None:
        self.engine.register_reminder("r1", "开会提醒", at_ts=0.0)
        ticker = HeartbeatTicker()
        # 未抢占：空闲 tick 产出主动发声提案
        result = ticker.tick()
        self.assertEqual(result["action"], "主动发声")
        # 有场景提案时：collect 产出
        out = self.engine.collect(now_ts=10.0)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["text"], "开会提醒")
        # 抢占后：tick 让位
        ticker.preempt.notify()
        result2 = ticker.tick()
        self.assertEqual(result2["action"], "让位")


if __name__ == "__main__":
    unittest.main()
