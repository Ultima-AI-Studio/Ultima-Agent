from __future__ import annotations

import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tasks.queue_engine.dispatcher import (
    DispatchLock,
    Dispatcher,
    guardian_parent_lost,
    spawn_hidden,
    visible_window_handles,
)
from tasks.queue_engine.storage import QueueStorage


def record(task_id: str, *, state: str = "QUEUED", group: str | None = None) -> dict[str, object]:
    return {
        "task_id": task_id,
        "state": state,
        "priority": 50,
        "dependsOn": [],
        "parallelGroup": group,
        "fileDomain": [str(PROJECT_ROOT / "tasks")],
        "reasoningEffort": "high",
        "created_at": "2026-10-21T00:00:00+00:00",
        "updated_at": "2026-10-21T00:00:00+00:00",
        "terminal_reason": None,
        "card_path": f"cards/{task_id}/task.md",
    }


class DispatcherTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.storage = QueueStorage(self.root)
        self.storage.ensure_layout()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def save(self, *records: dict[str, object]) -> None:
        self.storage.save_tasks(records)

    def harmless_command(self, delay: float = 0.05) -> list[str]:
        return [sys.executable, "-c", f"import time; time.sleep({delay})"]

    def test_default_serial_gate_leaves_candidate_queued_and_records_reason(self) -> None:
        self.save(record("running", state="EXECUTING"), record("candidate"))
        decision = Dispatcher(self.storage).dispatch("candidate", self.harmless_command())
        self.assertFalse(decision.dispatched)
        self.assertIn("串行闸门", decision.reason)
        self.assertEqual("QUEUED", self.storage.load_tasks()[1]["state"])

    def test_parallel_group_allows_second_but_never_third_execution(self) -> None:
        self.save(record("one", state="EXECUTING", group="g"), record("two", group="g"))
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch("two", self.harmless_command())
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        self.assertEqual(0, handle.wait(timeout=5))

        self.save(record("one", state="EXECUTING", group="g"), record("two", state="EXECUTING", group="g"), record("three", group="g"))
        denied = Dispatcher(self.storage).dispatch("three", self.harmless_command())
        self.assertFalse(denied.dispatched)
        self.assertIn("已达 2", denied.reason)

    def test_each_idempotency_probe_blocks_and_probe_error_fails_closed(self) -> None:
        scenarios = (
            ({"process_probe": lambda _: True}, "派发进程在跑"),
            ({"session_probe": lambda _: True}, "执行会话在跑"),
            ({"active_run_probe": lambda _: True}, "存在活跃 run"),
        )
        for probes, reason in scenarios:
            with self.subTest(reason=reason):
                self.save(record("candidate"))
                decision = Dispatcher(self.storage, **probes).dispatch("candidate", self.harmless_command())
                self.assertFalse(decision.dispatched)
                self.assertIn(reason, decision.reason)
        self.save(record("candidate"))
        failed_probe = Dispatcher(
            self.storage, process_probe=lambda _: (_ for _ in ()).throw(OSError("probe unavailable"))
        ).dispatch("candidate", self.harmless_command())
        self.assertFalse(failed_probe.dispatched)
        self.assertIn("探测失败，按忙处理", failed_probe.reason)

    def test_pause_marker_prevents_dispatch(self) -> None:
        self.save(record("candidate"))
        (self.root / ".pause-dispatch").touch()
        decision = Dispatcher(self.storage).dispatch("candidate", self.harmless_command())
        self.assertFalse(decision.dispatched)
        self.assertIn("只读审计", decision.reason)

    def test_real_duplicate_dispatch_creates_only_one_run(self) -> None:
        self.save(record("candidate"))
        first_dispatcher = Dispatcher(self.storage)
        first = first_dispatcher.dispatch("candidate", self.harmless_command(0.3))
        self.assertTrue(first.dispatched)
        duplicate = Dispatcher(self.storage).dispatch("candidate", self.harmless_command())
        self.assertFalse(duplicate.dispatched)
        self.assertIn("幂等保护", duplicate.reason)
        handle = first_dispatcher.take_process(first.pid or 0)
        self.assertEqual(0, handle.wait(timeout=5))
        run_files = list((self.storage.runs_dir / "candidate").iterdir())
        self.assertEqual(6, len(run_files), "duplicate dispatch must not create another six-pack")

    @unittest.skipUnless(os.name == "nt", "Windows lock and visible-window integration")
    def test_real_lock_contention_is_fail_closed_and_holder_has_no_window(self) -> None:
        self.save(record("candidate"))
        ready = self.root / "lock-ready"
        code = (
            "import sys,time;from pathlib import Path;"
            f"sys.path.insert(0,{str(PROJECT_ROOT)!r});"
            "from tasks.queue_engine.dispatcher import DispatchLock;"
            f"lock=DispatchLock(Path({str(self.root / '.dispatch.lock')!r}));"
            "assert lock.acquire();"
            f"Path({str(ready)!r}).write_text('ready');"
            "time.sleep(1);lock.release()"
        )
        holder = spawn_hidden([sys.executable, "-c", code], cwd=self.root)
        deadline = time.monotonic() + 5
        observed_windows: set[int] = set()
        while not ready.exists() and time.monotonic() < deadline:
            observed_windows.update(visible_window_handles(holder.pid))
            time.sleep(0.01)
        self.assertTrue(ready.exists(), "lock holder failed to signal readiness")
        decision = Dispatcher(self.storage).dispatch("candidate", self.harmless_command())
        observed_windows.update(visible_window_handles(holder.pid))
        self.assertFalse(decision.dispatched)
        self.assertIn("锁竞争", decision.reason)
        self.assertEqual(set(), observed_windows)
        self.assertEqual(0, holder.wait(timeout=5))

    @unittest.skipUnless(os.name == "nt", "Windows no-window integration")
    def test_actual_dispatched_child_has_zero_visible_windows(self) -> None:
        self.save(record("candidate"))
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch("candidate", self.harmless_command(0.4))
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        observed_windows: set[int] = set()
        while handle.process.poll() is None:
            observed_windows.update(visible_window_handles(handle.process.pid))
            time.sleep(0.01)
        self.assertEqual(0, handle.wait(timeout=5))
        self.assertEqual(set(), observed_windows)
        session = json.loads((decision.run_paths or {})["session"].read_text(encoding="utf-8"))
        self.assertEqual(handle.process.pid, session["pid"])

    def test_guardian_marks_parent_loss_and_requests_graceful_exit(self) -> None:
        marker = self.root / "parent-lost.json"
        self.assertTrue(guardian_parent_lost(2_147_483_647, marker))
        payload = json.loads(marker.read_text(encoding="utf-8"))
        self.assertEqual(("read-only", "graceful-exit"), (payload["mode"], payload["action"]))


if __name__ == "__main__":
    unittest.main()
