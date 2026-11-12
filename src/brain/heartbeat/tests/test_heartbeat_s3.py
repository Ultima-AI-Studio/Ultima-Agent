"""s3-heartbeat 验收测试（M27 · ACCEPT-1~5）。"""

import unittest

from src.brain.heartbeat.ticker import HeartbeatConfig, HeartbeatTicker, IdleBudget


class TestHeartbeat(unittest.TestCase):
    def test_tick_cycle(self):  # ACCEPT-1
        cfg = HeartbeatConfig(tick_seconds=1.0, idle_budget_max=3)
        state = {"s": "idle"}
        hb = HeartbeatTicker(config=cfg, busy_state_provider=lambda: state["s"])
        r1 = hb.tick()
        self.assertEqual(r1["action"], "主动发声")
        self.assertEqual(hb.snapshot()["ticks"], 1)

    def test_message_preempt(self):  # ACCEPT-2
        hb = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=3),
                             busy_state_provider=lambda: "idle")
        hb.preempt.notify()
        r = hb.tick()
        self.assertEqual(r["action"], "让位")
        self.assertEqual(hb.preempt.count, 1)

    def test_idle_budget_capped(self):  # ACCEPT-3
        hb = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=2),
                             busy_state_provider=lambda: "idle")
        self.assertTrue(hb.tick()["action"] == "主动发声")
        self.assertTrue(hb.tick()["action"] == "主动发声")
        r3 = hb.tick()
        self.assertEqual(r3["action"], "静默")
        self.assertEqual(r3["reason"], "空闲思考预算已封顶")
        self.assertEqual(hb.budget.used, 2)

    def test_speak_only_when_idle(self):  # ACCEPT-4
        state = {"s": "speaking"}
        hb = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=3),
                             busy_state_provider=lambda: state["s"])
        r = hb.tick()
        self.assertEqual(r["action"], "等待")
        self.assertIn("speaking", r["reason"])
        state["s"] = "listening"
        r2 = hb.tick()
        self.assertEqual(r2["action"], "等待")

    def test_budget_reset_after_busy(self):
        hb = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=1),
                             busy_state_provider=lambda: "idle")
        hb.tick()
        self.assertEqual(hb.budget.used, 1)
        # 忙态等待后预算复位
        busy = {"s": "busy"}
        hb2 = HeartbeatTicker(config=HeartbeatConfig(idle_budget_max=1),
                              busy_state_provider=lambda: busy["s"])
        hb2.tick()
        self.assertEqual(hb2.budget.used, 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
