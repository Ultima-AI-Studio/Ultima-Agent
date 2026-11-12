"""s10-device-mcp 验收测试：MCP stdio 运行时 + 设备可控性过滤 + 冒烟。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.iot.device_profile import (
    Controlability,
    ControlabilityJudge,
    DeviceProfile,
    DeviceRegistry,
    ProvisionChain,
)
from src.brain.iot.mcp_runtime import (
    McpError,
    McpRuntime,
    make_fake_config,
)


def _unconfigured() -> McpRuntime:
    return McpRuntime(None)


class TestMcpRuntime(unittest.TestCase):
    # ACCEPT-4：无 server 配置如实报告未接入
    def test_unconfigured_reports_not_connected(self) -> None:
        rt = _unconfigured()
        self.assertFalse(rt.available)
        self.assertEqual(rt.initialize()["ok"], False)
        self.assertIn("未接入", rt.initialize()["reason"])
        with self.assertRaises(McpError):
            rt.list_tools()
        self.assertEqual(rt.call_tool("env/read")["ok"], False)

    # ACCEPT-1：全链冒烟（启动/初始化/list_tools/call_tool）
    def test_full_chain_smoke(self) -> None:
        with McpRuntime(make_fake_config()) as rt:
            init = rt.initialize()
            self.assertTrue(init["ok"])
            self.assertEqual(init["server"]["serverInfo"]["name"], "fake-mcp")
            tools = rt.list_tools()
            names = {t["name"] for t in tools}
            self.assertIn("env/read", names)
            self.assertIn("device/control", names)
            res = rt.call_tool("env/read")
            self.assertTrue(res["ok"])
            self.assertIn("cwd", res["result"])
            res2 = rt.call_tool("device/read")
            self.assertTrue(res2["ok"])
            self.assertEqual(res2["result"]["value"], 1)

    # ACCEPT-2：确定性错误（工具失败 / 超时 / 非法）
    def test_tool_failure_deterministic(self) -> None:
        with McpRuntime(make_fake_config(fail_tool="device/read")) as rt:
            rt.initialize()
            rt.list_tools()
            res = rt.call_tool("device/read")
            self.assertTrue(res["ok"])   # 传输层 OK
            self.assertFalse(res["result"]["ok"])  # 业务层失败如实返回
            self.assertIn("模拟失败", res["result"]["error"])

    def test_crash_deterministic(self) -> None:
        cfg = make_fake_config()
        cfg.command = [cfg.command[0], "-u", "-c", "import sys; sys.exit(1)"]
        rt = McpRuntime(cfg)
        with self.assertRaises(McpError):
            rt.initialize()

    # ACCEPT-3：设备档案 + 可控性过滤
    def test_device_gate_filters_tools(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            registry = DeviceRegistry(Path(td))
            chain = ProvisionChain(registry)
            # 发现 + 建档 + 凭证
            chain.discover("d1", "测试开关", "mcp", entity_type="switch")
            chain.provision("d1", "cred://d1")
            # 可控性：可控（凭证+switch）
            chain.check("d1", reachable=True)
            with McpRuntime(make_fake_config(), device_registry=registry,
                            provision_chain=chain) as rt:
                rt.initialize()
                rt.list_tools()
                # 可控设备：read/write/control 全放行
                self.assertTrue(rt.call_tool("device/read", device_id="d1")["ok"])
                self.assertTrue(rt.call_tool("device/write", device_id="d1")["ok"])
                self.assertTrue(rt.call_tool("device/control", device_id="d1")["ok"])
            # 不可控设备（无凭证）：拒绝并留原因
            chain.discover("d2", "不可控灯", "mcp", entity_type="light")
            with McpRuntime(make_fake_config(), device_registry=registry,
                            provision_chain=chain) as rt:
                rt.initialize()
                rt.list_tools()
                gate = rt.call_tool("device/control", device_id="d2")
                self.assertFalse(gate["ok"])
                self.assertIn("不可", gate["reason"])
                self.assertIn("可控性", gate["reason"])

    def test_device_gate_unknown_device(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            registry = DeviceRegistry(Path(td))
            chain = ProvisionChain(registry)
            with McpRuntime(make_fake_config(), device_registry=registry,
                            provision_chain=chain) as rt:
                rt.initialize()
                rt.list_tools()
                res = rt.call_tool("device/read", device_id="ghost")
                self.assertFalse(res["ok"])
                self.assertIn("未建档", res["reason"])

    def test_device_gate_unknown_tool(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            registry = DeviceRegistry(Path(td))
            chain = ProvisionChain(registry)
            chain.discover("d1", "测试", "mcp", entity_type="switch")
            chain.provision("d1", "cred://d1")
            with McpRuntime(make_fake_config(), device_registry=registry,
                            provision_chain=chain) as rt:
                rt.initialize()
                rt.list_tools()
                res = rt.call_tool("bogus/tool", device_id="d1")
                self.assertFalse(res["ok"])
                self.assertIn("受控清单", res["reason"])

    def test_unreachable_device_reported(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            registry = DeviceRegistry(Path(td))
            chain = ProvisionChain(registry)
            chain.discover("d1", "不可达", "mcp", entity_type="switch")
            chain.provision("d1", "cred://d1")
            chain.check("d1", reachable=False)  # 不可达 → 全部 False
            with McpRuntime(make_fake_config(), device_registry=registry,
                            provision_chain=chain) as rt:
                rt.initialize()
                rt.list_tools()
                res = rt.call_tool("device/read", device_id="d1")
                self.assertFalse(res["ok"])
                self.assertIn("不可", res["reason"])


if __name__ == "__main__":
    unittest.main()
