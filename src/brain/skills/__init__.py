"""L2 领域知识与技能注册（P2 补建 · 首域=任务域）。

对齐 capability-list L2「每域内容清单、技能注册表（skill-dispatch）」与
plugin-bus-spec §3 清单纪律（先静态登记、后运行时注册）：
- 技能注册表 = 静态登记 + 驻留管控（未登记不得使用）；
- 技能白名单 = 确定性授权判定（未授权拒绝 100%，对齐 L8 未授权拒绝基线）；
- 任务域派发 = domain.resolve 首域实现：任务卡 category/skill 字段
  白名单校验后解析到唯一技能。

本模块位于 H:\\UltimaAI\\UltimaAgent\\ 写域内，只写本目录。
"""

from .registry import (
    SkillRegistry,
    SkillRegistrationError,
    ResidencyViolationError,
)
from .whitelist import SkillWhitelist, SkillDecision
from .dispatch import resolve_skill, dispatch_decision

__all__ = [
    "SkillRegistry",
    "SkillRegistrationError",
    "ResidencyViolationError",
    "SkillWhitelist",
    "SkillDecision",
    "resolve_skill",
    "dispatch_decision",
]
