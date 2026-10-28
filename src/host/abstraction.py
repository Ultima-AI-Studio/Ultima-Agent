"""S13 宿主抽象层（M25 前置 · roadmap Next）。

对齐 ADR-001 三层架构：终端宿主薄壳（四 IO + 渲染 + 协议）/ 智能体服务器
承载全部智能。本模块定义宿主抽象接口（协议），能力层只依赖接口不绑定
Windows 技术栈（ADR-004 Python 3.13 跨平台基线）；多端形态本体仍冻结
（无外设测试），本层仅做抽象与 Windows 适配，不做多端实现。

接口分组（对齐 ADR-001 四 IO + 渲染 + 协议）：
- HostIO（输入/输出）：文本/语音 输入输出；
- HostRenderer（渲染）：画布渲染（orb.render 指令）/ 窗口渲染（A2UI 组件树）；
- HostEvents（事件）：用户交互事件（征询响应 / 输入提交 / 画布交互）。

设计约束：
- 全部接口用 typing.Protocol（鸭子类型），零 Windows API / ctypes 依赖；
- 接口只定义签名与契约，不含业务智能（宿主薄壳定位）；
- 现有 Windows 实现（文件 IPC / 悬浮球）通过适配器接入，行为不倒退；
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


# ---------------------------------------------------------------------------
# 渲染指令契约（与现有 HostOrbPusher / orb.render 契约同构）
# ---------------------------------------------------------------------------
RENDER_KIND_ORB = "orb.render"


@runtime_checkable
class HostIO(Protocol):
    """宿主 IO 抽象：能力层与终端之间的输入输出通道（跨平台）。"""

    def send_text(self, text: str) -> dict[str, Any]:
        """向终端输出文本（结论先行，汇报范式由能力层负责）。返回投递回执。"""
        ...

    def send_voice(self, text: str, *, voice: str = "") -> dict[str, Any]:
        """向终端输出语音（TTS 播报）。voice 留空由宿主选默认音色。返回投递回执。"""
        ...

    def receive_input(self) -> list[dict[str, Any]]:
        """收取终端输入（文本/语音意图）。返回 [{kind,text,ts}] 列表；无输入返回空列表。"""
        ...


@runtime_checkable
class HostRenderer(Protocol):
    """宿主渲染抽象：画布（悬浮球）与窗口（组合窗口/A2UI）。"""

    def render_canvas(self, command: dict[str, Any]) -> dict[str, Any]:
        """渲染画布指令（如 orb.render）。command 须含 kind 与 state（契约校验）。返回落盘后指令。"""
        ...

    def render_window(self, component_tree: dict[str, Any]) -> dict[str, Any]:
        """渲染组合窗口（A2UI 组件树 DSL）。返回渲染回执。"""
        ...


@runtime_checkable
class HostEvents(Protocol):
    """宿主事件抽象：用户交互事件流（征询响应 / 提交 / 画布交互）。"""

    def poll_events(self, *, timeout_ms: int = 0) -> list[dict[str, Any]]:
        """轮询用户事件。返回 [{type,payload,ts}]；无事件返回空列表。"""
        ...

    def wait_event(self, *, timeout_ms: int = 0) -> dict[str, Any] | None:
        """阻塞等待下一条用户事件（用于征询等同步场景）；超时返回 None。"""
        ...


# ---------------------------------------------------------------------------
# 组合宿主（能力层统一入口）
# ---------------------------------------------------------------------------
class CompositeHost:
    """组合宿主：把 IO / 渲染 / 事件三组接口聚合为单一入口。

    能力层只依赖 CompositeHost 与上述 Protocol，不触碰任何终端实现细节。
    """

    def __init__(self, *, io: Any = None, renderer: Any = None,
                 events: Any = None) -> None:
        self.io = io
        self.renderer = renderer
        self.events = events

    # -- IO 透传 -------------------------------------------------------------

    def send_text(self, text: str) -> dict[str, Any]:
        if self.io is None or not hasattr(self.io, "send_text"):
            raise HostAbstractionError("宿主未接入 IO.send_text")
        return self.io.send_text(text)

    def send_voice(self, text: str, *, voice: str = "") -> dict[str, Any]:
        if self.io is None or not hasattr(self.io, "send_voice"):
            raise HostAbstractionError("宿主未接入 IO.send_voice")
        return self.io.send_voice(text, voice=voice)

    # -- 渲染透传 ------------------------------------------------------------

    def render_canvas(self, command: dict[str, Any]) -> dict[str, Any]:
        if self.renderer is None or not hasattr(self.renderer, "render_canvas"):
            raise HostAbstractionError("宿主未接入 Renderer.render_canvas")
        return self.renderer.render_canvas(command)

    def render_window(self, component_tree: dict[str, Any]) -> dict[str, Any]:
        if self.renderer is None or not hasattr(self.renderer, "render_window"):
            raise HostAbstractionError("宿主未接入 Renderer.render_window")
        return self.renderer.render_window(component_tree)

    # -- 事件透传 ------------------------------------------------------------

    def poll_events(self, *, timeout_ms: int = 0) -> list[dict[str, Any]]:
        if self.events is None or not hasattr(self.events, "poll_events"):
            return []
        return self.events.poll_events(timeout_ms=timeout_ms)

    def wait_event(self, *, timeout_ms: int = 0) -> dict[str, Any] | None:
        if self.events is None or not hasattr(self.events, "wait_event"):
            return None
        return self.events.wait_event(timeout_ms=timeout_ms)

    # -- 就绪自检 ------------------------------------------------------------

    def ready(self) -> dict[str, Any]:
        """宿主就绪自检：报告各接口是否接入（fail-closed 前预检）。"""
        return {
            "io": bool(self.io is not None),
            "renderer": bool(self.renderer is not None),
            "events": bool(self.events is not None),
            "complete": all(v is not None for v in (self.io, self.renderer, self.events)),
        }


class HostAbstractionError(Exception):
    """宿主抽象层操作失败。"""


__all__ = [
    "HostIO", "HostRenderer", "HostEvents", "CompositeHost",
    "HostAbstractionError", "RENDER_KIND_ORB",
]
