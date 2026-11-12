"""反思条目与遗忘边界（s3-memory-base · ACCEPT-3）。

- 反思条目：kind=reflection，写入程序式层（procedural），由审计/评估驱动
  （对齐 jarvis-reverse-architecture §1.2.7 域⑦：反思条目回写程序式记忆）；
- 遗忘边界：retention_days + max_entries 规则生效（由 MemoryLayers 强制执行），
  本模块提供规则查询与驱逐统计。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .layers import MemoryLayers, MemoryEntry


@dataclass
class Reflection:
    id: str = ""
    ts: str = ""
    content: str = ""
    target: str = ""          # 反思指向的对象（任务/模块/事件）
    outcome: str = ""         # 结论（keep/change/stop）
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id, "ts": self.ts, "content": self.content,
            "target": self.target, "outcome": self.outcome, "note": self.note,
        }


class ReflectionWriter:
    """反思条目写入器：反思结果以 reflection 类型落程序式记忆。"""

    def __init__(self, layers: MemoryLayers) -> None:
        self._layers = layers

    def write(
        self,
        content: str,
        *,
        target: str,
        outcome: str,
        note: str = "",
        source: str = "engine",
    ) -> Reflection:
        entry = self._layers.write(
            "procedural",
            content,
            kind="reflection",
            trusted=True,
            source=source,
            meta={"reflection": {"target": target, "outcome": outcome, "note": note}},
        )
        return Reflection(
            id=entry.id, ts=entry.ts, content=entry.content,
            target=target, outcome=outcome, note=note,
        )

    def list(self, top_k: int = 20) -> list[Reflection]:
        out = []
        for entry in self._layers.read("", layer="procedural", top_k=top_k,
                                       kinds=("reflection",)):
            meta = entry.meta.get("reflection", {})
            out.append(Reflection(
                id=entry.id, ts=entry.ts, content=entry.content,
                target=meta.get("target", ""), outcome=meta.get("outcome", ""),
                note=meta.get("note", ""),
            ))
        return out


def forgetting_rules(layers: MemoryLayers) -> dict[str, Any]:
    """遗忘边界规则快照（供审计/查询）。"""
    return {
        "retention_days": dict(layers.retention_days),
        "max_entries": dict(layers.max_entries),
        "stats": layers.stats(),
    }


__all__ = ["ReflectionWriter", "Reflection", "forgetting_rules"]
