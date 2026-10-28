"""T2 更新 UI 服务桥测试（RU-08 呈现层：状态/触发/页面端点，零弹窗）。"""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from update.channel import UpdateChannel, UpdateInfo  # noqa: E402
from update.triggers import UpdateTriggerEngine, AVAILABLE  # noqa: E402
from update.ui_server import UpdateUiServer, DEFAULT_PORT  # noqa: E402

SRC_UPDATE = ROOT / "src" / "update"
PUBLIC_KEY = SRC_UPDATE / "public_key.pem"


class _FakeChannel(UpdateChannel):
    def __init__(self, result: UpdateInfo | None = None):
        object.__setattr__(self, "public_key_path", PUBLIC_KEY)
        self._result = result

    def check_for_update(self, current_version, *, force_fetch=False):
        return self._result

    def apply_update(self, info, *, target_path, current_version, launcher_args=None):
        from update.channel import UpdateResult

        return UpdateResult(
            checked=True, updated=True, old_version=current_version,
            new_version=info.version,
        )


def _make_info(version="1.0.1", force=False):
    return UpdateInfo(
        version=version,
        package_filename="UltimaAgent-Setup-1.0.1.exe",
        package_sha256="0" * 64,
        force_update=force,
        release_url="https://example.invalid/downloads/pkg.exe",
        published_at="2026-10-28T00:00:00Z",
    )


class TestUpdateUiServer(unittest.TestCase):
    def setUp(self):
        self.td = tempfile.TemporaryDirectory()
        self.root = Path(self.td.name)
        ui_dir = ROOT / "src" / "ui"
        ch = _FakeChannel(result=_make_info("1.0.1"))
        state_file = self.root / "update-state.json"
        self.engine = UpdateTriggerEngine(
            ch,
            current_version_provider=lambda: "1.0.0",
            target_path=self.root / "app.exe",
            state_file=state_file,
        )
        self.server = UpdateUiServer(self.engine, ui_dir, port=0)  # 系统自动分配
        self.base = self.server.start()

    def tearDown(self):
        self.server.stop()
        self.td.cleanup()

    def _get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=5) as resp:
            return resp.status, resp.read()

    def _post(self, path):
        req = urllib.request.Request(self.base + path, method="POST")
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status, resp.read()

    def test_page_served(self):
        status, body = self._get("/")
        self.assertEqual(status, 200)
        self.assertIn(b"UltimaAgent", body)

    def test_state_endpoint(self):
        status, body = self._get("/update-state.json")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertIn("status", data)

    def test_check_endpoint_marks_available(self):
        status, body = self._post("/update/check")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertEqual(data["status"], "no_update")  # 手动检查返回 None
        # 引擎状态已更新
        self.assertEqual(self.engine.state.status, AVAILABLE)
        self.assertEqual(self.engine.state.target_version, "1.0.1")

    def test_apply_endpoint_returns_updated(self):
        status, body = self._post("/update/apply")
        self.assertEqual(status, 200)
        data = json.loads(body)
        self.assertTrue(data["updated"])
        self.assertEqual(data["new_version"], "1.0.1")


if __name__ == "__main__":
    unittest.main(verbosity=2)
