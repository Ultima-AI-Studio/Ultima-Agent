r"""M4 范式拼装出口验收测试（LangGraph 图状态机）。

覆盖：
1. LangGraphStateMachine 构建与运行（真实图状态机）
2. 审批门强制：标记审批节点未批准即 hold（fail-closed）
3. 审批通过后节点执行完成
4. 状态转换审计留痕（AuditTrail 记录每次转换）
5. OrchestrationRegistry 驻留标记（unload 拒绝）
6. RouterPolicy ABC 契约（select_model 按复杂度路由）

运行（项目根目录）：
    H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\brain\orchestration\tests -p "test_*.py" -v
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
LIBS_BASE = ROOT / "libs" / "base" / "openjarvis" / "src"
if str(LIBS_BASE) not in sys.path:
    sys.path.insert(0, str(LIBS_BASE))

from openjarvis.learning._stubs import RouterPolicy  # noqa: E402
from openjarvis.core.types import RoutingContext  # noqa: E402

from src.brain.orchestration import (  # noqa: E402
    LangGraphStateMachine,
    OrchestrationRegistry,
    ResidencyViolationError,
    StepResult,
)


def _collect(state):
    got = state.setdefault("outputs", {})
    got.setdefault("items", []).append("collect")
    return {"items": got["items"]}


def _analyze(state):
    got = state.setdefault("outputs", {})
    got.setdefault("items", []).append("analyze")
    return {"items": got["items"]}


def _finish(state):
    got = state.setdefault("outputs", {})
    got.setdefault("items", []).append("finish")
    return {"items": got["items"]}


class TestLangGraphStateMachine(unittest.TestCase):
    def setUp(self) -> None:
        OrchestrationRegistry.reset()
        self.engine = LangGraphStateMachine(engine_key="langgraph")

    def tearDown(self) -> None:
        OrchestrationRegistry.reset()

    # ------------------------------------------------------------------
    def test_is_router_policy(self) -> None:
        self.assertIsInstance(self.engine, RouterPolicy)

    def test_select_model_routes_by_complexity(self) -> None:
        low = RoutingContext(query="hi", complexity_score=0.1)
        mid = RoutingContext(query="x", complexity_score=0.5)
        high = RoutingContext(query="x", complexity_score=0.9)
        self.assertEqual(self.engine.select_model(low), "qwen2.5:7b")
        self.assertEqual(self.engine.select_model(mid), "qwen2.5:14b")
        self.assertEqual(self.engine.select_model(high), "qwen3-8b-uncensored")

    # ------------------------------------------------------------------
    def test_approval_gate_blocks_unapproved(self) -> None:
        self.engine.add_node("collect", _collect)
        self.engine.add_node("analyze", _analyze)
        self.engine.add_node("finish", _finish)
        self.engine.add_approval_required("analyze")  # 只标记 analyze
        self.engine.build(
            ["collect", "analyze", "finish"],
            {"collect": ["analyze"], "analyze": ["finish"], "finish": []},
            entry="collect",
        )
        state = self.engine.run()
        # analyze 未批准 → hold
        self.assertEqual(state.get("status"), "hold")
        self.assertIn("analyze", state.get("history", []))

    def test_approved_node_executes(self) -> None:
        self.engine.add_node("collect", _collect)
        self.engine.add_node("analyze", _analyze)
        self.engine.add_node("finish", _finish)
        self.engine.add_approval_required("analyze")
        self.engine.approve("analyze", approver="auditor-1")
        self.engine.build(
            ["collect", "analyze", "finish"],
            {"collect": ["analyze"], "analyze": ["finish"], "finish": []},
            entry="collect",
        )
        state = self.engine.run()
        self.assertEqual(state.get("status"), "completed")
        self.assertEqual(state.get("outputs", {}).get("items"),
                         ["collect", "analyze", "finish"])

    def test_auto_approve_passes_all(self) -> None:
        eng = LangGraphStateMachine(engine_key="lg-auto", auto_approve=True)
        eng.add_node("a", lambda s: {"ok": True})
        eng.add_approval_required("a")
        eng.build(["a"], {"a": []}, entry="a")
        state = eng.run()
        self.assertEqual(state.get("status"), "completed")

    # ------------------------------------------------------------------
    def test_audit_trail_records_transitions(self) -> None:
        self.engine.add_node("collect", _collect)
        self.engine.add_node("finish", _finish)
        self.engine.build(
            ["collect", "finish"],
            {"collect": ["finish"], "finish": []},
            entry="collect",
        )
        self.engine.run()
        records = self.engine.audit().records()
        self.assertGreaterEqual(len(records), 3)  # START + collect + finish
        decisions = self.engine.audit().decisions()
        self.assertNotIn("hold", decisions)

    def test_audit_hold_recorded(self) -> None:
        self.engine.add_node("collect", _collect)
        self.engine.add_node("analyze", _analyze)
        self.engine.add_approval_required("analyze")
        self.engine.build(
            ["collect", "analyze"],
            {"collect": ["analyze"], "analyze": []},
            entry="collect",
        )
        self.engine.run()
        self.assertIn("hold", self.engine.audit().decisions())

    # ------------------------------------------------------------------
    def test_registered_and_resident(self) -> None:
        self.assertTrue(OrchestrationRegistry.is_resident("langgraph"))
        self.assertIn("langgraph", OrchestrationRegistry.keys())

    def test_resident_cannot_unload(self) -> None:
        with self.assertRaises(ResidencyViolationError):
            OrchestrationRegistry.unload("langgraph")

    def test_dict_error_interrupts_chain(self) -> None:
        """dict 返回含 _error 键 → 节点 error，后续节点不执行。"""
        self.engine.add_node("check", lambda s: {"_error": "guard blocked"})
        self.engine.add_node("after", lambda s: {"ran": True})
        self.engine.build(
            ["check", "after"],
            {"check": ["after"], "after": []},
            entry="check",
        )
        state = self.engine.run()
        self.assertEqual(state.get("status"), "error")
        self.assertNotIn("ran", state.get("outputs", {}))

    def test_dict_hold_interrupts_chain(self) -> None:
        """dict 返回含 _hold 键 → 节点 hold，后续节点不执行。"""
        self.engine.add_node("pause", lambda s: {"_hold": "need approval"})
        self.engine.add_node("after", lambda s: {"ran": True})
        self.engine.build(
            ["pause", "after"],
            {"pause": ["after"], "after": []},
            entry="pause",
        )
        state = self.engine.run()
        self.assertEqual(state.get("status"), "hold")
        self.assertNotIn("ran", state.get("outputs", {}))

    def test_unregistered_key_is_not_resident(self) -> None:
        self.assertFalse(OrchestrationRegistry.is_resident("no-such-key"))

    def test_duplicate_register_raises(self) -> None:
        with self.assertRaises(ValueError):
            OrchestrationRegistry.register("langgraph", object(), resident=True)

    def test_snapshot(self) -> None:
        snap = self.engine.snapshot()
        self.assertEqual(snap["engine"], "langgraph")
        self.assertTrue(snap["resident"])
        self.assertFalse(snap["graph_built"])
        self.assertEqual(snap["model_keys"][0], "qwen3-8b-uncensored")


if __name__ == "__main__":
    unittest.main(verbosity=2)
