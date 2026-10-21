from __future__ import annotations

import hashlib
import json
import sys
import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.queue_source import QUEUE_STATES, read_queue_status
from tasks.queue_engine import QueuePlanner, QueueState, QueueStorage, StateMachine


def record(task_id: str) -> dict[str, object]:
    stamp = "2026-10-21T00:00:00+00:00"
    return {
        "task_id": task_id,
        "state": "QUEUED",
        "priority": 50,
        "dependsOn": [],
        "parallelGroup": None,
        "fileDomain": [str(PROJECT_ROOT / "src" / "brain")],
        "reasoningEffort": "high",
        "created_at": stamp,
        "updated_at": stamp,
        "terminal_reason": None,
        "card_path": f"cards/{task_id}/task.md",
    }


def write_card(storage: QueueStorage, task_id: str) -> None:
    path = storage.cards_dir / task_id / "task.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"# 任务卡\n\n- **标题**：任务 {task_id}\n", encoding="utf-8")


def transition_to(storage: QueueStorage, task_id: str, target: QueueState) -> None:
    tasks = storage.load_tasks()
    index = next(number for number, item in enumerate(tasks) if item["task_id"] == task_id)
    current = tasks[index]
    machine = StateMachine(storage)
    if target is QueueState.QUEUED:
        return
    if target is QueueState.BLOCKED:
        current, _ = machine.block_for_unclear_audit(
            current, actor="auditor", reason="验收证据不明确"
        )
    elif target is QueueState.CANCELLED:
        current, _ = machine.transition(
            current, target, actor="human", reason="用户取消"
        )
    else:
        path = [QueueState.EXECUTING]
        if target not in {QueueState.EXECUTING, QueueState.FAILED}:
            path.append(QueueState.SELF_CHECK)
        if target in {QueueState.AUDIT, QueueState.COMPLETED}:
            path.append(QueueState.AUDIT)
        if target is QueueState.COMPLETED:
            path.append(QueueState.COMPLETED)
        if target is QueueState.FAILED:
            path.append(QueueState.FAILED)
        for step in path:
            current, _ = machine.transition(
                current,
                step,
                actor="auditor" if step is QueueState.COMPLETED else "developer",
                reason=f"迁移到 {step.value}",
                audit_passed=step is QueueState.COMPLETED,
            )
    tasks[index] = current
    storage.save_tasks(tasks)


def tree_signature(root: Path) -> list[str]:
    return sorted(
        path.relative_to(root).as_posix() + (
            "/"
            if path.is_dir()
            else ":" + hashlib.sha256(path.read_bytes()).hexdigest()
        )
        for path in root.rglob("*")
    )


class QueueSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.storage = QueueStorage(self.root)
        self.storage.ensure_layout()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def add(self, task_id: str, target: QueueState) -> None:
        write_card(self.storage, task_id)
        QueuePlanner(self.storage).enqueue(record(task_id))
        transition_to(self.storage, task_id, target)

    def test_real_storage_reports_all_eight_current_states_and_fields(self) -> None:
        for state in QueueState:
            self.add(f"state-{state.value.lower()}", state)
        snapshot = read_queue_status(
            self.root, now=datetime(2026, 10, 21, 0, 1, tzinfo=UTC)
        )
        self.assertTrue(snapshot.ok)
        self.assertEqual(tuple(state.value for state in QueueState), QUEUE_STATES)
        self.assertEqual(8, snapshot.total)
        self.assertEqual({state: 1 for state in QUEUE_STATES}, snapshot.counts)
        self.assertEqual(2, len(snapshot.anomalies))
        print(
            "QUEUE_COUNTS "
            + json.dumps(snapshot.counts, ensure_ascii=False, sort_keys=True)
        )
        self.assertEqual({"FAILED", "BLOCKED"}, {item.state for item in snapshot.anomalies})
        self.assertNotIn("CANCELLED", {item.state for item in snapshot.anomalies})
        for item in snapshot.tasks:
            self.assertTrue(item.task_id)
            self.assertTrue(item.title_zh)
            self.assertIn(item.state, QUEUE_STATES)
            self.assertEqual(50, item.priority)
            self.assertRegex(item.duration, r"^\d{2}:\d{2}:\d{2}$")

    def test_historical_failure_does_not_remain_a_current_anomaly(self) -> None:
        self.add("recovered", QueueState.FAILED)
        tasks = self.storage.load_tasks()
        recovered, _ = StateMachine(self.storage).transition(
            tasks[0], QueueState.QUEUED, actor="queue-engine", reason="修复后重试"
        )
        tasks[0] = recovered
        self.storage.save_tasks(tasks)
        transition_to(self.storage, "recovered", QueueState.COMPLETED)
        event_text = (self.storage.events_dir / "recovered.jsonl").read_text(encoding="utf-8")
        self.assertIn('"to":"FAILED"', event_text)

        snapshot = read_queue_status(self.root)
        self.assertEqual("COMPLETED", snapshot.tasks[0].state)
        self.assertEqual([], list(snapshot.anomalies))

    def test_empty_production_library_is_reported_without_mutation(self) -> None:
        production = PROJECT_ROOT / "tasks"
        before = hashlib.sha256((production / "tasks.json").read_bytes()).hexdigest()
        snapshot = read_queue_status(production)
        after = hashlib.sha256((production / "tasks.json").read_bytes()).hexdigest()
        self.assertTrue(snapshot.ok)
        self.assertEqual(0, snapshot.total)
        self.assertEqual(before, after)

    def test_missing_corrupt_and_illegal_storage_fail_closed(self) -> None:
        missing_root = self.root / "missing"
        missing_root.mkdir()
        missing = read_queue_status(missing_root)
        self.assertFalse(missing.ok)
        self.assertEqual("状态读取失败", missing.status)
        self.assertFalse((missing_root / "tasks.json").exists())

        self.storage.index_path.write_text("{broken", encoding="utf-8")
        corrupt = read_queue_status(self.root)
        self.assertFalse(corrupt.ok)
        self.assertEqual("状态读取失败", corrupt.status)
        self.assertIsNone(corrupt.total)

        invalid = record("invalid-state")
        invalid["state"] = "UNKNOWN"
        self.storage.index_path.write_text(
            json.dumps([invalid], ensure_ascii=False), encoding="utf-8"
        )
        illegal = read_queue_status(self.root)
        self.assertFalse(illegal.ok)
        self.assertEqual("状态读取失败", illegal.status)

    def test_incomplete_library_read_preserves_tree_and_bytes(self) -> None:
        scenarios = (("empty", "[]", True), ("corrupt", "{broken", False))
        for label, payload, expected_ok in scenarios:
            with self.subTest(label=label):
                library = self.root / f"incomplete-{label}"
                library.mkdir()
                (library / "tasks.json").write_text(payload, encoding="utf-8")
                before = tree_signature(library)
                result = read_queue_status(library)
                after = tree_signature(library)
                print(
                    "READONLY_TREE "
                    + json.dumps(
                        {"label": label, "before": before, "after": after},
                        ensure_ascii=False,
                    )
                )
                self.assertEqual(expected_ok, result.ok)
                self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
