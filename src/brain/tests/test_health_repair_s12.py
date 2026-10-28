r"""S12 系统体检自动修复闭环 · 单测（正式可复跑版）。

覆盖（对应批次规划 S12 T1/T2/T3/T4）：
  1. 问题分级：磁盘/内存/异常/基线变化 → P0/P1/P2 提案（确定性规则）
  2. 修复提案：改什么/影响面/回滚方式 三字段必填
  3. 审批门：未批准不执行（fail-closed）；高危动作自动拒；显式批准后放行
  4. 修复执行：注册表内安全动作执行 → 复检 → 回执落盘；未注册动作不自动执行
  5. 审计链：全程留痕（append-only verify 仍 ok）

运行：
  H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\brain\tests -p "test_health_repair_s12.py" -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.guardrails.audit_log import AppendOnlyAuditLog  # noqa: E402
from src.brain.health.repair import (  # noqa: E402
    DISK_CRITICAL_GB,
    DISK_WARN_GB,
    HealthRepairer,
    RepairGate,
    RepairProposal,
    triage,
)


def _fake_profile(*, disks=None, mem_avail=8.0, mem_total=16.0,
                  anomalies=None) -> SimpleNamespace:
    return SimpleNamespace(
        disks=disks or [{"mount": "C:\\", "free_gb": 50.0}],
        hardware={"memory_total_gb": mem_total, "memory_available_gb": mem_avail},
        anomalies=anomalies or [],
    )


class TestTriage(unittest.TestCase):
    """问题分级与提案字段。"""

    def test_p0_disk_critical(self) -> None:
        profile = _fake_profile(disks=[{"mount": "C:\\", "free_gb": 1.2}])
        props = triage(profile)
        p0 = [p for p in props if p.severity == "P0" and p.issue_id.startswith("disk-")]
        self.assertEqual(len(p0), 1)
        self.assertEqual(p0[0].severity, "P0")
        # 三字段必填
        self.assertTrue(p0[0].action and p0[0].impact and p0[0].rollback)

    def test_p1_disk_warn(self) -> None:
        profile = _fake_profile(disks=[{"mount": "D:\\", "free_gb": 5.0}])
        props = triage(profile)
        p1 = [p for p in props if p.severity == "P1" and p.issue_id.startswith("disk-")]
        self.assertEqual(len(p1), 1)
        self.assertEqual(p1[0].severity, "P1")

    def test_mem_p0_and_p1(self) -> None:
        p0 = triage(_fake_profile(mem_avail=0.5))
        self.assertTrue(any(p.severity == "P0" and p.issue_id == "mem-critical" for p in p0))
        p1 = triage(_fake_profile(mem_avail=1.5))
        self.assertTrue(any(p.severity == "P1" and p.issue_id == "mem-warn" for p in p1))

    def test_anomalies_p2(self) -> None:
        profile = _fake_profile(anomalies=["磁盘 C 剩余空间不足 3.2GB", "网络接口枚举为空"])
        props = triage(profile)
        p2 = [p for p in props if p.severity == "P2" and p.issue_id.startswith("anomaly-")]
        self.assertEqual(len(p2), 2)

    def test_diff_changes_p2(self) -> None:
        profile = _fake_profile()
        diff = {"has_baseline": True, "changed": ["磁盘 C 剩余空间变化 50→40GB"]}
        props = triage(profile, diff=diff)
        self.assertTrue(any(p.issue_id.startswith("diff-") for p in props))

    def test_healthy_no_p0(self) -> None:
        profile = _fake_profile(disks=[{"mount": "C:\\", "free_gb": 80.0}], mem_avail=10.0)
        props = triage(profile)
        self.assertFalse(any(p.severity in ("P0", "P1") for p in props))


class TestRepairGate(unittest.TestCase):
    """审批门：先报告后执行。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = AppendOnlyAuditLog(Path(self.tmp.name) / "audit.jsonl")
        self.gate = RepairGate(audit=self.audit)

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _proposal(self, issue_id="disk-C-critical", action="清理缓存",
                  auto=False) -> RepairProposal:
        return RepairProposal(
            issue_id=issue_id, severity="P0", title="磁盘不足",
            action=action, impact="释放空间", rollback="可重建缓存",
            auto_allowed=auto,
        )

    def test_unapproved_requires_approval(self) -> None:
        decision = self.gate.decide(self._proposal())
        self.assertEqual(decision["verdict"], "requires_approval")

    def test_auto_allowed_when_registered(self) -> None:
        self.gate.register_auto("清理缓存")
        decision = self.gate.decide(self._proposal(auto=True))
        self.assertEqual(decision["verdict"], "auto")

    def test_approval_gate_flow(self) -> None:
        prop = self._proposal()
        self.gate.approve(prop.issue_id, by="user")
        decision = self.gate.decide(prop)
        self.assertEqual(decision["verdict"], "approved")

    def test_high_risk_auto_denied(self) -> None:
        prop = self._proposal(action="删除 C:\\Windows 缓存")
        decision = self.gate.decide(prop)
        self.assertEqual(decision["verdict"], "requires_approval_high_risk")

    def test_high_risk_approvable_by_user(self) -> None:
        prop = self._proposal(action="删除 C:\\Windows 缓存")
        self.gate.approve(prop.issue_id, by="user")
        decision = self.gate.decide(prop)
        self.assertEqual(decision["verdict"], "approved")

    def test_audit_trail_untouched(self) -> None:
        self.gate.decide(self._proposal())
        self.gate.approve("disk-C-critical")
        self.assertTrue(self.audit.verify().get("ok"))


class TestHealthRepairer(unittest.TestCase):
    """修复执行器：注册动作执行 + 复检 + 回执。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = AppendOnlyAuditLog(Path(self.tmp.name) / "audit.jsonl")
        self.receipt_dir = Path(self.tmp.name) / "receipts"
        self.repairer = HealthRepairer(
            gate=RepairGate(audit=self.audit),
            receipt_dir=self.receipt_dir, audit=self.audit,
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _proposal(self, issue_id="disk-C-critical", action="清理缓存",
                  auto=True) -> RepairProposal:
        return RepairProposal(
            issue_id=issue_id, severity="P1", title="磁盘偏低",
            action=action, impact="释放空间", rollback="可重建缓存",
            auto_allowed=auto,
        )

    def test_execute_registered_auto_action(self) -> None:
        calls = []
        self.repairer.register_action(
            "清理缓存",
            lambda ctx: (calls.append(ctx["issue_id"]), {"cleaned": 12.5})[1],
        )
        receipt = self.repairer.execute(self._proposal())
        self.assertTrue(receipt.executed)
        self.assertEqual(receipt.verdict, "auto")
        self.assertEqual(calls, ["disk-C-critical"])
        # 回执落盘
        target = self.receipt_dir / "receipt-disk-C-critical.json"
        self.assertTrue(target.exists())

    def test_unregistered_action_not_auto_executed(self) -> None:
        receipt = self.repairer.execute(self._proposal(auto=True))
        self.assertFalse(receipt.executed)
        self.assertEqual(receipt.verdict, "requires_approval")

    def test_unapproved_not_executed(self) -> None:
        self.repairer.register_action(
            "清理缓存",
            lambda ctx: {"cleaned": 1.0},
        )
        receipt = self.repairer.execute(self._proposal(auto=False))
        self.assertFalse(receipt.executed)
        self.assertEqual(receipt.verdict, "requires_approval")

    def test_approved_executes(self) -> None:
        prop = self._proposal(auto=False)
        self.repairer.register_action(
            "清理缓存",
            lambda ctx: {"cleaned": 2.0},
        )
        self.repairer.gate.approve(prop.issue_id, by="user")
        receipt = self.repairer.execute(prop)
        self.assertTrue(receipt.executed)
        self.assertEqual(receipt.verdict, "approved")

    def test_high_risk_denied_even_if_registered(self) -> None:
        self.repairer.register_action(
            "删除 C:\\Windows 缓存",
            lambda ctx: {"deleted": True},
        )
        prop = RepairProposal(
            issue_id="hr-1", severity="P0", title="高危",
            action="删除 C:\\Windows 缓存", impact="系统级",
            rollback="不可回滚", auto_allowed=True,
        )
        receipt = self.repairer.execute(prop)
        self.assertFalse(receipt.executed)
        self.assertEqual(receipt.verdict, "requires_approval_high_risk")

    def test_audit_chain_intact(self) -> None:
        self.repairer.register_action("清理缓存", lambda ctx: {"cleaned": 1.0})
        self.repairer.execute(self._proposal())
        self.assertTrue(self.audit.verify().get("ok"))


if __name__ == "__main__":
    unittest.main()
