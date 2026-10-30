"""羁绊系统（s3-bond-system · M18）。

对齐 form-expansion-plan §3 阶段二 + jarvis-reverse-architecture §4.2 域⑥：
1. SOUL/MEMORY/USER 三档案组织；
2. 关系档位：默认=贾维斯式专业距离（克制、可靠）；亲密档=用户显式开放后启用；
3. 关系事实可回溯（append 历史）；称呼/口吻持久化；
4. 疲劳/无聊等不诚实表达模拟禁止（边界固化）；
5. 跨形态共享状态轴预留（单一 bond state 供各形态消费）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

TIERS = ("专业距离", "亲密")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


class BondError(Exception):
    pass


@dataclass
class SoulProfile:
    """SOUL 档案：身份与人格基线。"""
    name: str
    persona: str = "贾维斯式管家：专业、克制、朋友般可靠"
    tone_default: str = "标准中文管理语言，不拟人化不撒娇"
    created_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "persona": self.persona,
                "tone_default": self.tone_default, "created_at": self.created_at}


@dataclass
class RelationFact:
    ts: str
    kind: str        # tier_open | tone_change | address_change | note
    detail: str
    scope: str = "general"   # general | preference | interaction（关系记忆字段）

    def as_dict(self) -> dict[str, Any]:
        return {"ts": self.ts, "kind": self.kind, "detail": self.detail,
                "scope": self.scope}


class BondSystem:
    """羁绊状态轴：默认专业距离，亲密档需用户显式开放。"""

    def __init__(self, data_dir: str | Path, soul: Optional[SoulProfile] = None) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.soul = soul or SoulProfile(name="Ultima")
        self.tier = "专业距离"
        self.address = "用户"
        self.tone = self.soul.tone_default
        self.facts: list[RelationFact] = []
        self._load()

    def _load(self) -> None:
        p = self.data_dir / "bond-state.json"
        if not p.exists():
            return
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            self.tier = d.get("tier", "专业距离")
            self.address = d.get("address", "用户")
            self.tone = d.get("tone", self.soul.tone_default)
            self.facts = [RelationFact(**f) for f in d.get("facts", [])]
        except (json.JSONDecodeError, TypeError):
            pass

    def _save(self) -> None:
        (self.data_dir / "bond-state.json").write_text(
            json.dumps({
                "soul": self.soul.as_dict(), "tier": self.tier,
                "address": self.address, "tone": self.tone,
                "facts": [f.as_dict() for f in self.facts],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # -- 关系档位 -----------------------------------------------------------

    def open_intimate_tier(self, *, granted_by: str = "user") -> None:
        """亲密档必须用户显式开放（granted_by=user）。"""
        if granted_by != "user":
            raise BondError(f"亲密档只能由用户显式开放（收到 {granted_by}）")
        if self.tier != "亲密":
            self.tier = "亲密"
            self.facts.append(RelationFact(_now_iso(), "tier_open",
                                           f"用户显式开放亲密档（由 {granted_by} 授权）"))
            self._save()

    def set_address_and_tone(self, address: str, tone: str) -> None:
        """称呼/口吻变更（仅在亲密档下允许，且持久化）。"""
        if self.tier != "亲密":
            raise BondError("称呼/口吻升级需先开放亲密档")
        self.address = address
        self.tone = tone
        self.facts.append(RelationFact(_now_iso(), "address_change",
                                       f"称呼→{address}；口吻→{tone}"))
        self._save()

    def close_intimate_tier(self, *, granted_by: str = "user") -> None:
        """亲密档回退（阶段二验收：可回退；留痕）。"""
        if self.tier != "亲密":
            raise BondError("当前不在亲密档，无需回退")
        self.tier = "专业距离"
        self.address = "用户"
        self.tone = self.soul.tone_default
        self.facts.append(RelationFact(_now_iso(), "tier_open",
                                       f"亲密档回退至专业距离（由 {granted_by} 授权）",
                                       scope="general"))
        self._save()

    def add_note(self, detail: str, *, scope: str = "general") -> None:
        """关系记忆沉淀：用户偏好 / 互动史（kind=note，字段齐全可查询）。"""
        if scope not in ("general", "preference", "interaction"):
            raise BondError(f"未知关系记忆域：{scope}")
        if not detail or not str(detail).strip():
            raise BondError("关系记忆内容不能为空")
        self.facts.append(RelationFact(_now_iso(), "note", str(detail).strip(), scope))
        self._save()

    def get_notes(self, *, kind: Optional[str] = None,
                  scope: Optional[str] = None) -> list[dict[str, Any]]:
        """关系记忆可查询：全量 / 按 kind / 按 scope 过滤。"""
        out = []
        for f in self.facts:
            if kind is not None and f.kind != kind:
                continue
            if scope is not None and f.scope != scope:
                continue
            out.append(f.as_dict())
        return out

    # -- 边界固化（禁止模拟） ------------------------------------------------

    @staticmethod
    def honesty_boundary() -> dict[str, Any]:
        """疲劳/无聊等不诚实表达模拟被禁止（边界固化）。"""
        return {
            "simulate_fatigue": False,
            "simulate_boredom": False,
            "reason": "诚实边界：不模拟人类疲劳/无聊等不诚实表达；状态如实呈现",
        }

    # -- 关系事实回溯 -------------------------------------------------------

    def history(self) -> list[dict[str, Any]]:
        return [f.as_dict() for f in self.facts]

    # -- 跨形态共享状态轴 ---------------------------------------------------

    def state_axis(self) -> dict[str, Any]:
        """单一状态轴：各形态（悬浮球/组合窗口/语音）共享消费。"""
        return {
            "tier": self.tier,
            "address": self.address,
            "tone": self.tone,
            "honesty": self.honesty_boundary(),
            "relation_memory": {
                "notes_count": sum(1 for f in self.facts if f.kind == "note"),
                "preferences_count": sum(1 for f in self.facts
                                         if f.kind == "note" and f.scope == "preference"),
                "interactions_count": sum(1 for f in self.facts
                                          if f.kind == "note" and f.scope == "interaction"),
                "facts_total": len(self.facts),
            },
            "updated_at": _now_iso(),
        }


__all__ = ["BondSystem", "SoulProfile", "RelationFact", "BondError", "TIERS"]
