"""L0/L6 悬浮球状态机（P2 #64，Claw 路线 + emotionId）。

对齐 theme-standard §4（图波主题 v1 悬浮球附件：流体玻璃球、
五态动画、emotionId 情绪表达）与 product-plan L6「悬浮球状态绑定」：
- 五态状态机：idle / listening / thinking / talking / processing / failed；
- 状态迁移带合法性约束（防非法跳变），过渡即发事件；
- emotionId 映射：每状态绑定情绪标识 + 视觉参数（Claw 路线：
  玻璃球颜色 / 透明度 / 流体强度 / 动画令牌）；
- 语音状态绑定：对接 src.brain.voice（TTS/ASR 子进程桥接状态），
  说话=音浪驱动、倾听=呼吸节奏、思考=液流加速；
- 输出渲染指令 dict（供宿主壳 WebView2 CSS/JS 消费，不依赖宿主壳）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

# 合法状态（对齐 theme-standard §4.3 + 毒液 ORB 方案 §4.3 五态）
VALID_STATES = (
    "idle",
    "listening",
    "thinking",
    "talking",
    "processing",
    "failed",
)

# 合法迁移（源状态 → 可迁入状态集）
_TRANSITIONS: Dict[str, frozenset] = {
    "idle": frozenset({"listening", "thinking", "talking", "processing", "failed"}),
    "listening": frozenset({"thinking", "talking", "processing", "idle", "failed"}),
    "thinking": frozenset({"talking", "processing", "idle", "listening", "failed"}),
    "talking": frozenset({"idle", "thinking", "processing", "listening", "failed"}),
    "processing": frozenset({"idle", "talking", "thinking", "listening", "failed"}),
    "failed": frozenset({"idle", "listening"}),
}

# 每状态 emotionId + Claw 视觉参数（图波主题 v1 令牌）
_EMOTION_PARAMS: Dict[str, Dict[str, Any]] = {
    "idle": {
        "emotionId": "calm",
        "label": "待机",
        "color": "#7cc6f4",
        "glass_opacity": 0.38,
        "fluid_strength": 0.25,
        "animation": "breathe-slow",
        "active_band": 0,
    },
    "listening": {
        "emotionId": "listening",
        "label": "倾听",
        "color": "#7cc6f4",
        "glass_opacity": 0.40,
        "fluid_strength": 0.4,
        "animation": "breathe-wave",
        "active_band": 1,
    },
    "thinking": {
        "emotionId": "thinking",
        "label": "思考",
        "color": "#5a7bff",
        "glass_opacity": 0.42,
        "fluid_strength": 0.65,
        "animation": "radar-accelerate",
        "active_band": 2,
    },
    "talking": {
        "emotionId": "speaking",
        "label": "说话",
        "color": "#7fa3ff",
        "glass_opacity": 0.45,
        "fluid_strength": 1.0,
        "animation": "audio-wave",
        "active_band": 3,
    },
    "processing": {
        "emotionId": "working",
        "label": "处理中",
        "color": "#ffa94d",
        "glass_opacity": 0.42,
        "fluid_strength": 0.5,
        "animation": "pulse-amber",
        "active_band": 4,
    },
    "failed": {
        "emotionId": "error",
        "label": "失败",
        "color": "#ff5a5a",
        "glass_opacity": 0.46,
        "fluid_strength": 0.6,
        "animation": "pulse-red",
        "active_band": 5,
    },
}


@dataclass
class OrbEvent:
    """一次状态迁移事件。"""

    from_state: str
    to_state: str
    ts: str
    payload: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_state": self.from_state,
            "to_state": self.to_state,
            "ts": self.ts,
            "payload": self.payload,
        }


class OrbStateMachine:
    """悬浮球状态机（底座侧，宿主壳消费渲染指令）。

    Parameters
    ----------
    initial_state:
        初始状态，默认 idle。
    on_transition:
        可选回调，每次迁移后调用（事件订阅，对齐 plugin-bus KP-006）。
    """

    def __init__(
        self,
        initial_state: str = "idle",
        *,
        on_transition: Optional[Callable[[OrbEvent], None]] = None,
    ) -> None:
        if initial_state not in VALID_STATES:
            raise ValueError(f"initial_state 非法: {initial_state}")
        self._state = initial_state
        self._on_transition = on_transition
        self._events: List[OrbEvent] = []

    # ------------------------------------------------------------------
    # 状态
    # ------------------------------------------------------------------
    @property
    def state(self) -> str:
        return self._state

    def transition(
        self,
        to_state: str,
        *,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """迁移到 *to_state*。非法迁移返回 False 并记录（不抛错）。

        failed → 仅可回 idle / listening（对齐状态语义：错误需复位）。
        """
        if to_state not in VALID_STATES:
            return False
        if to_state == self._state:
            return True  # 幂等：同状态不产生事件
        allowed = _TRANSITIONS.get(self._state, frozenset())
        if to_state not in allowed:
            self._events.append(
                OrbEvent(
                    from_state=self._state,
                    to_state=to_state,
                    ts=self._now(),
                    payload={"invalid": True, "reason": "迁移不被允许"},
                )
            )
            return False
        self._events.append(
            OrbEvent(
                from_state=self._state,
                to_state=to_state,
                ts=self._now(),
                payload=payload or {},
            )
        )
        self._state = to_state
        if self._on_transition is not None:
            self._on_transition(self._events[-1])
        return True

    # ------------------------------------------------------------------
    # 语音状态绑定（对接 src.brain.voice）
    # ------------------------------------------------------------------
    def bind_voice_status(self, voice_status: Dict[str, Any]) -> bool:
        """按语音链路状态映射悬浮球状态（best-effort）。

        Parameters
        ----------
        voice_status:
            来自 voice 桥接的状态 dict，支持：
            - {"kind": "tts_started" | "tts_done" | "asr_started" |
               "asr_done" | "idle" | "error"}
            - 或 {"state": "listening"|"talking"|...} 直接指定。

        Returns
        -------
        bool
            是否发生了有效迁移。
        """
        kind = voice_status.get("kind") or voice_status.get("state")
        if kind is None:
            return False
        mapping = {
            "tts_started": "talking",
            "tts_done": "idle",
            "asr_started": "listening",
            "asr_done": "thinking",
            "thinking": "thinking",
            "processing": "processing",
            "error": "failed",
            "idle": "idle",
        }
        target = mapping.get(kind)
        if target is None:
            return False
        return self.transition(target, payload={"source": "voice", "kind": kind})

    # ------------------------------------------------------------------
    # 渲染指令（供宿主壳 WebView2 CSS/JS 消费，Claw 路线）
    # ------------------------------------------------------------------
    def render_command(self) -> Dict[str, Any]:
        """输出当前状态渲染指令（HS-005 语义，宿主壳消费）。"""
        params = _EMOTION_PARAMS[self._state]
        return {
            "kind": "orb.render",
            "state": self._state,
            "emotionId": params["emotionId"],
            "label": params["label"],
            "visual": {
                "color": params["color"],
                "glass_opacity": params["glass_opacity"],
                "fluid_strength": params["fluid_strength"],
                "animation": params["animation"],
                "active_band": params["active_band"],
            },
            "ts": self._now(),
        }

    def emotion_params(self, state: Optional[str] = None) -> Dict[str, Any]:
        """返回指定状态（默认当前态）的完整情绪参数。"""
        s = state or self._state
        return dict(_EMOTION_PARAMS.get(s, _EMOTION_PARAMS["idle"]))

    # ------------------------------------------------------------------
    # 审计
    # ------------------------------------------------------------------
    def events(self, last_n: Optional[int] = None) -> List[OrbEvent]:
        """返回事件流（append-only，供审计）。"""
        if last_n is None:
            return list(self._events)
        return self._events[-last_n:]

    def snapshot(self) -> Dict[str, Any]:
        return {
            "state": self._state,
            "emotionId": _EMOTION_PARAMS[self._state]["emotionId"],
            "event_count": len(self._events),
            "last_event": self._events[-1].to_dict() if self._events else None,
        }

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


__all__ = ["OrbStateMachine", "OrbEvent", "VALID_STATES", "OrbEvent"]
