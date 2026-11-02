"""s3-browser-channel 验收测试（M13 · ACCEPT-1~5）。"""

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.browser.channel import BrowserChannel, RedlineGate


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="browser_s3_"))


class TestBrowserChannel(unittest.TestCase):
    def test_navigate_observe_execute(self):  # ACCEPT-1
        d = make_tmp()
        bc = BrowserChannel(profile_dir=d / "profiles",
                            whitelist_sites=["https://example.com"],
                            audit_path=d / "audit.jsonl")
        sid = bc.new_session("s1")
        self.assertTrue(sid["isolated"])
        obs = bc.navigate(sid["session_id"], "https://example.com/page")
        self.assertEqual(obs.url, "https://example.com/page")
        obs2 = bc.observe(sid["session_id"], "https://example.com/page")
        self.assertIn("观察", obs2.note)
        r = bc.execute(sid["session_id"], "click", "https://example.com/btn")
        self.assertTrue(r["ok"])

    def test_session_isolated(self):  # ACCEPT-2
        d = make_tmp()
        bc = BrowserChannel(profile_dir=d / "profiles")
        s1 = bc.new_session("u1")
        s2 = bc.new_session("u2")
        self.assertNotEqual(s1["profile"], s2["profile"])
        # 每个会话独立 profile 目录
        self.assertIn("u1", s1["profile"])
        self.assertIn("u2", s2["profile"])

    def test_redline_rejected_and_logged(self):  # ACCEPT-3
        d = make_tmp()
        bc = BrowserChannel(profile_dir=d / "profiles",
                            whitelist_sites=["https://x.com"],
                            audit_path=d / "audit.jsonl")
        sid = bc.new_session("s1")
        for action in ("post", "comment", "like", "login", "enter_password"):
            r = bc.execute(sid["session_id"], action, "https://x.com/")
            self.assertFalse(r["ok"])
            self.assertIn("只读红线", r["reason"])
        # 非白名单站点拒绝
        r2 = bc.execute(sid["session_id"], "click", "https://evil-site.com/btn")
        self.assertFalse(r2["ok"])
        self.assertIn("白名单", r2["reason"])

    def test_audit_trail(self):  # ACCEPT-4
        d = make_tmp()
        bc = BrowserChannel(profile_dir=d / "profiles", audit_path=d / "audit.jsonl")
        sid = bc.new_session("s1")
        bc.execute(sid["session_id"], "click", "https://example.com/a")
        bc.execute(sid["session_id"], "post", "https://example.com/b")
        out = bc.flush_audit()
        lines = [json.loads(l) for l in out.read_text(encoding="utf-8").splitlines() if l.strip()]
        self.assertEqual(len(lines), 2)
        self.assertTrue(any(l["allowed"] for l in lines))
        self.assertTrue(any(not l["allowed"] and "红线" in l["reason"] for l in lines))
        # 拒绝动作带 reason 留痕
        denied = [l for l in lines if not l["allowed"]]
        self.assertTrue(all(l["reason"] for l in denied))


if __name__ == "__main__":
    unittest.main(verbosity=2)
