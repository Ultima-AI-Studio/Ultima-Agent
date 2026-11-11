from __future__ import annotations

import json
import re
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
        records = [prerequisite, dependent]
        changes = self.machine.block_failed_dependents(records)
        self.assertEqual("QUEUED", dependent["state"])
        self.assertEqual("BLOCKED", records[1]["state"])
        self.assertEqual("依赖 base 未完成", records[1]["terminal_reason"])
        self.assertEqual("dependent", changes[0][0])
        event_path = self.storage.events_dir / "dependent.jsonl"
        event = json.loads(event_path.read_text(encoding="utf-8").strip())
        self.assertEqual(("QUEUED", "BLOCKED"), (event["from"], event["to"]))

    def test_regular_queued_to_blocked_remains_illegal(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "illegal transition: QUEUED -> BLOCKED"):
            self.machine.transition(
                task(), QueueState.BLOCKED, actor="queue-engine", reason="no freeze gate"
            )

    def test_dependency_freeze_requires_queued_source(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "requires a QUEUED source"):
            self.machine.transition(
                task(state="FAILED"),
                QueueState.BLOCKED,
                actor="queue-engine",
                reason="wrong source",
                freeze="dependency",
            )

    def test_dependency_freeze_requires_controlled_actor(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "only by queue-engine, brain, or human"):
            self.machine.transition(
                task(),
                QueueState.BLOCKED,
                actor="developer",
                reason="wrong actor",
                freeze="dependency",
            )

    def test_freeze_gate_only_targets_blocked(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "only targets BLOCKED"):
            self.machine.transition(
                task(),
                QueueState.EXECUTING,
                actor="queue-engine",
                reason="wrong target",
                freeze="dependency",
            )

    def test_unclear_audit_freeze_requires_controlled_actor(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "only by auditor or brain"):
            self.machine.transition(
                task(),
                QueueState.BLOCKED,
                actor="developer",
                reason="wrong actor",
                freeze="unclear_audit",
            )

    def test_unclear_audit_freeze_rejects_terminal_sources(self) -> None:
        for state in ("COMPLETED", "CANCELLED"):
            with self.subTest(state=state):
                with self.assertRaisesRegex(InvalidTransition, "terminal task cannot be frozen"):
                    self.machine.transition(
                        task(state=state),
                        QueueState.BLOCKED,
                        actor="auditor",
                        reason="terminal source",
                        freeze="unclear_audit",
                    )

    def test_unknown_freeze_gate_is_rejected(self) -> None:
        with self.assertRaisesRegex(InvalidTransition, "unknown freeze gate"):
            self.machine.transition(
                task(),
                QueueState.BLOCKED,
                actor="queue-engine",
                reason="unknown gate",
                freeze="other",
            )

    def test_state_changes_have_single_formal_write_path(self) -> None:
        queue_engine = Path(__file__).resolve().parents[1] / "queue_engine"
        assignment = re.compile(r"\[\s*(?:\"state\"|'state')\s*\]\s*=(?!=)")
        expected_counts = {
            "state_machine.py": 1,
            "priority_deps.py": 0,
            "auto_relay_poc.py": 0,
        }
        for filename, expected in expected_counts.items():
            with self.subTest(filename=filename):
                source = (queue_engine / filename).read_text(encoding="utf-8")
                self.assertEqual(expected, len(assignment.findall(source)))

    def test_blocked_release_requires_human_or_brain(self) -> None:
        blocked = task(state="BLOCKED", retry_count=2)
        with self.assertRaisesRegex(InvalidTransition, "only by human or brain"):
            self.machine.transition(blocked, QueueState.QUEUED, actor="queue-engine", reason="automatic")
        released, _ = self.machine.transition(blocked, QueueState.QUEUED, actor="brain", reason="manual ruling")
        self.assertEqual("QUEUED", released["state"])


if __name__ == "__main__":
    unittest.main()
