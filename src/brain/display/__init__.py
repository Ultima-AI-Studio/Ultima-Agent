"""L0/L6 输出呈现（P2 #64）。

悬浮球状态机（OrbStateMachine）：五态 + emotionId + Claw 路线视觉参数，
供宿主壳（WebView2 CSS/JS）消费渲染指令。语音链路（src.brain.voice）
经 bind_voice_status 驱动状态迁移。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from .orb import OrbEvent, OrbStateMachine, VALID_STATES

__all__ = ["OrbStateMachine", "OrbEvent", "VALID_STATES"]
