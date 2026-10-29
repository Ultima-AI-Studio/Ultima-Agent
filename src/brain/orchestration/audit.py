"""L10 范式引擎审计日志（状态转换留痕）。

审计留痕是 L10 出口验收硬指标：每次节点执行、审批决策
都追加结构化审计记录，支撑 M5 全通全绿审计复核。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

try:
    from ..events import emit_event
except ImportError:  # 兼容 src/brain 在 sys.path 时的顶层 orchestration 包
    from events import emit_event

logger = logging.getLogger(__name__)


def _emit_safely(event_type: str, data: dict[str, Any]) -> None:
    try:
        emit_event(event_type, data)
    except Exception as exc:  # noqa: BLE001 - 可观测性不得阻断审计主链路
        logger.warning("event emission failed: %s", exc)


@dataclass
class AuditRecord:
    """单条状态转换审计记录。"""

    timestamp: str
    workflow_id: str
    node: str
    transition: str  # "from_state -> to_state"
    decision: str  # "approved" | "hold" | "completed" | "error"
    approver: str
    detail: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "workflow_id": self.workflow_id,
            "node": self.node,
            "transition": self.transition,
            "decision": self.decision,
            "approver": self.approver,
            "detail": self.detail,
        }


class AuditTrail:
    """审计日志：内存追加 + 可选 JSONL 落盘。

    Parameters
    ----------
    log_path:
        JSONL 审计文件路径。为 None 时仅内存留痕。
    """

    def __init__(self, log_path: Optional[str] = None) -> None:
        self._records: List[AuditRecord] = []
        self._log_path = log_path

    def append(
        self,
        workflow_id: str,
        node: str,
        transition: str,
        decision: str,
        approver: str = "engine",
        detail: Optional[Dict[str, Any]] = None,
    ) -> AuditRecord:
        rec = AuditRecord(
            timestamp=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            workflow_id=workflow_id,
            node=node,
            transition=transition,
            decision=decision,
            approver=approver,
            detail=detail or {},
        )
        self._records.append(rec)
        if self._log_path:
            line = json.dumps(rec.to_dict(), ensure_ascii=False)
            with open(self._log_path, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        _emit_safely("audit_record", rec.to_dict())
        return rec

    def records(self) -> List[AuditRecord]:
        return list(self._records)

    def last(self, n: int = 1) -> List[AuditRecord]:
        return self._records[-n:]

    def decisions(self) -> List[str]:
        return [r.decision for r in self._records]

    def count(self) -> int:
        return len(self._records)


__all__ = ["AuditRecord", "AuditTrail"]
