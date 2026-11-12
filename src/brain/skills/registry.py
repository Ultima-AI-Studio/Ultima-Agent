"""L2 技能注册表（静态登记 + 驻留管控）。

对齐 registry.md 纪律「先静态登记、后运行时注册；未登记不得使用」：
- 注册表为进程内静态登记，register 幂等判重（重复注册拒绝）；
- 白名单内的首域技能（任务域）登记为驻留（resident），禁止热卸载；
- 技能六字段对齐 registry.md §一：ID / 角色 / 职责边界 / 适用任务类型 /
  产出标准 / 验收口径。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


class SkillRegistrationError(RuntimeError):
    """技能登记失败（重复登记 / 字段非法）。"""


class ResidencyViolationError(RuntimeError):
    """技能为驻留登记，拒绝热卸载。"""


@dataclass(frozen=True)
class SkillRecord:
    """一条技能登记（对齐 registry.md §一六字段）。"""

    skill_id: str            # 如 eng.code
    role: str                # 角色（规范中文）
    scope: str               # 职责边界
    task_types: tuple        # 适用任务类型（tuple[str, ...]）
    output_std: str          # 产出标准
    acceptance: str          # 验收口径
    resident: bool = False   # 驻留标记（首域任务域技能驻留）


class SkillRegistry:
    """技能注册表：登记、查询、驻留、卸载（驻留者拒绝）。

    Parameters
    ----------
    task_domain:
        当前登记的领域名（默认 "task"=任务域，首域）。
    """

    _registry: Dict[str, SkillRecord] = {}
    _resident: set[str] = set()

    @classmethod
    def register(
        cls,
        skill_id: str,
        role: str,
        scope: str,
        task_types,
        output_std: str,
        acceptance: str,
        *,
        resident: bool = True,
    ) -> None:
        """登记一条技能。重复登记抛 SkillRegistrationError（防覆盖）。"""
        if skill_id in cls._registry:
            raise SkillRegistrationError(
                f"SkillRegistry 已登记 '{skill_id}'（重复登记拒绝，防覆盖）"
            )
        if not skill_id or not skill_id.strip():
            raise SkillRegistrationError("skill_id 不得为空")
        if not task_types:
            raise SkillRegistrationError(
                f"技能 '{skill_id}' 适用任务类型不得为空"
            )
        record = SkillRecord(
            skill_id=skill_id,
            role=role,
            scope=scope,
            task_types=tuple(task_types),
            output_std=output_std,
            acceptance=acceptance,
            resident=resident,
        )
        cls._registry[skill_id] = record
        if resident:
            cls._resident.add(skill_id)

    @classmethod
    def get(cls, skill_id: str) -> SkillRecord:
        try:
            return cls._registry[skill_id]
        except KeyError:
            raise KeyError(
                f"技能 '{skill_id}' 未登记（未登记不得使用）"
            ) from None

    @classmethod
    def exists(cls, skill_id: str) -> bool:
        return skill_id in cls._registry

    @classmethod
    def is_resident(cls, skill_id: str) -> bool:
        return skill_id in cls._resident

    @classmethod
    def all(cls) -> tuple:
        """返回全部登记（按登记顺序）。"""
        return tuple(cls._registry.values())

    @classmethod
    def by_task_type(cls, task_type: str) -> tuple:
        """按适用任务类型反查技能（同一任务类型可命中多个）。"""
        return tuple(
            r for r in cls._registry.values() if task_type in r.task_types
        )

    @classmethod
    def unload(cls, skill_id: str) -> bool:
        """卸载非驻留技能；驻留技能抛 ResidencyViolationError。"""
        if skill_id not in cls._registry:
            return False
        if skill_id in cls._resident:
            raise ResidencyViolationError(
                f"L2 技能 '{skill_id}' 为驻留登记，禁止热卸载"
            )
        del cls._registry[skill_id]
        return True

    @classmethod
    def reset(cls) -> None:
        """清空注册表（测试用）。"""
        cls._registry.clear()
        cls._resident.clear()

    # ------------------------------------------------------------------
    # 任务域内置登记（首域=任务域，与 registry.md §一 11 技能一致）
    # ------------------------------------------------------------------
    _TASK_DOMAIN_SKILLS: Optional[Dict[str, Dict[str, Any]]] = None

    @classmethod
    def _task_domain_defaults(cls) -> Dict[str, Dict[str, Any]]:
        if cls._TASK_DOMAIN_SKILLS is not None:
            return cls._TASK_DOMAIN_SKILLS
        cls._TASK_DOMAIN_SKILLS = {
            "eng.code": {
                "role": "智能工程师",
                "scope": "写代码/修缺陷/重构/单元自检",
                "task_types": ("code",),
                "output_std": "源码落 fileDomain",
                "acceptance": "编译通过+自检+回执",
            },
            "eng.ui": {
                "role": "UI 工程师",
                "scope": "组件/界面/动效实现",
                "task_types": ("ui",),
                "output_std": "组件/页面按积木规格",
                "acceptance": "视觉核对+交互可用",
            },
            "eng.audit": {
                "role": "审计工程师",
                "scope": "一致性/质量/回执核对/修正任务",
                "task_types": ("audit",),
                "output_std": "审计结论+修正任务",
                "acceptance": "偏差全部闭环",
            },
            "eng.security": {
                "role": "安全工程师",
                "scope": "越界/权限/凭证/漏洞核查",
                "task_types": ("security",),
                "output_std": "安全报告+加固",
                "acceptance": "高危项清零",
            },
            "eng.arch": {
                "role": "架构工程师",
                "scope": "分层/接口/选型/依赖",
                "task_types": ("arch",),
                "output_std": "架构方案+依赖图",
                "acceptance": "评审通过+落规格",
            },
            "eng.database": {
                "role": "数据库工程师",
                "scope": "建模/存储/查询/迁移",
                "task_types": ("database",),
                "output_std": "模型+迁移脚本",
                "acceptance": "数据校验通过",
            },
            "eng.test": {
                "role": "测试工程师",
                "scope": "验证/回归/验收证据",
                "task_types": ("test",),
                "output_std": "测试报告",
                "acceptance": "验收项全过",
            },
            "eng.infra": {
                "role": "运维工程师",
                "scope": "部署/环境/守护/日志/设备集群",
                "task_types": ("infra",),
                "output_std": "部署/运行状态",
                "acceptance": "服务可用",
            },
            "eng.voice": {
                "role": "语音/多媒体",
                "scope": "语音链路/音色/音频/CV3 接线",
                "task_types": ("voice",),
                "output_std": "链路验证+证据",
                "acceptance": "真机验证报告",
            },
            "eng.docs": {
                "role": "文档工程师",
                "scope": "范式/规格/纪要/调研落盘",
                "task_types": ("docs",),
                "output_std": "文档落盘",
                "acceptance": "回读一致+可追溯",
            },
            "eng.generic": {
                "role": "通用执行器",
                "scope": "兜底/无法判定任务",
                "task_types": ("generic",),
                "output_std": "按任务卡产出",
                "acceptance": "按 acceptance",
            },
        }
        return cls._TASK_DOMAIN_SKILLS

    @classmethod
    def install_task_domain(cls) -> int:
        """登记任务域 11 技能（幂等：已登记跳过）。返回本次新登记数。"""
        count = 0
        for skill_id, spec in cls._task_domain_defaults().items():
            if cls.exists(skill_id):
                continue
            cls.register(
                skill_id,
                role=spec["role"],
                scope=spec["scope"],
                task_types=spec["task_types"],
                output_std=spec["output_std"],
                acceptance=spec["acceptance"],
                resident=True,
            )
            count += 1
        return count


__all__ = [
    "SkillRecord",
    "SkillRegistry",
    "SkillRegistrationError",
    "ResidencyViolationError",
]
