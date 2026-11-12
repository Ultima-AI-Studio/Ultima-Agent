"""s3-websearch-upgrade 验收测试（M14 · ACCEPT-1~4）。"""

import unittest

from src.brain.search.upgrade import SearchOrchestrator, SSRFGuard


class TestWebSearchUpgrade(unittest.TestCase):
    def test_multi_engine_orchestration(self):  # ACCEPT-1
        so = SearchOrchestrator()
        so.register("primary", lambda q: [{"title": "A", "url": "https://example.com/a",
                                           "snippet": "s1"}])
        so.register("fallback", lambda q: [{"title": "B", "url": "https://example.com/b",
                                            "snippet": "s2"}])
        r = so.search("测试")
        self.assertEqual(r["engine"], "primary")
        self.assertFalse(r["degraded"])
        self.assertEqual(len(r["results"]), 1)
        self.assertEqual(r["results"][0]["engine"], "primary")

    def test_fallback_and_degraded_flag(self):  # ACCEPT-2
        so = SearchOrchestrator()
        so.register("primary", lambda q: (_ for _ in ()).throw(RuntimeError("引擎挂了")))
        so.register("fallback", lambda q: [{"title": "B", "url": "https://example.com/b",
                                            "snippet": "s2"}])
        r = so.search("测试")
        self.assertEqual(r["engine"], "fallback")
        self.assertTrue(r["degraded"])
        self.assertIn("失败", r["degraded_reason"])
        self.assertEqual(r["results"][0]["url"], "https://example.com/b")

    def test_ssrf_guard(self):  # ACCEPT-3
        g = SSRFGuard()
        self.assertTrue(g.validate("https://example.com/page")[0])
        for bad in ("http://127.0.0.1/admin", "http://192.168.1.1/x",
                    "http://169.254.169.254/latest/meta-data",
                    "http://localhost:8080", "http://10.0.0.1/x"):
            ok, why = g.validate(bad)
            self.assertFalse(ok, f"应拒绝 {bad}")
            self.assertIn("SSRF", why)

    def test_source_marked_and_ssrf_blocked_in_search(self):  # ACCEPT-4
        so = SearchOrchestrator()
        so.register("primary", lambda q: [
            {"title": "OK", "url": "https://example.com/a", "snippet": "s"},
            {"title": "INNER", "url": "http://169.254.169.254/latest/meta-data", "snippet": "s"},
        ])
        r = so.search("测试")
        self.assertEqual(r["engine"], "primary")
        self.assertEqual(len(r["results"]), 1)  # SSRF 目标被拦截
        self.assertEqual(r["blocked_count"], 1)
        self.assertEqual(r["results"][0]["url"], "https://example.com/a")


if __name__ == "__main__":
    unittest.main(verbosity=2)
