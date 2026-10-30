"""极简 pkg_resources 兼容层（写域 shim，仅服务 CV3 推理子进程）。

runtime310（Python 3.10 + setuptools 84）已移除 pkg_resources，但依赖链仍在
调用其接口：
1. lightning 2.2.4 在 fabric/pytorch 两处 `__init__.py` 调用
   `__import__("pkg_resources").declare_namespace(__name__)`
2. tiktoken（whisper 依赖）import 时调用 `pkg_resources.get_distribution(name)`
   读取包版本

本 shim 只实现该调用面：
- declare_namespace 为 no-op（命名空间包注册对单进程推理无副作用）；
- get_distribution 基于 importlib.metadata 返回轻量 Distribution（真实版本），
  供 tiktoken 等包做版本检查，避免抛 "can't determine version"。

注入方式：推理子进程 PYTHONPATH 前置本目录。
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version


def declare_namespace(name: str) -> None:
    """命名空间包声明，no-op。"""
    return None


class Distribution:
    """轻量 Distribution 占位（仅暴露依赖方使用的字段）。"""

    def __init__(self, name: str) -> None:
        self.project_name = name
        self.key = name.lower().replace("-", "_")
        try:
            self.version = version(name)
        except PackageNotFoundError:
            self.version = "0.0.0"
        self.location = ""
        self._parsed_pkg_info = None

    def __repr__(self) -> str:
        return f"Distribution({self.project_name} {self.version})"


def get_distribution(name: str) -> Distribution:
    """返回指定发行版的分发信息（真实版本优先）。"""
    return Distribution(name)


__all__ = ["declare_namespace", "get_distribution", "Distribution"]
