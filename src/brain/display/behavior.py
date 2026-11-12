"""悬浮球与组合窗口行为层（s3-behavior-layer · M07/M08）。

在已冻结悬浮球/组合窗口对外行为之上做增量补齐（不推翻）：
1. 心跳/思考/聆听三态可视化：任务/语音/编排状态事件 → 可视化状态映射；
2. 记忆可视化：记忆节点/关联点亮（能力边界适度，不对齐完整焦点栈）；
3. 组合窗口多场景编排：对话/任务/环境/长内容场景组件树动态组装；
4. 主题令牌全量对齐 + 状态事件全量映射；
5. AR/VR 接口预留登记（远期，仅接口）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional

# ── 主题令牌（对齐 theme-standard） ────────────────────────────────────────

THEME_TOKENS = {
    "background": "#0a0a0f",
    "surface": "#12121a",
    "primary": "#1a1a24",
    "accent": "#3d5afe",
    "text": "#e8e8f0",
    "muted": "#8a8aa0",
    "danger": "#ff5252",
    "success": "#4caf50",
    "idle_glow": "#1a1a24",
    "thinking_glow": "#3d5afe",
    "listening_glow": "#4caf50",
    "speaking_glow": "#ff9800",
    "memory_lit": "#7c4dff",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ── 1. 状态事件 → 可视化映射 ───────────────────────────────────────────────

@dataclass
class VisualState:
    """悬浮球可视化状态（由源事件映射而来）。"""
    state: str                      # idle | thinking | listening | speaking | busy
    glow_color: str
    breathe_amp: float              # 呼吸幅度（0~1）
    breathe_period_s: float
    label: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "state": self.state, "glow_color": self.glow_color,
            "breathe_amp": self.breathe_amp, "breathe_period_s": self.breathe_period_s,
            "label": self.label,
        }


class BehaviorMapper:
    """状态事件全量映射：源事件（任务/语音/编排）→ 可视化状态。"""

    _MAP = {
        # 任务事件
        "task.running": VisualState("busy", THEME_TOKENS["primary"], 0.06, 2.4, "任务执行中"),
        "task.waiting": VisualState("idle", THEME_TOKENS["idle_glow"], 0.03, 4.0, "待命中"),
        "task.done": VisualState("idle", THEME_TOKENS["success"], 0.05, 3.0, "任务完成"),
        "task.error": VisualState("busy", THEME_TOKENS["danger"], 0.10, 1.6, "任务异常"),
        # 语音事件
        "voice.listening": VisualState("listening", THEME_TOKENS["listening_glow"], 0.05, 2.0, "聆听中"),
        "voice.thinking": VisualState("thinking", THEME_TOKENS["thinking_glow"], 0.07, 2.2, "思考中"),
        "voice.speaking": VisualState("speaking", THEME_TOKENS["speaking_glow"], 0.08, 2.0, "播报中"),
        "voice.idle": VisualState("idle", THEME_TOKENS["idle_glow"], 0.03, 4.0, "待命中"),
        # 编排事件
        "queue.progress": VisualState("busy", THEME_TOKENS["primary"], 0.06, 2.4, "队列推进中"),
    }

    def map(self, event: str) -> VisualState:
        return self._MAP.get(event, VisualState("idle", THEME_TOKENS["idle_glow"], 0.03, 4.0))

    @property
    def coverage(self) -> list[str]:
        return sorted(self._MAP.keys())


# ── 2. 记忆可视化 ──────────────────────────────────────────────────────────

@dataclass
class MemoryNode:
    node_id: str
    kind: str            # declarative | procedural | working ...
    summary: str
    lit: bool = False    # 点亮

    def as_dict(self) -> dict[str, Any]:
        return {"node_id": self.node_id, "kind": self.kind,
                "summary": self.summary, "lit": self.lit}


class MemoryVisualizer:
    """记忆节点/关联点亮（适度能力：按事件点亮命中节点）。"""

    def __init__(self) -> None:
        self.nodes: dict[str, MemoryNode] = {}
        self.links: list[tuple[str, str]] = []

    def add(self, node_id: str, kind: str, summary: str) -> None:
        self.nodes[node_id] = MemoryNode(node_id, kind, summary)

    def link(self, a: str, b: str) -> None:
        if a in self.nodes and b in self.nodes and (a, b) not in self.links:
            self.links.append((a, b))

    def light(self, node_ids: list[str]) -> list[str]:
        lit: list[str] = []
        for nid in node_ids:
            node = self.nodes.get(nid)
            if node is not None and not node.lit:
                node.lit = True
                lit.append(nid)
        return lit

    def snapshot(self) -> dict[str, Any]:
        return {
            "nodes": [n.as_dict() for n in self.nodes.values()],
            "links": [list(l) for l in self.links],
            "lit_count": sum(1 for n in self.nodes.values() if n.lit),
        }


# ── 3. 组合窗口多场景编排 ──────────────────────────────────────────────────

@dataclass
class SceneComponent:
    comp_id: str
    kind: str            # header | chat | tasklist | envcard | article | footer
    payload: dict[str, Any] = field(default_factory=dict)


SCENE_COMPONENT_ORDER: dict[str, list[str]] = {
    "对话": ["header", "chat", "footer"],
    "任务": ["header", "tasklist", "footer"],
    "环境": ["header", "envcard", "footer"],
    "长内容": ["header", "article", "footer"],
}


class SceneComposer:
    """组合窗口多场景组件树动态组装（增量完善，不推翻既有场景）。"""

    def __init__(self) -> None:
        self._scenes: dict[str, list[SceneComponent]] = {}
        self._recent: Optional[str] = None

    def assemble(self, scene: str, payloads: Optional[dict[str, dict[str, Any]]] = None) -> list[SceneComponent]:
        if scene not in SCENE_COMPONENT_ORDER:
            raise ValueError(f"未知场景 {scene}（支持：{list(SCENE_COMPONENT_ORDER)}）")
        order = SCENE_COMPONENT_ORDER[scene]
        payloads = payloads or {}
        comps = [SceneComponent(f"{scene}.{kind}", kind, payloads.get(kind, {})) for kind in order]
        self._scenes[scene] = comps
        self._recent = scene
        return comps

    def tree(self) -> dict[str, Any]:
        return {
            "recent": self._recent,
            "scenes": {k: [c.comp_id for c in v] for k, v in self._scenes.items()},
        }

    def regression_ok(self) -> bool:
        """既有场景回归：对话/任务/环境/长内容均可组装出完整组件序。"""
        return all(self.assemble(s) for s in SCENE_COMPONENT_ORDER)


# ── 4/5. AR/VR 接口预留 ────────────────────────────────────────────────────

class XRInterfaceReserve:
    """AR/VR 接口预留登记（远期，仅接口不实现）。"""

    def __init__(self) -> None:
        self.registered: dict[str, dict[str, Any]] = {
            "xr.frame": {"stage": "预留", "desc": "沉浸帧同步回调", "impl": False},
            "xr.gesture": {"stage": "预留", "desc": "手势/注视输入归一化", "impl": False},
            "xr.space": {"stage": "预留", "desc": "空间锚点与坐标系", "impl": False},
        }

    def register(self, name: str, desc: str) -> None:
        self.registered[name] = {"stage": "预留", "desc": desc, "impl": False}

    def snapshot(self) -> dict[str, Any]:
        return {"interfaces": self.registered, "reserved_at": _now_iso()}


__all__ = ["BehaviorMapper", "MemoryVisualizer", "SceneComposer", "XRInterfaceReserve",
           "THEME_TOKENS", "VisualState"]
