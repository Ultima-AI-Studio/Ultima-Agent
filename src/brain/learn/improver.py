"""S11 学习闭环 · 改进器（M21 深化 · 阶段二智能陪伴）。

根据评测结果（EvalReport）调整可配置的执行范式参数（工具优先级 / 重试
策略 / 审计松紧），并将失败/兜底轨迹沉淀为回归用例（供后续回归集），
全程留痕（append-only）。不做模型微调前期。

对齐蓝图 §4.3.1 阶段二第 5 项「轨迹 → 评测 → 改进闭环（不做模型微调前期）」：
- 改进输入：EvalReport（signal + 各意图成功率 + 兜底次数）
- 改进动作：
  1. 工具优先级调整（低成功率意图的工具白名单排序前移/后移）
  2. 重试策略调整（失败批次的重试次数上限 +1 封顶，防止无限重试）
  3. 用例沉淀（rejected / replanned / degraded 意图的轨迹入回归集）
- 留痕：所有调整写入追加式调整日志（adjust_log，append-only）

设计约束：
- 确定性：同一评测结果产生同一调整序列（无随机）
- 边界：重试次数有封顶；工具优先级只重排白名单内工具；不新增白名单外工具
- 不触碰：模型权重、冻结参数基线之外的内容；真实凭据
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, Sequence

from .evaluator import EvalReport
from .trace_collector import TraceRecord

MAX_RETRY_BOOST = 3          # 重试策略调整封顶（每意图最多累计 +3）
TOOL_PRIORITY_PENALTY = 3    # 低成功率意图的工具排序惩罚步长


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ImprovementAction:
    """一次改进动作（可留痕、可回滚）。"""

    kind: str                       # tool_priority | retry_policy | case_sink
    target: str                     # 意图名 / 工具名 / 用例 id
    payload: dict[str, Any]
    reason: str
    ts: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind, "target": self.target,
            "payload": dict(self.payload), "reason": self.reason, "ts": self.ts,
        }


class Improver:
    """评测驱动的改进器：参数调整 + 用例沉淀 + 留痕。"""

    def __init__(
        self,
        *,
        adjust_log: Any = None,
        case_dir: Optional[str | Path] = None,
        retry_limits: Optional[dict[str, int]] = None,
        tool_orders: Optional[dict[str, list[str]]] = None,
    ) -> None:
        """参数：
        - adjust_log：追加式留痕对象（append(kind, source, payload) 即可）；None=内存列表
        - case_dir：回归用例落盘目录；None=不落盘（仅内存）
        - retry_limits：意图 → 重试上限 的当前策略（可空，默认 1）
        - tool_orders：意图 → 工具优先级列表（可空，默认空）
        """
        self.case_dir = Path(case_dir) if case_dir else None
        if self.case_dir is not None:
            self.case_dir.mkdir(parents=True, exist_ok=True)
        self.adjust_log = adjust_log
        self._memory_log: list[dict[str, Any]] = []
        self.retry_limits = dict(retry_limits or {})
        self.tool_orders = {k: list(v) for k, v in (tool_orders or {}).items()}
        self.actions: list[ImprovementAction] = []

    # -- 改进入口 ------------------------------------------------------------

    def improve(
        self,
        report: EvalReport,
        traces: Sequence[TraceRecord],
    ) -> list[ImprovementAction]:
        """按评测报告执行改进，返回本次动作序列（已留痕）。"""
        self.actions = []
        # 1) 低成功率意图 → 工具优先级调整 + 用例沉淀
        for intent, bucket in report.by_intent.items():
            rate = float(bucket.get("success_rate", 0.0))
            if bucket.get("total", 0) == 0:
                continue
            if rate < 0.8 and bucket.get("replanned", 0) + bucket.get("rejected", 0) > 0:
                action = self._adjust_tool_priority(intent, bucket, report)
                if action is not None:
                    self._record(action)
            if report.signal == "degraded" or bucket.get("rejected", 0) > 0:
                for trace in traces:
                    if trace.intent == intent and trace.status in ("rejected", "replanned", "partial"):
                        self._sink_case(trace, report)

        # 2) 兜底次数高 → 重试策略调整
        if report.fallback_hits > 0 and report.signal in ("degraded", "steady"):
            for intent, bucket in report.by_intent.items():
                if bucket.get("replanned", 0) >= 1:
                    action = self._adjust_retry_policy(intent, report)
                    if action is not None:
                        self._record(action)

        # 3) 全局 degraded → 兜底用例沉淀（未覆盖的失败轨迹）
        if report.signal == "degraded":
            sunk = {a.target for a in self.actions if a.kind == "case_sink"}
            for trace in traces:
                if trace.status in ("rejected", "replanned", "partial") and trace.intent not in sunk:
                    self._sink_case(trace, report)

        return list(self.actions)

    # -- 调整动作 ------------------------------------------------------------

    def _adjust_tool_priority(
        self, intent: str, bucket: dict[str, Any], report: EvalReport,
    ) -> Optional[ImprovementAction]:
        tools = self.tool_orders.get(intent)
        if not tools:
            return None
        # 低成功率意图：白名单内工具按当前顺序整体前移一级（惩罚步长内）
        moved = tools[:]
        if len(moved) > 1:
            moved = moved[1:] + moved[:1]
        self.tool_orders[intent] = moved
        return ImprovementAction(
            kind="tool_priority", target=intent,
            payload={"from": tools, "to": moved},
            reason=f"意图成功率 {bucket.get('success_rate')} < 0.8，工具优先级前移",
            ts=_now_iso(),
        )

    def _adjust_retry_policy(
        self, intent: str, report: EvalReport,
    ) -> Optional[ImprovementAction]:
        current = self.retry_limits.get(intent, 1)
        if current >= MAX_RETRY_BOOST:
            return None
        updated = current + 1
        self.retry_limits[intent] = updated
        return ImprovementAction(
            kind="retry_policy", target=intent,
            payload={"from": current, "to": updated, "cap": MAX_RETRY_BOOST},
            reason=f"意图兜底次数≥1（replanned），重试上限上调（封顶 {MAX_RETRY_BOOST}）",
            ts=_now_iso(),
        )

    def _sink_case(self, trace: TraceRecord, report: EvalReport) -> None:
        case_id = f"case-{trace.flow_id}"
        case = {
            "case_id": case_id, "flow_id": trace.flow_id, "intent": trace.intent,
            "status": trace.status, "ts": trace.ts, "tools": list(trace.tools),
            "verdicts": [dict(v) for v in trace.verdicts],
            "eval_signal": report.signal, "sink_ts": _now_iso(),
        }
        if self.case_dir is not None:
            target = self.case_dir / f"{case_id}.json"
            target.write_text(
                json.dumps(case, ensure_ascii=False, indent=2), encoding="utf-8",
            )
        action = ImprovementAction(
            kind="case_sink", target=case_id,
            payload={"status": trace.status, "intent": trace.intent},
            reason="失败/兜底轨迹沉淀为回归用例", ts=_now_iso(),
        )
        self._record(action)

    # -- 留痕 ----------------------------------------------------------------

    def _record(self, action: ImprovementAction) -> None:
        self.actions.append(action)
        if self.adjust_log is not None:
            try:
                self.adjust_log.append(
                    "learn.adjust", "ultima.brain.learn", action.as_dict(),
                    session_id=f"learn-{action.kind}",
                )
                return
            except Exception:  # noqa: BLE001 - 留痕失败不阻断改进（best-effort）
                pass
        self._memory_log.append(action.as_dict())

    def log_entries(self) -> list[dict[str, Any]]:
        """读取留痕（内存或审计日志回读）。"""
        if self.adjust_log is not None:
            try:
                entries = self.adjust_log.query(event_type="learn.adjust")
                return [
                    {"ts": e.ts if hasattr(e, "ts") else e.get("ts", ""),
                     "payload": e.payload if hasattr(e, "payload") else e.get("payload", {})}
                    for e in entries
                ]
            except Exception:  # noqa: BLE001
                return list(self._memory_log)
        return list(self._memory_log)


__all__ = ["Improver", "ImprovementAction", "MAX_RETRY_BOOST", "TOOL_PRIORITY_PENALTY"]
