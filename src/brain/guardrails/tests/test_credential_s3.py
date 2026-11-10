"""s3-credential-bus 验收测试（M20 凭证中心接总线）。

覆盖：
- ACCEPT-1：插件经闸门后凭证注入正常，keyId 引用、明文不出本地
- ACCEPT-2：用完不落盘；日志/回执脱敏（无明文）
- ACCEPT-3：三类凭证（大模型 key/渠道 token/设备凭证）可注册可引用
- ACCEPT-4：既有凭证中心测试集回归全绿（由独立 24/24 套件保持，本文件不破坏）

运行：tools\\venv-openjarvis\\Scripts\\python.exe -X utf8 src\\brain\\guardrails\\tests\\test_credential_s3.py
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]  # H:\UltimaAI\UltimaAgent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
_PKG = ROOT / "execution" / "packages" / "credential" / "ultima.credential.center" / "0.1.0"
if str(_PKG) not in sys.path:
    sys.path.insert(0, str(_PKG))
TEST_ROOT = ROOT / "data" / "test-tmp" / "cred-s3"
TEST_ROOT.mkdir(parents=True, exist_ok=True)

from src.brain.guardrails.credentials import CredentialCenter, CredentialError, redact  # noqa: E402


def _fresh_plugin():
    """独立临时库 + 独立审计路径的插件实例（不污染真实凭证库/审计）。"""
    store = TEST_ROOT / f"store-{id(object())}.json"
    audit = TEST_ROOT / f"audit-{id(object())}.jsonl"
    if store.exists():
        store.unlink()
    if audit.exists():
        audit.unlink()
    from ultima_credential_center_v0_1_0.main import create_plugin
    p = create_plugin()
    p._center = CredentialCenter(store_path=store)
    p._audit_path = str(audit)
    p.load()
    return p, store, audit


class TestCredentialPluginRegister(unittest.TestCase):
    def test_register_three_namespaces(self):
        p, _, _ = _fresh_plugin()
        for key_id, value in (
            ("model:qwen3-8b-uncensored", "sk-ultima-llm-0001"),
            ("channel:feishu", "tok-ultima-channel-0002"),
            ("device:pc-01", "dev-ultima-cred-0003"),
        ):
            r = p.credential_register(key_id, value)
            self.assertTrue(r["ok"])
            self.assertEqual(r["key_id"], key_id)
            self.assertNotIn(value, json.dumps(r))  # 回执不含明文

    def test_register_empty_rejected(self):
        p, _, _ = _fresh_plugin()
        with self.assertRaises(CredentialError):
            p.credential_register("model:x", "   ")

    def test_reregister_keeps_standby(self):
        p, _, _ = _fresh_plugin()
        p.credential_register("model:q", "value-A")
        p.credential_register("model:q", "value-B")
        st = p.credential_status("model:q")
        self.assertTrue(st["active"])
        self.assertTrue(st["standby"])  # 旧主降级备用，四层凭证层保留


class TestCredentialPluginStatus(unittest.TestCase):
    def test_status_no_plaintext(self):
        p, _, _ = _fresh_plugin()
        p.credential_register("model:q", "sk-secret-value-xyz")
        st = p.credential_status("model:q")
        payload = json.dumps(st)
        self.assertNotIn("sk-secret-value-xyz", payload)
        self.assertEqual(st["state"], "active")

    def test_status_missing(self):
        p, _, _ = _fresh_plugin()
        st = p.credential_status("model:never-registered")
        self.assertEqual(st["state"], "missing")
        self.assertFalse(st["ok"])

    def test_list_no_plaintext(self):
        p, _, _ = _fresh_plugin()
        p.credential_register("device:pc", "dev-secret-0009")
        p.credential_register("channel:tg", "tok-secret-0010")
        lst = p.credential_list()
        self.assertEqual(lst["count"], 2)
        payload = json.dumps(lst)
        self.assertNotIn("dev-secret-0009", payload)
        self.assertNotIn("tok-secret-0010", payload)


class TestCredentialPluginInject(unittest.TestCase):
    def test_inject_plaintext_memory_only(self):
        p, _, _ = _fresh_plugin()
        p.credential_register("model:q", "sk-ultima-inject-042")
        r = p.credential_inject("model:q")
        self.assertTrue(r["ok"])
        self.assertEqual(r["value"], "sk-ultima-inject-042")  # 服务器能力层明文（仅内存）
        self.assertTrue(r["memory_only"])

    def test_inject_unregistered_fails(self):
        p, _, _ = _fresh_plugin()
        r = p.credential_inject("model:nope")
        self.assertFalse(r["ok"])


class TestCredentialSecurity(unittest.TestCase):
    def test_store_on_disk_no_plaintext(self):
        p, store, _ = _fresh_plugin()
        secret = "sk-plaintext-must-never-persist-987"
        p.credential_register("model:q", secret)
        raw = store.read_text(encoding="utf-8")
        self.assertNotIn(secret, raw)  # DPAPI 密文

    def test_audit_no_plaintext(self):
        p, _, audit = _fresh_plugin()
        secret = "sk-audit-must-not-leak-111"
        p.credential_register("model:q", secret)
        p.credential_inject("model:q")
        p.credential_rotate("model:q", "sk-new-rotated-222")
        audit_text = audit.read_text(encoding="utf-8")
        self.assertNotIn(secret, audit_text)
        self.assertNotIn("sk-new-rotated-222", audit_text)

    def test_register_receipt_redacted(self):
        p, _, _ = _fresh_plugin()
        secret = "sk-receipt-redact-333"
        r = p.credential_register("model:q", secret)
        payload = json.dumps(r)
        self.assertNotIn(secret, payload)
        self.assertIn("***", payload)  # 脱敏形


class TestCredentialBus(unittest.TestCase):
    def setUp(self):
        from execution.server.ultima_bus.kernel import BusKernel

        self.kernel = BusKernel(package_root=ROOT / "execution" / "packages")
        self.kernel.discover()
        self.kernel.load("ultima.guard.policy")
        self.kernel.load("ultima.paradigm.flow")
        self.kernel.load("ultima.credential.center")
        # 总线实例注入独立临时凭证库，避免污染真实单例库
        from src.brain.guardrails.credentials import CredentialCenter

        inst = self.kernel._get_instance("ultima.credential.center", "0.1.0")
        inst._center = CredentialCenter(store_path=TEST_ROOT / f"bus-store-{id(self)}.json")
        inst._audit_path = str(TEST_ROOT / f"bus-audit-{id(self)}.jsonl")

    def tearDown(self):
        self.kernel.close()

    def test_bus_discover_and_routing(self):
        r = self.kernel.registry.records["ultima.credential.center"]
        self.assertEqual(r["versions"]["0.1.0"]["state"], "routing")

    def test_bus_status_call(self):
        self.kernel.call("credential.register", "model:bus", "sk-bus-secret-01")
        out = self.kernel.call("credential.status", "model:bus")
        self.assertTrue(out["ok"])
        self.assertEqual(out["data"]["state"], "active")
        self.assertNotIn("sk-bus-secret-01", json.dumps(out))

    def test_bus_list_call(self):
        self.kernel.call("credential.register", "device:bus", "dev-bus-secret-02")
        out = self.kernel.call("credential.list")
        self.assertTrue(out["ok"])
        self.assertNotIn("dev-bus-secret-02", json.dumps(out))

    def test_bus_inject_call(self):
        self.kernel.call("credential.register", "model:bus", "sk-bus-inject-03")
        out = self.kernel.call("credential.inject", "model:bus")
        self.assertTrue(out["ok"])
        self.assertEqual(out["data"]["value"], "sk-bus-inject-03")  # 能力层注入（同进程内存）

    def test_bus_unauthorized_caller_denied(self):
        # 调用方（memory.lite）未声明 cap:credential.inject → 授权拒绝
        out = self.kernel.call("credential.inject", "model:bus", caller_module_id="ultima.memory.lite")
        self.assertFalse(out["ok"])
        self.assertIn("undeclared capability scope", out.get("error", {}).get("message", ""))

    def test_bus_resident_unload_denied(self):
        # L8 域驻留：unload 被拒（与 guard 同域硬约束，PermissionDenied）
        from execution.server.ultima_bus.errors import PermissionDenied

        with self.assertRaises(PermissionDenied) as ctx:
            self.kernel.unload("ultima.credential.center")
        self.assertIn("resident plugin cannot be unloaded", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
