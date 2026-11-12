"""s4-brain-loop 主脑决策回路测试（M01 + TD-05 参数契约）。

验收口径（tasks/cards/s4-brain-loop/task.md）：
- ACCEPT-1 全链端到端；ACCEPT-2 下发参数七字段；ACCEPT-3 返回明细结构查；
- ACCEPT-4 四查各自可触发；ACCEPT-5 路由分工接口；ACCEPT-6 入口兼容；
- ACCEPT-7 回执字段完整（ReceiptValidator 在验收脚本单独校验）。

全部数据落 tempfile 临时目录，不污染真实库。
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from src.brain.loop.brain_loop import BrainLoop, Correctors, ExternalExecutorStub
from src.brain.loop.params import ExecutionParams, PARAM_KEYS, REPORT_KEYS
from src.brain.guardrails.paradigm import ParadigmGate
from src.brain.orchestration.queue import TaskQueue
from src.brain.guardrails.scope import ScopePolicy
from src.brain.guardrails.audit_log import AppendOnlyAuditLog
from src.brain.memory.layers import MemoryLayers
from src.brain.display.behavior import BehaviorMapper


def _make_loop(tmp: Path, executor=None) -> BrainLoop:
    scope = ScopePolicy(cap=["exec.run", "ultima_task_query"], dev=["read"], cred=[])
    return BrainLoop(
        tmp,
        gate=ParadigmGate(),
        queue=TaskQueue(tmp / "queue"),
        scope=scope,
        audit=AppendOnlyAuditLog(tmp / "audit.jsonl"),
        memory=MemoryLayers(tmp / "memory"),
        behavior=BehaviorMapper(),
        executor=executor if executor is not None else ExternalExecutorStub().run,
    )


class TestBrainLoopS4(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    # ACCEPT-1：全链端到端
    def test_accept1_full_chain(self) -> None:
        loop = _make_loop(self.root)
        result = loop.run("查询任务状态", entry="voice")
        self.assertEqual(result.status, "approved")
        self.assertIsNotNone(result.task_id)
        # 任务到回执
        rec = loop.queue._tasks[result.task_id]
        self.assertEqual(rec.phase, "回执")
        # 审计留痕（每环 append）
        self.assertGreater(len(result.audit_ids), 10)
        # 记忆归档
        self.assertTrue(result.memory_archived)
        # 呈现（行为层状态）
        self.assertIsNotNone(result.presentation)
        self.assertIn("state", result.presentation)

    # ACCEPT-2：下发参数七字段齐全
    def test_accept2_params_complete(self) -> None:
        loop = _make_loop(self.root)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "approved")
        params = result.params.as_dict()
        self.assertEqual(set(PARAM_KEYS), set(params.keys()))
        for key in PARAM_KEYS:
            self.assertIn(key, params)

    # ACCEPT-3：返回明细结构查（缺明细打回）
    def test_accept3_report_structure(self) -> None:
        def bad_executor(task, params):
            return {"model": "stub", "actual_turns": 1}  # 缺 trace/self_check/over_limits 等
        loop = _make_loop(self.root, executor=bad_executor)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "replanned")
        checks = {v.check: v.passed for v in result.verdicts}
        self.assertFalse(checks["structure"])

    # ACCEPT-4a：方向查（自评未达标打回）
    def test_accept4_direction(self) -> None:
        def bad_executor(task, params):
            report = ExternalExecutorStub().run(task, params)
            report["self_check"] = {"gate": "fail"}
            return report
        loop = _make_loop(self.root, executor=bad_executor)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "replanned")
        checks = {v.check: v.passed for v in result.verdicts}
        self.assertFalse(checks["direction"])

    # ACCEPT-4b：权限查（动作越界拒绝）
    def test_accept4_permission(self) -> None:
        def bad_executor(task, params):
            report = ExternalExecutorStub().run(task, params)
            report["trace"][1] = {"segment": "ACTION", "tool": "rm"}
            return report
        loop = _make_loop(self.root, executor=bad_executor)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "rejected")
        checks = {v.check: v.passed for v in result.verdicts}
        self.assertFalse(checks["permission"])

    # ACCEPT-4c：一致性查（与记忆冲突拒绝）
    def test_accept4_consistency(self) -> None:
        def bad_executor(task, params):
            report = ExternalExecutorStub().run(task, params)
            report["trace"][3] = {"segment": "FINAL", "content": "包含危险指令的文本"}
            return report
        loop = _make_loop(self.root, executor=bad_executor)
        result = loop.run("查询任务状态",
                          context={"memory_digest": {"forbidden": ["危险"]}})
        self.assertEqual(result.status, "rejected")
        checks = {v.check: v.passed for v in result.verdicts}
        self.assertFalse(checks["consistency"])

    # ACCEPT-4d：结构查（缺字段打回）
    def test_accept4_structure(self) -> None:
        def bad_executor(task, params):
            report = ExternalExecutorStub().run(task, params)
            del report["over_limits"]
            return report
        loop = _make_loop(self.root, executor=bad_executor)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "replanned")
        checks = {v.check: v.passed for v in result.verdicts}
        self.assertFalse(checks["structure"])

    # ACCEPT-5：本地/外部路由分工接口（替换执行端即真实路由接线点）
    def test_accept5_router_interface(self) -> None:
        def custom_executor(task, params):
            report = ExternalExecutorStub().run(task, params)
            report["model"] = "external-router"
            report["actual_turns"] = 3
            report["tokens"] = 4096
            return report
        loop = _make_loop(self.root, executor=custom_executor)
        result = loop.run("查询任务状态")
        self.assertEqual(result.status, "approved")
        self.assertEqual(result.report["model"], "external-router")
        self.assertEqual(result.report["actual_turns"], 3)

    # ACCEPT-6：入口兼容（cli/voice/im 均通过）
    def test_accept6_entry_compat(self) -> None:
        loop = _make_loop(self.root)
        for entry in ("cli", "voice", "im"):
            result = loop.run("查询任务状态", entry=entry)
            self.assertEqual(result.status, "approved", entry)

    # ACCEPT-7：回执字段完整（ReceiptValidator 在验收脚本复核）
    def test_accept7_receipt_fields(self) -> None:
        loop = _make_loop(self.root)
        result = loop.run("查询任务状态")
        data = result.as_dict()
        for key in ("query", "entry", "status", "execution_params", "execution_report",
                    "verdicts", "loop_trace", "reason"):
            self.assertIn(key, data)
        self.assertEqual(data["execution_report"]["self_check"]["gate"], "pass")

    # Correctors 单测
    def test_correctors(self) -> None:
        good = ExternalExecutorStub().run({"title": "t", "goal": "g"}, ExecutionParams())
        self.assertTrue(Correctors.direction_check("g", good).passed)
        self.assertTrue(Correctors.permission_check(good, ("none",)).passed)
        self.assertTrue(Correctors.consistency_check(good, {"forbidden": ["绝不出现XYZ"]}).passed)
        self.assertFalse(Correctors.consistency_check(good, {"forbidden": ["stub-executor"]}).passed)
        self.assertTrue(Correctors.structure_check(good).passed)
        self.assertFalse(Correctors.structure_check({"model": "m"}).passed)


if __name__ == "__main__":
    unittest.main()
