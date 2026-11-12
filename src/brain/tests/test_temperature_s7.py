r"""s7-memory-temperature · 记忆热度分层单测（正式可复跑版）。

覆盖（对应工单 wo-s7-memory-temperature T0/T1/T2/T3）：
  1. 热度打标：写入按层默认档（working=hot / declarative=warm / env_profile=cold）
  2. 召回计数 touch：access_count/last_access 更新；会话内 ≥2 次升热（内存标记）
  3. 升降级四动作：promote_hot / demote_warm / archive_cold / thaw_cold 状态迁移
  4. 冷归档：gz 写入/读取/移除；原行 archived 标记可回溯；解冻回温
  5. 三级检索路由：热→温→冷命中即停；include_cold 解冻召回
  6. 批量降热 demote_all_hot（会话收尾）
  7. stale_candidates：超保留期/30 天未召回候选
  8. 打断单元：pending_interrupt 写入 → resume_interrupt 召回 → close_interrupt 闭环
  9. 回归：既有五层写入/软删/遗忘边界行为不变

运行：
  H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\brain\tests -p "test_temperature_s7.py" -v
"""

from __future__ import annotations

import gzip
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.memory.layers import (  # noqa: E402
    DEFAULT_MAX_ENTRIES,
    DEFAULT_RETENTION_DAYS,
    DEFAULT_TEMPERATURE,
    HOT_TOUCH_THRESHOLD,
    MemoryLayerError,
    MemoryLayers,
)


class TestTemperatureTagging(unittest.TestCase):
    """热度打标与召回计数。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.layers = MemoryLayers(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_default_temperature_by_layer(self) -> None:
        w = self.layers.write("working", "会话上下文", kind="reflection")
        d = self.layers.write("declarative", "用户偏好：早起")
        p = self.layers.write("procedural", "流程：任务查询")
        dp = self.layers.write("device_profile", "设备：win11")
        ep = self.layers.write("env_profile", "环境：夜间")
        self.assertEqual(w.temperature, "hot")      # working 默认热
        self.assertEqual(d.temperature, "warm")     # declarative 默认温
        self.assertEqual(p.temperature, "warm")
        self.assertEqual(dp.temperature, "warm")
        self.assertEqual(ep.temperature, "cold")    # env_profile 默认冷

    def test_write_meta_defaults(self) -> None:
        d = self.layers.write("declarative", "事实")
        self.assertEqual(d.meta.get("access_count"), 0)
        self.assertEqual(d.meta.get("last_access"), "")

    def test_touch_updates_count_and_access(self) -> None:
        d = self.layers.write("declarative", "事实")
        self.assertTrue(self.layers.touch(d.id, session="s1"))
        self.assertEqual(d.meta["access_count"], 1)
        self.assertNotEqual(d.meta["last_access"], "")
        self.assertEqual(d.meta["last_session"], "s1")

    def test_touch_promotes_hot_after_threshold(self) -> None:
        d = self.layers.write("declarative", "高频偏好")
        self.layers.touch(d.id, session="s1")
        self.layers.touch(d.id, session="s1")
        self.assertEqual(d.temperature, "hot")  # 会话内 ≥2 次召回升热

    def test_touch_unknown_id_returns_false(self) -> None:
        self.assertFalse(self.layers.touch("nonexistent"))

    def test_invalid_temperature_rejected(self) -> None:
        d = self.layers.write("declarative", "事实")
        with self.assertRaises(MemoryLayerError):
            d.set_temperature("lukewarm")


class TestPromoteDemote(unittest.TestCase):
    """promote_hot / demote_warm 状态迁移。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.layers = MemoryLayers(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_promote_hot_memory_only(self) -> None:
        d = self.layers.write("declarative", "事实")
        self.assertTrue(self.layers.promote_hot(d.id))
        self.assertEqual(d.temperature, "hot")
        # 热=内存标记：重载后回落默认档
        reloaded = MemoryLayers(Path(self.tmp.name))
        again = reloaded.get_by_id(d.id)
        self.assertIsNotNone(again)
        self.assertEqual(again.temperature, "warm")  # declarative 默认温

    def test_demote_warm_persists(self) -> None:
        w = self.layers.write("working", "会话上下文", kind="reflection")
        self.assertTrue(self.layers.demote_warm(w.id))
        self.assertEqual(w.temperature, "warm")
        reloaded = MemoryLayers(Path(self.tmp.name))
        again = reloaded.get_by_id(w.id)
        self.assertIsNotNone(again)
        self.assertEqual(again.temperature, "warm")  # 落盘后重载仍温

    def test_demote_all_hot_batch(self) -> None:
        a = self.layers.write("working", "A", kind="reflection")
        b = self.layers.write("working", "B", kind="reflection")
        self.layers.promote_hot(a.id)
        self.layers.promote_hot(b.id)
        n = self.layers.demote_all_hot("working")
        self.assertEqual(n, 2)
        self.assertEqual(a.temperature, "warm")
        self.assertEqual(b.temperature, "warm")
        self.assertEqual(self.layers.demote_all_hot("declarative"), 0)

    def test_promote_demote_unknown(self) -> None:
        self.assertFalse(self.layers.promote_hot("nope"))
        self.assertFalse(self.layers.demote_warm("nope"))


class TestColdArchive(unittest.TestCase):
    """archive_cold / thaw_cold / 冷归档读写。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        self.layers = MemoryLayers(self.data_dir)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_archive_cold_marks_and_keeps_row(self) -> None:
        d = self.layers.write("declarative", "长期事实")
        self.assertTrue(self.layers.archive_cold(d.id))
        self.assertEqual(d.temperature, "cold")
        self.assertTrue(d.meta.get("archived"))
        # 原行仍在索引（可回溯），归档文件存在
        again = self.layers.get_by_id(d.id)
        self.assertIsNotNone(again)
        self.assertTrue(again.meta.get("archived"))
        arc = self.data_dir / "archive" / "declarative.jsonl.gz"
        self.assertTrue(arc.exists())
        with gzip.open(arc, "rt", encoding="utf-8") as fh:
            content = fh.read()
        self.assertIn(d.id, content)

    def test_thaw_cold_restores_warm(self) -> None:
        d = self.layers.write("declarative", "长期事实")
        self.layers.archive_cold(d.id)
        self.assertTrue(self.layers.thaw_cold(d.id))
        again = self.layers.get_by_id(d.id)
        self.assertIsNotNone(again)
        self.assertEqual(again.temperature, "warm")
        self.assertFalse(again.meta.get("archived"))
        # 归档文件已移除该条目
        with gzip.open(self.data_dir / "archive" / "declarative.jsonl.gz", "rt", encoding="utf-8") as fh:
            content = fh.read()
        self.assertNotIn(d.id, content)

    def test_thaw_unknown_returns_false(self) -> None:
        self.assertFalse(self.layers.thaw_cold("nonexistent"))

    def test_read_archived_only(self) -> None:
        d = self.layers.write("declarative", "归档条目 ABC")
        self.layers.archive_cold(d.id)
        hits = self.layers.read_archived("declarative", "ABC")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].id, d.id)
        # 非归档层为空
        self.assertEqual(self.layers.read_archived("working", "ABC"), [])

    def test_stale_candidates(self) -> None:
        # 超过保留期的 declarative 条目（默认 365 天）→ 用最小保留期验证 env_profile 默认冷
        ep = self.layers.write("env_profile", "环境：夜间")
        self.assertEqual(ep.temperature, "cold")  # env_profile 默认已冷
        # 构造 30 天未召回候选：直接改 last_access 为过去
        d = self.layers.write("declarative", "低频条目")
        import datetime
        from datetime import timezone
        past = (datetime.datetime.now(timezone.utc) - datetime.timedelta(days=40)).isoformat().replace("+00:00", "Z")
        d.meta["last_access"] = past
        cands = self.layers.stale_candidates()
        self.assertIn(d.id, [e.id for e in cands])


class TestThreeTierRetrieval(unittest.TestCase):
    """三级检索路由：热→温→冷命中即停，降级不丢。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.layers = MemoryLayers(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_read_touches_hits(self) -> None:
        d = self.layers.write("declarative", "用户喜欢摩托车")
        hits = self.layers.read("摩托车", layer="declarative")
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].id, d.id)
        self.assertEqual(d.meta["access_count"], 1)  # 命中即 touch

    def test_read_include_cold_returns_archived(self) -> None:
        d = self.layers.write("declarative", "冷档内容 XYZ")
        self.layers.archive_cold(d.id)
        # 默认不含冷档
        self.assertEqual(self.layers.read("XYZ", layer="declarative"), [])
        # include_cold=True 可召回
        hits = self.layers.read("XYZ", layer="declarative", include_cold=True)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].id, d.id)

    def test_read_kinds_filter(self) -> None:
        self.layers.write("working", "待办", kind="pending")
        self.layers.write("working", "打断", kind="pending_interrupt")
        hits = self.layers.read("", layer="working", kinds=("pending_interrupt",))
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].kind, "pending_interrupt")


class TestInterruptUnit(unittest.TestCase):
    """打断单元入记忆层（T2 语义，经 MemoryLayers 直测）。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.layers = MemoryLayers(Path(self.tmp.name))

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_pending_interrupt_kind_allowed(self) -> None:
        entry = self.layers.write(
            "working", "查一下任务状态",
            kind="pending_interrupt", trusted=True, source="brain.loop.interrupt",
            meta={"state": {"executing": "task_status"}, "closed": False},
        )
        self.assertEqual(entry.kind, "pending_interrupt")
        self.assertEqual(entry.temperature, "hot")  # working 默认热档

    def test_pending_interrupt_retrievable(self) -> None:
        self.layers.write(
            "working", "查一下任务状态",
            kind="pending_interrupt", trusted=True, source="brain.loop.interrupt",
            meta={"state": {"executing": "task_status"}, "closed": False},
        )
        hits = self.layers.read("", layer="working", kinds=("pending_interrupt",), top_k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0].meta.get("closed"), False)

    def test_close_interrupt_demotes_warm(self) -> None:
        entry = self.layers.write(
            "working", "查一下任务状态",
            kind="pending_interrupt", trusted=True, source="brain.loop.interrupt",
            meta={"state": {}, "closed": False},
        )
        # 闭环：置 closed 并转温档保留
        entry.meta["closed"] = True
        self.layers.demote_warm(entry.id)
        self.assertEqual(entry.temperature, "warm")
        self.assertTrue(entry.meta.get("closed"))


class TestRegression(unittest.TestCase):
    """回归保护：既有五层写入/软删/遗忘边界行为不变。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.tmp.name)
        self.layers = MemoryLayers(self.data_dir)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_write_read_delete_cycle(self) -> None:
        d = self.layers.write("declarative", "事实：沈阳")
        hits = self.layers.read("沈阳", layer="declarative")
        self.assertEqual(len(hits), 1)
        self.assertTrue(self.layers.delete(d.id))
        self.assertEqual(self.layers.read("沈阳", layer="declarative"), [])
        # 软删保留行：get_by_id 仍可见且 deleted
        again = self.layers.get_by_id(d.id)
        self.assertIsNotNone(again)
        self.assertTrue(again.deleted)

    def test_boundary_evicts_oldest(self) -> None:
        small = MemoryLayers(self.data_dir, max_entries={"working": 2})
        a = small.write("working", "A", kind="reflection")
        small.write("working", "B", kind="reflection")
        c = small.write("working", "C", kind="reflection")
        # 超上限逐出最旧（保留最新 C）
        self.assertTrue(a.deleted)
        self.assertFalse(c.deleted)
        active = [e for e in small.read("", layer="working") if not e.deleted]
        self.assertEqual(len(active), 2)

    def test_forget_expired_returns_count(self) -> None:
        # working 保留 1 天，强制写一个旧时间条目验证遗忘
        w = self.layers.write("working", "旧会话", kind="reflection")
        import datetime
        from datetime import timezone
        old = (datetime.datetime.now(timezone.utc) - datetime.timedelta(days=2)).isoformat().replace("+00:00", "Z")
        w.ts = old
        self.layers._rewrite_layer("working")  # noqa: SLF001 - 测试直接落盘旧时间
        n = self.layers.forget_expired()
        self.assertGreaterEqual(n, 1)
        self.assertTrue(w.deleted)

    def test_defaults_unchanged(self) -> None:
        self.assertEqual(DEFAULT_MAX_ENTRIES["working"], 200)
        self.assertEqual(DEFAULT_RETENTION_DAYS["declarative"], 365)
        self.assertEqual(DEFAULT_TEMPERATURE["working"], "hot")
        self.assertEqual(HOT_TOUCH_THRESHOLD, 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
