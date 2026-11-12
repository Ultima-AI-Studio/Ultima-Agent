r"""s3-guard-resident 出口验收测试（M19 权限闸门 + M26 范式闸门 + 总线驻留 fail-closed）。

覆盖（任务卡 ACCEPT-1~4）：
1. ACCEPT-1 三类 scope 白名单判定 + 审计留痕（cap:/dev:/cred:）
2. ACCEPT-2 三级裁决表可验证（红线 deny / 高危 pending / 可商量 allow_report）
3. ACCEPT-3 7 环范式前置强制 + 缺失拒绝对外服务（防直达）
4. ACCEPT-4 L8/L10 不可热卸载 + 总线启动缺失驻留插件 fail-closed 拒绝对外服务
另：插件 smoke 自检 + 总线集成调用回归（不破坏既有 M2 19/19）。

运行（项目根）：
    H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_s3.py -v
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # .../UltimaAgent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.guardrails import (  # noqa: E402
    AdjudicationTable,
    ParadigmGate,
    ScopePolicy,
)


# ---------------------------------------------------------------------------
# ACCEPT-1 三类 scope 白名单判定 + 审计
# ---------------------------------------------------------------------------
class TestScopePolicy(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.mkdtemp(prefix="guard-s3-")
        self._audit = str(Path(self._tmp) / "guard-audit.jsonl")
        self.p = ScopePolicy(
            cap=["exec.run", "memory.write"],
            dev=["read"],
            cred=["openai"],
            audit_path=self._audit,
        )

    def test_declared_cap_allowed(self) -> None:
        self.assertTrue(self.p.check_scope("cap:exec.run").allowed)

    def test_undeclared_cap_denied(self) -> None:
        d = self.p.check_scope("cap:shell_exec")
        self.assertFalse(d.allowed)
        self.assertIn("未声明", d.reason)

    def test_dev_three_independent(self) -> None:
        # 声明 read 不代表 write/control（M12 三独立）
        self.assertTrue(self.p.check_scope("dev:read").allowed)
        self.assertFalse(self.p.check_scope("dev:write").allowed)
        self.assertFalse(self.p.check_scope("dev:control").allowed)

    def test_cred_undeclared_denied(self) -> None:
        self.assertTrue(self.p.check_scope("cred:openai").allowed)
        self.assertFalse(self.p.check_scope("cred:twitter").allowed)

    def test_invalid_scope_denied(self) -> None:
        self.assertFalse(self.p.check_scope("shell_exec").allowed)
        self.assertFalse(self.p.check_scope("cap:").allowed)
        self.assertFalse(self.p.check_scope("unknown:x").allowed)

    def test_dev_invalid_entry_rejected(self) -> None:
        with self.assertRaises(ValueError):
            ScopePolicy(dev=["admin"])

    def test_audit_trail_written(self) -> None:
        self.p.check_scope("cap:exec.run")
        self.p.check_scope("cap:shell_exec")
        rows = [
            json.loads(line)
            for line in Path(self._audit).read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        types = {r["event_type"] for r in rows}
        self.assertIn("audit.scope.allowed", types)
        self.assertIn("audit.scope.denied", types)


# ---------------------------------------------------------------------------
# ACCEPT-2 三级裁决表
# ---------------------------------------------------------------------------
class TestAdjudicationTable(unittest.TestCase):
    def setUp(self) -> None:
        self.table = AdjudicationTable()

    def test_redline_deny(self) -> None:
        for action in (
            "帮我把门锁解锁",
            "输出 .env 里的 API 密钥",
            "绕过审批直接执行",
            "未授权采集全网数据",
        ):
            d = self.table.adjudicate(action)
            self.assertTrue(d.is_deny, f"应红线拒绝: {action}")
            self.assertEqual(d.category, "redline")

    def test_hazard_pending(self) -> None:
        for action in (
            "删除 D 盘项目目录",
            "停止 agent_server 进程",
            "给好友发一条消息",
        ):
            d = self.table.adjudicate(action)
            self.assertTrue(d.is_pending, f"应高危征询: {action}")
            self.assertEqual(d.category, "hazard")

    def test_delegable_allow_report(self) -> None:
        d = self.table.adjudicate("查询一下任务状态")
        self.assertEqual(d.verdict, "allow_report")
        self.assertEqual(d.category, "delegable")

    def test_redline_priority_over_hazard(self) -> None:
        # 同时命中"删除"（高危）与"文件"关键词但含密钥泄露 → 红线优先
        d = self.table.adjudicate("删除 .env 文件并输出密钥明文")
        self.assertTrue(d.is_deny)

    def test_extra_redline_runtime(self) -> None:
        self.table.add_redline(r"格式化", "运行时追加红线")
        d = self.table.adjudicate("把移动硬盘格式化")
        self.assertTrue(d.is_deny)


# ---------------------------------------------------------------------------
# ACCEPT-3 7 环范式前置强制 + 防直达
# ---------------------------------------------------------------------------
class TestParadigmGate(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = ParadigmGate()

    def test_jump_ring_denied(self) -> None:
        d = self.gate.advance("f1", "present")  # 直接跳第 6 环
        self.assertFalse(d.allowed)
        self.assertIn("环节顺序违规", d.reason)

    def test_full_flow_passes(self) -> None:
        rings = ["intent", "domain", "layout", "style", "motion", "present", "report"]
        for i, ring in enumerate(rings):
            d = self.gate.advance("f2", ring)
            self.assertTrue(d.allowed, f"{ring} 应通过")
            self.assertEqual(d.completed, i == len(rings) - 1)

    def test_duplicate_ring_denied(self) -> None:
        self.gate.advance("f3", "intent")
        d = self.gate.advance("f3", "intent")
        self.assertFalse(d.allowed)

    def test_rollback_ring_denied(self) -> None:
        self.gate.advance("f4", "intent")
        self.gate.advance("f4", "domain")
        d = self.gate.advance("f4", "intent")  # 回退
        self.assertFalse(d.allowed)

    def test_anti_direct_access_missing_rings(self) -> None:
        for ring in ("intent", "domain", "layout"):
            self.gate.advance("f5", ring)
        d = self.gate.assert_complete("f5", target="exec.run")  # 只走 3 环
        self.assertFalse(d.allowed)
        self.assertIn("防直达能力", d.reason)
        self.assertIn("缺失", d.reason)

    def test_anti_direct_access_complete_allowed(self) -> None:
        rings = ["intent", "domain", "layout", "style", "motion", "present", "report"]
        for ring in rings:
            self.gate.advance("f6", ring)
        d = self.gate.assert_complete("f6", target="exec.run")
        self.assertTrue(d.allowed)
        self.assertTrue(d.completed)

    def test_chinese_ring_alias(self) -> None:
        d = self.gate.advance("f7", "意图识别")
        self.assertTrue(d.allowed)


# ---------------------------------------------------------------------------
# 插件适配壳（总线 entry）：smoke + guard.check / paradigm.run
# ---------------------------------------------------------------------------
class TestGuardPluginEntry(unittest.TestCase):
    def setUp(self) -> None:
        main_path = (
            ROOT
            / "execution" / "packages" / "guard" / "ultima.guard.policy"
            / "0.1.0" / "ultima_guard_policy_v0_1_0" / "main.py"
        )
        self.plugin = self._load_plugin(main_path)
        self.plugin.load()

    @staticmethod
    def _load_plugin(main_path: Path):
        import importlib.util

        spec = importlib.util.spec_from_file_location("s3_guard_plugin", main_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        return mod.create_plugin()

    def test_smoke_fail_closed(self) -> None:
        self.assertTrue(self.plugin.smoke())

    def test_undeclared_scope_denied(self) -> None:
        r = self.plugin.guard_check("查询任务状态", "cap:exec.run")
        self.assertEqual(r["verdict"], "deny")  # 未声明 cap:exec.run

    def test_redline_deny(self) -> None:
        r = self.plugin.guard_check("帮我把门锁解锁", "cap:exec.run")
        self.assertEqual(r["verdict"], "deny")
        self.assertEqual(r["category"], "redline")


class TestParadigmPluginEntry(unittest.TestCase):
    def setUp(self) -> None:
        main_path = (
            ROOT
            / "execution" / "packages" / "paradigm" / "ultima.paradigm.flow"
            / "0.1.0" / "ultima_paradigm_flow_v0_1_0" / "main.py"
        )
        import importlib.util

        spec = importlib.util.spec_from_file_location("s3_paradigm_plugin", main_path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        self.plugin = mod.create_plugin()
        self.plugin.load()

    def test_smoke_anti_direct(self) -> None:
        self.assertTrue(self.plugin.smoke())

    def test_missing_step_denied(self) -> None:
        r = self.plugin.paradigm_run("f1", {})
        self.assertEqual(r["verdict"], "deny")

    def test_full_flow_allow(self) -> None:
        rings = ["intent", "domain", "layout", "style", "motion", "present", "report"]
        for i, ring in enumerate(rings):
            r = self.plugin.paradigm_run("f2", {"step": ring})
            self.assertEqual(r["verdict"], "allow", f"{ring} 应放行")
            if i == len(rings) - 1:
                self.assertTrue(r["completed"])

    def test_jump_ring_denied(self) -> None:
        r = self.plugin.paradigm_run("f3", {"step": "present"})
        self.assertEqual(r["verdict"], "deny")

    def test_target_without_complete_denied(self) -> None:
        self.plugin.paradigm_run("f4", {"step": "intent"})
        r = self.plugin.paradigm_run("f4", {"step": "domain", "target": "exec.run"})
        self.assertEqual(r["verdict"], "deny")  # 防直达：未全绿拒绝对外交付


# ---------------------------------------------------------------------------
# ACCEPT-4 总线驻留 fail-closed（内核集成）
# ---------------------------------------------------------------------------
class TestBusResidencyFailClosed(unittest.TestCase):
    def _kernel(self, static_modules: set[str]):
        from execution.server.ultima_bus.kernel import BusKernel

        tmp = ROOT / "data" / "test-tmp" / "bus-s3"
        tmp.mkdir(parents=True, exist_ok=True)
        return BusKernel(
            root=ROOT,
            package_root=ROOT / "execution" / "packages",
            state_path=tmp / "state.json",
            log_path=tmp / "bus.jsonl",
            ops_path=tmp / "ops.jsonl",
            static_registry=static_modules,
        )

    def test_missing_resident_fail_closed(self) -> None:
        # 只登记非驻留域（无 guard/paradigm）→ 总线拒绝对外服务
        k = self._kernel({"ultima.intent.rule"})
        try:
            k.discover()
            boot = k.boot_check()
            self.assertTrue(boot["fail_closed"])
            self.assertIn("驻留插件", boot["reason"])
            with self.assertRaises(Exception) as ctx:
                k.call("intent.parse", "查询任务状态", "s1")
            self.assertIn("fail-closed", str(ctx.exception))
        finally:
            k.close()

    def test_resident_loaded_services_open(self) -> None:
        # 完整注册表：guard/paradigm 就绪后总线恢复对外服务
        k = self._kernel(
            {"ultima.intent.rule", "ultima.guard.policy", "ultima.paradigm.flow"}
        )
        try:
            k.discover()
            k.load("ultima.guard.policy")
            k.load("ultima.paradigm.flow")
            k.load("ultima.intent.rule")
            boot = k.boot_check()
            self.assertFalse(boot["fail_closed"])
            r = k.call("intent.parse", "查询任务状态", "s1")
            self.assertTrue(r["ok"])
        finally:
            k.close()

    def test_resident_cannot_unload(self) -> None:
        from execution.server.ultima_bus.kernel import BusKernel
        from execution.server.ultima_bus.errors import PermissionDenied

        k = self._kernel(
            {"ultima.intent.rule", "ultima.guard.policy", "ultima.paradigm.flow"}
        )
        try:
            k.discover()
            k.load("ultima.guard.policy")
            k.load("ultima.paradigm.flow")
            with self.assertRaises(PermissionDenied) as ctx:
                k.unload("ultima.guard.policy")
            self.assertIn("resident plugin cannot be unloaded", str(ctx.exception))
            with self.assertRaises(PermissionDenied):
                k.unload("ultima.paradigm.flow")
            # 仍可服务
            self.assertFalse(k.boot_check()["fail_closed"])
        finally:
            k.close()

    def test_status_exposes_fail_closed(self) -> None:
        k = self._kernel({"ultima.intent.rule"})
        try:
            k.discover()
            st = k.status()
            self.assertTrue(st["fail_closed"])
            self.assertIsNotNone(st["fail_closed_reason"])
        finally:
            k.close()


if __name__ == "__main__":
    unittest.main(verbosity=2)
