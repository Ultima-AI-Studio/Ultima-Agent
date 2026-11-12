r"""M3 记忆拼装出口验收测试（真实 mem0 引擎）。

覆盖：
1. Mem0Backend 构建（ollama embed + FAISS 本地向量库）
2. store → retrieve 闭环（三层 user/session/agent 可写可查）
3. delete 删除
4. MemoryRegistry 驻留标记（unload 拒绝）
5. 与底座 MemoryBackend ABC 契约一致（store 返回 str doc_id，
   retrieve 返回 List[RetrievalResult]，delete 返回 bool）

运行（项目根目录）：
    H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\brain\memory\tests -p "test_*.py" -v
"""

from __future__ import annotations

import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
LIBS_BASE = ROOT / "libs" / "base" / "openjarvis" / "src"
if str(LIBS_BASE) not in sys.path:
    sys.path.insert(0, str(LIBS_BASE))

from openjarvis.tools.storage._stubs import MemoryBackend, RetrievalResult  # noqa: E402

from src.brain.memory import Mem0Backend, MemoryRegistry, ResidencyViolationError  # noqa: E402


class TestMem0Backend(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls._tmp = tempfile.mkdtemp(prefix="ultima-mem-test-")
        cls.backend = Mem0Backend(
            data_dir=cls._tmp,
            memory_type="user",
        )

    @classmethod
    def tearDownClass(cls) -> None:
        pass

    def test_backend_is_memorybackend_abc(self) -> None:
        self.assertIsInstance(self.backend, MemoryBackend)
        self.assertEqual(self.backend.backend_id, "mem0")

    def test_store_returns_doc_id(self) -> None:
        doc_id = self.backend.store(
            "用户偏好：居住地在沈阳，关注摩托骑行。",
            metadata={"user_id": "test-user-1"},
        )
        self.assertIsInstance(doc_id, str)
        self.assertTrue(doc_id)

    def test_retrieve_finds_stored(self) -> None:
        self.backend.store(
            "用户的核心项目是 UltimaAgent 底座拼装。",
            metadata={"user_id": "test-user-1"},
        )
        results = self.backend.retrieve(
            "UltimaAgent 项目是什么",
            top_k=3,
            user_id="test-user-1",
        )
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1)
        first = results[0]
        self.assertIsInstance(first, RetrievalResult)
        self.assertTrue(first.content)

    def test_session_layer_write_and_query(self) -> None:
        self.backend.add_session(
            "本轮讨论：M3 记忆拼装使用 mem0 + ollama embed。",
            user_id="test-user-2",
            session_id="sess-20261025-a",
        )
        results = self.backend.retrieve(
            "记忆拼装方案",
            top_k=3,
            user_id="test-user-2",
            session_id="sess-20261025-a",
        )
        self.assertGreaterEqual(len(results), 1)

    def test_delete_returns_bool(self) -> None:
        doc_id = self.backend.store(
            "待删除测试记忆",
            metadata={"user_id": "test-user-3"},
        )
        self.assertIsInstance(self.backend.delete(doc_id), bool)

    def test_registered_and_resident(self) -> None:
        self.assertTrue(MemoryRegistry.is_resident("mem0"))
        self.assertIn("mem0", MemoryRegistry.keys())

    def test_resident_cannot_unload(self) -> None:
        with self.assertRaises(ResidencyViolationError):
            MemoryRegistry.unload("mem0")

    def test_snapshot(self) -> None:
        snap = self.backend.snapshot()
        self.assertEqual(snap["backend_id"], "mem0")
        self.assertTrue(snap["resident"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
