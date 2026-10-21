from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tasks.queue_engine.state_machine import InvalidTransition, QueueState, StateMachine
from tasks.queue_engine.storage import QueueStorage


def task(task_id: str = "sample", state: str = "QUEUED", retry_count: int = 0) -> dict[str, object]:
    return {
        "task_id": task_id,
        "state": state,
        "retryCount": retry_count,
        "dependsOn": [],
        "updated_at": "2026-10-21T00:00:00+00:00",
        "terminal_reason": None,
    }


class StateMachineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.storage = QueueStorage(self.temporary.name)
        self.machine = StateMachine(self.storage)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def move(self, record: dict[str, object], target: QueueState, *, audit_passed: bool = False) -> dict[str, object]:
        updated, _ = self.machine.transition(
            record,
            target,
            actor="developer" if target is not QueueState.COMPLETED else "auditor",
            reason=f"test {target.value}",
            audit_passed=audit_passed,
        )
        return updated

    def test_all_eight_states_are_defined(self) -> None:
        self.assertEqual(
            {"QUEUED", "EXECUTING", "SELF-CHECK", "AUDIT", "COMPLETED", "FAILED", "BLOCKED", "CANCELLED"},
            {state.value for state in QueueState},
        )

    def test_happy_path_requires_explicit_audit_pass(self) -> None:
        record = task()
        for state in (QueueState.EXECUTING, QueueState.SELF_CHECK, QueueState.AUDIT):
            record = self.move(record, state)
        with self.assertRaisesRegex(InvalidTransition, "explicit audit PASS"):
            self.move(record, QueueState.COMPLETED)
        record = self.move(record, QueueState.COMPLETED, audit_passed=True)
        self.assertEqual("COMPLETED", record["state"])

    def test_failed_retries_twice_then_blocks(self) -> None:
        record = task(state="FAILED")
        record, _ = self.machine.retry_or_block(record, actor="queue-engine", reason="retry one")
        self.assertEqual(("QUEUED", 1), (record["state"], record["retryCount"]))
        record["state"] = "FAILED"
        record, _ = self.machine.retry_or_block(record, actor="queue-engine", reason="retry two")
        self.assertEqual(("QUEUED", 2), (record["state"], record["retryCount"]))
        record["state"] = "FAILED"
        record, _ = self.machine.retry_or_block(record, actor="queue-engine", reason="limit reached")
        self.assertEqual(("BLOCKED", 2), (record["state"], record["retryCount"]))

    def test_retry_count_recovers_from_events_without_polluting_index_fields(self) -> None:
        record = task(state="FAILED")
        record.pop("retryCount")
        record, _ = self.machine.retry_or_block(record, actor="queue-engine", reason="retry one")
        self.assertNotIn("retryCount", record)
        record["state"] = "FAILED"
        recovered_machine = StateMachine(self.storage)
        record, _ = recovered_machine.retry_or_block(record, actor="queue-engine", reason="retry two")
        self.assertEqual("QUEUED", record["state"])
        record["state"] = "FAILED"
        recovered_again = StateMachine(self.storage)
        record, _ = recovered_again.retry_or_block(record, actor="queue-engine", reason="limit reached")
        self.assertEqual("BLOCKED", record["state"])

    def test_cancelled_is_reachable_but_executing_cannot_be_cancelled(self) -> None:
        cancelled = self.move(task(), QueueState.CANCELLED)
        self.assertEqual("CANCELLED", cancelled["state"])
        executing = self.move(task(), QueueState.EXECUTING)
        with self.assertRaisesRegex(InvalidTransition, "EXECUTING -> CANCELLED"):
            self.move(executing, QueueState.CANCELLED)

    def test_executing_cannot_jump_directly_to_completed(self) -> None:
        executing = self.move(task(), QueueState.EXECUTING)
        with self.assertRaisesRegex(InvalidTransition, "EXECUTING -> COMPLETED"):
            self.move(executing, QueueState.COMPLETED, audit_passed=True)

    def test_dependency_failure_blocks_queued_dependents_with_reason(self) -> None:
        prerequisite = task("base", "FAILED")
        dependent = task("dependent")
        dependent["dependsOn"] = ["base"]
        changes = self.machine.block_failed_dependents([prerequisite, dependent])
        self.assertEqual("BLOCKED", dependent["state"])
        self.assertEqual("依赖 base 未完成", dependent["terminal_reason"])
        self.assertEqual("dependent", changes[0][0])
        event_path = self.storage.events_dir / "dependent.jsonl"
        event = json.loads(event_path.read_text(encoding="utf-8").strip())
        self.assertEqual(("QUEUED", "BLOCKED"), (event["from"], event["to"]))

    def test_blocked_release_requires_human_or_brain(self) -> None:
        blocked = task(state="BLOCKED", retry_count=2)
        with self.assertRaisesRegex(InvalidTransition, "only by human or brain"):
            self.machine.transition(blocked, QueueState.QUEUED, actor="queue-engine", reason="automatic")
        released, _ = self.machine.transition(blocked, QueueState.QUEUED, actor="brain", reason="manual ruling")
        self.assertEqual("QUEUED", released["state"])


if __name__ == "__main__":
    unittest.main()
