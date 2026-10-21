from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from tasks.queue_engine.dispatcher import Dispatcher
from tasks.queue_engine.dispatcher import spawn_hidden
from tasks.queue_engine.priority_deps import DependencyCycle, QueuePlanner, QueuePlanningError
from tasks.queue_engine.storage import QueueStorage


def record(
    task_id: str,
    *,
    state: str = "QUEUED",
    priority: int = 50,
    created: str = "2026-10-21T00:00:00+00:00",
    depends: list[str] | None = None,
) -> dict[str, object]:
    return {
        "task_id": task_id,
        "state": state,
        "priority": priority,
        "dependsOn": depends or [],
        "parallelGroup": None,
        "fileDomain": [str(PROJECT_ROOT / "tasks")],
        "reasoningEffort": "medium",
        "created_at": created,
        "updated_at": created,
        "terminal_reason": None,
        "card_path": f"cards/{task_id}/task.md",
    }


class PriorityDependencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.storage = QueueStorage(self.temporary.name)
        self.storage.ensure_layout()
        self.planner = QueuePlanner(self.storage)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_priority_descending_and_same_priority_fifo(self) -> None:
        tasks = [
            record("normal-old", created="2026-10-21T00:00:00+00:00"),
            record("urgent", priority=100, created="2026-10-21T00:00:02+00:00"),
            record("normal-new", created="2026-10-21T00:00:01+00:00"),
        ]
        self.assertEqual(
            ["urgent", "normal-old", "normal-new"],
            [task["task_id"] for task in self.planner.ordered_tasks(tasks)],
        )

    def test_requeue_before_persists_order_and_audit_event(self) -> None:
        self.storage.save_tasks([record("first"), record("second"), record("third")])
        self.planner.requeue_before("third", "first", actor="human", reason="owner expedite")
        self.assertEqual(
            ["third", "first", "second"],
            [task["task_id"] for task in self.planner.ordered_tasks()],
        )
        event = json.loads((self.storage.events_dir / "third.jsonl").read_text(encoding="utf-8"))
        self.assertEqual({"ts", "from", "to", "reason", "actor"}, set(event))
        self.assertIn("插队到 first 之前", event["reason"])

    def test_requeue_before_cli_runs_as_actual_hidden_process(self) -> None:
        self.storage.save_tasks([record("first"), record("second"), record("third")])
        process = spawn_hidden(
            [
                sys.executable,
                str(PROJECT_ROOT / "tasks" / "queue_engine" / "cli.py"),
                "--root",
                str(self.storage.root),
                "requeue",
                "third",
                "--before",
                "first",
                "--reason",
                "cli integration",
            ],
            cwd=PROJECT_ROOT,
        )
        self.assertEqual(0, process.wait(timeout=5))
        self.assertEqual(
            ["third", "first", "second"],
            [task["task_id"] for task in self.planner.ordered_tasks()],
        )

    def test_adjustment_rejects_executing_and_validates_range(self) -> None:
        self.storage.save_tasks([record("running", state="EXECUTING")])
        with self.assertRaisesRegex(QueuePlanningError, "only QUEUED"):
            self.planner.adjust_priority("running", 90, actor="human", reason="must not interrupt")
        with self.assertRaisesRegex(QueuePlanningError, "0 to 100"):
            self.planner.adjust_priority("running", 101, actor="human", reason="invalid")

    def test_enqueue_rejects_three_node_cycle_and_reports_full_path(self) -> None:
        existing = [record("A", depends=["B"]), record("B", depends=["C"])]
        self.storage.save_tasks(existing)
        with self.assertRaises(DependencyCycle) as captured:
            self.planner.enqueue(record("C", depends=["A"]))
        self.assertEqual(["A", "B", "C", "A"], captured.exception.path)
        self.assertEqual(2, len(self.storage.load_tasks()), "cycle must be rejected before persistence")

    def test_dispatch_waits_for_dependency_and_blocks_on_failed_dependency(self) -> None:
        command = [sys.executable, "-c", "raise SystemExit(0)"]
        self.storage.save_tasks([record("base", state="EXECUTING"), record("dependent", depends=["base"])])
        waiting = Dispatcher(self.storage).dispatch("dependent", command)
        self.assertFalse(waiting.dispatched)
        self.assertIn("等待依赖 base", waiting.reason)
        self.assertEqual("QUEUED", self.storage.load_tasks()[1]["state"])

        self.storage.save_tasks([record("base", state="FAILED"), record("dependent", depends=["base"])])
        blocked = Dispatcher(self.storage).dispatch("dependent", command)
        self.assertFalse(blocked.dispatched)
        self.assertIn("任务已冻结", blocked.reason)
        dependent = self.storage.load_tasks()[1]
        self.assertEqual("BLOCKED", dependent["state"])
        self.assertEqual("依赖 base 未完成", dependent["terminal_reason"])

    def test_completed_dependency_allows_real_dispatch(self) -> None:
        self.storage.save_tasks([record("base", state="COMPLETED"), record("dependent", depends=["base"])])
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch("dependent", [sys.executable, "-c", "raise SystemExit(0)"])
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        self.assertEqual(0, handle.wait(timeout=5))


if __name__ == "__main__":
    unittest.main()
