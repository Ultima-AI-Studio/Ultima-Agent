"""L9 记忆注册表（驻留标记）。

记忆为底座核心原语（五原语之一），注册后加驻留标记，禁止热卸载，
保证 Agent 长期记忆不因误操作丢失。

【待裁决 · 2026-11-12】本模块的驻留策略（默认 resident=True，即「与 L8 同规」）
尚未获得 plugin-bus-spec §5.4 认可——该表只列 L8/L10 两域强制驻留，L9 不在其中。
域级 BusKernel 因此判定 ultima.memory.lite「可卸载」，与本节实例级判定相反。
裁决记录见 docs/decisions/pd-20261112-l9驻留域两级判定裁决.md，
裁决前按现行 spec 执行（域级判可卸），勿据本 docstring 反向覆盖规格。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from typing import Any, Dict, Optional


class ResidencyViolationError(RuntimeError):
    """记忆组件为驻留组件，拒绝热卸载。"""


class MemoryRegistry:
    """记忆后端注册表：注册、驻留、查询、卸载（驻留者拒绝）。"""

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
            raise ValueError(f"MemoryRegistry already has an entry for '{key}'")
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
            raise KeyError(f"MemoryRegistry does not have an entry for '{key}'") from None

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
                f"L9 记忆 '{key}' 为驻留组件，禁止热卸载"
            )
        del cls._registry[key]
        return True

    @classmethod
    def reset(cls) -> None:
        cls._registry.clear()
        cls._resident.clear()


__all__ = ["MemoryRegistry", "ResidencyViolationError"]
