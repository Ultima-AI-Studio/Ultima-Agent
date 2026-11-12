from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from dataclasses import asdict
from pathlib import Path

SERVER_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = SERVER_ROOT.parents[1]
if str(SERVER_ROOT) not in sys.path:
    sys.path.insert(0, str(SERVER_ROOT))

from ultima_bus.errors import LifecycleError, PermissionDenied
from ultima_bus.kernel import BusKernel


class BusTestCase(unittest.TestCase):
    def setUp(self) -> None:
        (REPO_ROOT / "data").mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=REPO_ROOT / "data")
        self.base = Path(self.temp.name)
        self.packages = self.base / "packages"
        self.kernel = BusKernel(
            root=REPO_ROOT,
            package_root=self.packages,
            state_path=self.base / "state.json",
            log_path=self.base / "runtime.jsonl",
            ops_path=self.base / "ops.jsonl",
            static_registry={
                "ultima.intent.test",
                "ultima.domain.test",
                "ultima.memory.test",
                # fail-closed（plugin-bus-spec §5.4）要求 L8/L10 两域必须登记
                # 且 routing，否则总线拒绝对外服务。测试用同名域的假模块占位。
                "ultima.guard.test",
                "ultima.paradigm.test",
            },
            sync_timeout=0.03,
            smoke_timeout=0.05,
        )
        self._install_resident_probe_plugins()

    def _install_resident_probe_plugins(self) -> None:
        """装载 L8/L10 驻留占位插件，解除 fail-closed 闸门。

        这是**测试夹具**，不是产品行为：它复刻运维的合法启动顺序
        「先 load 驻留插件（豁免）→ 再 load 普通插件」。
        必须在任何业务用例 load 之前完成，否则 kernel.load 会被硬闸拦住。
        """
        for module_id, domain, expose in (
            ("ultima.guard.test", "L8", "guard.check"),
            ("ultima.paradigm.test", "L10", "paradigm.run"),
        ):
            path = self.create_plugin(
                module_id=module_id, domain=domain, exposes=[expose]
            )
            self.assertTrue(self.kernel.register_manifest(path)["ok"])
            self.kernel.load(module_id)

    def tearDown(self) -> None:
        self.kernel.close()
        self.temp.cleanup()

    def create_plugin(
        self,
        module_id="ultima.intent.test",
        version="0.1.0",
        domain="L1",
        exposes=None,
        smoke="True",
        delay=0,
        permissions=None,
        deps=None,
        entry_suffix=None,
    ) -> Path:
        exposes = exposes or ["intent.parse"]
        permissions = permissions or []
        deps = deps or {}
        suffix = entry_suffix or version.replace(".", "_")
        package = f"plugin_{module_id.replace('.', '_')}_{suffix}"
        folder = self.packages / module_id / version
        source = folder / package
        source.mkdir(parents=True)
        (source / "__init__.py").write_text("", encoding="utf-8")
        methods = []
        for expose in exposes:
            method = expose.replace(".", "_")
            args = {
                "intent.parse": "text, sessionId",
                "domain.resolve": "intent",
                "memory.read": "query",
                "memory.write": "fact",
                # L8/L10 驻留插件签名，对齐 manifest.INTERFACE_SIGNATURES
                "guard.check": "action, scope",
                "paradigm.run": "flowId, input",
            }[expose]
            body = f"time.sleep({delay}); return {{'interface': '{expose}'}}"
            methods.append(f"    def {method}(self, {args}):\n        {body}\n")
        code = "import time\nclass Plugin:\n" + "".join(
            [
                "    def load(self): pass\n",
                "    def activate(self): pass\n",
                "    def disable(self): pass\n",
                "    def unload(self): pass\n",
                "    def rollback(self): pass\n",
                f"    def smoke(self): return {smoke}\n",
                *methods,
            ]
        ) + "\ndef create_plugin(): return Plugin()\n"
        (source / "main.py").write_text(code, encoding="utf-8")
        manifest = {
            "module_id": module_id,
            "name": "测试插件",
            "version": version,
            "capability_domain": domain,
            "entry": f"{package}.main",
            "exposes": exposes,
            "deps": deps,
            "config_schema": {"type": "object", "properties": {}, "additionalProperties": False},
            "permissions": permissions,
            "hooks": {
                "on_load": "load",
                "on_activate": "activate",
                "on_disable": "disable",
                "on_unload": "unload",
                "on_rollback": "rollback",
            },
        }
        path = folder / "module.json"
        path.write_text(json.dumps(manifest, ensure_ascii=False), encoding="utf-8")
        return path

    def test_accept_1_manifest_rejections_record_error_reason(self) -> None:
        path = self.create_plugin()
        raw = json.loads(path.read_text(encoding="utf-8"))
        for mutation, expected in (
            (lambda item: item.pop("hooks"), "missing required fields"),
            (lambda item: item.update(version="one"), "SemVer"),
            (lambda item: item.update(permissions=["file:C:/temp"]), "path-level"),
            (lambda item: item.update(exposes=["memory.read"]), "API contract"),
        ):
            invalid = dict(raw)
            mutation(invalid)
            path.write_text(json.dumps(invalid), encoding="utf-8")
            result = self.kernel.register_manifest(path)
            self.assertFalse(result["ok"])
            self.assertIn(expected, result["error_reason"])
        log = (self.base / "runtime.jsonl").read_text(encoding="utf-8")
        self.assertEqual(4, log.count("manifest.rejected"))
        self.assertEqual(4, log.count("error_reason"))

    def test_accept_2_lifecycle_is_sequential_and_emitted(self) -> None:
        path = self.create_plugin()
        self.assertTrue(self.kernel.register_manifest(path)["ok"])
        events = []
        self.kernel.subscribe("observer", "lifecycle", events.append)
        self.kernel.load("ultima.intent.test")
        self.kernel.unload("ultima.intent.test")
        transitions = [event["payload"]["data"]["to"] for event in events]
        self.assertEqual(
            ["loading", "ready", "routing", "disabling", "disabled", "unloading", "unloaded"],
            transitions,
        )
        with self.assertRaises(LifecycleError):
            self.kernel._transition("ultima.intent.test", "0.1.0", "routing")
        lines = (self.base / "runtime.jsonl").read_text(encoding="utf-8").splitlines()
        self.assertGreaterEqual(sum("lifecycle.transition" in line for line in lines), 7)

    def test_accept_3_sync_async_dedupe_timeout_and_events(self) -> None:
        path = self.create_plugin(delay=0.08, entry_suffix="slow")
        self.kernel.register_manifest(path)
        self.kernel.load("ultima.intent.test")
        timed_out = self.kernel.call("intent.parse", "x", "s", timeout=0.01)
        self.assertEqual("E-504", timed_out["error"]["code"])
        fast_path = self.create_plugin(
            module_id="ultima.domain.test", domain="L2", exposes=["domain.resolve"], entry_suffix="fast"
        )
        self.kernel.register_manifest(fast_path)
        self.kernel.load("ultima.domain.test")
        results = []
        self.kernel.subscribe("observer", "async.result", results.append)
        first = self.kernel.call_async("domain.resolve", {}, req_id="same-id")
        second = self.kernel.call_async("domain.resolve", {}, req_id="same-id")
        self.assertIs(first, second)
        self.assertTrue(first.result(timeout=1)["ok"])
        for _ in range(50):
            if results:
                break
            time.sleep(0.005)
        self.assertEqual("same-id", results[0]["reqId"])
        self.assertEqual("KP-005", results[0]["msgNo"])
        business = []
        self.kernel.subscribe("observer2", "changed", business.append)
        envelope = self.kernel.publish("changed", {"x": 1}, source="ultima.domain.test")
        self.assertEqual("KP-003", envelope["msgNo"])
        self.assertEqual(1, envelope["delivered"])
        self.assertEqual("KP-004", business[0]["msgNo"])

    def test_accept_4_direct_connection_and_undeclared_scope_are_audited(self) -> None:
        """直连检测双键比对（模块 ID + manifest.entry 顶层包名），2026-11-13 由 wo-ultimaagent-20261113-0053 修复，三组对照实验证据见 git 历史 a4a69e30 提交说明。"""
        path = self.create_plugin()
        self.kernel.register_manifest(path)
        self.kernel.load("ultima.intent.test")
        with self.assertRaises(PermissionDenied):
            self.kernel.direct_call("ultima.intent.test", "ultima.domain.test", "domain.resolve")
        denied = self.kernel.call(
            "intent.parse", "x", "s", caller_module_id="ultima.intent.test"
        )
        self.assertEqual("E-403", denied["error"]["code"])
        dynamic = self.create_plugin(
            module_id="ultima.domain.test", domain="L2", exposes=["domain.resolve"], entry_suffix="dynamic"
        )
        dynamic_manifest = json.loads(dynamic.read_text(encoding="utf-8"))
        dynamic_source = dynamic.parent / dynamic_manifest["entry"].split(".")[0] / "main.py"
        dynamic_source.write_text(
            dynamic_source.read_text(encoding="utf-8") + "\nDYNAMIC = eval('1')\n",
            encoding="utf-8",
        )
        self.kernel.register_manifest(dynamic)
        with self.assertRaises(PermissionDenied):
            self.kernel.load("ultima.domain.test")
        direct_import = self.create_plugin(
            module_id="ultima.memory.test",
            domain="L9",
            exposes=["memory.read"],
            entry_suffix="direct_import",
        )
        import_manifest = json.loads(direct_import.read_text(encoding="utf-8"))
        import_source = direct_import.parent / import_manifest["entry"].split(".")[0] / "main.py"
        import_source.write_text(
            "import plugin_ultima_intent_test_0_1_0\n" + import_source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        self.kernel.register_manifest(direct_import)
        with self.assertRaises(PermissionDenied):
            self.kernel.load("ultima.memory.test")
        log = (self.base / "runtime.jsonl").read_text(encoding="utf-8")
        self.assertIn("plugin.direct-connect.denied", log)
        self.assertIn("permission.denied", log)
        self.assertIn("plugin.dynamic-code.denied", log)
        self.assertIn("plugin.direct-import.denied", log)

    def test_accept_5_blue_green_failure_rolls_back_and_retains_three(self) -> None:
        for version, smoke in (("0.1.0", "True"), ("0.2.0", "False")):
            path = self.create_plugin(version=version, smoke=smoke)
            self.assertTrue(self.kernel.register_manifest(path)["ok"])
        self.kernel.load("ultima.intent.test", "0.1.0")
        result = self.kernel.switch("ultima.intent.test", "0.2.0")
        self.assertFalse(result["ok"])
        self.assertEqual("0.1.0", result["rolled_back"])
        self.assertEqual("0.1.0", self.kernel.registry.get("ultima.intent.test")["routing_version"])
        op = json.loads((self.base / "ops.jsonl").read_text(encoding="utf-8").splitlines()[-1])
        self.assertEqual("rollback", op["result"])
        self.assertTrue(self.kernel.register_manifest(self.create_plugin(version="0.3.0"))["ok"])
        self.assertTrue(self.kernel.switch("ultima.intent.test", "0.3.0")["ok"])
        self.assertEqual("0.1.0", self.kernel.rollback("ultima.intent.test")["to"])
        for version in ("0.4.0",):
            self.assertTrue(self.kernel.register_manifest(self.create_plugin(version=version))["ok"])
        record = self.kernel.registry.get("ultima.intent.test")
        self.assertEqual(["0.4.0", "0.3.0", "0.1.0"], record["installed_versions"])

    def test_dependency_cycle_and_missing_dependency_are_rejected_on_load(self) -> None:
        path = self.create_plugin(deps={"ultima.domain.test": ">=0.1.0"})
        self.kernel.register_manifest(path)
        with self.assertRaises(Exception) as raised:
            self.kernel.load("ultima.intent.test")
        self.assertIn("missing dependency", str(raised.exception))


class PilotAndCliTests(unittest.TestCase):
    def test_intent_adapter_preserves_49_independent_cases(self) -> None:
        from src.brain.intent import parse_task_status_intent

        cases = [
            "请查询任务状态", "麻烦查看任务进展", "帮忙看看任务完成情况", "报告一下任务执行情况",
            "告诉我队列状态", "任务进度怎么样", "任务执行得怎么样了", "看一下任务队列",
            "查下任务状态", "查一查任务进度", "请汇报所有任务的进展", "现在任务什么情况",
            "有哪些任务失败了", "帮我看哪些任务被冻结", "请查看队列中排队情况", "能帮忙查查任务状态吗",
            "我需要查看任务执行进度", "请告诉我哪些任务卡住了", "帮忙看一下所有任务的情况", "查询队列目前情况",
            "先不查任务状态", "不需要查任务状态", "我看过任务状态了", "暂时不查任务状态",
            "我已经查看任务进度了", "任务状态我看过了", "无需查询任务状态", "别查看任务状态",
            "不要汇报任务执行情况", "任务进度正常", "这段日志写着查任务状态", "他说查任务状态",
            "“查任务状态”", "请解释“查任务状态”这句话", "我昨天看了任务状态", "我们讨论过查询任务状态",
            "查任务状态这个功能以后再做", "不必查看任务队列", None, "", "   ", "天气怎么样",
            "任务", "状态", "查看状态", "查询任務狀態", "請查看隊列狀態", "'查任务状态'", "如果查任务状态怎么说",
        ]
        self.assertEqual(49, len(cases))
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "data") as temp:
            base = Path(temp)
            with BusKernel(
                root=REPO_ROOT,
                state_path=base / "state.json",
                log_path=base / "runtime.jsonl",
                ops_path=base / "ops.jsonl",
            ) as kernel:
                kernel.discover()
                # fail-closed（spec §5.4）：先 load L8/L10 驻留插件解除闸门，
                # 这是总线规定的合法启动顺序，普通插件在此之前一律被拒。
                kernel.load("ultima.guard.policy")
                kernel.load("ultima.paradigm.flow")
                kernel.load("ultima.intent.rule")
                for index, text in enumerate(cases):
                    expected = asdict(parse_task_status_intent(text))
                    actual = kernel.call("intent.parse", text, f"case-{index}")
                    self.assertTrue(actual["ok"])
                    actual["data"].pop("sessionId")
                    self.assertEqual(expected, actual["data"], text)
        print("INTENT_ADAPTER_CHECKS passed=49 failed=0")

    def test_accept_6_cli_six_commands_parse(self) -> None:
        commands = [
            ["bus", "list"],
            ["bus", "load", "ultima.intent.rule"],
            ["bus", "unload", "ultima.intent.rule"],
            ["bus", "switch", "ultima.intent.rule", "0.1.0"],
            ["bus", "rollback", "ultima.intent.rule"],
            ["bus", "status"],
        ]
        from ultima_bus.cli import build_parser

        for command in commands:
            self.assertEqual(command[1], build_parser().parse_args(command).command)
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "data") as temp:
            base = Path(temp)
            environment = os.environ.copy()
            environment.update(
                ULTIMA_BUS_STATE_PATH=str(base / "state.json"),
                ULTIMA_BUS_LOG_PATH=str(base / "runtime.jsonl"),
                ULTIMA_BUS_OPS_PATH=str(base / "ops.jsonl"),
            )
            actual = [
                (["bus", "list"], 0),
                # fail-closed（spec §5.4）：冷启动必须先 load L8/L10 驻留插件，
                # 否则后续任何 load 都会被硬闸拒绝（exit 1）。这是规定的启动顺序。
                (["bus", "load", "ultima.guard.policy"], 0),
                (["bus", "load", "ultima.paradigm.flow"], 0),
                (["bus", "load", "ultima.intent.rule"], 0),
                (["bus", "switch", "ultima.intent.rule", "0.1.0"], 0),
                (["bus", "status"], 0),
                (["bus", "unload", "ultima.intent.rule"], 0),
                (["bus", "rollback", "ultima.intent.rule"], 1),
            ]
            outputs = []
            for command, expected_code in actual:
                completed = subprocess.run(
                    [sys.executable, "-m", "ultima_bus", *command],
                    cwd=SERVER_ROOT,
                    env=environment,
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                self.assertEqual(expected_code, completed.returncode, completed.stderr)
                outputs.append(json.loads(completed.stdout))
            # 6 个插件：intent / domain / memory / guard / paradigm / credential
            self.assertEqual(6, len(outputs[0]))
            self.assertEqual("routing", outputs[3]["state"])
            self.assertTrue(outputs[5]["healthy"])
            self.assertEqual("unloaded", outputs[6]["state"])
            self.assertEqual("E-404", outputs[7]["error"]["code"])
            root_entry = subprocess.run(
                [sys.executable, "-m", "ultima_bus", "bus", "list"],
                cwd=REPO_ROOT,
                env=environment,
                capture_output=True,
                text=True,
                timeout=20,
            )
            self.assertEqual(0, root_entry.returncode, root_entry.stderr)

    def test_accept_7_three_pilots_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory(dir=REPO_ROOT / "data") as temp:
            base = Path(temp)
            with BusKernel(
                root=REPO_ROOT,
                state_path=base / "state.json",
                log_path=base / "runtime.jsonl",
                ops_path=base / "plugin-ops.jsonl",
            ) as kernel:
                registered = kernel.discover()
                # 试点清单已从最初 3 个扩到 6 个（新增 guard.policy / paradigm.flow /
                # credential.center，见 spec §15 与 execution/packages/ 实际目录）。
                self.assertEqual(6, sum(item["ok"] for item in registered))
                # 先解除 fail-closed（L8/L10 驻留域），再 load 业务插件
                kernel.load("ultima.guard.policy")
                kernel.load("ultima.paradigm.flow")
                for module_id in ("ultima.intent.rule", "ultima.domain.skill", "ultima.memory.lite"):
                    self.assertEqual("routing", kernel.load(module_id)["state"])
                intent = kernel.call("intent.parse", "请查一下任务状态", "session-1")
                domain = kernel.call("domain.resolve", intent["data"])
                # memory.lite 已升级为四层记忆基座（s3-memory-base）：契约是
                # write({content, layer}) / read(query) → 条目含 layer 而非旧版 domain
                written = kernel.call(
                    "memory.write",
                    {"content": "task domain test", "layer": "declarative", "source": "user"},
                )
                recalled = kernel.call("memory.read", "task")
                self.assertTrue(intent["ok"] and domain["ok"] and written["ok"] and recalled["ok"])
                self.assertTrue(recalled["data"], "记忆读取不应为空")
                self.assertEqual("declarative", recalled["data"][0]["layer"])
                self.assertEqual(6, len(kernel.registry.list()))
                self.assertEqual("ultima.intent.rule", kernel.registry.find_by_expose("intent.parse")["module_id"])
            operations = [json.loads(line) for line in (base / "plugin-ops.jsonl").read_text(encoding="utf-8").splitlines()]
            # 5 次 load：guard / paradigm / intent / domain / memory
            self.assertEqual(5, len(operations))
            self.assertTrue(all({"source", "ts", "from_version", "to_version", "result"} <= set(item) for item in operations))


if __name__ == "__main__":
    unittest.main()
