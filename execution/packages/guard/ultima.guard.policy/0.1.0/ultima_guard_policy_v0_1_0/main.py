"""L8 权限闸门总线插件（M19：guard.check）。

承载三类 scope 权限矩阵（cap/dev/cred）+ 三级裁决表（红线/可商量/高危）。
全部复用既有 L8 组件（ScopePolicy / AdjudicationTable / CapabilityPolicy），
不另造体系；本包仅做总线适配壳。

- guard.check(action, scope)：
    1. AdjudicationTable 三级裁决（红线直接拒绝）
    2. ScopePolicy 逐次判定（未声明拒绝，fail-closed）
    任一步拒绝即返回 deny；高危命中返回 pending（交 HS-007 征询）。
- 强制驻留：总线 L8 域硬约束（unload/disable 拒绝），插件自身不实现卸载副作用。
"""

from __future__ import annotations

from pathlib import Path

# 审计留痕默认落 plugin-bus 日志同目录（相对项目根）
_AUDIT_PATH = Path(__file__).resolve().parents[4] / "logs" / "guard-audit.jsonl"


class GuardPolicyPlugin:
    def load(self) -> None:
        from src.brain.guardrails import AdjudicationTable, ScopePolicy

        # 默认最小权限：不声明任何 cap/dev/cred → 一切未声明调用拒绝
        self._scope = ScopePolicy(audit_path=str(_AUDIT_PATH))
        self._table = AdjudicationTable(audit_path=str(_AUDIT_PATH))

    def activate(self) -> None:
        pass

    def disable(self) -> None:
        pass

    def unload(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def smoke(self) -> bool:
        if self._scope is None:
            return False
        d = self._scope.check_scope("cap:__smoke_probe__")
        return not d.allowed  # 未声明必须拒绝 = fail-closed 生效

    def guard_check(self, action: str, scope: str):
        """guard.check(action, scope) —— 三级裁决 + scope 矩阵。"""
        # 惰性初始化：总线 call 现场建实例时保证组件就绪（幂等）
        if not hasattr(self, "_table"):
            self.load()
        # 第一步：裁决表（红线 deny / 高危 pending / 可商量 allow_report）
        adj = self._table.adjudicate(action, scope)
        if adj.is_deny:
            return {
                "verdict": "deny",
                "reason": adj.reason,
                "category": adj.category,
                "scope": scope,
            }
        # 第二步：scope 逐次判定（未声明拒绝）
        sc = self._scope.check_scope(scope)
        if not sc.allowed:
            return {
                "verdict": "deny",
                "reason": sc.reason,
                "category": "scope",
                "scope": scope,
            }
        # 高危：先报告后执行 → pending（交 HS-007 征询）
        if adj.is_pending:
            return {
                "verdict": "pending",
                "reason": adj.reason,
                "category": adj.category,
                "scope": scope,
            }
        # 可商量：自决放行 + 事后报备（审计已由 adjudicate 记录 report 事件）
        return {
            "verdict": "allow",
            "reason": adj.reason,
            "category": adj.category,
            "scope": scope,
        }


def create_plugin() -> GuardPolicyPlugin:
    return GuardPolicyPlugin()
