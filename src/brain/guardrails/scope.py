"""L8 三类 scope 权限矩阵（M19：权限闸门）。

对齐 jarvis-reverse-architecture M19 / M12 / M20 与 security-spec §2：

- `cap:<能力入口>`：能力入口调用权限（如 cap:exec.run / cap:memory.write），
  与总线 `_authorize` 的 cap: 判定同口径，本闸门做调用侧二次判定；
- `dev:read` / `dev:write` / `dev:control`：本机执行三独立（M12），
  read（只读）/ write（写文件/改状态）/ control（设备/UI/进程控制）互不授权；
- `cred:<keyId>`：凭证引用权限（M20），未声明引用的 keyId 拒绝，防止越权取凭证。

清单声明 + 闸门逐次判定：声明矩阵是唯一授权源，未声明调用一律拒绝（fail-closed）
并记审计事件（写 plugin-bus.jsonl 同构事件流 + 返回拒绝原因）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import os
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set, Tuple


@dataclass(frozen=True)
class ScopeDecision:
    """一次 scope 判定结果。"""

    allowed: bool
    scope: str
    reason: str
    verdict: str = "allow"  # "allow" | "deny"

    def to_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "scope": self.scope,
            "reason": self.reason,
            "verdict": self.verdict,
        }


# dev 三独立固定集合（M12：read/write/control 互不授权）
DEV_SCOPES = frozenset({"read", "write", "control"})


def parse_scope(scope: str) -> Tuple[str, str]:
    """解析 scope 字符串为 (类别, 条目)。

    "cap:exec.run" -> ("cap", "exec.run")
    "dev:write"    -> ("dev", "write")
    "cred:openai"  -> ("cred", "openai")
    """
    if ":" not in scope:
        raise ValueError(f"非法 scope 格式（缺少类别前缀）: {scope!r}")
    prefix, item = scope.split(":", 1)
    if prefix not in {"cap", "dev", "cred"}:
        raise ValueError(f"未知 scope 类别: {prefix!r}")
    if not item:
        raise ValueError(f"scope 条目为空: {scope!r}")
    return prefix, item


class ScopePolicy:
    """三类 scope 权限矩阵（清单声明 + 逐次判定 + 审计留痕）。"""

    def __init__(
        self,
        *,
        cap: Optional[Iterable[str]] = None,
        dev: Optional[Iterable[str]] = None,
        cred: Optional[Iterable[str]] = None,
        audit_path: Optional[str] = None,
    ) -> None:
        self._cap: Set[str] = set(cap or [])
        self._dev: Set[str] = set(dev or [])
        self._cred: Set[str] = set(cred or [])
        # dev 只接受三独立枚举
        unknown = self._dev - set(DEV_SCOPES)
        if unknown:
            raise ValueError(f"dev scope 仅允许 read/write/control，含未知项: {sorted(unknown)}")
        self._audit_path = audit_path
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # 声明
    # ------------------------------------------------------------------
    def declare_cap(self, *entries: str) -> None:
        with self._lock:
            self._cap.update(entries)

    def declare_dev(self, *entries: str) -> None:
        with self._lock:
            unknown = set(entries) - set(DEV_SCOPES)
            if unknown:
                raise ValueError(f"dev scope 仅允许 read/write/control，含未知项: {sorted(unknown)}")
            self._dev.update(entries)

    def declare_cred(self, *key_ids: str) -> None:
        with self._lock:
            self._cred.update(key_ids)

    # ------------------------------------------------------------------
    # 判定
    # ------------------------------------------------------------------
    def check_scope(self, scope: str) -> ScopeDecision:
        """逐次判定 scope。未声明拒绝（fail-closed）+ 审计留痕。"""
        try:
            prefix, item = parse_scope(scope)
        except ValueError as exc:
            d = ScopeDecision(False, scope, f"scope 格式非法: {exc}", "deny")
            self._audit(d)
            return d
        with self._lock:
            if prefix == "cap":
                ok = item in self._cap
                reason = (
                    f"能力入口 '{item}' 已声明授权" if ok
                    else f"能力入口 '{item}' 未声明（fail-closed 拒绝）"
                )
            elif prefix == "dev":
                ok = item in self._dev
                reason = (
                    f"本机执行 '{item}' 已声明授权" if ok
                    else f"本机执行 '{item}' 未声明（dev 三独立，fail-closed 拒绝）"
                )
            else:  # cred
                ok = item in self._cred
                reason = (
                    f"凭证 '{item}' 已声明可引用" if ok
                    else f"凭证 '{item}' 未声明可引用（fail-closed 拒绝）"
                )
        d = ScopeDecision(ok, scope, reason, "allow" if ok else "deny")
        self._audit(d)
        return d

    # ------------------------------------------------------------------
    # 审计
    # ------------------------------------------------------------------
    def _audit(self, decision: ScopeDecision) -> None:
        if not self._audit_path:
            return
        try:
            row = {
                "ts": datetime.now(timezone.utc).isoformat(),
                "source": "ultima.guard.policy",
                "event_type": (
                    "audit.scope.denied" if not decision.allowed else "audit.scope.allowed"
                ),
                "payload": decision.to_dict(),
            }
            Path(self._audit_path).parent.mkdir(parents=True, exist_ok=True)
            with open(self._audit_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        except OSError:
            pass  # 审计日志失败不阻断判定（业务侧仍拿到拒绝结果）

    # ------------------------------------------------------------------
    # 快照
    # ------------------------------------------------------------------
    def snapshot(self) -> dict:
        with self._lock:
            return {
                "cap": sorted(self._cap),
                "dev": sorted(self._dev),
                "cred": sorted(self._cred),
                "audit_path": self._audit_path,
            }


__all__ = ["ScopePolicy", "ScopeDecision", "parse_scope", "DEV_SCOPES"]
