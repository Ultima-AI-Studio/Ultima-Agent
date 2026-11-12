"""能力清单指令页（s6-capability-page · B 类）。

解决"不知道 Agent 能干什么"：把已实现能力盘点为同源数据源，供双界面线呈现：
- 数据权威：sync/capability-manifest.json（单一来源，悬浮球与组合窗口同读）；
- 悬浮球侧：语音意图 capability.query → summarize 摘要文本 → 既有 TTS 播报；
- 组合窗口侧：to_a2ui_messages → ActiveRenderer → 安全 HTML（零 JS CSP），
  可直接进组合窗口 WebView2 / A2UI 链路。

安全约束：
- 只读数据源，不写回；缺失/损坏文件确定性报错；
- A2UI 组件走 active_renderer schema 白名单（UltimaListCard/UltimaStatusTag/Text），
  无任意样式注入；
- 不把"规划中"项当可用（planned 独立分组）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MANIFEST = PROJECT_ROOT / "sync" / "capability-manifest.json"


class CapabilityError(Exception):
    """能力清单确定性错误。"""


def load_manifest(path: Optional[Path] = None) -> dict[str, Any]:
    """读取同源能力清单（只读；缺失/损坏确定性报错）。"""
    target = Path(path) if path is not None else DEFAULT_MANIFEST
    if not target.exists():
        raise CapabilityError(f"能力清单不存在：{target}")
    try:
        raw = target.read_text(encoding="utf-8")
        data = json.loads(raw)
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise CapabilityError(f"能力清单无法解析：{target}（{exc}）") from exc
    if not isinstance(data, dict) or "capabilities" not in data:
        raise CapabilityError(f"能力清单结构非法：{target}（缺 capabilities 字段）")
    return data


def summarize(manifest: dict[str, Any]) -> str:
    """生成结构化中文摘要（供语音播报：总数/类别/示例可呼唤）。"""
    caps = manifest.get("capabilities") or []
    if not isinstance(caps, list):
        raise CapabilityError("能力清单 capabilities 字段非法")
    available = [c for c in caps if isinstance(c, dict) and c.get("status") == "可用"]
    planned = manifest.get("planned") or []
    total = len(available)
    if total == 0:
        return "我当前没有已上线的可用能力。"
    # 可呼唤示例（前 5 个非被动/非占位 voice_call）
    callable_examples = []
    for cap in available:
        call = str(cap.get("voice_call", "")).strip()
        if (
            call
            and "被动" not in call
            and "（" not in call
            and ")" not in call
            and len(callable_examples) < 5
        ):
            callable_examples.append(call)
    example_text = "、".join(callable_examples) if callable_examples else "（多为被动支撑能力）"
    planned_text = f"另有 {len(planned)} 项规划中能力（{', '.join(str(p.get('name', '')) for p in planned[:3])} 等）。" if planned else ""
    return (
        f"我当前有 {total} 项可用能力，涵盖：语音对话、悬浮球与组合窗口、任务队列与子智能体、"
        f"联网检索、浏览器只读操作、本机执行通道、环境认知、记忆与人格、安全闸门、"
        f"审计留痕、外部深度模型路由等。你可以对我说：{example_text}。{planned_text}"
    )


def to_a2ui_messages(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    """把能力清单转为 A2UI messages（组合窗口同源呈现，active_renderer 可渲染）。"""
    caps = manifest.get("capabilities") or []
    planned = manifest.get("planned") or []
    components: list[dict[str, Any]] = []
    child_ids: list[str] = []
    idx = 0

    def cid(tag: str) -> str:
        nonlocal idx
        idx += 1
        return f"cap-{tag}-{idx}"

    def text(value: str, usage: str = "body") -> str:
        t_id = cid("text")
        components.append({"id": t_id, "component": {
            "Text": {"text": {"literalString": value}, "usageHint": usage},
        }})
        return t_id

    def status_tag(label: str, state: str) -> str:
        s_id = cid("tag")
        components.append({"id": s_id, "component": {
            "UltimaStatusTag": {"label": {"literalString": label}, "state": state},
        }})
        return s_id

    # 标题
    head = text("UltimaAgent 能力清单", "h2")
    sub = text(f"共 {len(caps)} 项可用能力 · 双界面线同源呈现（悬浮球 / 组合窗口）", "caption")
    card_ids: list[str] = []
    for cap in caps:
        if not isinstance(cap, dict):
            continue
        card_children: list[str] = []
        desc = str(cap.get("description", ""))
        if desc:
            card_children.append(text(desc))
        name = str(cap.get("name", cap.get("id", "")))
        status = str(cap.get("status", "可用"))
        state = "normal" if status == "可用" else "info"
        call = str(cap.get("voice_call", "")).strip()
        if call and "被动" not in call:
            card_children.append(text(f"可呼唤：{call}"))
        card_children.append(status_tag(name, state))
        card_id = cid("listcard")
        components.append({"id": card_id, "component": {
            "UltimaListCard": {
                "title": {"literalString": name},
                "children": {"explicitList": card_children},
            },
        }})
        card_ids.append(card_id)
    # 规划中
    if planned:
        planned_children = [text("阶段后置项（规划中，不作可用）：")]
        for item in planned:
            planned_children.append(
                text(f"{item.get('name', item.get('id', ''))}（{item.get('phase', '')}）")
            )
        planned_card = cid("listcard")
        components.append({"id": planned_card, "component": {
            "UltimaListCard": {
                "title": {"literalString": "规划中能力"},
                "children": {"explicitList": planned_children},
            },
        }})
        card_ids.append(planned_card)

    root = cid("column")
    components.append({"id": root, "component": {
        "Column": {"children": {"explicitList": [head, sub] + card_ids}},
    }})
    surface_id = "capability-overview"
    from src.window.a2ui_validator import ULTIMA_CATALOG_ID

    return [
        {"surfaceUpdate": {"surfaceId": surface_id, "components": components}},
        {"beginRendering": {
            "surfaceId": surface_id, "catalogId": ULTIMA_CATALOG_ID, "root": root,
        }},
    ]


def render_capability_page(
    manifest: dict[str, Any],
    *,
    title: str = "UltimaAgent 能力清单",
) -> str:
    """组合窗口侧：A2UI 安全渲染能力清单页（ActiveRenderer，零 JS CSP）。"""
    from src.window.active_renderer import render_active_html

    messages = to_a2ui_messages(manifest)
    return render_active_html(messages, title=title)


__all__ = [
    "load_manifest", "summarize", "to_a2ui_messages", "render_capability_page",
    "CapabilityError", "DEFAULT_MANIFEST",
]
