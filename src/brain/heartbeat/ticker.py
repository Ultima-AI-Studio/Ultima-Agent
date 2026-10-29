"""主动心跳（s3-heartbeat · M27）。

对齐 jarvis-reverse-architecture M27 主动心跳：
1. TICK 周期调度：固定周期轮询关注点；
2. 消息抢占：新消息到达时心跳让位（用户优先）；
3. 空闲思考预算：空闲期思考/内省有预算封顶，不无限自转；
4. 主动发言边界：仅空闲态可主动发声，忙碌/监听中不打断。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

try:
    from ..events import emit_event
except ImportError:  # 兼容 src/brain 在 sys.path 时的顶层 heartbeat 包
    from events import emit_event

logger = logging.getLogger(__name__)


def _emit_safely(event_type: str, data: dict[str, Any]) -> None:
    try:
        emit_event(event_type, data)
    except Exception as exc:  # noqa: BLE001 - 可观测性不得阻断心跳
        logger.warning("event emission failed: %s", exc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


@dataclass
class HeartbeatConfig:
    tick_seconds: float = 30.0          # TICK 周期
    idle_budget_max: int = 3            # 空闲思考预算（次/周期封顶）
    idle_budget_seconds: float = 10.0   # 单次内省耗时预算


class MessagePreempt:
    """消息抢占：新消息到达抢占心跳（心跳让位）。"""

    def __init__(self) -> None:
        self._event = threading.Event()
        self._count = 0
        self._lock = threading.Lock()

    def notify(self) -> None:
        with self._lock:
            self._count += 1
            self._event.set()

    def consume(self) -> bool:
        """心跳前检查：有新消息则让位并清标记。"""
        with self._lock:
            if self._event.is_set():
                self._event.clear()
                return True
            return False

    @property
    def count(self) -> int:
        return self._count


class IdleBudget:
    """空闲思考预算：封顶，不无限自转。"""

    def __init__(self, max_ticks: int) -> None:
        self.max_ticks = max_ticks
        self._used = 0

    def try_use(self) -> bool:
        if self._used >= self.max_ticks:
            return False
        self._used += 1
        return True

    def reset(self) -> None:
        self._used = 0

    @property
    def used(self) -> int:
        return self._used


class HeartbeatTicker:
    """主动心跳调度：TICK 周期 + 抢占 + 预算 + 发言边界。"""

    def __init__(
        self,
        *,
        config: Optional[HeartbeatConfig] = None,
        busy_state_provider: Optional[Callable[[], str]] = None,
    ) -> None:
        self.config = config or HeartbeatConfig()
        self.preempt = MessagePreempt()
        self.budget = IdleBudget(self.config.idle_budget_max)
        self._busy = busy_state_provider or (lambda: "idle")
        self._ticks = 0
        self._proposals: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def tick(self) -> dict[str, Any]:
        """执行一次 TICK：返回本轮动作。"""
        with self._lock:
            self._ticks += 1
            # 1) 消息抢占：有新消息 → 让位，本轮不动作
            if self.preempt.consume():
                self.budget.reset()
                result = {"tick": self._ticks, "action": "让位", "reason": "新消息到达"}
                _emit_safely("tick", result)
                return result
            # 2) 发言边界：仅空闲态可主动发声
            state = self._busy()
            if state != "idle":
                self.budget.reset()
                result = {"tick": self._ticks, "action": "等待", "reason": f"当前状态 {state} 不主动发声"}
                _emit_safely("tick", result)
                return result
            # 3) 空闲思考预算：封顶
            if not self.budget.try_use():
                result = {"tick": self._ticks, "action": "静默", "reason": "空闲思考预算已封顶"}
                _emit_safely("tick", result)
                return result
            proposal = {"tick": self._ticks, "action": "主动发声", "reason": "空闲心跳",
                        "budget_left": self.config.idle_budget_max - self.budget.used}
            self._proposals.append(proposal)
            _emit_safely("tick", proposal)
            return proposal

    def snapshot(self) -> dict[str, Any]:
        return {
            "ticks": self._ticks,
            "budget_used": self.budget.used,
            "budget_max": self.config.idle_budget_max,
            "preempt_count": self.preempt.count,
            "proposals": list(self._proposals),
        }


__all__ = ["HeartbeatTicker", "HeartbeatConfig", "MessagePreempt", "IdleBudget"]
