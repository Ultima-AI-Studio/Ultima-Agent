"""s3-device-profile 验收测试（M15 · ACCEPT-1~6）。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.iot.device_profile import (
    ControlabilityJudge,
    DeviceCred,
    DeviceProfile,
    DeviceRegistry,
    McpAdapter,
    ProvisionChain,
    Reading,
)


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="iot_s3_"))


class TestDeviceProfile(unittest.TestCase):
    def test_four_entities_rw(self):  # ACCEPT-1
        d = make_tmp()
        reg = DeviceRegistry(d)
        reg.upsert(DeviceProfile("dev-1", "客厅灯", "matter", entity_type="light"))
        reg.provision_cred(DeviceCred("dev-1", "cred://dev-1", provisioned=True))
        reg.add_reading(Reading("dev-1", "brightness", 80, unit="%"))
        reg2 = DeviceRegistry(d)  # 持久化读回
        self.assertEqual(reg2.get("dev-1").name, "客厅灯")
        self.assertTrue(reg2.cred("dev-1").provisioned)
        self.assertEqual(len(reg2._readings), 1)

    def test_controlability_three_independent(self):  # ACCEPT-2
        judge = ControlabilityJudge()
        c1 = judge.judge(entity_type="switch", reachable=False, cred_provisioned=True)
        self.assertFalse(c1.readable)
        self.assertFalse(c1.writable)
        self.assertFalse(c1.controllable)
        c2 = judge.judge(entity_type="switch", reachable=True, cred_provisioned=False)
        self.assertTrue(c2.readable)
        self.assertTrue(c2.writable)
        self.assertFalse(c2.controllable)  # 无凭证不可控制
        c3 = judge.judge(entity_type="sensor", reachable=True, cred_provisioned=True)
        self.assertTrue(c3.readable)
        self.assertTrue(c3.writable)
        self.assertFalse(c3.controllable)  # sensor 类型不可控制（防误控）

    def test_mcp_adapter(self):  # ACCEPT-3
        d = make_tmp()
        cfg = d / "mcp.json"
        ad = McpAdapter(cfg)
        self.assertFalse(ad.endpoint("ha")["ok"])
        ad.configure("ha", "http://127.0.0.1:8123", kind="http")
        ep = ad.endpoint("ha")
        self.assertTrue(ep["ok"])
        self.assertEqual(ep["url"], "http://127.0.0.1:8123")
        # 插件不直连 MCP：换 server 只改配置
        ad.configure("ha", "http://192.168.1.9:8123")
        self.assertEqual(ad.endpoint("ha")["url"], "http://192.168.1.9:8123")

    def test_provision_chain(self):  # ACCEPT-4
        d = make_tmp()
        reg = DeviceRegistry(d)
        chain = ProvisionChain(reg)
        r1 = chain.check("dev-x")  # 未建档
        self.assertFalse(r1["ok"])
        self.assertEqual(r1["stage"], "档案")
        chain.discover("dev-x", "空调", "mqtt", entity_type="thermostat")
        r2 = chain.check("dev-x")  # 未配凭证
        self.assertFalse(r2["ok"])
        self.assertEqual(r2["stage"], "凭证")
        chain.provision("dev-x", "cred://dev-x")
        r3 = chain.check("dev-x")  # 全链通过
        self.assertTrue(r3["ok"])
        self.assertTrue(r3["controlability"]["controllable"])

    def test_single_protocol_pilot(self):  # ACCEPT-5
        d = make_tmp()
        reg = DeviceRegistry(d)
        chain = ProvisionChain(reg)
        chain.discover("dev-matter", "灯", "matter", entity_type="light")
        chain.provision("dev-matter", "cred://matter")
        ok_reachable = chain.check("dev-matter", reachable=True)
        self.assertTrue(ok_reachable["ok"])
        # 不可达设备如实报告（不编造）
        not_reachable = chain.check("dev-matter", reachable=False)
        self.assertTrue(not_reachable["ok"])
        self.assertFalse(not_reachable["controlability"]["readable"])
        self.assertIn("不可达", not_reachable["controlability"]["reason"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
