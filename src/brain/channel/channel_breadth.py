"""渠道铺开（s9-channel-breadth · M24 渠道注册表与多通道适配）。

对齐 jarvis-reverse-architecture M24 渠道连接器；复用 s3-ime-bridge 既有
WAL/Outbox、ApprovalCoordinator 两端审批、ChannelRedline 只读红线，不另起炉灶：
1. ChannelRegistry：通道适配器注册/列出/获取（id/名称/类型/方向/状态）；
2. 多通道适配：本地通知（local_notify）+ 邮件 Outbox 占位（mail_outbox）；
   统一接口：ingest（入站→WAL）/ dispatch（出站→Outbox）；
3. 高危 dispatch 走两端审批（超时 fail-safe 取消）；红线动作直接拒绝。

禁止：不代登录/不索要密码/审批不绕过；不接真实外部账号（适配器为可接线占位）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

from src.brain.channel.ime_bridge import (
    HIGH_RISK_ACTIONS,
    REDLINE_CHANNEL,
    ApprovalCoordinator,
    ChannelRedline,
    InboundMessage,
    WALOutboxStore,
)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class ChannelError(Exception):
    pass


@dataclass
class ChannelAdapter:
    """通道适配器登记项。"""
    channel_id: str
    name: str
    kind: str            # local_notify | mail | im | ...
    direction: str       # in / out / both
    status: str = "registered"   # registered | active | disabled
    adapter: Any = None  # 可调用对象（ingest/dispatch）或 None（占位）

    def as_dict(self) -> dict[str, Any]:
        return {"channel_id": self.channel_id, "name": self.name, "kind": self.kind,
                "direction": self.direction, "status": self.status}


class ChannelRegistry:
    """渠道注册表：注册/列出/获取/启停。"""

    def __init__(self) -> None:
        self._channels: dict[str, ChannelAdapter] = {}

    def register(self, adapter: ChannelAdapter) -> None:
        if adapter.channel_id in self._channels:
            raise ChannelError(f"通道已注册：{adapter.channel_id}")
        self._channels[adapter.channel_id] = adapter

    def list(self) -> list[dict[str, Any]]:
        return [c.as_dict() for c in self._channels.values()]

    def get(self, channel_id: str) -> ChannelAdapter:
        c = self._channels.get(channel_id)
        if c is None:
            raise ChannelError(f"通道未注册：{channel_id}")
        return c

    def set_status(self, channel_id: str, status: str) -> None:
        if status not in ("registered", "active", "disabled"):
            raise ChannelError(f"非法通道状态：{status}")
        self.get(channel_id).status = status


class ChannelDispatcher:
    """渠道铺开总装：注册表 + WAL/Outbox + 审批 + 红线，统一 ingest/dispatch。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.registry = ChannelRegistry()
        self.store = WALOutboxStore(data_dir)
        self.approval = ApprovalCoordinator()
        self.redline = ChannelRedline()
        self.bus_events: list[dict[str, Any]] = []
        self._wire_defaults()

    def _wire_defaults(self) -> None:
        """内置占位通道：本地通知 + 邮件 Outbox（可接线，不真发）。"""
        self.registry.register(ChannelAdapter(
            channel_id="local_notify", name="本地通知", kind="local_notify",
            direction="out", status="active", adapter=self._local_notify_dispatch))
        self.registry.register(ChannelAdapter(
            channel_id="mail_outbox", name="邮件 Outbox", kind="mail",
            direction="both", status="registered", adapter=None))

    # -- 入站（→ WAL）--------------------------------------------------------

    def ingest(self, channel_id: str, sender: str, text: str) -> InboundMessage:
        ch = self.registry.get(channel_id)
        if ch.direction not in ("in", "both"):
            raise ChannelError(f"通道 {channel_id} 不支持入站（方向 {ch.direction}）")
        msg = InboundMessage(msg_id=f"{channel_id}-{int(time.time()*1000)}",
                             channel=channel_id, sender=sender, text=text)
        self.store.append_wal(msg)
        self.bus_events.append({"kind": "channel.inbound", "channel": channel_id,
                                "msg_id": msg.msg_id, "ts": _now_iso()})
        return msg

    # -- 出站（→ Outbox，高危走审批）-----------------------------------------

    def dispatch(self, channel_id: str, text: str, *,
                 action: str = "channel_send",
                 approval_id: Optional[str] = None) -> dict[str, Any]:
        """统一出站：红线先拒；高危走两端审批；普通直接写 Outbox。"""
        ch = self.registry.get(channel_id)
        if ch.direction not in ("out", "both"):
            raise ChannelError(f"通道 {channel_id} 不支持出站（方向 {ch.direction}）")

        ok, reason = self.redline.check(action)
        if not ok:
            self.redline.record(action, ok, reason)
            self.bus_events.append({"kind": "channel.redline.denied", "channel": channel_id,
                                    "action": action, "reason": reason, "ts": _now_iso()})
            return {"ok": False, "channel": channel_id, "action": action, "reason": reason}

        if action in HIGH_RISK_ACTIONS:
            aid = approval_id or f"ap-{int(time.time()*1000)}"
            rec = self.approval.request(aid, action, f"{channel_id}: {text}")
            self.bus_events.append({"kind": "channel.approval.requested",
                                    "approval_id": aid, "channel": channel_id,
                                    "action": action, "ts": _now_iso()})
            return {"ok": False, "channel": channel_id, "action": action,
                    "approval_id": aid, "status": "pending",
                    "note": "高危出站：两端审批中（IM+桌面）"}

        entry = {"channel": channel_id, "action": action, "text": text,
                 "ts": _now_iso(), "status": "dispatched"}
        self.store.append_outbox(entry)
        self.bus_events.append({"kind": "channel.dispatched", "channel": channel_id,
                                "action": action, "ts": _now_iso()})
        return {"ok": True, "channel": channel_id, "action": action}

    # -- 本地通知适配器 -------------------------------------------------------

    def _local_notify_dispatch(self, text: str) -> dict[str, Any]:
        return {"ok": True, "channel": "local_notify", "text": text,
                "ts": _now_iso(), "note": "桌面播报占位（接线 L0/L6 呈现层后生效）"}

    def local_notify(self, text: str) -> dict[str, Any]:
        """本地通知快捷出站（走统一 dispatch，普通动作）。"""
        return self.dispatch("local_notify", text, action="channel_send")

    # -- 审批结算（复用 ApprovalCoordinator）---------------------------------

    def approve(self, approval_id: str, side: str, approve: bool) -> dict[str, Any]:
        if side not in ("im", "desktop"):
            raise ChannelError(f"非法征询端 {side}")
        return self.approval.vote(approval_id, side, approve)

    def settle(self, approval_id: str, *, now: Optional[float] = None) -> dict[str, Any]:
        rec = self.approval.resolve(approval_id, now=now)
        if rec["status"] == "approved":
            self.bus_events.append({"kind": "channel.approval.approved",
                                    "approval_id": approval_id, "ts": _now_iso()})
        elif rec["status"] == "cancelled":
            self.bus_events.append({"kind": "channel.approval.cancelled",
                                    "approval_id": approval_id,
                                    "reason": rec.get("cancel_reason", ""), "ts": _now_iso()})
        return rec

    def snapshot(self) -> dict[str, Any]:
        return {
            "channels": self.registry.list(),
            "wal_count": len(self.store.read_wal()),
            "outbox_count": len(self.store.read_outbox()),
            "events_count": len(self.bus_events),
        }


__all__ = ["ChannelRegistry", "ChannelAdapter", "ChannelDispatcher", "ChannelError"]
