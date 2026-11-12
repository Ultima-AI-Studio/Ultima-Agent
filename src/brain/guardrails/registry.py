"""L8 驻留标记注册表（fail-closed，热插拔拒绝卸载）。

对齐 tech-progression-plan §2.3：L8/L10 注册后加驻留标记，
热插拔 CLI 拒绝卸载，保证安全护栏不可被误摘。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple


class ResidencyViolationError(RuntimeError):
    """Raised when attempting to unload a resident (pinned) component."""


class GuardrailsRegistry:
    """安全护栏注册表：注册、驻留、查询、卸载（驻留者拒绝卸载）。

    线程安全：并发场景下 registry 读写由调用方加锁，本类不做隐式锁。
    """

    _registry: Dict[str, Dict[str, Any]] = {}
    _resident: set[str] = set()
    _lock_owner: Optional[str] = None

    # ------------------------------------------------------------------
    # 注册
    # ------------------------------------------------------------------
    @classmethod
    def register(
        cls,
        key: str,
        entry: Any,
        *,
        resident: bool = False,
        description: str = "",
    ) -> None:
        """注册 *entry* 到 *key*。resident=True 时加驻留标记（默认 fail-closed）。

        Raises
        ------
        ValueError
            若 *key* 已注册。
        """
        if key in cls._registry:
            raise ValueError(f"GuardrailsRegistry already has an entry for '{key}'")
        cls._registry[key] = {
            "entry": entry,
            "resident": resident,
            "description": description,
        }
        if resident:
            cls._resident.add(key)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    @classmethod
    def get(cls, key: str) -> Any:
        """返回 *key* 对应的 entry。缺失时抛 KeyError。"""
        try:
            return cls._registry[key]["entry"]
        except KeyError:
            raise KeyError(f"GuardrailsRegistry does not have an entry for '{key}'") from None

    @classmethod
    def is_registered(cls, key: str) -> bool:
        """*key* 是否已注册。"""
        return key in cls._registry

    @classmethod
    def is_resident(cls, key: str) -> bool:
        """*key* 是否为驻留组件。"""
        return key in cls._resident

    @classmethod
    def keys(cls) -> Tuple[str, ...]:
        """所有已注册 key。"""
        return tuple(cls._registry.keys())

    @classmethod
    def items(cls) -> Tuple[Tuple[str, Dict[str, Any]], ...]:
        """所有 (key, meta) 条目。"""
        return tuple(cls._registry.items())

    @classmethod
    def size(cls) -> int:
        return len(cls._registry)

    # ------------------------------------------------------------------
    # 卸载（驻留者拒绝）
    # ------------------------------------------------------------------
    @classmethod
    def unload(cls, key: str) -> bool:
        """卸载 *key*。驻留组件拒绝卸载，抛 ResidencyViolationError。

        Returns
        -------
        bool
            是否确实移除（不存在时返回 False，不抛错）。
        """
        if key not in cls._registry:
            return False
        if key in cls._resident:
            raise ResidencyViolationError(
                f"L8 护栏 '{key}' 为驻留组件（fail-closed），禁止热卸载"
            )
        del cls._registry[key]
        return True

    @classmethod
    def reset(cls) -> None:
        """测试用：清空全部注册与驻留标记。"""
        cls._registry.clear()
        cls._resident.clear()
        cls._lock_owner = None


__all__ = [
    "GuardrailsRegistry",
    "ResidencyViolationError",
]
