"""L3 环境认知（P1）：启动即环境快照——验收测试。"""

from __future__ import annotations

import json
import os
import tempfile
import unittest
from pathlib import Path

import sys

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain import environment as env  # noqa: E402


class EnvironmentSnapshotTest(unittest.TestCase):
    def test_version_constant(self) -> None:
        self.assertEqual(env.SNAPSHOT_VERSION, "1.0.0")

    def test_hardware_shape(self) -> None:
        hw, timed = env.scan_hardware()
        self.assertIsInstance(hw.os_name, str)
        self.assertGreaterEqual(hw.memory_total_gb, 0.0)
        self.assertIsInstance(hw.gpu, list)
        self.assertIsInstance(timed, list)

    def test_disks_contain_system_letter(self) -> None:
        disks, timed = env.scan_disks()
        letters = [d.mount for d in disks]
        self.assertTrue(any("C:" in m for m in letters), f"缺 C 盘: {letters}")
        for d in disks:
            self.assertGreater(d.total_gb, 0)

    def test_files_targets(self) -> None:
        targets = [r"H:\UltimaAI\UltimaAgent\src\brain\bootstrap.py", r"C:\nonexistent-xyz"]
        files, timed = env.scan_files(targets)
        self.assertEqual(len(files), 2)
        self.assertTrue(files[0].exists)
        self.assertFalse(files[1].exists)

    def test_apps_runs(self) -> None:
        apps, timed = env.scan_apps()
        self.assertIsInstance(apps, list)

    def test_capture_snapshot_roundtrip(self) -> None:
        snap = env.capture_snapshot(file_targets=[r"H:\UltimaAI\UltimaAgent\tasks"])
        self.assertEqual(snap.version, "1.0.0")
        self.assertTrue(snap.captured_at)
        self.assertTrue(snap.hostname)
        self.assertGreaterEqual(len(snap.disks), 1)
        # JSON 往返
        data = json.loads(snap.to_json())
        self.assertEqual(data["version"], "1.0.0")
        self.assertIn("hardware", data)

    def test_snapshot_to_file_and_load(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "snap.json")
            snap = env.capture_snapshot()
            written = env.snapshot_to_file(snap, out)
            self.assertTrue(os.path.exists(written))
            loaded = env.load_snapshot(out)
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.hostname, snap.hostname)

    def test_load_missing_returns_none(self) -> None:
        self.assertIsNone(env.load_snapshot(r"C:\definitely-missing-ultima-snap.json"))

    def test_timed_out_field_present(self) -> None:
        snap = env.capture_snapshot()
        self.assertIsInstance(snap.timed_out, list)


if __name__ == "__main__":
    unittest.main(verbosity=2)
