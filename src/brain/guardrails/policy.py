"""L8 能力白名单策略（未授权拒绝 100%）。

对齐 tech-progression-plan §2.4：社区/能力模块先入白名单审计，
不合规不启用。本策略是确定性、离线可用的授权判定：
- 授权工具：config 白名单内 → 放行
- 未授权工具 / 敏感文件 / 危险操作 → 一律拒绝（BLOCK）

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List, Optional, Set, Tuple

from openjarvis.security.file_policy import is_sensitive_file


@dataclass
class PolicyDecision:
    """一次授权判定结果。"""

    allowed: bool
    reason: str
    action: str = ""  # "allow" | "deny"

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "action": self.action,
        }


class CapabilityPolicy:
    """能力白名单策略。

    Parameters
    ----------
    allowed_tools:
        授权工具名集合（如 {"calculator", "think"}）。不在集合内的一律拒绝。
    allowed_dirs:
        授权读写目录（绝对路径）。文件操作不在授权目录内一律拒绝。
    deny_tools:
        明确禁止的工具（与 allowed_tools 冲突时以 deny 为准）。
    sensitive_mode:
        是否启用敏感文件拦截（走底座 is_sensitive_file）。
    """

    def __init__(
        self,
        allowed_tools: Optional[Iterable[str]] = None,
        allowed_dirs: Optional[Iterable[str]] = None,
        deny_tools: Optional[Iterable[str]] = None,
        *,
        sensitive_mode: bool = True,
    ) -> None:
        self._allowed_tools: Set[str] = set(allowed_tools or {"calculator", "think"})
        self._deny_tools: Set[str] = set(deny_tools or {"shell_exec", "code_interpreter"})
        self._allowed_dirs: Set[str] = {
            str(Path(d).resolve()) for d in (allowed_dirs or [])
        }
        self._sensitive_mode = sensitive_mode

    # -- 工具授权 ---------------------------------------------------------

    def check_tool(self, tool_name: str) -> PolicyDecision:
        """判定工具是否授权。

        Rules
        -----
        1. deny_tools 命中 → 拒绝
        2. allowed_tools 未包含 → 拒绝（未授权 100% 拒绝）
        3. 其余 → 放行
        """
        if tool_name in self._deny_tools:
            return PolicyDecision(
                allowed=False,
                reason=f"工具 '{tool_name}' 在禁止清单中（deny-list）",
                action="deny",
            )
        if tool_name not in self._allowed_tools:
            return PolicyDecision(
                allowed=False,
                reason=f"工具 '{tool_name}' 未在授权白名单中（未授权拒绝）",
                action="deny",
            )
        return PolicyDecision(
            allowed=True,
            reason=f"工具 '{tool_name}' 已授权",
            action="allow",
        )

    # -- 文件路径授权 -----------------------------------------------------

    def check_path(self, path: str) -> PolicyDecision:
        """判定文件路径是否可读写。

        Rules
        -----
        1. 敏感文件（底座 is_sensitive_file）→ 拒绝
        2. 不在授权目录内 → 拒绝
        3. 其余 → 放行
        """
        try:
            p = Path(path).resolve()
        except Exception as exc:  # 非法路径
            return PolicyDecision(
                allowed=False,
                reason=f"路径解析失败（{exc}）",
                action="deny",
            )

        if self._sensitive_mode and is_sensitive_file(p):
            return PolicyDecision(
                allowed=False,
                reason=f"路径命中敏感文件策略: {p}",
                action="deny",
            )

        if self._allowed_dirs:
            if not any(
                str(p).lower().startswith(d.lower()) for d in self._allowed_dirs
            ):
                return PolicyDecision(
                    allowed=False,
                    reason=f"路径 '{p}' 不在授权目录内（未授权拒绝）",
                    action="deny",
                )
        return PolicyDecision(
            allowed=True,
            reason=f"路径 '{p}' 授权通过",
            action="allow",
        )

    # -- 汇总判定 ---------------------------------------------------------

    def check(self, tool_name: str, *, path: Optional[str] = None) -> PolicyDecision:
        """组合判定：工具 + 可选路径，任一不授权即拒绝。"""
        tool_decision = self.check_tool(tool_name)
        if not tool_decision.allowed:
            return tool_decision
        if path is not None:
            path_decision = self.check_path(path)
            if not path_decision.allowed:
                return path_decision
        return PolicyDecision(
            allowed=True,
            reason=f"工具 '{tool_name}' 授权通过（含路径校验）",
            action="allow",
        )

    # -- 快照 -------------------------------------------------------------

    def snapshot(self) -> dict:
        return {
            "allowed_tools": sorted(self._allowed_tools),
            "deny_tools": sorted(self._deny_tools),
            "allowed_dirs": sorted(self._allowed_dirs),
            "sensitive_mode": self._sensitive_mode,
        }


__all__ = ["CapabilityPolicy", "PolicyDecision"]
