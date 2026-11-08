"""L10 范式引擎——LangGraph 图状态机（审批门 + 审计留痕）。

对齐底座：实现 openjarvis.learning._stubs.RouterPolicy（模型路由策略），
同时承担任务编排：LangGraph StateGraph 建图，节点执行前强制过
ApprovalGate，状态转换追加 AuditTrail。

接线范式（tech-progression-plan §2）：
1. 接口对齐：RouterPolicy.select_model(context) -> model_key
2. 注册接入：OrchestrationRegistry.register("langgraph", engine, resident=True)
3. 审批门：approval_gate 节点前置，未批准节点 hold
4. 审计留痕：AuditTrail 记录每次节点执行/审批决策
5. 锁版本：langgraph 1.2.17（wheels 缓存）

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Callable, Dict, List, Optional

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph
from typing_extensions import TypedDict

from openjarvis.learning._stubs import RouterPolicy
from openjarvis.core.types import RoutingContext

from .audit import AuditTrail
from .registry import OrchestrationRegistry


class WorkflowState(TypedDict, total=False):
    """LangGraph 图状态（任务编排上下文）。"""

    workflow_id: str
    current_node: str
    inputs: Dict[str, Any]
    query: str
    outputs: Dict[str, Any]
    status: str  # running | hold | completed | error
    history: List[str]
    approval_required: bool
    approved: bool
    approver: str


class StepResult:
    """节点执行结果。"""

    def __init__(self, outputs: Optional[Dict[str, Any]] = None, *, error: str = ""):
        self.outputs = outputs or {}
        self.error = error

    @property
    def ok(self) -> bool:
        return not self.error


class ApprovalGate:
    """审批门：节点执行前的强制审批检查。

    默认 deny-on-unapproved（fail-closed）：未显式批准即 hold，
    不进入节点执行。
    """

    def __init__(self, *, approver: str = "system", auto_approve: bool = False):
        self._approver = approver
        self._auto_approve = auto_approve
        self._approved_nodes: set[str] = set()

    def require(self, node: str) -> None:
        """登记需要审批的节点。"""
        if self._auto_approve:
            self._approved_nodes.add(node)

    def approve(self, node: str, approver: str = "system") -> None:
        """批准节点执行（写入审批人）。"""
        self._approved_nodes.add(node)
        self._approver = approver

    def is_approved(self, node: str) -> bool:
        return node in self._approved_nodes

    def reset(self) -> None:
        self._approved_nodes.clear()


class LangGraphStateMachine(RouterPolicy):
    """基于 LangGraph 的范式引擎。

    双重角色：
    - 模型路由（RouterPolicy ABC）：按复杂度路由 qwen3-8b-uncensored 等本地模型
    - 任务编排：StateGraph 建图 + 审批门 + 审计留痕

    Parameters
    ----------
    engine_key:
        注册表键（默认 "langgraph"）。
    log_path:
        审计 JSONL 落盘路径；None 仅内存。
    auto_approve:
        是否自动审批所有节点（演示/调试用，默认 False = fail-closed）。
    """

    def __init__(
        self,
        *,
        engine_key: str = "langgraph",
        log_path: Optional[str] = None,
        auto_approve: bool = False,
    ) -> None:
        self._key = engine_key
        self._audit = AuditTrail(log_path)
        self._gate = ApprovalGate(auto_approve=auto_approve)
        self._graph: Optional[CompiledStateGraph] = None
        self._node_handlers: Dict[str, Callable[[WorkflowState], Any]] = {}
        self._approval_required: set[str] = set()
        self._model_keys = ("qwen3-8b-uncensored", "qwen2.5:14b", "qwen2.5:7b")

        # 幂等注册：同 key 已注册时跳过（同进程多次实例化合法）
        if not OrchestrationRegistry.is_registered(self._key):
            OrchestrationRegistry.register(
                self._key,
                self,
                resident=True,
                description="L10 范式引擎（LangGraph 图状态机，驻留）",
            )

    # ------------------------------------------------------------------
    # RouterPolicy ABC：模型路由
    # ------------------------------------------------------------------
    def select_model(self, context: RoutingContext) -> str:
        """按复杂度路由本地模型（复杂度越高用越大模型）。"""
        c = context.complexity_score
        if c >= 0.66:
            return self._model_keys[0]
        if c >= 0.33:
            return self._model_keys[1]
        return self._model_keys[2]

    # ------------------------------------------------------------------
    # 图构建
    # ------------------------------------------------------------------
    def add_node(self, name: str, handler: Callable[[WorkflowState], Any]) -> None:
        """注册节点处理函数（LangGraph 节点）。"""
        self._node_handlers[name] = handler

    def add_approval_required(self, node: str) -> None:
        """标记节点需要审批（fail-closed：未批准即 hold）。"""
        self._approval_required.add(node)
        if self._gate._auto_approve:
            self._gate.approve(node)

    def is_approved(self, node: str) -> bool:
        """审批通过判定：普通节点默认放行，审批节点需显式批准。"""
        if node not in self._approval_required:
            return True
        return self._gate.is_approved(node)

    def build(
        self,
        nodes: List[str],
        edges: Dict[str, List[str]],
        *,
        entry: str,
        approval_required: Optional[List[str]] = None,
    ) -> None:
        """构建 LangGraph 图。

        Parameters
        ----------
        nodes:
            全部节点名（必须已 add_node）。
        edges:
            {from_node: [to_node, ...]}；END 用 None 表示终止。
        entry:
            入口节点。
        approval_required:
            需要审批的节点清单。
        """
        for n in (approval_required or []):
            self.add_approval_required(n)

        g = StateGraph(WorkflowState)

        # 入口包装：审计进入
        def _entry(state: WorkflowState) -> WorkflowState:
            state.setdefault("workflow_id", uuid.uuid4().hex[:12])
            state["status"] = "running"
            state["history"] = state.get("history", []) + [f"START->{entry}"]
            self._audit.append(
                state["workflow_id"], "START", f"->{entry}",
                "completed", approver="engine",
            )
            return state

        for name in nodes:
            handler = self._node_handlers[name]

            def _make(name=name, handler=handler):
                def _node(state: WorkflowState) -> WorkflowState:
                    state["current_node"] = name
                    state["history"] = state.get("history", []) + [name]

                    # 审批门（fail-closed：审批节点未批准一律 hold）
                    if not self.is_approved(name):
                        state["status"] = "hold"
                        self._audit.append(
                            state["workflow_id"], name, "->HOLD",
                            "hold", approver=self._gate._approver,
                            detail={"reason": "approval_required"},
                        )
                        return state

                    try:
                        result = handler(state)
                        if isinstance(result, StepResult):
                            if not result.ok:
                                state["status"] = "error"
                                self._audit.append(
                                    state["workflow_id"], name, "->ERROR",
                                    "error", approver="engine",
                                    detail={"error": result.error},
                                )
                                return state
                            merged = dict(result.outputs)
                            state.setdefault("outputs", {}).update(merged)
                        elif isinstance(result, dict):
                            # 支持 dict 返回的显式中止约定：
                            #   {"_error": msg}  -> error
                            #   {"_hold": msg}   -> hold
                            merged = dict(result)
                            if "_error" in merged:
                                err = merged.pop("_error")
                                state.setdefault("outputs", {}).update(merged)
                                state["status"] = "error"
                                self._audit.append(
                                    state["workflow_id"], name, "->ERROR",
                                    "error", approver="engine",
                                    detail={"error": str(err)},
                                )
                                return state
                            if "_hold" in merged:
                                reason = merged.pop("_hold")
                                state.setdefault("outputs", {}).update(merged)
                                state["status"] = "hold"
                                self._audit.append(
                                    state["workflow_id"], name, "->HOLD",
                                    "hold", approver="engine",
                                    detail={"reason": str(reason)},
                                )
                                return state
                            state.setdefault("outputs", {}).update(merged)
                        state["status"] = "completed"
                        self._audit.append(
                            state["workflow_id"], name, "->completed",
                            "completed", approver="engine",
                        )
                    except Exception as exc:  # noqa: BLE001
                        state["status"] = "error"
                        self._audit.append(
                            state["workflow_id"], name, "->ERROR",
                            "error", approver="engine",
                            detail={"error": str(exc)},
                        )
                    return state

                return _node

            g.add_node(name, _make())

        g.add_node("__entry__", _entry)
        g.set_entry_point("__entry__")
        g.add_edge("__entry__", entry)

        # 条件路由：节点 hold/error 时终止（审批门 fail-closed 的真正语义），
        # 否则走正常边。LangGraph 声明式图必须用条件边才能中断后续执行。
        for frm, tos in edges.items():
            if not tos:
                g.add_edge(frm, END)
                continue

            path_map = {"__TERMINAL__": END}
            for to in tos:
                path_map[to] = to

            def _router(state, _tos=tos):
                if state.get("status") in ("hold", "error"):
                    return "__TERMINAL__"
                # fan-out 不在本方案范围，取首个目标
                return _tos[0]

            g.add_conditional_edges(frm, _router, path_map)

        self._graph = g.compile()
        return self

    def run(self, inputs: Optional[Dict[str, Any]] = None) -> WorkflowState:
        """执行图（同步）。"""
        if self._graph is None:
            raise RuntimeError("LangGraphStateMachine 尚未 build()")
        return self._graph.invoke(inputs or {})

    # ------------------------------------------------------------------
    # 查询与快照
    # ------------------------------------------------------------------
    def approve(self, node: str, approver: str = "system") -> None:
        self._gate.approve(node, approver)

    def audit(self) -> AuditTrail:
        return self._audit

    def snapshot(self) -> dict:
        return {
            "engine": self._key,
            "resident": OrchestrationRegistry.is_resident(self._key),
            "graph_built": self._graph is not None,
            "nodes": sorted(self._node_handlers.keys()),
            "approval_required": sorted(self._approval_required),
            "audit_entries": self._audit.count(),
            "model_keys": list(self._model_keys),
        }


__all__ = ["ApprovalGate", "LangGraphStateMachine", "StepResult", "WorkflowState"]
