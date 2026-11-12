"""状态与记忆共享轴（s4-state-axis · M04）：四类全局状态统一供读。

对齐产品对齐报告缺口 N3（product-alignment-20261027）：
1. StateAxis 聚合四类全局状态：会话（voice 三态）+ 身份关系（bond 状态轴）
   + 设备档案（device-profile 摘要）+ 任务队列（orchestration 视图）；
2. 统一只读视图：每类状态含更新时间戳 + 聚合版本号；消费方不直接改底层；
3. 跨形态同步：悬浮球/组合窗口消费同一 StateAxis 快照（复用 display/behavior
   状态机）；
4. 事件推送：订阅者模式（总线事件 → StateAxis 刷新 → 订阅者收到新快照）。

禁止：绕过既有组件直接改底层状态；测试污染真实库；向 fileDomain 之外写文件。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

SESSION_EVENTS = ("voice.idle", "voice.listening", "voice.thinking", "voice.speaking")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass
class StateAxis:
    """状态与记忆共享轴：聚合只读视图 + 版本号 + 订阅推送。

    依赖注入四类数据源（本批次真实组件实例；消费方不直接改底层）：
    - bond: BondSystem（身份关系状态轴 state_axis()）
    - registry: DeviceRegistry（设备档案 all()）
    - queue: TaskQueue（任务队列 view()）
    - behavior: BehaviorMapper（行为层状态机，跨形态消费同一快照）
    """

    bond: Any
    registry: Any
    queue: Any
    behavior: Any

    def __post_init__(self) -> None:
        self._version: int = 0
        self._updated: dict[str, str] = {}
        self._session_state: str = "idle"
        self._subscribers: list[Callable[[dict[str, Any]], None]] = []
        # 初始化即聚合一次
        self.refresh()

    # -- 订阅 ---------------------------------------------------------------

    def subscribe(self, callback: Callable[[dict[str, Any]], None]) -> None:
        """注册订阅者；refresh 后收到最新快照。"""
        if callback not in self._subscribers:
            self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[dict[str, Any]], None]) -> None:
        self._subscribers = [c for c in self._subscribers if c != callback]

    # -- 聚合（只读视图） ----------------------------------------------------

    def _session(self) -> dict[str, Any]:
        return {
            "state": self._session_state,
            "visual": self.behavior.map(f"voice.{self._session_state}").as_dict(),
        }

    def _identity(self) -> dict[str, Any]:
        try:
            return self.bond.state_axis()
        except Exception as exc:  # noqa: BLE001 - 单类失败不阻断聚合
            return {"error": str(exc)}

    def _device(self) -> list[dict[str, Any]]:
        try:
            return [p.as_dict() for p in self.registry.all()]
        except Exception as exc:  # noqa: BLE001
            return [{"error": str(exc)}]

    def _tasks(self) -> dict[str, Any]:
        try:
            rows = self.queue.view()
            counts: dict[str, int] = {}
            for row in rows:
                phase = row.get("phase", "未知")
                counts[phase] = counts.get(phase, 0) + 1
            return {"total": len(rows), "counts": counts, "rows": rows}
        except Exception as exc:  # noqa: BLE001
            return {"error": str(exc)}

    def snapshot(self) -> dict[str, Any]:
        """统一只读视图：四类状态 + 各自 updated_ts + 聚合版本号。"""
        parts = {
            "session": self._session(),
            "identity": self._identity(),
            "device": self._device(),
            "tasks": self._tasks(),
        }
        return {
            "version": self._version,
            "updated_at": _now_iso(),
            "categories": {
                key: {"value": value, "updated_ts": self._updated.get(key, "")}
                for key, value in parts.items()
            },
        }

    # -- 刷新与事件推送 -----------------------------------------------------

    def apply_voice_state(self, state: str) -> None:
        """会话状态更新（voice 三态：idle/listening/thinking/speaking）。"""
        if state not in SESSION_EVENTS and state not in ("idle", "listening", "thinking", "speaking"):
            state = "idle"
        self._session_state = state if state in ("idle", "listening", "thinking", "speaking") else "idle"
        self._mark("session")
        return self.refresh()

    def on_bus_event(self, event_type: str, payload: Optional[dict[str, Any]] = None) -> dict[str, Any]:
        """总线事件回调挂点：bus 事件 → 刷新对应类别 → 通知订阅者。"""
        payload = dict(payload or {})
        if event_type in SESSION_EVENTS or event_type.startswith("voice."):
            self._session_state = event_type.split(".", 1)[-1]
            self._mark("session")
        elif event_type.startswith("bond."):
            self._mark("identity")
        elif event_type.startswith("device."):
            self._mark("device")
        elif event_type.startswith("queue.") or event_type.startswith("task."):
            self._mark("tasks")
        return self.refresh()

    def refresh(self) -> dict[str, Any]:
        """整体刷新：版本号递增 + 通知全部订阅者（消费方收到同一快照）。"""
        self._version += 1
        snap = self.snapshot()
        for callback in list(self._subscribers):
            try:
                callback(snap)
            except Exception:  # noqa: BLE001 - 订阅者异常不阻断推送
                pass
        return snap

    def _mark(self, category: str) -> None:
        self._updated[category] = _now_iso()

    # -- 跨形态消费 ---------------------------------------------------------

    def visual_snapshot(self) -> dict[str, Any]:
        """悬浮球/组合窗口消费同一快照：行为层状态机映射。"""
        return self._session()["visual"]


__all__ = ["StateAxis", "SESSION_EVENTS"]
