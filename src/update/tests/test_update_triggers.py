"""T2 三触发 + 更新 UI 状态机单元测试（RU-05~RU-08）。

- RU-05 启动自检：启动时查 latest，有新版按策略；无新版静默回空闲
- RU-06 手动检查：设置页按钮触发，结果进状态文件供 UI 读取
- RU-07 静默强制：force_update=true 无条件执行更新
- RU-08 状态展示：状态机 idle/checking/available/updating/updated/failed
  全部写状态文件（UI 读取），全程零弹窗（N7）
"""
from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from update.channel import UpdateChannel, UpdateInfo  # noqa: E402
from update.triggers import (  # noqa: E402
    UpdateTriggerEngine,
    IDLE,
    CHECKING,
    AVAILABLE,
    UPDATING,
    UPDATED,
    FAILED,
)

SRC_UPDATE = ROOT / "src" / "update"
PUBLIC_KEY = SRC_UPDATE / "public_key.pem"


class _FakeChannel(UpdateChannel):
    """可编程通道：注入 fake 结果，不真联网。"""

    def __init__(self, result: UpdateInfo | None = None, exc: Exception | None = None):
        object.__setattr__(self, "public_key_path", PUBLIC_KEY)
        self._result = result
        self._exc = exc
        self.check_calls = 0
        self.apply_calls = 0

    def check_for_update(self, current_version, *, force_fetch=False):
        self.check_calls += 1
        if self._exc is not None:
            raise self._exc
        return self._result

    def apply_update(self, info, *, target_path, current_version, launcher_args=None):
        self.apply_calls += 1
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


def _engine(channel, td):
    state_file = Path(td) / "update-state.json"
    return UpdateTriggerEngine(
        channel,
        current_version_provider=lambda: "1.0.0",
        target_path=Path(td) / "app.exe",
        state_file=state_file,
    ), state_file


class TestStartupCheck(unittest.TestCase):
    def test_no_new_version_silent_idle(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=None)
            eng, state_file = _engine(ch, td)
            result = eng.startup_check()
            self.assertIsNone(result)
            self.assertEqual(eng.state.status, IDLE)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], IDLE)
            self.assertIsNotNone(data["last_checked_at"])

    def test_new_version_available_marks_state(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=_make_info("1.0.1", force=False))
            eng, state_file = _engine(ch, td)
            eng.startup_check()
            self.assertEqual(eng.state.status, AVAILABLE)
            self.assertEqual(eng.state.target_version, "1.0.1")
            self.assertFalse(eng.state.force)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], AVAILABLE)

    def test_check_failure_silent_idle(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(exc=RuntimeError("no network"))
            eng, _ = _engine(ch, td)
            eng.startup_check()
            # N6：失败不误报新版，回空闲
            self.assertEqual(eng.state.status, IDLE)
            self.assertIsNone(eng.state.error)


class TestManualCheck(unittest.TestCase):
    def test_manual_check_available(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=_make_info("1.0.1"))
            eng, state_file = _engine(ch, td)
            eng.manual_check()
            self.assertEqual(eng.state.status, AVAILABLE)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["target_version"], "1.0.1")

    def test_manual_check_no_update(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=None)
            eng, state_file = _engine(ch, td)
            eng.manual_check()
            self.assertEqual(eng.state.status, IDLE)


class TestSilentForce(unittest.TestCase):
    def test_force_update_executes(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=_make_info("1.0.2", force=True))
            eng, state_file = _engine(ch, td)
            eng.startup_check()
            self.assertEqual(ch.apply_calls, 1)
            self.assertEqual(eng.state.status, UPDATED)
            self.assertEqual(eng.state.current_version, "1.0.2")
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], UPDATED)

    def test_force_update_no_new_version_no_apply(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=None)
            eng, _ = _engine(ch, td)
            eng.startup_check()
            self.assertEqual(ch.apply_calls, 0)


class TestUIState(unittest.TestCase):
    def test_state_machine_transitions(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=_make_info("1.0.1"))
            eng, _ = _engine(ch, td)
            self.assertEqual(eng.state.status, IDLE)
            eng.startup_check()
            # 非强制：checking → available
            self.assertEqual(eng.state.status, AVAILABLE)
            eng.apply(ch._result)
            self.assertEqual(eng.state.status, UPDATED)

    def test_state_file_persisted_for_ui(self):
        with tempfile.TemporaryDirectory() as td:
            ch = _FakeChannel(result=_make_info("1.0.1"))
            eng, state_file = _engine(ch, td)
            eng.startup_check()
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], AVAILABLE)
            self.assertEqual(data["current_version"], "1.0.0")
            self.assertEqual(data["target_version"], "1.0.1")

    def test_apply_failure_records_failed(self):
        from update.channel import UpdateResult

        class FailChannel(_FakeChannel):
            def apply_update(self, info, *, target_path, current_version, launcher_args=None):
                return UpdateResult(
                    checked=True, updated=False, rolled_back=True,
                    error="smoke launch failed; rolled back",
                    old_version=current_version, new_version=info.version,
                )

        with tempfile.TemporaryDirectory() as td:
            ch = FailChannel(result=_make_info("1.0.1", force=True))
            eng, state_file = _engine(ch, td)
            eng.startup_check()
            self.assertEqual(eng.state.status, FAILED)
            data = json.loads(state_file.read_text(encoding="utf-8"))
            self.assertEqual(data["status"], FAILED)


if __name__ == "__main__":
    unittest.main(verbosity=2)
