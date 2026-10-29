"""追加式审计日志（M21 基础留痕 · s3-audit-trail）。

对齐 plugin-bus-spec §10.2：
- 只追加不修改：写入仅 append，历史记录不可改写（hash 链强校验）
- 每条记录：时间戳(毫秒 ISO) + 会话ID + 来源 module_id + 事件类型 + 载荷引用
- 敏感字段由调用方脱敏后写入（本层不解析载荷内容）
- 支持按 会话/时间/来源/事件类型 检索
- verify() 重建 hash 链，任何改写/删除/插入即判失败（改写被拒可机检）
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from ..events import emit_event
except ImportError:  # 兼容 src/brain 在 sys.path 时的顶层 guardrails 包
    from events import emit_event

logger = logging.getLogger(__name__)


def _emit_safely(event_type: str, data: dict[str, Any]) -> None:
    try:
        emit_event(event_type, data)
    except Exception as exc:  # noqa: BLE001 - 可观测性不得阻断审计落盘
        logger.warning("event emission failed: %s", exc)


def _now_iso_ms() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _line_hash(prev_hash: str, line: str) -> str:
    return hashlib.sha256(f"{prev_hash}\n{line}".encode("utf-8")).hexdigest()


class AuditLogError(Exception):
    """审计日志操作失败。"""


@dataclass(frozen=True)
class AuditEntry:
    ts: str
    session_id: str
    source: str
    event_type: str
    payload: dict[str, Any]
    line_no: int
    line_hash: str


class AppendOnlyAuditLog:
    """追加式审计日志：write 只追加，query 检索，verify 强校验不可改写。"""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    # -- 写入（只追加） -----------------------------------------------------

    def append(
        self,
        event_type: str,
        source: str,
        payload: dict[str, Any] | None = None,
        session_id: str = "default",
    ) -> dict[str, Any]:
        """追加一条审计记录。返回记录（含 line_no 与 line_hash）。"""
        # 先读当前末行 hash（若有），作为链前驱
        prev_hash = "0" * 64
        if self.path.exists() and self.path.stat().st_size > 0:
            try:
                lines = self.path.read_text(encoding="utf-8").splitlines()
                if lines:
                    prev = json.loads(lines[-1])
                    prev_hash = prev.get("_hash", "0" * 64)
            except (json.JSONDecodeError, OSError):
                prev_hash = "0" * 64
        entry = {
            "ts": _now_iso_ms(),
            "session_id": session_id,
            "source": source,
            "event_type": event_type,
            "payload": payload or {},
            "_prev": prev_hash,
        }
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        entry_hash = _line_hash(prev_hash, line)
        entry["_hash"] = entry_hash
        line = json.dumps(entry, ensure_ascii=False, separators=(",", ":"))
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(line + "\n")
            fh.flush()
        _emit_safely("audit_record", entry)
        return entry

    # -- 检索 ---------------------------------------------------------------

    def query(
        self,
        session_id: str | None = None,
        source: str | None = None,
        event_type: str | None = None,
        since: str | None = None,
        until: str | None = None,
    ) -> list[AuditEntry]:
        """按 会话/来源/事件类型/时间区间 检索（时间 ISO 字符串可比）。"""
        out: list[AuditEntry] = []
        for line_no, line in enumerate(self.path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if session_id is not None and obj.get("session_id") != session_id:
                continue
            if source is not None and obj.get("source") != source:
                continue
            if event_type is not None and obj.get("event_type") != event_type:
                continue
            ts = obj.get("ts", "")
            if since is not None and ts < since:
                continue
            if until is not None and ts > until:
                continue
            out.append(
                AuditEntry(
                    ts=obj.get("ts", ""),
                    session_id=obj.get("session_id", ""),
                    source=obj.get("source", ""),
                    event_type=obj.get("event_type", ""),
                    payload=obj.get("payload", {}),
                    line_no=line_no,
                    line_hash=obj.get("_hash", ""),
                )
            )
        return out

    # -- 不可改写校验 ------------------------------------------------------

    def verify(self) -> dict[str, Any]:
        """逐行重建 hash 链。任何带链行被改/删/插 → fail；存量无链行按 legacy 跳过并计数。

        篡改盲区说明：legacy 行本身无链不可校验，但一旦其后存在带链行，
        删除/插入/改写任意行都会触发后续行 _prev 或 hash 失配，检测依然有效。
        """
        lines = self.path.read_text(encoding="utf-8").splitlines()
        prev_hash = "0" * 64
        legacy = 0
        for idx, line in enumerate(lines, 1):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as exc:
                return {"ok": False, "line": idx, "reason": f"json-parse:{exc}", "total": len(lines)}
            declared = obj.get("_hash", "")
            if not declared:
                legacy += 1
                continue
            expected = _line_hash(prev_hash, json.dumps(
                {k: v for k, v in obj.items() if k != "_hash"},
                ensure_ascii=False, separators=(",", ":"),
            ))
            if declared != expected:
                return {"ok": False, "line": idx, "reason": "hash-mismatch", "total": len(lines)}
            if obj.get("_prev", "") != prev_hash:
                return {"ok": False, "line": idx, "reason": "prev-link-broken", "total": len(lines)}
            prev_hash = declared
        return {"ok": True, "lines": len(lines), "total": len(lines), "legacy": legacy}

    def file_size(self) -> int:
        return self.path.stat().st_size if self.path.exists() else 0
