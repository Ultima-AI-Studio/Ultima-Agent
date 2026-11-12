"""L2 技能白名单策略（未授权拒绝 100%，对齐 L8 基线）。

对齐 tech-progression-plan §2.4「社区/能力模块先入白名单审计，
不合规不启用」与 guardrails/policy.py 的确定性授权范式：
- 白名单内技能 → 放行（allow）；
- 未登记/未入白名单技能 → 拒绝（deny），原因记录；
- 白名单 = 静态登记表（SkillRegistry 任务域）+ 动态追加授权集。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Optional, Set

from .registry import SkillRegistry


@dataclass
class SkillDecision:
    """一次技能授权判定结果。"""

    allowed: bool
    reason: str
    action: str = ""  # "allow" | "deny"
    skill_id: str = ""
    record: object = None  # SkillRecord | None（允许时附登记）

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "action": self.action,
            "skill_id": self.skill_id,
        }


class SkillWhitelist:
    """技能白名单策略。

    Parameters
    ----------
    allowed_skills:
        动态追加授权技能集（如任务域外试点技能）。默认空。
    require_registered:
        是否要求技能必须先静态登记（registry.md 纪律，默认 True）。
    """

    def __init__(
        self,
        allowed_skills: Optional[Iterable[str]] = None,
        *,
        require_registered: bool = True,
    ) -> None:
        self._extra: Set[str] = set(allowed_skills or [])
        self._require_registered = require_registered

    # -- 判定 ------------------------------------------------------------

    def check(self, skill_id: str) -> SkillDecision:
        """判定技能是否授权。

        Rules
        -----
        A. require_registered=True（默认，注册表即白名单）：
           1. 未静态登记 → 拒绝（未登记不得使用）；
           2. 静态登记且 resident（任务域 11 技能）→ 放行；
           3. 静态登记但非 resident → 仅在 extra 授权集内放行。
        B. require_registered=False（注册表仅目录，白名单=extra 集）：
           1. 未在 extra 授权集 → 拒绝（未授权拒绝）；
           2. 在 extra → 放行。
        """
        registered = SkillRegistry.exists(skill_id)

        if not registered:
            # 未登记：仅 B 场景下 extra 显式授权可放行
            if self._require_registered or skill_id not in self._extra:
                return SkillDecision(
                    allowed=False,
                    reason=f"技能 '{skill_id}' 未静态登记（未登记不得使用）",
                    action="deny",
                    skill_id=skill_id,
                )
            return SkillDecision(
                allowed=True,
                reason=f"技能 '{skill_id}' 经 extra 显式授权（未登记但已授权）",
                action="allow",
                skill_id=skill_id,
            )

        # 已登记
        record = SkillRegistry.get(skill_id)
        if not self._require_registered:
            # 目录模式：仅 extra 授权
            if skill_id not in self._extra:
                return SkillDecision(
                    allowed=False,
                    reason=f"技能 '{skill_id}' 未在授权白名单中（未授权拒绝）",
                    action="deny",
                    skill_id=skill_id,
                )
            return SkillDecision(
                allowed=True,
                reason=f"技能 '{skill_id}' 已授权（extra 集）",
                action="allow",
                skill_id=skill_id,
                record=record,
            )
        # 注册表模式
        if record.resident:
            return SkillDecision(
                allowed=True,
                reason=f"技能 '{skill_id}' 已授权（驻留技能）",
                action="allow",
                skill_id=skill_id,
                record=record,
            )
        if skill_id not in self._extra:
            return SkillDecision(
                allowed=False,
                reason=f"技能 '{skill_id}' 静态登记但非驻留、未入授权集（未授权拒绝）",
                action="deny",
                skill_id=skill_id,
            )
        return SkillDecision(
            allowed=True,
            reason=f"技能 '{skill_id}' 已授权（extra 集）",
            action="allow",
            skill_id=skill_id,
            record=record,
        )

    def is_allowed(self, skill_id: str) -> bool:
        return self.check(skill_id).allowed

    # -- 动态授权集 ------------------------------------------------------

    def add(self, skill_id: str) -> None:
        self._extra.add(skill_id)

    def remove(self, skill_id: str) -> None:
        self._extra.discard(skill_id)

    # -- 快照 ------------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "task_domain_skills": sorted(
                r.skill_id for r in SkillRegistry.all()
            ),
            "extra_allowed": sorted(self._extra),
            "require_registered": self._require_registered,
        }


__all__ = ["SkillWhitelist", "SkillDecision"]
