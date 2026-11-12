"""s3-supply-chain 验收测试（M23 供应链闸门 · ACCEPT-1~6）。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.guardrails.supply_chain import (
    SupplyChainGate,
    SupplyChainError,
    LICENSE_DENYLIST,
)


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="supply_s3_"))


class TestSupplyChain(unittest.TestCase):
    def test_whitelist_register_and_reject(self):  # ACCEPT-1
        d = make_tmp()
        gate = SupplyChainGate(d)
        gate.register("requests", "2.31.0", "pypi", "Apache-2.0",
                      owner_approved=True, security_reviewed=True)
        self.assertTrue(gate.is_registered("requests", "2.31.0"))
        self.assertFalse(gate.is_registered("unknown-pkg"))
        r = gate.gate_load("unknown-pkg", "1.0.0")
        self.assertFalse(r["allowed"])
        self.assertTrue(any("未登记" in e for e in r["errors"]))

    def test_license_gpl_rejected(self):  # ACCEPT-2
        d = make_tmp()
        gate = SupplyChainGate(d)
        ok, why = gate.check_license("GPL-3.0")
        self.assertFalse(ok)
        self.assertIn("拒绝", why)
        ok2, _ = gate.check_license("MIT")
        self.assertTrue(ok2)

    def test_cve_blocks_high(self):  # ACCEPT-3
        d = make_tmp()
        gate = SupplyChainGate(d, cve_db={
            "badpkg": [{"cve": "CVE-2026-9999", "severity": "high", "fix": ">=2.0"}],
        })
        gate.register("badpkg", "1.0.0", "pypi", "MIT",
                      owner_approved=True, security_reviewed=True)
        r = gate.gate_load("badpkg", "1.0.0", license="MIT")
        self.assertFalse(r["allowed"])
        self.assertTrue(any("CVE" in e for e in r["errors"]))
        # 无漏洞依赖可加载
        gate.register("okpkg", "1.0.0", "pypi", "MIT",
                      owner_approved=True, security_reviewed=True)
        self.assertTrue(gate.gate_load("okpkg", "1.0.0", license="MIT")["allowed"])

    def test_third_party_approval_trail(self):  # ACCEPT-4
        d = make_tmp()
        gate = SupplyChainGate(d)
        gate.register("plugin-x", "1.0.0", "github", "MIT")
        # 未批准未审查 → 拒绝
        r1 = gate.gate_load("plugin-x", "1.0.0")
        self.assertFalse(r1["allowed"])
        # Owner 批准 + 独立安全审查留痕 → 通过
        gate.approve_owner("plugin-x", True)
        gate.security_review("plugin-x", True)
        self.assertTrue(gate.gate_load("plugin-x", "1.0.0")["allowed"])
        rec = gate._registry["plugin-x"]
        self.assertTrue(rec.approved_at)
        self.assertTrue(rec.reviewed_at)

    def test_vendor_lock(self):  # ACCEPT-5
        d = make_tmp()
        gate = SupplyChainGate(d)
        gate.register("mylib", "1.2.0", "vendor", "MIT",
                      owner_approved=True, security_reviewed=True)
        src = d / "mylib-1.2.0.whl"
        src.write_bytes(b"PK-DEMO")
        dest = gate.vendor_lock("mylib", src)
        self.assertTrue(dest.exists())
        self.assertIn("mylib-1.2.0", dest.name)
        # 版本锁定后，不同版本未登记 → 拒绝
        self.assertFalse(gate.is_registered("mylib", "9.9.9"))

    def test_registry_persist(self):
        d = make_tmp()
        gate = SupplyChainGate(d)
        gate.register("persist-pkg", "0.1.0", "pypi", "BSD-3-Clause",
                      owner_approved=True, security_reviewed=True)
        gate2 = SupplyChainGate(d)
        self.assertTrue(gate2.is_registered("persist-pkg", "0.1.0"))
        self.assertTrue(gate2.gate_load("persist-pkg", "0.1.0")["allowed"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
