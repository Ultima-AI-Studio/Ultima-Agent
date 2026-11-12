"""s3-ime-bridge 验收测试（M24 · ACCEPT-1~5）。"""

import tempfile
import time
import unittest
from pathlib import Path

from src.brain.channel.ime_bridge import ImBridge


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="ime_s3_"))


class TestImeBridge(unittest.TestCase):
    def test_adapter_wal_outbox(self):  # ACCEPT-1
        d = make_tmp()
        b = ImBridge(d)
        msg = b.inbound("feishu", "user-1", "你好，查询任务状态")
        self.assertEqual(msg.channel, "feishu")
        self.assertEqual(b.store.read_wal()[0]["text"], "你好，查询任务状态")
        # 普通动作走 Outbox
        r = b.act("read_task", "查询任务列表")
        self.assertTrue(r["ok"])
        out = b.store.read_outbox()
        self.assertEqual(out[0]["action"], "read_task")

    def test_approval_two_sides_and_timeout(self):  # ACCEPT-2
        d = make_tmp()
        b = ImBridge(d)
        r = b.act("send_money", "转账 1000", approval_id="ap1")
        self.assertEqual(r["status"], "pending")
        b.approve("ap1", "im", True)
        b.approve("ap1", "desktop", True)
        settled = b.settle("ap1")
        self.assertEqual(settled["status"], "approved")
        # 超时取消（fail-safe）
        r2 = b.act("send_money", "转账", approval_id="ap2")
        b.approval._set_requested_ts("ap2", time.time() - 120)
        settled2 = b.settle("ap2")
        self.assertEqual(settled2["status"], "cancelled")
        self.assertIn("超时", settled2["cancel_reason"])

    def test_redline_no_login(self):  # ACCEPT-3
        d = make_tmp()
        b = ImBridge(d)
        for action in ("ask_password", "login_as", "collect_credential"):
            r = b.act(action, "x")
            self.assertFalse(r["ok"])
            self.assertIn("红线", r["reason"])
        self.assertTrue(any(e["kind"] == "channel.redline.denied" for e in b.bus_events))

    def test_bus_circuit(self):  # ACCEPT-4
        d = make_tmp()
        b = ImBridge(d)
        b.inbound("wechat", "u", "hi")
        r = b.act("read_task", "t")
        self.assertTrue(r["ok"])
        kinds = {e["kind"] for e in b.bus_events}
        self.assertIn("channel.inbound", kinds)
        self.assertIn("channel.action.executed", kinds)
        # 高危动作审批事件入流
        b.act("post_publish", "x", approval_id="ap3")
        b.approve("ap3", "im", True)
        b.approve("ap3", "desktop", True)
        b.settle("ap3")
        kinds2 = {e["kind"] for e in b.bus_events}
        self.assertIn("channel.approval.requested", kinds2)
        self.assertIn("channel.approval.approved", kinds2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
