"""s6-capability-page 验收测试：能力清单同源数据源 + 双界面呈现（全 tempfile/内存，无污染）。"""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.capability import (
    CapabilityError,
    load_manifest,
    render_capability_page,
    summarize,
    to_a2ui_messages,
)
from src.brain.intent import CAPABILITY_INTENT, TASK_STATUS_INTENT, parse_capability_intent
from src.brain.reporter import respond_to_text
from src.window.a2ui_validator import validate_batch


class TestManifest(unittest.TestCase):
    """ACCEPT-1/2：数据源盘点一致 + 加载确定性错误。"""

    def test_manifest_present_and_consistent(self):
        manifest = load_manifest()
        caps = manifest["capabilities"]
        available = [c for c in caps if c.get("status") == "可用"]
        self.assertGreaterEqual(len(available), 24)  # 对齐报告 24+ 项可用（C 类后 29 项）
        # 阶段预留：原 4 项中 m15 设备实操已转可用（s10），余 3 项规划中
        self.assertGreaterEqual(len(manifest.get("planned", [])), 3)
        for cap in caps:
            for field in ("id", "name", "description", "status", "module", "evidence"):
                self.assertIn(field, cap, f"{cap.get('id')} 缺 {field}")
            self.assertTrue(cap.get("evidence"), f"{cap.get('id')} 证据为空")

    def test_load_missing_raises(self):
        with self.assertRaises(CapabilityError):
            load_manifest(Path(tempfile.mkdtemp()) / "nope.json")

    def test_load_corrupt_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{not json", encoding="utf-8")
            with self.assertRaises(CapabilityError):
                load_manifest(bad)


class TestSummarize(unittest.TestCase):
    """ACCEPT-3：结构化中文摘要。"""

    def test_summary_contains_counts_and_examples(self):
        text = summarize(load_manifest())
        self.assertIn("项可用能力", text)
        self.assertIn("你可以对我说", text)
        self.assertIn("规划中", text)


class TestA2uiRendering(unittest.TestCase):
    """ACCEPT-4：A2UI 校验 + 安全 HTML（零 JS CSP）。"""

    def test_messages_pass_validation(self):
        messages = to_a2ui_messages(load_manifest())
        self.assertTrue(validate_batch(messages, final=True).ready_to_render)

    def test_render_no_script_csp(self):
        html_doc = render_capability_page(load_manifest())
        self.assertIn("<title>UltimaAgent 能力清单</title>", html_doc)
        self.assertIn("script-src 'none'", html_doc)
        self.assertNotIn("<script", html_doc)
        self.assertIn("UltimaAgent 能力清单", html_doc)


class TestIntentBoundary(unittest.TestCase):
    """ACCEPT-5：能力意图命中/不命中边界，不干扰任务状态。"""

    def test_hits(self):
        for text in ("你有什么能力", "你能做什么", "都有哪些功能", "你会什么技能", "介绍一下你的能力"):
            result = parse_capability_intent(text)
            self.assertTrue(result.matched, f"应命中：{text}")
            self.assertEqual(result.intent, CAPABILITY_INTENT)

    def test_miss_task_status_not_capability(self):
        result = parse_capability_intent("查询任务状态")
        self.assertFalse(result.matched, "任务状态查询不应命中能力意图")
        from src.brain.intent import parse_task_status_intent
        self.assertEqual(parse_task_status_intent("查询任务状态").intent, TASK_STATUS_INTENT)

    def test_miss_negation_and_reference(self):
        for text in ("不用查能力", "昨天问过你有什么能力了", "他说你会什么"):
            result = parse_capability_intent(text)
            self.assertFalse(result.matched, f"不应命中：{text}")


class TestReporterConsumption(unittest.TestCase):
    """ACCEPT-6：reporter 消费 capability.query；任务状态查询不受影响。"""

    def test_capability_query_returns_summary(self):
        response = respond_to_text("你有什么能力", queue_root=Path(tempfile.mkdtemp()))
        self.assertTrue(response.handled)
        self.assertTrue(response.ok)
        self.assertIn("项可用能力", response.text)

    def test_task_status_unaffected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "tasks.json").write_text("[]", encoding="utf-8")
            response = respond_to_text("查询任务状态", queue_root=root)
        self.assertTrue(response.handled)
        self.assertTrue(response.ok)
        self.assertIn("任务库为空", response.text)


if __name__ == "__main__":
    unittest.main()
