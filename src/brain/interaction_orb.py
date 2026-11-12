"""L7 悬浮球征询载体接线（InteractionLoop ↔ OrbStateMachine 桥接）。

对齐 product-plan v2.3 §6 L7 验收口径（征询闭环 + 异步三拍）与
用户拍板「L7 征询载体=悬浮球」：

- 交互响应（InteractionResponse）→ 悬浮球六态 + 征询文本（prompt）
  映射，输出 orb.render 渲染指令（HS-005 契约，宿主壳 WebView2 消费）；
- 征询闭环在悬浮球上的呈现：
  查询完成 → 悬浮球 talking（交付呈现，prompt=结果摘要）
  → 征询（"你觉得怎么样"）→ 确认 → idle 待命；
- 异步三拍第一拍 acknowledge_delivery → thinking（"稍等，我整理一下"）；
- 调整指令（插队/优先级）→ 完成回 idle / 失败 failed 提示；
- 状态迁移合法性由 OrbStateMachine 校验（非法迁移不产生事件）；
- 事件流 append-only（含 prompt 文本），供审计。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .interaction import InteractionLoop, InteractionResponse
from .display.orb import OrbStateMachine

# 征询提示前缀（对齐 product-plan L7 征询闭环口径）
_CONSULT_PROMPT = "你觉得怎么样？需要调整（插队或改优先级）可以说，或回复确认。"


@dataclass(frozen=True, slots=True)
class OrbBridgeEvent:
    """一次桥接事件（状态迁移 + 征询文本），append-only。"""

    ts: str
    from_state: str
    to_state: str
    reason: str
    prompt: str
    ok: bool

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class InteractionOrbBridge:
    """L7 交互循环 → 悬浮球载体桥接器。

    Parameters
    ----------
    queue_root:
        任务库根目录（透传给 InteractionLoop）。
    """

    def __init__(self, queue_root: str | Path) -> None:
        self.loop = InteractionLoop(queue_root)
        self.orb = OrbStateMachine(initial_state="idle")
        self._events: List[OrbBridgeEvent] = []

    # ------------------------------------------------------------------
    # 对外入口：处理一条交互文本（文字/语音均走此入口）
    # ------------------------------------------------------------------
    def handle(self, text: str | None, *, detail_task_id: str | None = None) -> InteractionResponse:
        """处理用户输入，按响应语义驱动悬浮球状态与征询文本。"""
        response = self.loop.handle(text, detail_task_id=detail_task_id)
        self._apply_response(response)
        return response

    def acknowledge_delivery(self, summary: str | None = None) -> str:
        """异步交付三拍第一拍：告知"稍等，我整理一下"（悬浮球 thinking）。"""
        text = self.loop.acknowledge_delivery(summary)
        self._transition("thinking", reason="异步交付告知", prompt=text, ok=True)
        return text

    # ------------------------------------------------------------------
    # 悬浮球状态映射（response → orb 状态 + prompt）
    # ------------------------------------------------------------------
    def _apply_response(self, response: InteractionResponse) -> None:
        reason = response.reason
        text = response.text or ""
        ok = response.ok
        phase = response.state.phase

        if reason == "查询完成":
            # 交付呈现 + 征询待命（征询闭环第一步）
            self._transition(
                "talking",
                reason=reason,
                prompt=_CONSULT_PROMPT if ok else text,
                ok=ok,
                last_text=text,
            )
            return
        if reason == "征询中":
            self._transition("talking", reason=reason, prompt=text, ok=True)
            return
        if reason == "确认通过":
            self._transition("idle", reason=reason, prompt=text, ok=True)
            return
        if reason == "等待调整参数":
            # 泛调整意图：等待用户给出具体参数（倾听语义）
            self._transition("listening", reason=reason, prompt=text, ok=True)
            return
        if reason == "子智能体调用":
            # 子智能体调度入口：交付提示（talking 呈现引导文本）
            self._transition("talking", reason=reason, prompt=text, ok=True)
            return
        if reason == "调整完成":
            self._transition("idle", reason=reason, prompt=text, ok=True)
            return
        if reason == "调整失败":
            self._transition("failed", reason=reason, prompt=text, ok=False)
            return
        if reason == "无待确认结果":
            self._transition("idle", reason=reason, prompt=text, ok=True)
            return
        if reason == "未命中":
            self._transition("idle", reason=reason, prompt="", ok=True)
            return
        if reason == "空输入":
            # 保持现状（不产生迁移）
            self._events.append(
                OrbBridgeEvent(
                    ts=self._now(),
                    from_state=self.orb.state,
                    to_state=self.orb.state,
                    reason=reason,
                    prompt="",
                    ok=True,
                )
            )
            return
        # 兜底：保持现状
        self._events.append(
            OrbBridgeEvent(
                ts=self._now(),
                from_state=self.orb.state,
                to_state=self.orb.state,
                reason=reason or "未知",
                prompt="",
                ok=ok,
            )
        )

    # ------------------------------------------------------------------
    # 内部：迁移 + 事件记录
    # ------------------------------------------------------------------
    def _transition(
        self,
        to_state: str,
        *,
        reason: str,
        prompt: str,
        ok: bool,
        last_text: str = "",
    ) -> None:
        from_state = self.orb.state
        transitioned = self.orb.transition(to_state)
        # 征询文本优先级：显式 prompt 优先，否则用最近结果文本
        display_prompt = prompt or last_text
        self._events.append(
            OrbBridgeEvent(
                ts=self._now(),
                from_state=from_state,
                to_state=self.orb.state,
                reason=reason,
                prompt=display_prompt,
                ok=ok,
            )
        )
        if not transitioned:
            # 非法迁移：记录但不抛（状态机语义：保持原状态）
            return

    # ------------------------------------------------------------------
    # 输出
    # ------------------------------------------------------------------
    def orb_command(self) -> Dict[str, Any]:
        """当前悬浮球渲染指令（orb.render + prompt 征询文本通道）。"""
        command = self.orb.render_command()
        command["prompt"] = self._latest_prompt()
        return command

    def _latest_prompt(self) -> str:
        if not self._events:
            return ""
        return self._events[-1].prompt

    def events(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """桥接事件流（append-only，供审计）。"""
        events = self._events if last_n is None else self._events[-last_n:]
        return [event.to_dict() for event in events]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "orb_state": self.orb.state,
            "last_prompt": self._latest_prompt(),
            "event_count": len(self._events),
            "last_event": self._events[-1].to_dict() if self._events else None,
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


__all__ = ["InteractionOrbBridge", "OrbBridgeEvent"]
