"""L10 范式引擎（M4）——LangGraph 图状态机接入。

接线范式（对齐 tech-progression-plan §2）：
1. 接口对齐：实现底座 RouterPolicy ABC（引擎路由/审批路由）
2. 注册接入：@Registry.register("langgraph") + 驻留标记（fail-closed）
3. 审批门：图中节点执行前强制过 approval_gate，未批准节点 hold
4. 审计留痕：每次状态转换、审批决策追加审计日志

本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from .engine import (
    ApprovalGate,
    LangGraphStateMachine,
    StepResult,
    WorkflowState,
)
from .registry import OrchestrationRegistry, ResidencyViolationError
from .audit import AuditTrail, AuditRecord

__all__ = [
    "ApprovalGate",
    "AuditRecord",
    "AuditTrail",
    "LangGraphStateMachine",
    "OrchestrationRegistry",
    "ResidencyViolationError",
    "StepResult",
    "WorkflowState",
]
