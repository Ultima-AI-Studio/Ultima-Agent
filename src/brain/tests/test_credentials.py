r"""L8 凭证中心 + 高危征询骨架 单测（B2 缺口补建验收）。

运行：tools\python31313\python.exe -X utf8 src\brain\tests\test_credentials.py
（直接导入 credentials/hazard 子模块，不经 guardrails __init__，
  避免拉入依赖 openjarvis 底座的 scanner 模块。）
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

# guardrails/__init__ 导入 scanner 依赖 openjarvis 底座，补底座 src 路径
LIBS_BASE = PROJECT_ROOT / "libs" / "base" / "openjarvis" / "src"
if str(LIBS_BASE) not in sys.path:
    sys.path.insert(0, str(LIBS_BASE))

from src.brain.guardrails.credentials import (
    CredentialCenter,
    CredentialError,
    CredentialNotFound,
    MissingSecret,
    redact,
    scrub_log_text,
)
from src.brain.guardrails.hazard import (
    HazardGate,
    HazardGateError,
)


def _make_center(tmp_root: Path) -> CredentialCenter:
    return CredentialCenter(tmp_root / "credential_store.json")


class TestDpapiRoundtrip(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        center = _make_center(Path(tempfile.mkdtemp()))
        center.set_secret("gmgn_api", "sk-ultima-test-secret-123456")
        value = center.get_secret("gmgn_api")
        self.assertEqual(value.value, "sk-ultima-test-secret-123456")
        self.assertEqual(value.layer, "active")

    def test_disk_never_plaintext(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        secret_value = "ULTIMA-SECRET-PLAINTEXT-8888"
        center.set_secret("api_a", secret_value)
        raw = (root / "credential_store.json").read_text(encoding="utf-8")
        self.assertNotIn(secret_value, raw, "磁盘不得出现凭证明文")

    def test_reload_after_new_instance(self):
        root = Path(tempfile.mkdtemp())
        c1 = _make_center(root)
        c1.set_secret("api_a", "value-1")
        c2 = _make_center(root)
        self.assertEqual(c2.get_secret("api_a").value, "value-1")

    def test_unknown_key_raises(self):
        center = _make_center(Path(tempfile.mkdtemp()))
        with self.assertRaises(CredentialNotFound):
            center.get_secret("nope")

    def test_empty_value_rejected(self):
        center = _make_center(Path(tempfile.mkdtemp()))
        with self.assertRaises(CredentialError):
            center.set_secret("api_a", "   ")


class TestLayers(unittest.TestCase):
    def test_rotate_keeps_standby(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "v1")
        center.rotate("api_a", "v2")
        status = center.status("api_a")
        self.assertTrue(status.active)
        self.assertTrue(status.standby)
        self.assertEqual(center.get_secret("api_a").value, "v2")

    def test_standby_promoted_when_active_broken(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "v1")
        center.rotate("api_a", "v2")
        # 破坏 active 密文（模拟解密失败）
        with center._lock:
            center._cache["api_a"]["active"]["enc"] = "Y2hhbmdlZA=="  # "changed"
            center._persist()
        center._plain_cache.pop("api_a", None)
        # 应自动切备用 v1
        value = center.get_secret("api_a")
        self.assertEqual(value.value, "v1")
        self.assertEqual(value.layer, "active")
        status = center.status("api_a")
        self.assertFalse(status.standby)  # 备用已提升，standby 位空

    def test_missing_when_all_broken(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "v1")
        center.rotate("api_a", "v2")
        with center._lock:
            for layer in ("active", "standby"):
                center._cache["api_a"][layer]["enc"] = "Y2hhbmdlZA=="
            center._persist()
        center._plain_cache.pop("api_a", None)
        with self.assertRaises(MissingSecret):
            center.get_secret("api_a")
        self.assertEqual(center.status("api_a").state, "missing")

    def test_derive_layer(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "main")
        center.derive("api_a", "derived-1")
        center.derive("api_a", "derived-2")
        self.assertEqual(center.status("api_a").derived, 2)
        self.assertEqual(center.get_derived("api_a").value, "derived-2")
        self.assertEqual(center.get_derived("api_a", 0).value, "derived-1")

    def test_delete(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "v1")
        self.assertTrue(center.delete("api_a"))
        self.assertFalse(center.delete("api_a"))
        self.assertEqual(center.status("api_a").state, "missing")


class TestRedactAndScrub(unittest.TestCase):
    def test_redact_short(self):
        self.assertEqual(redact("abc"), "***")

    def test_redact_long(self):
        self.assertEqual(redact("sk-ultima-1234567890"), "sk***90")

    def test_redact_empty(self):
        self.assertEqual(redact(""), "")

    def test_scrub_log_text(self):
        secrets = ["sk-super-secret-abcdef"]
        cleaned = scrub_log_text("call api with sk-super-secret-abcdef now", secrets)
        self.assertNotIn("sk-super-secret-abcdef", cleaned)
        self.assertIn("sk***ef", cleaned)


class TestAuditEvents(unittest.TestCase):
    def test_audit_no_plaintext(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "ULTIMA-SECRET-XYZ")
        center.rotate("api_a", "ULTIMA-SECRET-ABC")
        audit = (root / "credential_audit.jsonl").read_text(encoding="utf-8")
        self.assertNotIn("ULTIMA-SECRET", audit, "审计事件不得含明文凭证")

    def test_audit_events_recorded(self):
        root = Path(tempfile.mkdtemp())
        center = _make_center(root)
        center.set_secret("api_a", "v1")
        center.rotate("api_a", "v2")
        lines = (root / "credential_audit.jsonl").read_text(encoding="utf-8").strip().splitlines()
        events = [json.loads(line)["event"] for line in lines]
        self.assertIn("set", events)
        self.assertIn("rotate", events)


class TestHazardGate(unittest.TestCase):
    def setUp(self):
        self.gate = HazardGate()

    def test_register_and_request_pending(self):
        self.gate.register_operation("queue_retry", requires_auth=True)
        decision = self.gate.request("queue_retry")
        self.assertTrue(decision.is_pending)
        self.assertEqual(self.gate.current("queue_retry").status, "pending")

    def test_approve_flow(self):
        self.gate.register_operation("queue_retry")
        self.gate.request("queue_retry")
        decision = self.gate.approve("queue_retry", actor="user", reason="用户确认重试")
        self.assertTrue(decision.is_granted)
        self.assertEqual(self.gate.history()[-1]["status"], "granted")

    def test_deny_flow(self):
        self.gate.register_operation("queue_cancel")
        self.gate.request("queue_cancel")
        decision = self.gate.deny("queue_cancel", actor="user", reason="用户拒绝")
        self.assertEqual(decision.status, "denied")

    def test_requires_auth_false_auto_granted(self):
        self.gate.register_operation("status_report", requires_auth=False)
        decision = self.gate.request("status_report")
        self.assertTrue(decision.is_granted)

    def test_unregistered_raises(self):
        with self.assertRaises(HazardGateError):
            self.gate.request("nope")

    def test_required_actor_enforced(self):
        self.gate.register_operation("queue_retry", required_actor="user")
        self.gate.request("queue_retry")
        with self.assertRaises(HazardGateError):
            self.gate.approve("queue_retry", actor="brain")
        decision = self.gate.approve("queue_retry", actor="user")
        self.assertTrue(decision.is_granted)

    def test_double_approve_raises(self):
        self.gate.register_operation("queue_retry")
        self.gate.request("queue_retry")
        self.gate.approve("queue_retry", actor="user")
        with self.assertRaises(HazardGateError):
            self.gate.approve("queue_retry", actor="user")

    def test_duplicate_register_raises(self):
        self.gate.register_operation("queue_retry")
        with self.assertRaises(HazardGateError):
            self.gate.register_operation("queue_retry")


if __name__ == "__main__":
    unittest.main(verbosity=2)
