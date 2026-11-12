"""s3-env-cognition 验收测试（M16 环境认知 · ACCEPT-1~5）。"""

import json
import tempfile
import unittest
from pathlib import Path

from src.brain.environment import capture_snapshot
from src.brain.environment_upgrade import (
    EnvProfileStore,
    HealthReporter,
    build_profile,
    scan_network,
    scan_processes,
)


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="env_s3_"))


class TestEnvCognition(unittest.TestCase):
    def test_five_scan_structured(self):  # ACCEPT-1
        snap = capture_snapshot()
        self.assertTrue(snap.hardware.cpu_cores >= 0)
        self.assertTrue(hasattr(snap, "disks"))
        net = scan_network()
        self.assertIsInstance(net.interfaces, list)
        procs = scan_processes(top_n=5)
        self.assertIsInstance(procs, list)
        # 五类（硬件/磁盘/应用/网络/进程）均可产出结构化结果
        profile = build_profile()
        self.assertTrue(profile.hardware)
        self.assertIsInstance(profile.disks, list)
        self.assertIsInstance(profile.apps, list)
        self.assertIsInstance(profile.network, dict)
        self.assertIsInstance(profile.processes, list)

    def test_baseline_diff_and_persist(self):  # ACCEPT-2
        d = make_tmp()
        store = EnvProfileStore(d)
        p1 = build_profile()
        store.save(p1)
        first = store.load_latest()
        self.assertIsNotNone(first)
        diff_none = store.diff(p1, None)
        self.assertFalse(diff_none["has_baseline"])
        # 二次建档：模拟应用变化后比对
        p2 = build_profile()
        store.save(p2)
        diff = store.diff(p2, store.load_latest())
        self.assertTrue(diff["has_baseline"])
        self.assertIsInstance(diff["added"], list)
        # 档案可检索（profiles 目录 + latest.json）
        self.assertTrue((d / "latest.json").exists())
        self.assertTrue(any(d.glob("profiles/profile-*.json")))

    def test_health_report(self):  # ACCEPT-3
        d = make_tmp()
        store = EnvProfileStore(d)
        p = build_profile()
        store.save(p)
        diff = store.diff(p, store.load_latest())
        rep = HealthReporter().report(p, diff)
        self.assertIn("结论", rep)
        self.assertIn("异常优先", rep)
        self.assertIn("硬件摘要", rep)
        # 异常优先：构造异常档案
        p2 = build_profile()
        p2.anomalies.append("磁盘 H: 剩余空间不足")
        rep2 = HealthReporter().report(p2, diff)
        self.assertEqual(rep2["结论"], "异常")
        self.assertTrue(any("磁盘" in x for x in rep2["异常优先"]))

    def test_existing_snapshot_not_regressed(self):  # ACCEPT-4
        # 既有 capture_snapshot/snapshot_to_file 行为不倒退
        snap = capture_snapshot()
        self.assertEqual(snap.version, "1.0.0")
        d = make_tmp()
        from src.brain.environment import snapshot_to_file
        path = snapshot_to_file(snap, str(d / "snap.json"))
        self.assertTrue(Path(path).exists())
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
        self.assertEqual(loaded["version"], "1.0.0")


if __name__ == "__main__":
    unittest.main(verbosity=2)
