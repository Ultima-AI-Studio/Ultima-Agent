"""S12 系统体检自动修复闭环（M16 深化 · roadmap Next）。

体检 → 问题分级 → 修复提案 → 审批门（先报告后执行）→ 修复执行 → 复检 → 回执。
"""

from .repair import (
    RepairGate,
    RepairProposal,
    RepairReceipt,
    HealthRepairer,
    Approval,
    triage,
)

__all__ = [
    "RepairGate", "RepairProposal", "RepairReceipt", "HealthRepairer",
    "Approval", "triage",
]
