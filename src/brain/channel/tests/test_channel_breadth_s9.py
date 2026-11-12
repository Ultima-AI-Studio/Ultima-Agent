"""s9-channel-breadth 验收测试：渠道注册表 + 多通道适配 + 审批/红线接线。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.channel.channel_breadth import (
    ChannelAdapter,
    ChannelDispatcher,
    ChannelError,
    ChannelRegistry,
)


class TestChannelBreadth(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self._tmp.name)
        self.disp = ChannelDispatcher(self.data_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：注册表注册/列出/获取
    def test_registry(self) -> None:
        reg = ChannelRegistry()
        reg.register(ChannelAdapter("t1", "测试通道", "test", "both"))
        self.assertEqual(len(reg.list()), 1)
        self.assertEqual(reg.get("t1").name, "测试通道")
        with self.assertRaises(ChannelError):
            reg.register(ChannelAdapter("t1", "重复", "test", "both"))
        with self.assertRaises(ChannelError):
            reg.get("missing")
        reg.set_status("t1", "disabled")
        self.assertEqual(reg.get("t1").status, "disabled")
        with self.assertRaises(ChannelError):
            reg.set_status("t1", "bogus")

    def test_defaults_registered(self) -> None:
        channels = self.disp.registry.list()
        ids = {c["channel_id"] for c in channels}
        self.assertIn("local_notify", ids)
        self.assertIn("mail_outbox", ids)

    # ACCEPT-2：本地通知 ingest/dispatch 走 WAL/Outbox
    def test_local_notify_dispatch_outbox(self) -> None:
        res = self.disp.local_notify("桌面提示：任务完成")
        self.assertTrue(res["ok"])
        outbox = self.disp.store.read_outbox()
        self.assertEqual(len(outbox), 1)
        self.assertEqual(outbox[0]["channel"], "local_notify")
        self.assertIn("任务完成", outbox[0]["text"])

    def test_ingest_wal(self) -> None:
        msg = self.disp.ingest("mail_outbox", "sender@example.com", "入站消息")
        self.assertEqual(msg.channel, "mail_outbox")
        wal = self.disp.store.read_wal()
        self.assertEqual(len(wal), 1)
        self.assertEqual(wal[0]["text"], "入站消息")

    # ACCEPT-3：邮件 Outbox 占位注册可用（不真发信）
    def test_mail_placeholder(self) -> None:
        ch = self.disp.registry.get("mail_outbox")
        self.assertEqual(ch.kind, "mail")
        # 占位通道方向 both：入站可用；出站占位（无 adapter 时走统一 dispatch 写 Outbox）
        res = self.disp.dispatch("mail_outbox", "占位邮件正文")
        self.assertTrue(res["ok"])
        self.assertEqual(len(self.disp.store.read_outbox()), 1)

    # ACCEPT-4：审批接线（高危出站两端审批超时取消）与红线
    def test_high_risk_approval_and_timeout(self) -> None:
        res = self.disp.dispatch("local_notify", "发起转账通知", action="send_money")
        self.assertFalse(res["ok"])
        self.assertEqual(res["status"], "pending")
        aid = res["approval_id"]
        # 双端批准
        self.disp.approve(aid, "im", True)
        self.disp.approve(aid, "desktop", True)
        rec = self.disp.settle(aid)
        self.assertEqual(rec["status"], "approved")
        # 超时取消（fail-safe）
        res2 = self.disp.dispatch("local_notify", "另一高危", action="purchase")
        aid2 = res2["approval_id"]
        self.disp.approve(aid2, "im", True)
        self.disp.approve(aid2, "desktop", True)
        rec2 = self.disp.settle(aid2, now=self.disp.approval._pending[aid2]["requested_ts"] + 9999)
        self.assertEqual(rec2["status"], "cancelled")
        self.assertIn("超时", rec2["cancel_reason"])

    def test_redline_rejects(self) -> None:
        res = self.disp.dispatch("local_notify", "x", action="ask_password")
        self.assertFalse(res["ok"])
        self.assertIn("红线", res["reason"])

    def test_wrong_direction(self) -> None:
        # local_notify 仅 out：入站拒绝
        with self.assertRaises(ChannelError):
            self.disp.ingest("local_notify", "s", "t")
        # mail_outbox both：出站可用
        self.assertTrue(self.disp.dispatch("mail_outbox", "t")["ok"])


if __name__ == "__main__":
    unittest.main()
