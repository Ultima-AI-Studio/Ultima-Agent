"""渠道桥接（s3-ime-bridge · M24）。

对齐 agent-capability-notes OpenClaw §⑥ / Coze/Manus §⑥：
1. IM 适配器（微信/飞书/Discord 等）：入站 WAL（Write-Ahead Log）/ 出站 Outbox 模式；
2. 审批两端同弹：高危动作在 IM 端与桌面端同时征询，超时取消（fail-safe 拒绝）；
3. 只读红线：不代登录、不索要密码、审批不绕过；
4. 经总线挂接主脑回路（审批事件/动作结果写入总线事件流）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

HIGH_RISK_ACTIONS = {"send_money", "post_publish", "account_op", "delete_data",
                     "purchase", "external_send"}

# 只读红线：不代登录/不索要密码
REDLINE_CHANNEL = {"ask_password", "login_as", "collect_credential"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ChannelError(Exception):
    pass


@dataclass
class InboundMessage:
    msg_id: str
    channel: str
    sender: str
    text: str
    received_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"msg_id": self.msg_id, "channel": self.channel, "sender": self.sender,
                "text": self.text, "received_at": self.received_at}


class WALOutboxStore:
    """入站 WAL / 出站 Outbox（追加式 JSONL，崩溃可恢复）。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.wal_path = self.data_dir / "inbound-wal.jsonl"
        self.outbox_path = self.data_dir / "outbox.jsonl"
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def append_wal(self, msg: InboundMessage) -> None:
        with self.wal_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(msg.as_dict(), ensure_ascii=False) + "\n")

    def append_outbox(self, entry: dict[str, Any]) -> None:
        with self.outbox_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def read_wal(self) -> list[dict[str, Any]]:
        return self._read(self.wal_path)

    def read_outbox(self) -> list[dict[str, Any]]:
        return self._read(self.outbox_path)

    @staticmethod
    def _read(p: Path) -> list[dict[str, Any]]:
        if not p.exists():
            return []
        return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


class ApprovalCoordinator:
    """审批两端同弹：IM 端 + 桌面端同时征询；超时取消（fail-safe 拒绝）。"""

    def __init__(self, *, timeout_seconds: float = 60.0) -> None:
        self.timeout_seconds = timeout_seconds
        self._pending: dict[str, dict[str, Any]] = {}

    def request(self, approval_id: str, action: str, detail: str) -> dict[str, Any]:
        """发起两端同弹审批：返回 pending（两端待批准）。"""
        rec = {
            "approval_id": approval_id, "action": action, "detail": detail,
            "status": "pending", "im_vote": None, "desktop_vote": None,
            "requested_at": _now_iso(), "requested_ts": time.time(),
        }
        self._pending[approval_id] = rec
        return rec

    def vote(self, approval_id: str, side: str, approve: bool) -> dict[str, Any]:
        if side not in ("im", "desktop"):
            raise ChannelError(f"非法征询端 {side}")
        rec = self._pending.get(approval_id)
        if rec is None:
            raise ChannelError(f"审批不存在 {approval_id}")
        key = f"{side}_vote"
        rec[key] = approve
        return rec

    def resolve(self, approval_id: str, *, now: Optional[float] = None) -> dict[str, Any]:
        """结算：两端均批准且未超时 → 批准；任一拒绝/超时 → 取消（fail-safe）。"""
        rec = self._pending.get(approval_id)
        if rec is None:
            raise ChannelError(f"审批不存在 {approval_id}")
        t = now if now is not None else time.time()
        requested = rec.get("requested_ts", 0.0)
        elapsed = t - requested
        if elapsed > self.timeout_seconds:
            rec["status"] = "cancelled"
            rec["cancel_reason"] = f"超时（{elapsed:.0f}s > {self.timeout_seconds}s）"
            return rec
        if rec.get("im_vote") is True and rec.get("desktop_vote") is True:
            rec["status"] = "approved"
        elif rec.get("im_vote") is False or rec.get("desktop_vote") is False:
            rec["status"] = "cancelled"
            rec["cancel_reason"] = "任一端拒绝"
        else:
            rec["status"] = "pending"
        return rec

    # 时间戳辅助：测试注入 requested_ts
    def _set_requested_ts(self, approval_id: str, ts: float) -> None:
        if approval_id in self._pending:
            self._pending[approval_id]["requested_ts"] = ts


class ChannelRedline:
    """渠道只读红线：不代登录/不索要密码。"""

    def __init__(self) -> None:
        self.events: list[dict[str, Any]] = []

    def check(self, action: str) -> tuple[bool, str]:
        if action in REDLINE_CHANNEL:
            return False, f"渠道红线：{action}（不代登录/不索要密码）被拒绝"
        return True, "允许"

    def record(self, action: str, allowed: bool, reason: str) -> None:
        self.events.append({"action": action, "allowed": allowed, "reason": reason,
                            "ts": _now_iso()})


class ImBridge:
    """IM 适配器总装：WAL/Outbox + 审批 + 红线 + 总线事件流。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.store = WALOutboxStore(data_dir)
        self.approval = ApprovalCoordinator()
        self.redline = ChannelRedline()
        self.bus_events: list[dict[str, Any]] = []

    # -- 入站 ---------------------------------------------------------------

    def inbound(self, channel: str, sender: str, text: str) -> InboundMessage:
        # 入站先落 WAL（崩溃可恢复）
        msg = InboundMessage(msg_id=f"{channel}-{int(time.time()*1000)}",
                             channel=channel, sender=sender, text=text)
        self.store.append_wal(msg)
        self.bus_events.append({"kind": "channel.inbound", "msg_id": msg.msg_id,
                                "channel": channel, "ts": _now_iso()})
        return msg

    # -- 高危动作审批 ---------------------------------------------------------

    def act(self, action: str, detail: str, *, approval_id: Optional[str] = None) -> dict[str, Any]:
        """动作执行：高危需两端审批；红线动作直接拒绝。"""
        ok, reason = self.redline.check(action)
        if not ok:
            self.redline.record(action, ok, reason)
            self.bus_events.append({"kind": "channel.redline.denied", "action": action,
                                    "reason": reason, "ts": _now_iso()})
            return {"ok": False, "action": action, "reason": reason}
        if action in HIGH_RISK_ACTIONS:
            aid = approval_id or f"ap-{int(time.time()*1000)}"
            rec = self.approval.request(aid, action, detail)
            self.bus_events.append({"kind": "channel.approval.requested", "approval_id": aid,
                                    "action": action, "ts": _now_iso()})
            return {"ok": False, "action": action, "approval_id": aid, "status": "pending",
                    "note": "高危动作：两端审批中（IM+桌面）"}
        # 普通动作：记录出站 Outbox
        entry = {"action": action, "detail": detail, "ts": _now_iso(), "status": "executed"}
        self.store.append_outbox(entry)
        self.bus_events.append({"kind": "channel.action.executed", "action": action, "ts": _now_iso()})
        return {"ok": True, "action": action}

    def approve(self, approval_id: str, side: str, approve: bool) -> dict[str, Any]:
        return self.approval.vote(approval_id, side, approve)

    def settle(self, approval_id: str) -> dict[str, Any]:
        rec = self.approval.resolve(approval_id)
        if rec["status"] == "approved":
            self.bus_events.append({"kind": "channel.approval.approved", "approval_id": approval_id,
                                    "ts": _now_iso()})
        elif rec["status"] == "cancelled":
            self.bus_events.append({"kind": "channel.approval.cancelled", "approval_id": approval_id,
                                    "reason": rec.get("cancel_reason", ""), "ts": _now_iso()})
        return rec


__all__ = ["ImBridge", "ApprovalCoordinator", "WALOutboxStore", "ChannelRedline",
           "InboundMessage", "HIGH_RISK_ACTIONS", "REDLINE_CHANNEL"]
