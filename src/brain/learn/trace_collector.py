"""S11 学习闭环 · 轨迹采集（M21 深化 · 阶段二智能陪伴）。

从追加式审计日志（AppendOnlyAuditLog）提取执行轨迹，标准化为可评测的
trace 记录（意图 / 工具 / 耗时 / 成败），供评测器（evaluator）评分。

对齐蓝图 §4.3.1 阶段二第 5 项「轨迹 → 评测 → 改进闭环（不做模型微调前期）」：
- 轨迹来源：brain_loop 在 loop.* 环写入的审计记录（receive/intent/domain/
  paradigm/plan/dispatch/gate/execute/audit.*/orchestrate/express/present/memory）
- 成败判定：执行环（execute）+ 审计环（audit.*）串联判定；存在 rejected /
  replanned 状态则视为失败轨迹
- 标准化输出：TraceRecord（flow_id / intent / domain / tools / phases /
  durations / verdicts / status / ts）

设计约束：
- 只读：不修改审计日志（append-only 强校验不被破坏）
- 不绑定 Windows 技术栈（S13 宿主抽象层前置兼容）
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

# 回路环名（与 brain_loop._PARADIGM_RINGS / 审计事件类型对齐）
_LOOP_EVENT_PREFIX = "loop."
_PHASE_KEYS = ("receive", "intent", "domain", "paradigm", "plan", "dispatch",
               "gate", "execute", "audit.direction", "audit.permission",
               "audit.consistency", "audit.structure", "orchestrate",
               "express", "present", "memory")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _parse_ts(value: str) -> Optional[float]:
    """解析 ISO 时间戳为 epoch 秒；失败返回 None（不阻断采集）。"""
    try:
        if value.endswith("Z"):
            value = value[:-1] + "+00:00"
        return datetime.fromisoformat(value).timestamp()
    except (ValueError, TypeError):
        return None


@dataclass(frozen=True, slots=True)
class TraceRecord:
    """一条标准化执行轨迹（可评测）。"""

    flow_id: str
    ts: str
    intent: str = ""
    domain: str = ""
    tools: tuple[str, ...] = ()
    phases: tuple[str, ...] = ()
    durations_ms: dict[str, float] = field(default_factory=dict)
    verdicts: tuple[dict[str, Any], ...] = ()
    status: str = "unknown"          # approved | rejected | replanned | partial | unknown
    model: str = ""
    loop_trace_count: int = 0
    notes: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "flow_id": self.flow_id, "ts": self.ts, "intent": self.intent,
            "domain": self.domain, "tools": list(self.tools),
            "phases": list(self.phases), "durations_ms": dict(self.durations_ms),
            "verdicts": [dict(v) for v in self.verdicts], "status": self.status,
            "model": self.model, "loop_trace_count": self.loop_trace_count,
            "notes": self.notes,
        }


def _status_from_events(events: list[dict[str, Any]], phase_map: dict[str, float]) -> str:
    """由事件序列判定轨迹成败。

    判定优先级（保守诚实）：
      1. 审计拒绝事件（audit.permission / audit.consistency 且 passed=False）→ rejected
      2. 审计打回（audit.direction / audit.structure passed=False）→ replanned
      3. 执行环缺失 → partial
      4. 回执环（orchestrate）存在且无失败 → approved
      5. 否则 unknown
    """
    texts: list[str] = []
    for ev in events:
        payload = ev.get("payload") or {}
        detail = str(payload.get("detail", ""))
        texts.append(f"{ev.get('event_type', '')}={detail}")
    joined = "\n".join(texts)

    # 审计环逐个判定
    for ev in events:
        et = ev.get("event_type", "")
        payload = ev.get("payload") or {}
        detail = str(payload.get("detail", ""))
        if et == "loop.audit.permission" and "passed=False" in detail and "越界" in detail:
            return "rejected"
        if et == "loop.audit.consistency" and "passed=False" in detail:
            return "rejected"
        if et == "loop.audit.direction" and "passed=False" in detail:
            return "replanned"
        if et == "loop.audit.structure" and "passed=False" in detail:
            return "replanned"

    if "loop.execute" not in joined:
        return "partial"
    if "loop.orchestrate" in joined and "loop.memory" in joined:
        return "approved"
    if "loop.orchestrate" in joined:
        return "approved"
    return "unknown"


class TraceCollector:
    """从审计日志提取并标准化执行轨迹。"""

    def __init__(self, audit_log: Any) -> None:
        """audit_log：AppendOnlyAuditLog 实例（或任何提供 query() 的对象）。"""
        self.audit_log = audit_log

    # -- 采集 ----------------------------------------------------------------

    def collect(
        self,
        *,
        session_id: Optional[str] = None,
        since: Optional[str] = None,
        until: Optional[str] = None,
        event_type_prefix: str = _LOOP_EVENT_PREFIX,
    ) -> list[TraceRecord]:
        """按 会话/时间区间 采集执行轨迹（按 flow 分组）。

        事件分组键：审计记录的 session_id 即 flow_id（brain_loop.mark 以
        flow_id 作为 session_id 写入）。
        """
        events = self.audit_log.query(
            session_id=session_id, since=since, until=until,
        )
        # 过滤回路事件（含 loop. 前缀或 event_type 以 loop. 开头）
        loop_events = [
            ev for ev in events
            if str(ev.event_type if hasattr(ev, "event_type") else ev.get("event_type", "")).startswith(event_type_prefix)
        ]
        if not loop_events:
            return []

        # 按 flow（session_id）分组，保持时间序
        groups: dict[str, list[dict[str, Any]]] = {}
        for ev in loop_events:
            sid = ev.session_id if hasattr(ev, "session_id") else ev.get("session_id", "")
            groups.setdefault(sid, []).append(
                {
                    "event_type": ev.event_type if hasattr(ev, "event_type") else ev.get("event_type", ""),
                    "ts": ev.ts if hasattr(ev, "ts") else ev.get("ts", ""),
                    "payload": ev.payload if hasattr(ev, "payload") else ev.get("payload", {}),
                    "line_no": ev.line_no if hasattr(ev, "line_no") else ev.get("line_no", 0),
                }
            )
        for g in groups.values():
            g.sort(key=lambda e: e.get("ts", ""))

        out: list[TraceRecord] = []
        for flow_id, flow_events in groups.items():
            rec = self._build_record(flow_id, flow_events)
            if rec is not None:
                out.append(rec)
        out.sort(key=lambda r: r.ts)
        return out

    # -- 单轨迹构建 ----------------------------------------------------------

    def _build_record(self, flow_id: str, events: list[dict[str, Any]]) -> Optional[TraceRecord]:
        if not events:
            return None
        # 时间
        ts_first = events[0].get("ts", "")
        ts_last = events[-1].get("ts", "")
        t0 = _parse_ts(ts_first)
        t1 = _parse_ts(ts_last)
        total_ms = round((t1 - t0) * 1000, 1) if (t0 is not None and t1 is not None) else 0.0

        # 相位与耗时
        phase_map: dict[str, float] = {}
        prev_ts: Optional[str] = None
        phases: list[str] = []
        for ev in events:
            et = str(ev.get("event_type", ""))
            phase = et[len(_LOOP_EVENT_PREFIX):] if et.startswith(_LOOP_EVENT_PREFIX) else et
            if phase not in phase_map:
                phases.append(phase)
            cur = ev.get("ts", "")
            if prev_ts is not None:
                p0 = _parse_ts(prev_ts)
                p1 = _parse_ts(cur)
                if p0 is not None and p1 is not None:
                    phase_map[phase] = round((p1 - p0) * 1000, 1)
            prev_ts = cur
        if total_ms:
            phase_map["total"] = total_ms

        # 意图 / 领域 / 工具 / 模型
        intent = ""
        domain = ""
        model = ""
        tools: set[str] = set()
        for ev in events:
            et = str(ev.get("event_type", ""))
            payload = ev.get("payload") or {}
            detail = str(payload.get("detail", ""))
            if et == "loop.intent":
                intent = detail
            elif et == "loop.domain":
                domain = detail
            elif et == "loop.execute":
                model = detail
            elif et == "loop.gate" and detail == "scope 全过":
                tools |= set()
            elif et.startswith("loop.audit."):
                # 审计环 detail 含 passed=... 理由，提取工具引用
                for tok in detail.split():
                    if tok.startswith("cap:"):
                        tools.add(tok[4:])
        # 工具白名单信息在 execution 参数里，审计 detail 通常含工具名，尽力提取
        for ev in events:
            payload = ev.get("payload") or {}
            detail = str(payload.get("detail", ""))
            for kw in ("ultima_", "exec.", "scene.", "voice."):
                idx = detail.find(kw)
                while idx != -1:
                    end = detail.find(" ", idx)
                    if end == -1:
                        end = len(detail)
                    tools.add(detail[idx:end].strip("()[],:："))
                    idx = detail.find(kw, end)

        verdicts: list[dict[str, Any]] = []
        for ev in events:
            et = str(ev.get("event_type", ""))
            if et.startswith("loop.audit."):
                payload = ev.get("payload") or {}
                detail = str(payload.get("detail", ""))
                verdicts.append({"check": et[len("loop.audit."):], "detail": detail})

        status = _status_from_events(events, phase_map)
        return TraceRecord(
            flow_id=flow_id, ts=ts_first, intent=intent, domain=domain,
            tools=tuple(sorted(tools)), phases=tuple(phases),
            durations_ms=phase_map, verdicts=tuple(verdicts), status=status,
            model=model, loop_trace_count=len(events),
        )


__all__ = ["TraceCollector", "TraceRecord", "TraceCollectorError"]

class TraceCollectorError(Exception):
    """轨迹采集失败。"""
