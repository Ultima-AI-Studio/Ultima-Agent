# -*- coding: utf-8 -*-
"""适配器单测（T3 AD-04/AD-06）：底座四段映射 + 错误码映射。

标准 unittest 结构（discover 可收集；脚本式 sys.exit 结构已废弃）。
运行：python -X utf8 -m unittest tests.test_adapters -v
      或：python -X utf8 tests\\test_adapters.py
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # src/brain

from orchestration.adapters import error_payload, map_exception_to_error_code, map_structured_to_contract


class StorageError(Exception):
    pass


class SecurityBlockError(Exception):
    pass


class RateLimitError(Exception):
    pass


class ModuleNotFoundError(Exception):
    pass


class OtherError(Exception):
    pass


class AdapterContractTests(unittest.TestCase):
    """AD-04 底座四段 → 契约四段映射 + AD-06 错误码映射。"""

    # ── AD-04：底座四段 → 契约四段 ─────────────────────────────
    def test_ad04_four_segment_mapping(self) -> None:
        sample = (
            "THOUGHT: 用户查询任务状态，先读队列快照\n"
            "TOOL: read_queue\n"
            "INPUT: {scope: all}\n"
            "FINAL_ANSWER: 当前共 0 个任务。"
        )
        mapped = map_structured_to_contract(sample)
        self.assertEqual(mapped["THOUGHT"], "用户查询任务状态，先读队列快照")
        self.assertEqual(mapped["ACTION"], "read_queue")
        self.assertEqual(mapped["OBSERVE"], "{scope: all}")
        self.assertEqual(mapped["FINAL"], "当前共 0 个任务。")

    def test_ad04_partial_without_final(self) -> None:
        partial = "THOUGHT: 思考中\nTOOL: think\nINPUT: 参数"
        mapped = map_structured_to_contract(partial)
        self.assertIsNone(mapped["FINAL"])
        self.assertEqual(mapped["OBSERVE"], "参数")

    # ── AD-06：错误码映射 ─────────────────────────────────────
    def test_ad06_error_code_mapping(self) -> None:
        self.assertEqual(map_exception_to_error_code(StorageError()), "E-6xx")
        self.assertEqual(map_exception_to_error_code(SecurityBlockError()), "E-403")
        self.assertEqual(map_exception_to_error_code(RateLimitError()), "E-429")
        self.assertEqual(map_exception_to_error_code(ModuleNotFoundError()), "E-7xx")
        self.assertEqual(map_exception_to_error_code(OtherError()), "E-5xx")

    def test_ad06_error_payload(self) -> None:
        payload = error_payload(StorageError("索引损坏"))
        self.assertIn("E-6xx", payload["code"])
        self.assertIn("StorageError", payload["type"])
        self.assertIn("索引损坏", payload["message"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
