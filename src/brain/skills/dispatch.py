"""L2 任务域派发（domain.resolve 首域实现）。

对齐 api-contract L2 入口 domain.resolve 与 plugin-bus-spec §3.2：
- 输入：任务类型（category，如 code/ui/audit/...）；
- 输出：唯一技能 + 授权判定（白名单）或拒绝原因；
- 兜底：任务类型无法命中 → generic（仍须在白名单内）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from typing import Optional

from .registry import SkillRegistry
from .whitelist import SkillWhitelist, SkillDecision


def dispatch_decision(
    task_type: str,
    whitelist: Optional[SkillWhitelist] = None,
    *,
    fallback_generic: bool = True,
) -> SkillDecision:
    """按任务类型解析技能并做白名单判定。

    Parameters
    ----------
    task_type:
        任务卡 category（如 "code" / "ui" / "audit"）。
    whitelist:
        白名单实例；None 时使用全量任务域（registry 即白名单）。
    fallback_generic:
        任务类型无精确命中时是否兜底到 eng.generic。默认 True。

    Returns
    -------
    SkillDecision
        allowed=False 时 reason 说明拒绝原因（未登记/未授权/类型未知）。
    """
    wl = whitelist or SkillWhitelist(require_registered=True)

    # 1) 精确命中
    hits = SkillRegistry.by_task_type(task_type)
    if hits:
        # 多个命中：取第一个（同任务类型多技能时由上层按上下文仲裁）
        skill_id = hits[0].skill_id
        decision = wl.check(skill_id)
        if not decision.allowed:
            return decision
        return SkillDecision(
            allowed=True,
            reason=f"任务类型 '{task_type}' → 技能 '{skill_id}'（精确命中）",
            action="allow",
            skill_id=skill_id,
            record=hits[0],
        )

    # 2) 兜底 generic
    if fallback_generic and SkillRegistry.exists("eng.generic"):
        decision = wl.check("eng.generic")
        if not decision.allowed:
            return decision
        return SkillDecision(
            allowed=True,
            reason=f"任务类型 '{task_type}' 无精确命中 → 兜底 'eng.generic'",
            action="allow",
            skill_id="eng.generic",
            record=SkillRegistry.get("eng.generic"),
        )

    # 3) 无法判定
    return SkillDecision(
        allowed=False,
        reason=f"任务类型 '{task_type}' 无法命中任何已登记技能",
        action="deny",
        skill_id="",
    )


def resolve_skill(task_type: str) -> Optional[str]:
    """解析任务类型到技能 ID（白名单全量可用；未命中返回 None）。"""
    decision = dispatch_decision(task_type)
    return decision.skill_id if decision.allowed else None


__all__ = ["dispatch_decision", "resolve_skill"]
