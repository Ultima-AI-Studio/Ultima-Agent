"""L8 高危操作征询骨架（HazardGate）。

对齐 product-plan L8「高危操作先征询（受控授权）」与 v2.3 §6
「状态只报告、操作（重试/取消）需授权」：

- 高危操作登记（register_operation）后，执行前必须先 request → 得到
  pending（待授权）状态，调用方据此进入征询闭环（对齐 L7）。
- approve/deny 由受控 actor 给出（brain/用户/Manager），状态迁移
  pending → granted / denied。
- 授权判定只出状态（pending/granted/denied），不代替业务执行；
  业务方在 granted 后才执行实际操作。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import threading
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .credentials import CredentialError, redact  # noqa: F401  复用脱敏


class HazardGateError(RuntimeError):
    """高危操作征询门错误（未登记/重复登记/状态非法）。"""


@dataclass(frozen=True)
class OperationSpec:
    """高危操作登记。"""

    name: str
    requires_auth: bool  # True=执行前必须征询授权；False=仅提示
    description: str = ""
    required_actor: str = ""  # 空=任意授权 actor；否则限定（如 "user"/"brain"）


@dataclass(frozen=True)
class AuthorizationDecision:
    """一次授权判定结果。"""

    operation: str
    status: str  # "pending" | "granted" | "denied"
    actor: str = ""
    reason: str = ""
    requested_at: str = ""
    decided_at: str = ""

    @property
    def is_granted(self) -> bool:
        return self.status == "granted"

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"


class HazardGate:
    """高危操作受控授权骨架。

    线程安全：请求/审批用独立锁，决策记录 append-only。
    """

    def __init__(self) -> None:
        self._specs: Dict[str, OperationSpec] = {}
        self._requests: Dict[str, Dict[str, Any]] = {}  # op -> 最近请求
        self._history: List[Dict[str, Any]] = []  # append-only 授权记录
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # 登记
    # ------------------------------------------------------------------
    def register_operation(
        self,
        name: str,
        *,
        requires_auth: bool = True,
        description: str = "",
        required_actor: str = "",
    ) -> None:
        """登记高危操作。同名重复登记抛错。"""
        with self._lock:
            if name in self._specs:
                raise HazardGateError(f"高危操作 '{name}' 已登记")
            self._specs[name] = OperationSpec(
                name=name,
                requires_auth=requires_auth,
                description=description,
                required_actor=required_actor,
            )

    def spec(self, name: str) -> OperationSpec:
        with self._lock:
            try:
                return self._specs[name]
            except KeyError:
                raise HazardGateError(f"高危操作 '{name}' 未登记") from None

    def operations(self) -> List[str]:
        with self._lock:
            return sorted(self._specs.keys())

    # ------------------------------------------------------------------
    # 请求 / 审批
    # ------------------------------------------------------------------
    def request(self, name: str, *, actor: str = "brain") -> AuthorizationDecision:
        """发起高危操作授权请求。未登记抛错。

        requires_auth=False 的操作直接 granted（仅提示性登记）。
        """
        spec = self.spec(name)
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            if not spec.requires_auth:
                decision = AuthorizationDecision(
                    operation=name,
                    status="granted",
                    actor=actor,
                    reason="该操作不要求授权（仅提示登记）",
                    requested_at=now,
                    decided_at=now,
                )
                self._record(decision)
                return decision
            self._requests[name] = {
                "actor": actor,
                "requested_at": now,
                "status": "pending",
            }
        return AuthorizationDecision(
            operation=name,
            status="pending",
            actor=actor,
            reason="等待授权",
            requested_at=now,
        )

    def approve(
        self,
        name: str,
        *,
        actor: str = "user",
        reason: str = "",
    ) -> AuthorizationDecision:
        """批准授权。未登记/无待审批请求抛错。required_actor 限定检查。"""
        spec = self.spec(name)
        with self._lock:
            req = self._requests.get(name)
            if req is None or req.get("status") != "pending":
                raise HazardGateError(f"高危操作 '{name}' 无待审批请求")
            if spec.required_actor and actor != spec.required_actor:
                raise HazardGateError(
                    f"高危操作 '{name}' 仅允许 {spec.required_actor} 授权，当前 actor='{actor}'"
                )
            req["status"] = "granted"
            req["decided_at"] = datetime.now(timezone.utc).isoformat()
            req["decided_by"] = actor
            req["reason"] = reason
            decision = AuthorizationDecision(
                operation=name,
                status="granted",
                actor=actor,
                reason=reason or "授权通过",
                requested_at=req.get("requested_at", ""),
                decided_at=req["decided_at"],
            )
            self._record(decision)
            return decision

    def deny(
        self,
        name: str,
        *,
        actor: str = "user",
        reason: str = "",
    ) -> AuthorizationDecision:
        """拒绝授权。"""
        spec = self.spec(name)
        with self._lock:
            req = self._requests.get(name)
            if req is None or req.get("status") != "pending":
                raise HazardGateError(f"高危操作 '{name}' 无待审批请求")
            if spec.required_actor and actor != spec.required_actor:
                raise HazardGateError(
                    f"高危操作 '{name}' 仅允许 {spec.required_actor} 授权，当前 actor='{actor}'"
                )
            req["status"] = "denied"
            req["decided_at"] = datetime.now(timezone.utc).isoformat()
            req["decided_by"] = actor
            req["reason"] = reason
            decision = AuthorizationDecision(
                operation=name,
                status="denied",
                actor=actor,
                reason=reason or "授权拒绝",
                requested_at=req.get("requested_at", ""),
                decided_at=req["decided_at"],
            )
            self._record(decision)
            return decision

    def current(self, name: str) -> AuthorizationDecision:
        """当前请求状态（无请求时返回空闲 pending=False 标记）。"""
        with self._lock:
            req = self._requests.get(name)
            if req is None:
                return AuthorizationDecision(
                    operation=name,
                    status="pending",
                    reason="无进行中的授权请求",
                )
            return AuthorizationDecision(
                operation=name,
                status=req.get("status", "pending"),
                actor=req.get("decided_by", req.get("actor", "")),
                reason=req.get("reason", ""),
                requested_at=req.get("requested_at", ""),
                decided_at=req.get("decided_at", ""),
            )

    # ------------------------------------------------------------------
    # 审计记录
    # ------------------------------------------------------------------
    def _record(self, decision: AuthorizationDecision) -> None:
        self._history.append(
            {
                "ts": decision.decided_at,
                "operation": decision.operation,
                "status": decision.status,
                "actor": decision.actor,
                "reason": decision.reason,
            }
        )

    def history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """授权历史（append-only）。"""
        with self._lock:
            return list(self._history[-limit:])

    def reset(self) -> None:
        """测试用：清空登记/请求/历史。"""
        with self._lock:
            self._specs.clear()
            self._requests.clear()
            self._history.clear()


__all__ = [
    "HazardGate",
    "HazardGateError",
    "OperationSpec",
    "AuthorizationDecision",
]
