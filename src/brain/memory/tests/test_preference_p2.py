"""L9 偏好最小记忆语义层（P2 #63）测试。

覆盖：
1. upsert 幂等（同 scope+key 覆盖，created_at 不变、updated_at 更新）
2. scope/key 校验（非法 scope、非法 key、非 JSON 值拒绝）
3. 精确读取 / 按 scope 列出 / 全量
4. 删除与清空（append-only 审计留痕）
5. 语义检索（backend 缺失时回退子串匹配）
6. 持久化重载（index.json 往返一致）
7. 快照（供审计）

运行：<venv-py> -X utf8 -W ignore -m unittest discover -s src\\brain\\memory\\tests -p "test_*.py"
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.memory.preference import PreferenceStore  # noqa: E402


class TestPreferenceStore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.store = PreferenceStore(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    # -- upsert ---------------------------------------------------------

    def test_set_and_get(self):
        e = self.store.set("personal", "name", "张三", source="user")
        self.assertEqual(e.scope, "personal")
        self.assertEqual(e.key, "name")
        self.assertEqual(e.value, "张三")
        self.assertEqual(e.created_at, e.updated_at)
        got = self.store.get("personal", "name")
        self.assertEqual(got.value, "张三")

    def test_upsert_idempotent(self):
        first = self.store.set("report", "style", "结论先行", source="user", priority=1)
        second = self.store.set("report", "style", "结论先行+异常优先", source="user", priority=2)
        self.assertEqual(first.created_at, second.created_at)
        self.assertNotEqual(first.updated_at, second.updated_at)
        self.assertEqual(second.priority, 2)
        self.assertEqual(self.store.get_value("report", "style"), "结论先行+异常优先")

    # -- 校验 -----------------------------------------------------------

    def test_invalid_scope_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set("bad-scope", "k", "v")

    def test_invalid_key_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set("personal", "Bad Key!", "v")

    def test_non_json_value_rejected(self):
        with self.assertRaises(ValueError):
            self.store.set("personal", "k", object())

    # -- 读取 -----------------------------------------------------------

    def test_get_missing_returns_none(self):
        self.assertIsNone(self.store.get("personal", "missing"))
        self.assertIsNone(self.store.get("bad-scope", "k"))

    def test_list_scope_and_all(self):
        self.store.set("personal", "a", 1)
        self.store.set("personal", "b", 2)
        self.store.set("report", "c", 3)
        self.assertEqual(len(self.store.list_scope("personal")), 2)
        self.assertEqual(len(self.store.all()), 3)

    # -- 删除 / 清空 ----------------------------------------------------

    def test_delete(self):
        self.store.set("device", "ac_temp", 24)
        self.assertTrue(self.store.delete("device", "ac_temp"))
        self.assertFalse(self.store.delete("device", "ac_temp"))
        self.assertIsNone(self.store.get("device", "ac_temp"))

    def test_clear(self):
        self.store.set("personal", "a", 1)
        self.store.set("report", "b", 2)
        self.assertEqual(self.store.clear(), 2)
        self.assertEqual(len(self.store.all()), 0)

    # -- 语义检索（回退模式）--------------------------------------------

    def test_search_substring_fallback(self):
        self.store.set("personal", "city", "沈阳")
        self.store.set("report", "style", "结论先行")
        hits = self.store.search("沈阳", top_k=5)
        self.assertTrue(hits)
        self.assertEqual(hits[0]["source"], "substring-fallback")
        self.assertEqual(hits[0]["entry"]["key"], "city")

    def test_search_scope_filter(self):
        self.store.set("personal", "city", "沈阳")
        self.store.set("report", "style", "结论先行")
        hits = self.store.search("沈阳", scopes=["report"])
        self.assertEqual(hits, [])

    # -- 持久化 ---------------------------------------------------------

    def test_persistence_reload(self):
        self.store.set("personal", "name", "张三")
        self.store.set("device", "ac_temp", 24)
        reloaded = PreferenceStore(self._tmp.name)
        self.assertEqual(reloaded.get_value("personal", "name"), "张三")
        self.assertEqual(reloaded.get_value("device", "ac_temp"), 24)

    def test_corrupt_index_does_not_block(self):
        idx = Path(self._tmp.name) / "index.json"
        idx.write_text("{broken json", encoding="utf-8")
        store = PreferenceStore(self._tmp.name)
        self.assertEqual(len(store.all()), 0)  # 不抛错，内存态空

    # -- 快照 -----------------------------------------------------------

    def test_snapshot(self):
        self.store.set("personal", "a", 1)
        snap = self.store.snapshot()
        self.assertEqual(snap["total"], 1)
        self.assertEqual(snap["by_scope"]["personal"], 1)
        self.assertFalse(snap["backend"])


if __name__ == "__main__":
    unittest.main()
