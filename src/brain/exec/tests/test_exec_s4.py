"""s4-local-exec 本机执行通道测试（M12）。

验收口径（tasks/cards/s4-local-exec/task.md）：
- ACCEPT-1 只读默认（未授权控制动作全拒）
- ACCEPT-2 桌面窗口只读探测可用
- ACCEPT-3 白名单登记后可执行；未登记拒绝
- ACCEPT-4 操作后重新观察接口存在并返回新快照
- ACCEPT-5 审计留痕（动作/拒绝带 reason）
- ACCEPT-6 回执完整
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.exec.channel import LocalExecChannel
from src.brain.guardrails.audit_log import AppendOnlyAuditLog


class TestLocalExecS4(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.audit = AppendOnlyAuditLog(self.root / "audit.jsonl")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：只读默认——未授权控制动作一律拒绝
    def test_accept1_read_only_default(self) -> None:
        ch = LocalExecChannel(audit=self.audit)
        for action in ("write", "exec", "control"):
            out = ch.perform(action)
            self.assertEqual(out["outcome"], "denied", action)
            self.assertIn("reason", out)
            self.assertTrue(out["reason"])
        # 审计留痕含拒绝原因
        lines = self.root.joinpath("audit.jsonl").read_text(encoding="utf-8").splitlines()
        denied = [l for l in lines if "exec.denied" in l]
        self.assertGreaterEqual(len(denied), 3)

    # ACCEPT-2：桌面窗口只读探测可用（枚举窗口/进程/属性）
    def test_accept2_read_probe(self) -> None:
        ch = LocalExecChannel(audit=self.audit)
        windows = ch.list_windows()
        self.assertIsInstance(windows, list)
        for w in windows:
            self.assertIn("hwnd", w)
            self.assertIn("title", w)
            self.assertIn("pid", w)
        processes = ch.list_processes()
        self.assertIsInstance(processes, list)

    # ACCEPT-3：白名单登记后可执行；未登记拒绝
    def test_accept3_whitelist_gate(self) -> None:
        calls: list[str] = []

        def open_app(target):
            calls.append(target)
            return {"opened": target}

        ch = LocalExecChannel(audit=self.audit, allowed_controls={"open_app"},
                              require_confirm=False)
        ch.register_control("open_app", open_app)
        # 登记+注册：放行
        out = ch.perform("open_app", target="notepad", confirmed=True)
        self.assertEqual(out["outcome"], "executed")
        self.assertEqual(calls, ["notepad"])
        self.assertIn("re_observe", out)
        # 未登记：拒绝
        out2 = ch.perform("kill_app", target="x", confirmed=True)
        self.assertEqual(out2["outcome"], "denied")
        # 已登记但未注册实现：拒绝（dynamic control 预留点）
        ch2 = LocalExecChannel(audit=self.audit, allowed_controls={"open_app"},
                               require_confirm=False)
        out3 = ch2.perform("open_app", confirmed=True)
        self.assertEqual(out3["outcome"], "denied")

    # ACCEPT-4：操作后重新观察接口存在并返回新快照
    def test_accept4_re_observe(self) -> None:
        ch = LocalExecChannel(audit=self.audit)
        snap = ch.re_observe()
        for key in ("ts", "window_count", "process_count", "snapshot"):
            self.assertIn(key, snap)
        self.assertEqual(snap["snapshot"], "fresh")
        out = ch.perform("observe")
        self.assertEqual(out["outcome"], "executed")
        self.assertEqual(out["result"]["snapshot"], "fresh")

    # ACCEPT-5：审计留痕（allow/deny 带 reason）
    def test_accept5_audit_trail(self) -> None:
        ch = LocalExecChannel(audit=self.audit)
        ch.perform("list")
        ch.perform("write")
        lines = self.root.joinpath("audit.jsonl").read_text(encoding="utf-8").splitlines()
        events = [l for l in lines if '"event_type"' in l]
        self.assertGreaterEqual(len(events), 2)
        text = "\n".join(lines)
        self.assertIn("exec.executed", text)
        self.assertIn("exec.denied", text)

    # ACCEPT-6：回执完整（字段齐全）
    def test_accept6_receipt(self) -> None:
        ch = LocalExecChannel(audit=self.audit)
        out = ch.perform("read")
        for key in ("action", "decision", "outcome", "result", "re_observe"):
            self.assertIn(key, out)
        self.assertEqual(out["decision"]["verdict"], "allow")


if __name__ == "__main__":
    unittest.main()
