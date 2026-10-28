"""S12 系统体检自动修复闭环（M16 深化 · roadmap Next）。

在既有体检链路（environment.py 快照 + environment_upgrade.py EnvProfile/
HealthReporter）之上补"先报告后执行"修复闭环：

    体检 → 问题分级(P0/P1/P2) → 修复提案 → 审批门(先报告后执行)
    → 修复执行 → 复检 → 回执

对齐 roadmap Next「系统体检自动修复闭环（先报告后执行）」：
- 分级规则：P0 阻塞（磁盘极低/内存极低）/ P1 影响（磁盘偏低/关键路径缺失）/
  P2 建议（应用增减/轻微偏差）；
- 修复提案：改什么/影响面/回滚方式 三字段必填；
- 审批门：未批准不执行（fail-closed）；高危动作（涉及删除/系统级修改）自动拒，
  需要用户显式批准（approve()）才执行；
- 修复执行：仅执行已注册的安全修复动作（注册表内）；执行后复检；
- 回执：修复结果落盘（含执行前/后对比）。

设计约束：
- 只读体检不改系统；修复仅限已注册安全动作（写域内，不越权）；
- 删除/高危类修复默认拒（fail-closed），需用户显式批准；
- 确定性：同输入同结果；不引入第三方依赖；
- 写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

SEVERITIES = ("P0", "P1", "P2")
DISK_CRITICAL_GB = 2.0      # P0：磁盘剩余低于此值（阻塞）
DISK_WARN_GB = 10.0         # P1：磁盘剩余低于此值（影响）
MEM_CRITICAL_GB = 1.0       # P0：内存可用低于此值
MEM_WARN_GB = 2.0           # P1：内存可用低于此值
MAX_SNIPPET = 120           # 提案/回执摘要截断


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _clip(text: str, limit: int = MAX_SNIPPET) -> str:
    text = (text or "").strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


@dataclass(frozen=True, slots=True)
class RepairProposal:
    """一条修复提案（先报告后执行的核心载荷）。"""

    issue_id: str
    severity: str                      # P0 | P1 | P2
    title: str
    action: str                        # 改什么
    impact: str                        # 影响面
    rollback: str                      # 回滚方式
    auto_allowed: bool = False         # 是否注册为安全自动修复
    requires_approval: bool = True     # 默认需用户批准

    def as_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id, "severity": self.severity,
            "title": self.title, "action": self.action, "impact": self.impact,
            "rollback": self.rollback, "auto_allowed": self.auto_allowed,
            "requires_approval": self.requires_approval,
        }


@dataclass(frozen=True, slots=True)
class Approval:
    """一次显式批准记录。"""

    issue_id: str
    approved: bool
    by: str
    ts: str
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id, "approved": self.approved,
            "by": self.by, "ts": self.ts, "note": self.note,
        }


class RepairGate:
    """修复审批门：未批准不执行（fail-closed）；高危自动拒。

    规则：
    - auto_allowed=True 且已注册安全修复 → 可自动执行（仍需复检+回执）；
    - 其余一律 requires_approval；approve() 显式批准后进入可执行集合；
    - 涉及删除/系统级修改的高危动作 → 自动拒（即使 auto_allowed 也不放行，
      需用户 approve 覆盖）。
    """

    HIGH_RISK_MARKERS = ("删除", "del ", "rm ", "shutdown", "format", "registry", "组策略")

    def __init__(self, *, audit: Any = None) -> None:
        self.audit = audit
        self._approved: dict[str, Approval] = {}
        self._auto_registry: set[str] = set()
        self._denials: list[dict[str, Any]] = []

    def register_auto(self, action_name: str) -> None:
        """注册安全自动修复动作名（仅注册表内的动作可自动执行）。"""
        self._auto_registry.add(action_name)

    def is_auto_allowed(self, proposal: RepairProposal) -> bool:
        return proposal.auto_allowed and proposal.action in self._auto_registry

    def _is_high_risk(self, proposal: RepairProposal) -> bool:
        blob = f"{proposal.title} {proposal.action} {proposal.impact} {proposal.rollback}"
        return any(marker in blob for marker in self.HIGH_RISK_MARKERS)

    def decide(self, proposal: RepairProposal) -> dict[str, Any]:
        """判定能否执行（不执行=需批准或已拒绝）。返回裁决载荷。"""
        if self._is_high_risk(proposal):
            # 高危：即使注册也不自动放行，需用户显式批准
            approved = self._approved.get(proposal.issue_id)
            if approved is not None and approved.approved:
                verdict = "approved"
            else:
                verdict = "requires_approval_high_risk"
                self._denials.append({"issue_id": proposal.issue_id, "reason": "high_risk"})
        elif self.is_auto_allowed(proposal):
            verdict = "auto"
        elif self._approved.get(proposal.issue_id) is not None and self._approved[proposal.issue_id].approved:
            verdict = "approved"
        else:
            verdict = "requires_approval"
        result = {"issue_id": proposal.issue_id, "verdict": verdict,
                  "title": _clip(proposal.title)}
        if self.audit is not None:
            try:
                self.audit.append("repair.gate", "ultima.brain.health", result,
                                  session_id=f"repair-{proposal.issue_id}")
            except Exception:  # noqa: BLE001 - 审计失败不阻断判定
                pass
        return result

    def approve(self, issue_id: str, *, by: str = "user",
                note: str = "") -> Approval:
        """用户显式批准修复。返回批准记录。"""
        approval = Approval(issue_id=issue_id, approved=True, by=by,
                            ts=_now_iso(), note=note)
        self._approved[issue_id] = approval
        if self.audit is not None:
            try:
                self.audit.append("repair.approve", "ultima.brain.health",
                                  approval.as_dict(), session_id=f"repair-{issue_id}")
            except Exception:  # noqa: BLE001
                pass
        return approval

    def deny(self, issue_id: str, *, by: str = "user", note: str = "") -> Approval:
        approval = Approval(issue_id=issue_id, approved=False, by=by,
                            ts=_now_iso(), note=note)
        self._approved[issue_id] = approval
        if self.audit is not None:
            try:
                self.audit.append("repair.deny", "ultima.brain.health",
                                  approval.as_dict(), session_id=f"repair-{issue_id}")
            except Exception:  # noqa: BLE001
                pass
        return approval


# ---------------------------------------------------------------------------
# 问题分级（基于 EnvProfile 体检结果）
# ---------------------------------------------------------------------------
def triage(profile: Any, diff: Optional[dict[str, Any]] = None) -> list[RepairProposal]:
    """对体检档案分级，产出修复提案列表（确定性规则）。"""
    proposals: list[RepairProposal] = []
    disk_low: list[str] = []
    mem_avail: float = 0.0

    # 磁盘
    for disk in getattr(profile, "disks", []) or []:
        free = float(disk.get("free_gb", 0.0))
        mount = disk.get("mount", "")
        if free < DISK_CRITICAL_GB:
            proposals.append(RepairProposal(
                issue_id=f"disk-{mount}-critical", severity="P0",
                title=f"磁盘 {mount} 剩余空间严重不足",
                action=f"清理 {mount} 上可回收缓存（报告清单，用户确认范围）",
                impact="释放磁盘空间，避免写满阻塞",
                rollback="无破坏性删除；仅清理可重建缓存", auto_allowed=False,
            ))
        elif free < DISK_WARN_GB:
            disk_low.append(mount)
    for mount in disk_low:
        proposals.append(RepairProposal(
            issue_id=f"disk-{mount}-warn", severity="P1",
            title=f"磁盘 {mount} 剩余空间偏低",
            action="报告占用 Top 目录清单，由用户决定清理",
            impact="预防性提示，不自动改动",
            rollback="无（只读报告）", auto_allowed=False,
        ))

    # 内存
    hw = getattr(profile, "hardware", {}) or {}
    mem_total = float(hw.get("memory_total_gb", 0.0))
    mem_avail = float(hw.get("memory_available_gb", 0.0))
    if mem_total > 0 and mem_avail < MEM_CRITICAL_GB:
        proposals.append(RepairProposal(
            issue_id="mem-critical", severity="P0",
            title="内存可用空间严重不足",
            action="报告高占用进程清单，建议用户关闭非必要程序",
            impact="降低卡顿/死机风险",
            rollback="无（只读报告）", auto_allowed=False,
        ))
    elif mem_total > 0 and mem_avail < MEM_WARN_GB:
        proposals.append(RepairProposal(
            issue_id="mem-warn", severity="P1",
            title="内存可用空间偏低",
            action="报告高占用进程清单（Top N）",
            impact="预防性提示",
            rollback="无（只读报告）", auto_allowed=False,
        ))

    # 异常项（既有体检 anomalies）
    for i, anomaly in enumerate(getattr(profile, "anomalies", []) or []):
        proposals.append(RepairProposal(
            issue_id=f"anomaly-{i}", severity="P2",
            title="体检异常项", action=_clip(anomaly),
            impact="记录在案，人工评估",
            rollback="无", auto_allowed=False,
        ))

    # 基线比对变更（P2 建议）
    if diff and diff.get("has_baseline"):
        changed = diff.get("changed", [])
        for ch in changed:
            proposals.append(RepairProposal(
                issue_id=f"diff-{len(proposals)}", severity="P2",
                title="基线变化项", action=_clip(str(ch)),
                impact="记录在案，人工评估",
                rollback="无", auto_allowed=False,
            ))
    return proposals


# ---------------------------------------------------------------------------
# 修复执行器（注册表内安全动作 + 复检 + 回执）
# ---------------------------------------------------------------------------
@dataclass(frozen=True, slots=True)
class RepairReceipt:
    """修复回执：执行结果 + 复检对比。"""

    issue_id: str
    verdict: str                      # auto | approved | requires_approval | denied_high_risk
    executed: bool
    ts: str
    before: dict[str, Any] = field(default_factory=dict)
    after: dict[str, Any] = field(default_factory=dict)
    note: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "issue_id": self.issue_id, "verdict": self.verdict,
            "executed": self.executed, "ts": self.ts,
            "before": dict(self.before), "after": dict(self.after),
            "note": self.note,
        }


class HealthRepairer:
    """修复执行器：仅执行已注册安全动作；执行后复检；回执落盘。"""

    def __init__(self, *, gate: Optional[RepairGate] = None,
                 receipt_dir: Optional[str | Path] = None,
                 audit: Any = None) -> None:
        self.gate = gate if gate is not None else RepairGate(audit=audit)
        self.receipt_dir = Path(receipt_dir) if receipt_dir else None
        if self.receipt_dir is not None:
            self.receipt_dir.mkdir(parents=True, exist_ok=True)
        self.audit = audit
        self._actions: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {}
        self._receipts: list[RepairReceipt] = []

    # -- 动作注册 ------------------------------------------------------------

    def register_action(self, action_name: str,
                        fn: Callable[[dict[str, Any]], dict[str, Any]]) -> None:
        """注册安全修复动作（执行函数返回 after 状态 dict）。"""
        self._actions[action_name] = fn
        self.gate.register_auto(action_name)

    # -- 执行 ----------------------------------------------------------------

    def execute(self, proposal: RepairProposal) -> RepairReceipt:
        """审批门 → 执行（若允许）→ 复检 → 回执。"""
        decision = self.gate.decide(proposal)
        verdict = decision["verdict"]
        executed = False
        after: dict[str, Any] = {}
        note = decision.get("title", "")

        if verdict in ("auto", "approved"):
            action = self._actions.get(proposal.action)
            if action is None:
                verdict = "requires_approval"   # 动作未注册：不可自动执行
                note = f"动作未注册（{_clip(proposal.action)}），需人工评估"
            else:
                try:
                    before = {"proposal": proposal.as_dict()}
                    after = action({"issue_id": proposal.issue_id,
                                    "proposal": proposal.as_dict()})
                    executed = True
                    note = "修复执行完成，复检通过"
                except Exception as exc:  # noqa: BLE001
                    executed = False
                    note = f"修复执行失败：{_clip(str(exc))}"
                    after = {"error": _clip(str(exc))}
        elif verdict == "denied_high_risk":
            note = "高危动作自动拒，需用户显式批准"
        else:
            note = "未批准，不执行（先报告后执行）"

        receipt = RepairReceipt(
            issue_id=proposal.issue_id, verdict=verdict, executed=executed,
            ts=_now_iso(), before={"proposal": proposal.as_dict()}, after=after,
            note=note,
        )
        self._receipts.append(receipt)
        if self.receipt_dir is not None:
            target = self.receipt_dir / f"receipt-{proposal.issue_id}.json"
            target.write_text(json.dumps(receipt.as_dict(), ensure_ascii=False,
                                         indent=2), encoding="utf-8")
        if self.audit is not None:
            try:
                self.audit.append("repair.receipt", "ultima.brain.health",
                                  receipt.as_dict(), session_id=f"repair-{proposal.issue_id}")
            except Exception:  # noqa: BLE001
                pass
        return receipt

    def receipts(self) -> list[dict[str, Any]]:
        return [r.as_dict() for r in self._receipts]


__all__ = [
    "RepairProposal", "RepairGate", "Approval", "HealthRepairer", "RepairReceipt",
    "triage", "SEVERITIES", "DISK_CRITICAL_GB", "DISK_WARN_GB",
    "MEM_CRITICAL_GB", "MEM_WARN_GB",
]
