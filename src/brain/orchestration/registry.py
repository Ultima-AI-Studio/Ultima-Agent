"""L10 范式注册表（驻留标记，与 L8/L9 同规）。

范式引擎为底座核心原语，注册后加驻留标记，禁止热卸载，
保证 Agent 任务编排不因误操作中断。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from typing import Any, Dict


class ResidencyViolationError(RuntimeError):
    """范式引擎为驻留组件，拒绝热卸载。"""


class OrchestrationRegistry:
    """范式引擎注册表：注册、驻留、查询、卸载（驻留者拒绝）。"""

    _registry: Dict[str, Dict[str, Any]] = {}
    _resident: set[str] = set()

    @classmethod
    def register(
        cls,
        key: str,
        entry: Any,
        *,
        resident: bool = True,
        description: str = "",
    ) -> None:
        if key in cls._registry:
            raise ValueError(
                f"OrchestrationRegistry already has an entry for '{key}'"
            )
        cls._registry[key] = {
            "entry": entry,
            "resident": resident,
            "description": description,
        }
        if resident:
            cls._resident.add(key)

    @classmethod
    def get(cls, key: str) -> Any:
        try:
            return cls._registry[key]["entry"]
        except KeyError:
            raise KeyError(
                f"OrchestrationRegistry does not have an entry for '{key}'"
            ) from None

    @classmethod
    def is_registered(cls, key: str) -> bool:
        return key in cls._registry

    @classmethod
    def is_resident(cls, key: str) -> bool:
        return key in cls._resident

    @classmethod
    def keys(cls) -> tuple:
        return tuple(cls._registry.keys())

    @classmethod
    def unload(cls, key: str) -> bool:
        if key not in cls._registry:
            return False
        if key in cls._resident:
            raise ResidencyViolationError(
                f"L10 范式引擎 '{key}' 为驻留组件，禁止热卸载"
            )
        del cls._registry[key]
        return True

    @classmethod
    def reset(cls) -> None:
        cls._registry.clear()
        cls._resident.clear()


__all__ = ["OrchestrationRegistry", "ResidencyViolationError"]
