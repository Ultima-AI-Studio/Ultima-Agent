"""主脑决策回路（s4-brain-loop · M01）。

把决策回路串接为一条真实可跑的链路，并落地执行参数契约（TD-05）：

    受理 → 意图 → 领域 → 范式 → 规划 → 派发 → 闸门 → 执行
    → 审计(四查三态) → 编排 → 表达 → 呈现 → 记忆归档

对齐：
- product-plan v2.3 L0-L10 验收口径（L10 范式前置、L8 闸门、L9 记忆归档）；
- docs/specs/execution-param-contract.md v0.1-draft（下发带参数 + 返回带明细
  + 审计校正四查三态）；
- 复用既有组件：TaskQueue（s3-orchestrator）、ParadigmGate（s3-guard-resident）、
  ScopePolicy（s3-guard-resident）、AppendOnlyAuditLog（s3-audit-trail）、
  MemoryLayers（s3-memory-base）、BehaviorMapper（s3-behavior-layer）。

设计约束：
- 14B 主脑是编排者：下发参数 + 审计返回；深度执行外发（本批次用确定性外部
  执行桩 ExternalExecutorStub，真实外部大模型路由预留接线点）；
- 不修改冻结参数基线；不绕过闸门/审计；
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

try:
    from ..events import emit_event
except ImportError:  # 兼容 src/brain 在 sys.path 时的顶层 loop 包
    from events import emit_event

from .params import (
    ExecutionParams,
    ParamContractError,
    validate_params,
    validate_report,
)

# 任务闭环阶段（与 queue.PHASES 对齐，编排环节使用）
TASK_PHASES = ("立项", "排队", "派发", "执行", "自检", "审计", "回执")

_PARADIGM_RINGS = ("intent", "domain", "layout", "style", "motion", "present", "report")
logger = logging.getLogger(__name__)


def _emit_safely(event_type: str, data: dict[str, Any]) -> None:
    try:
        emit_event(event_type, data)
    except Exception as exc:  # noqa: BLE001 - 可观测性不得阻断决策回路
        logger.warning("event emission failed: %s", exc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _new_flow_id() -> str:
    return f"flow-{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# 审计校正（四查三态）
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class Correction:
    """一次审计校正结果（四查之一）。"""

    passed: bool
    check: str      # direction | permission | consistency | structure
    reason: str
    remedy: str = ""


class Correctors:
    """审计校正四查：方向 / 权限 / 一致性 / 结构。"""

    @staticmethod
    def direction_check(target: str, report: dict[str, Any]) -> Correction:
        """方向查：返回是否偏离任务目标。"""
        self_check = report.get("self_check")
        if not isinstance(self_check, dict):
            return Correction(False, "direction", "返回缺 self_check，无法判定方向", "打回重算：补 self_check 并对照目标")
        gate = self_check.get("gate")
        if gate != "pass":
            return Correction(False, "direction", f"自评未达标（gate={gate!r}）", "打回重算：对照任务目标重出方案")
        if not target or not str(target).strip():
            return Correction(False, "direction", "任务目标为空，方向无法判定", "打回重算：补齐任务目标")
        return Correction(True, "direction", "方向未偏离（自评达标）")

    @staticmethod
    def permission_check(report: dict[str, Any], allowlist: tuple[str, ...]) -> Correction:
        """权限查：动作/工具是否在白名单内。

        trace 缺失视为结构问题（由 structure_check 兜底打回），不在此判拒绝；
        仅 trace 存在且 ACTION 工具越界时才拒绝。
        """
        trace = report.get("trace")
        if not isinstance(trace, list):
            return Correction(True, "permission", "trace 缺失，动作审计跳过（结构查兜底）")
        used: list[str] = []
        for step in trace:
            if isinstance(step, dict) and step.get("segment") == "ACTION":
                tool = step.get("tool") or step.get("action")
                if tool and tool != "none":
                    used.append(str(tool))
        out_of = [tool for tool in used if tool not in allowlist]
        if out_of:
            return Correction(False, "permission", f"动作越界（不在白名单）: {sorted(set(out_of))}",
                              "拒绝：越界动作不执行，本地处理或征询")
        return Correction(True, "permission", "动作均在白名单内")

    @staticmethod
    def consistency_check(report: dict[str, Any], memory_digest: Optional[dict[str, Any]]) -> Correction:
        """一致性查：与本地记忆/档案/状态是否冲突。"""
        if not memory_digest:
            return Correction(True, "consistency", "无记忆摘要，一致性放行（基础规则）")
        forbidden = memory_digest.get("forbidden", [])
        text = json.dumps(report, ensure_ascii=False)
        hit = [flag for flag in forbidden if flag and flag in text]
        if hit:
            return Correction(False, "consistency", f"与记忆冲突标记冲突: {hit}", "拒绝：冲突不执行，征询用户")
        return Correction(True, "consistency", "与本地记忆一致")

    @staticmethod
    def structure_check(report: dict[str, Any]) -> Correction:
        """结构查：输出合规 + 参数明细齐全（缺=打回）。"""
        try:
            missing = validate_report(report)
        except (ParamContractError, TypeError) as exc:
            return Correction(False, "structure", f"结构非法: {exc}", "打回重算：按 execution_report 六字段回传")
        if missing:
            return Correction(False, "structure", f"参数明细缺失: {missing}",
                              f"打回重算：补齐 execution_report.{'.'.join(missing)}")
        return Correction(True, "structure", "结构与参数明细齐全")


# ---------------------------------------------------------------------------
# 外部执行桩（本批次确定性执行；真实外部模型路由预留接线点）
# ---------------------------------------------------------------------------
class ExternalExecutorStub:
    """确定性外部执行端：按参数契约回传 execution_report（可断言）。

    真实外部大模型路由接线点：替换 run() 内部实现即可（模型名/轮次/token
    消耗/trace 留痕来自真实调用），参数契约与审计校正逻辑不变。
    """

    def run(self, task: dict[str, Any], params: ExecutionParams) -> dict[str, Any]:
        allowlist = params.tools_allowlist
        action_tool = allowlist[0] if allowlist else "none"
        gate = dict(params.acceptance_gate or {})
        gate["result"] = "pass"
        return {
            "model": "stub-executor",
            "actual_turns": 1,
            "tokens": 0,
            "trace": [
                {"segment": "THOUGHT", "content": f"目标：{task.get('goal', '')}"},
                {"segment": "ACTION", "tool": action_tool},
                {"segment": "OBSERVE", "content": "桩观察：执行成功"},
                {"segment": "FINAL", "content": f"完成 {task.get('title', '')}"},
            ],
            "self_check": {"gate": "pass", "note": "确定性执行桩"},
            "over_limits": None,
        }


# ---------------------------------------------------------------------------
# 回路结果
# ---------------------------------------------------------------------------
@dataclass
class LoopResult:
    query: str
    entry: str
    status: str                     # approved | rejected | replanned
    task_id: Optional[str]
    params: ExecutionParams
    report: Optional[dict[str, Any]]
    verdicts: list[Correction] = field(default_factory=list)
    audit_ids: list[str] = field(default_factory=list)
    memory_archived: bool = False
    presentation: Optional[dict[str, Any]] = None
    reason: str = ""
    loop_trace: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "query": self.query, "entry": self.entry, "status": self.status,
            "task_id": self.task_id, "execution_params": self.params.as_dict(),
            "execution_report": self.report, "verdicts": [
                {"check": v.check, "passed": v.passed, "reason": v.reason} for v in self.verdicts
            ],
            "audit_ids": self.audit_ids, "memory_archived": self.memory_archived,
            "presentation": self.presentation, "reason": self.reason,
            "loop_trace": self.loop_trace,
        }


# ---------------------------------------------------------------------------
# 主脑决策回路
# ---------------------------------------------------------------------------
class BrainLoop:
    """主脑决策回路：受理 → 意图 → 领域 → 范式 → 规划 → 派发 → 闸门
    → 执行 → 审计(四查三态) → 编排 → 表达 → 呈现 → 记忆归档。"""

    def __init__(
        self,
        data_dir: str | Path,
        *,
        gate: Any = None,
        queue: Any = None,
        scope: Any = None,
        audit: Any = None,
        memory: Any = None,
        behavior: Any = None,
        executor: Optional[Callable[[dict[str, Any], ExecutionParams], dict[str, Any]]] = None,
        resolve_domain: Optional[Callable[[str], str]] = None,
        parse_intent: Optional[Callable[[str], dict[str, Any]]] = None,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        # 默认组件（可注入替换；全部用临时目录/内存，测试不污染真实库）
        from ..guardrails.paradigm import ParadigmGate
        from ..orchestration.queue import TaskQueue
        from ..guardrails.scope import ScopePolicy
        from ..guardrails.audit_log import AppendOnlyAuditLog
        from ..memory.layers import MemoryLayers
        from ..display.behavior import BehaviorMapper

        self.gate = gate if gate is not None else ParadigmGate()
        self.queue = queue if queue is not None else TaskQueue(self.data_dir / "queue")
        self.scope = scope if scope is not None else ScopePolicy(
            cap=["exec.run"], dev=["read"], cred=[]
        )
        self.audit = audit if audit is not None else AppendOnlyAuditLog(self.data_dir / "audit.jsonl")
        self.memory = memory if memory is not None else MemoryLayers(self.data_dir / "memory")
        self.behavior = behavior if behavior is not None else BehaviorMapper()
        self.executor = executor if executor is not None else ExternalExecutorStub().run
        self.resolve_domain = resolve_domain or self._default_domain
        self.parse_intent = parse_intent or self._default_intent

    # -- 轻量默认实现（可注入替换） -----------------------------------------

    def _default_intent(self, query: str) -> dict[str, Any]:
        q = query.lower()
        if any(k in q for k in ("任务", "队列", "状态", "task", "queue")):
            return {"name": "task_status", "slots": {"query": query}}
        return {"name": "unknown", "slots": {"query": query}}

    def _default_domain(self, intent_name: str) -> str:
        return {"task_status": "task", "unknown": "core"}.get(intent_name, "core")

    # -- 记忆热度轴钩子（s7-memory-temperature） ------------------------------

    def record_interrupt(
        self,
        query: str,
        *,
        state: Optional[dict[str, Any]] = None,
        session: Optional[str] = None,
    ) -> Optional[str]:
        """打断不遗忘：被打断轮次写入 pending_interrupt 单元（working 层，默认热档）。

        字段：原指令 / 理解与执行状态 / 打断时间。下轮启动优先召回该单元，
        合并上下文后可接着原任务不重来。
        """
        query = (query or "").strip()
        if not query:
            return None
        try:
            entry = self.memory.write(
                "working", query,
                kind="pending_interrupt", trusted=True, source="brain.loop.interrupt",
                meta={
                    "state": dict(state or {}),
                    "interrupted_at": _now_iso(),
                    "session": session or "",
                    "closed": False,
                },
            )
            return entry.id
        except Exception:  # noqa: BLE001 - 打断写入不阻断主链路（best-effort）
            return None

    def resume_interrupt(self, session: Optional[str] = None) -> Optional[dict[str, Any]]:
        """下轮启动优先召回未闭环打断单元；返回合并上下文（含原指令/状态）。"""
        try:
            hits = self.memory.read(
                "", layer="working", kinds=("pending_interrupt",), top_k=1,
            )
        except Exception:  # noqa: BLE001
            return None
        for entry in hits:
            if entry.meta.get("closed"):
                continue
            if session and entry.meta.get("session") and entry.meta.get("session") != session:
                continue
            state = dict(entry.meta.get("state") or {})
            state["resumed_from"] = entry.id
            state["original_query"] = entry.content
            return state
        return None

    def close_interrupt(self, entry_id: str) -> bool:
        """打断单元闭环（任务完成/用户确认放弃）：标记 closed。"""
        entry = self.memory.get_by_id(entry_id) if hasattr(self.memory, "get_by_id") else None
        if entry is None:
            return False
        entry.meta["closed"] = True
        entry.meta["closed_at"] = _now_iso()
        try:
            self.memory.demote_warm(entry_id)  # 闭环后转温档保留
            return True
        except Exception:  # noqa: BLE001
            return False

    def end_session(self, session: Optional[str] = None) -> int:
        """会话结束钩子：working 层 hot 条目批量 demote_warm；未闭环打断单元转温档保留。

        返回处理的条目数。
        """
        try:
            if hasattr(self.memory, "demote_all_hot"):
                return int(self.memory.demote_all_hot("working"))
        except Exception:  # noqa: BLE001 - 会话收尾不阻断主链路（best-effort）
            return 0
        return 0

    # -- 入口 ----------------------------------------------------------------

    def run(
        self,
        query: str,
        *,
        entry: str = "cli",
        context: Optional[dict[str, Any]] = None,
        params: Optional[ExecutionParams] = None,
    ) -> LoopResult:
        trace: list[dict[str, Any]] = []
        audit_ids: list[str] = []
        flow_id = _new_flow_id()
        ctx = dict(context or {})

        def mark(ring: str, detail: str) -> None:
            entry = self.audit.append("loop." + ring, "ultima.brain.loop",
                                      {"detail": detail}, session_id=flow_id)
            trace.append({"ts": entry.get("ts", _now_iso()), "ring": ring,
                          "detail": detail, "hash": entry.get("_hash")})
            if entry.get("_hash"):
                audit_ids.append(str(entry["_hash"]))

        # ① 受理
        query = (query or "").strip()
        if not query:
            return self._reject("query 为空，拒绝受理", [], params)
        _emit_safely("message_received", {"query": query, "entry": entry, "flow_id": flow_id})
        mark("receive", f"entry={entry}")

        # ② 意图
        intent = self.parse_intent(query)
        mark("intent", intent["name"])

        # ③ 领域
        domain = self.resolve_domain(intent["name"])
        mark("domain", domain)

        # ④ 范式（7 环前置，L10）
        for ring in _PARADIGM_RINGS:
            decision = self.gate.advance(flow_id, ring)
            if not decision.allowed:
                return self._reject(f"范式环未过（{ring}）：{decision.reason}", trace, params)
        mark("paradigm", "7 环全过")

        # ⑤ 规划
        exec_params = params if params is not None else ExecutionParams(
            tools_allowlist=("ultima_task_query",) if intent["name"] == "task_status" else (),
            acceptance_gate={"gate": "pass"},
        )
        try:
            missing = validate_params(exec_params.as_dict())
        except ParamContractError as exc:
            return self._reject(f"执行参数契约非法：{exc}", trace, exec_params)
        if missing:
            return self._reject(f"执行参数缺失：{missing}（下发缺参数=违反标准）", trace, exec_params)
        record = self.queue.create(
            title=(query[:40] or "无标题"), priority=50,
            permissions=tuple(exec_params.permission_scope),
        )
        self.queue.enqueue(record.task_id)
        mark("plan", record.task_id)

        # ⑥ 派发
        self.queue.advance(record.task_id, "派发")
        parent = ctx.get("parent_task")
        if parent:
            try:
                self.queue.dispatch_subtask(parent, f"子任务-{record.task_id}",
                                            tuple(exec_params.permission_scope))
            except Exception as exc:  # noqa: BLE001 - 编排拒绝即回路拒绝
                return self._reject(f"子代理权限继承失败：{exc}", trace, exec_params)
        mark("dispatch", record.task_id)

        # ⑦ 闸门（权限判定，L8）：dev 只读声明 + 工具白名单 cap 入口
        if "dev" in exec_params.permission_scope:
            dev_decision = self.scope.check_scope("dev:read")
            if not dev_decision.allowed:
                return self._reject(f"闸门拒绝 dev:read：{dev_decision.reason}", trace, exec_params)
        for tool in exec_params.tools_allowlist:
            cap_decision = self.scope.check_scope(f"cap:{tool}")
            if not cap_decision.allowed:
                return self._reject(f"闸门拒绝 cap:{tool}：{cap_decision.reason}", trace, exec_params)
        mark("gate", "scope 全过")

        # ⑧ 执行（本地直答 or 外部执行桩）
        task = {"task_id": record.task_id, "title": record.title, "goal": query,
                "intent": intent["name"], "domain": domain}
        report = self.executor(task, exec_params)
        _emit_safely("tool_call", {"task": task, "report": report})
        for step in report.get("trace", []):
            if isinstance(step, dict) and step.get("segment") == "FINAL" and step.get("content"):
                _emit_safely("message", {"role": "jarvis", "text": step["content"]})
                break
        mark("execute", report.get("model", "unknown"))

        # ⑨ 审计（四查三态）
        verdicts = [
            Correctors.direction_check(query, report),
            Correctors.permission_check(report, exec_params.tools_allowlist),
            Correctors.consistency_check(report, ctx.get("memory_digest")),
            Correctors.structure_check(report),
        ]
        for v in verdicts:
            mark("audit." + v.check, f"passed={v.passed} {v.reason}")
        failed = [v for v in verdicts if not v.passed]
        if failed:
            if any(v.check in ("permission", "consistency") for v in failed):
                return self._reject(f"审计拒绝：{failed[0].reason}", trace, exec_params, verdicts=verdicts)
            return self._replan(f"审计打回：{failed[0].reason}", trace, exec_params, verdicts, remedy=failed[0].remedy)

        # ⑩ 编排（阶段流转）
        self.queue.advance(record.task_id, "执行")
        self.queue.advance(record.task_id, "自检")
        self.queue.advance(record.task_id, "审计")
        self.queue.advance(record.task_id, "回执")
        mark("orchestrate", "回执")

        # ⑪ 表达（结论先行）
        summary = "任务已完成：执行参数与审计均达标。"
        if intent["name"] == "task_status":
            summary = "任务状态查询已完成，队列视图已聚合。"
        mark("express", summary)

        # ⑫ 呈现（行为层状态事件）
        visual = self.behavior.map("task.done")
        presentation = visual.as_dict()
        mark("present", presentation["state"])

        # ⑬ 记忆归档（L9，经闸门）
        try:
            self.memory.write("working", summary, kind="reflection", trusted=True,
                              source="brain.loop", meta={"flow_id": flow_id, "task_id": record.task_id})
            archived = True
        except Exception:  # noqa: BLE001 - 记忆写入失败不阻断主链路（best-effort）
            archived = False
        mark("memory", f"archived={archived}")

        return LoopResult(
            query=query, entry=entry, status="approved", task_id=record.task_id,
            params=exec_params, report=report, verdicts=verdicts,
            audit_ids=audit_ids, memory_archived=archived,
            presentation=presentation, reason="全链通过",
            loop_trace=trace,
        )

    # -- 三态构造 ------------------------------------------------------------

    def _reject(self, reason: str, trace: list[dict[str, Any]],
                params: Optional[ExecutionParams],
                verdicts: Optional[list[Correction]] = None) -> LoopResult:
        return LoopResult(query="", entry="", status="rejected", task_id=None,
                          params=params or ExecutionParams(), report=None,
                          verdicts=list(verdicts or []), reason=reason, loop_trace=trace)

    def _replan(self, reason: str, trace: list[dict[str, Any]],
                params: ExecutionParams, verdicts: list[Correction],
                remedy: str) -> LoopResult:
        return LoopResult(query="", entry="", status="replanned", task_id=None,
                          params=params, report=None, verdicts=verdicts,
                          reason=reason, loop_trace=trace)


__all__ = ["BrainLoop", "LoopResult", "Correction", "Correctors", "ExternalExecutorStub"]
