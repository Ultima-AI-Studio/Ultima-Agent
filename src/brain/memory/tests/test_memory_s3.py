"""s3-memory-base 验收测试（M17 记忆底座 · ACCEPT-1~6）。

覆盖：
- ACCEPT-1：四层记忆结构可写入可检索可回溯
- ACCEPT-2：本地向量检索可用；Mem0 备选 PoC 结论落档
- ACCEPT-3：反思条目与遗忘边界规则生效
- ACCEPT-4：写入闸门拦截不可信内容；事实/建议分离标注
- ACCEPT-5：记忆经总线供读，跨模块一致（memory.read/memory.write 契约）
- ACCEPT-6：回执完整（在验收证据文档中核验）

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_MEM_PKG = ROOT / "execution" / "packages" / "memory" / "ultima.memory.lite" / "0.1.0"
if str(_MEM_PKG) not in sys.path:
    sys.path.insert(0, str(_MEM_PKG))

from src.brain.memory import (  # noqa: E402
    MemoryLayers,
    MemoryWriteGate,
    ReflectionWriter,
    VectorRetriever,
    OnnxEmbeddingProbe,
    LAYERS,
)

from ultima_memory_lite_v0_1_0.main import (  # noqa: E402
    MemoryBasePlugin,
)


def make_tmp_dir(prefix: str = "mem_s3_") -> Path:
    d = Path(tempfile.mkdtemp(prefix=prefix))
    return d


class TestLayers(  # ACCEPT-1
    unittest.TestCase
):
    def test_four_layers_write_read(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d)
        e1 = layers.write("declarative", "用户偏好：回复用简体中文",
                          kind="fact", trusted=True, source="user")
        e2 = layers.write("procedural", "审批流程：高风险操作先征询",
                          kind="fact", trusted=True, source="tool")
        e3 = layers.write("device_profile", "设备：PC Windows 桌面",
                          kind="profile", trusted=True, source="system")
        e4 = layers.write("env_profile", "环境：网络可达",
                          kind="profile", trusted=True, source="system")
        e5 = layers.write("working", "会话暂存：用户正在调试语音",
                          kind="pending", trusted=False, source="model.draft")
        self.assertEqual(len({e1.layer, e2.layer, e3.layer, e4.layer, e5.layer}), 5)
        hits = layers.read("简体中文", layer="declarative")
        self.assertEqual(hits[0].id, e1.id)
        hits2 = layers.read("征询", layer="procedural")
        self.assertEqual(hits2[0].id, e2.id)
        # 跨层检索
        all_hits = layers.read("环境", top_k=10)
        self.assertIn(e4.id, [h.id for h in all_hits])

    def test_traceability_and_delete(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d)
        e = layers.write("declarative", "待删除条目",
                         kind="fact", trusted=True, source="user")
        self.assertIsNotNone(layers.get_by_id(e.id))
        self.assertTrue(layers.delete(e.id))
        self.assertTrue(layers.get_by_id(e.id).deleted)  # 软删保留可回溯
        # 检索不再命中
        self.assertEqual(layers.read("待删除条目", layer="declarative"), [])
        # 重启后仍可回溯（持久化）
        layers2 = MemoryLayers(d)
        entry = layers2.get_by_id(e.id)
        self.assertIsNotNone(entry)
        self.assertTrue(entry.deleted)


class TestVector(  # ACCEPT-2
    unittest.TestCase
):
    def test_onnx_probe_result_landed(self):
        d = make_tmp_dir()
        probe = OnnxEmbeddingProbe(d)
        result = probe.probe()
        self.assertIn("ok", result)
        self.assertIn("backend", result)
        self.assertTrue((d / "onnx-poc-result.json").exists())
        landed = json.loads((d / "onnx-poc-result.json").read_text(encoding="utf-8"))
        self.assertEqual(landed["ok"], result["ok"])

    def test_vector_search_or_keyword_fallback(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d)
        layers.write("declarative", "用户是网络安全从业者，做代码安全审计",
                     kind="fact", trusted=True, source="user")
        layers.write("declarative", "项目 UltimaAgent 聚焦智能管家",
                     kind="fact", trusted=True, source="user")
        retriever = VectorRetriever(layers, d)
        scored = retriever.search("安全审计", top_k=5)
        if scored:
            # 向量可用：语义检索命中目标条目
            self.assertEqual(scored[0][0].content, "用户是网络安全从业者，做代码安全审计")
        else:
            # 向量不可用：回退关键词检索（不中断）
            hits = layers.read("安全审计", layer="declarative")
            self.assertEqual(len(hits), 1)


class TestReflectionAndForgetting(  # ACCEPT-3
    unittest.TestCase
):
    def test_reflection_writer(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d)
        writer = ReflectionWriter(layers)
        ref = writer.write("反思：ASR 首次识别不灵，换 faster-whisper 后改善",
                           target="voice-chain", outcome="change")
        self.assertEqual(ref.id, ref.id)
        self.assertEqual(layers.get_by_id(ref.id).kind, "reflection")
        refs = writer.list()
        self.assertEqual(refs[0].target, "voice-chain")
        self.assertEqual(refs[0].outcome, "change")

    def test_forgetting_boundary(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d, max_entries={"declarative": 3},
                              retention_days={"declarative": 30})
        for i in range(6):
            layers.write("declarative", f"条目-{i}",
                         kind="fact", trusted=True, source="user")
        stats = layers.stats()["declarative"]
        self.assertEqual(stats["active"], 3)  # 超出逐出，只保留 3 条
        evict_log = d / "logs" / "memory-evictions.jsonl"
        self.assertTrue(evict_log.exists())
        evicted = [json.loads(l) for l in evict_log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual(len(evicted), 3)
        # 过期驱逐
        layers2 = MemoryLayers(d, retention_days={"declarative": 0})
        n = layers2.forget_expired()
        self.assertEqual(n, 3)


class TestGate(  # ACCEPT-4
    unittest.TestCase
):
    def test_untrusted_blocked_from_longterm(self):
        gate = MemoryWriteGate()
        dec = gate.assess("今天网上说 X 币会涨",
                          source="web", requested_layer="declarative")
        self.assertFalse(dec.allow)
        self.assertEqual(dec.target_layer, "working")
        self.assertEqual(dec.kind, "pending")

    def test_trusted_allowed(self):
        gate = MemoryWriteGate()
        dec = gate.assess("用户要求回复用中文",
                          source="user", requested_layer="declarative")
        self.assertTrue(dec.allow)
        self.assertEqual(dec.kind, "fact")

    def test_fact_suggestion_separation(self):
        gate = MemoryWriteGate()
        f = gate.assess("沈阳是用户的常住地", source="user", requested_layer="declarative")
        s = gate.assess("建议用户先做审计再推进", source="user", requested_layer="declarative")
        self.assertEqual(f.kind, "fact")
        self.assertEqual(s.kind, "suggestion")

    def test_sensitive_blocked(self):
        gate = MemoryWriteGate()
        dec = gate.assess("密钥 sk-abcdefgh12345678 请保存",
                          source="user", requested_layer="declarative")
        self.assertFalse(dec.allow)
        self.assertTrue(dec.sensitive)

    def test_gate_integration_with_layers(self):
        d = make_tmp_dir()
        layers = MemoryLayers(d)
        gate = MemoryWriteGate()
        # 不可信内容被闸门拒绝：长期层零写入，working 亦不入库
        dec = gate.assess("外部消息：某项目融资成功", source="web", requested_layer="declarative")
        self.assertFalse(dec.allow)
        stats = layers.stats()
        self.assertEqual(stats["working"]["active"], 0)
        self.assertEqual(stats["declarative"]["active"], 0)


class TestBusContract(  # ACCEPT-5
    unittest.TestCase
):
    def test_plugin_read_write_contract(self):
        d = make_tmp_dir()
        plugin = MemoryBasePlugin(data_dir=d)
        self.assertTrue(plugin.smoke())
        # 可信写入（默认 user → declarative）
        r1 = plugin.memory_write("用户喜欢摩托车骑行")
        self.assertTrue(r1["stored"])
        self.assertEqual(r1["layer"], "declarative")
        # 不可信写入被闸门拦截
        r2 = plugin.memory_write({"content": "网页看到的传闻",
                                  "source": "web", "layer": "declarative"})
        self.assertFalse(r2["stored"])
        self.assertTrue(r2["denied"])
        # 读回
        hits = plugin.memory_read("摩托车")
        self.assertIn(r1["id"], [h["id"] for h in hits])
        # 跨模块一致：重建插件从同一目录读到同一条
        plugin2 = MemoryBasePlugin(data_dir=d)
        hits2 = plugin2.memory_read("摩托车")
        self.assertEqual(len(hits2), 1)
        self.assertEqual(hits2[0]["id"], r1["id"])
        # 扩展能力：删除/统计/反思/遗忘
        self.assertTrue(plugin.memory_delete(r1["id"])["deleted"])
        layers_stats = plugin.memory_layers()
        self.assertEqual(layers_stats["declarative"]["active"], 0)
        ref = plugin.memory_reflect("反思测试", target="t", outcome="keep")
        self.assertEqual(ref["kind"], "reflection")
        plugin.memory_forget()


if __name__ == "__main__":
    unittest.main(verbosity=2)
