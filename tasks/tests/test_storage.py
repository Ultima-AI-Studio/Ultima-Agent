from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tasks.queue_engine.storage import INDEX_FIELDS, RUN_PARTS, QueueStorage, StorageError


def index_record(task_id: str, state: str = "QUEUED", order: int = 0) -> dict[str, object]:
    return {
        "task_id": task_id,
        "state": state,
        "priority": 50,
        "dependsOn": [],
        "parallelGroup": None,
        "fileDomain": [r"H:\UltimaAI\UltimaAgent\tasks"],
        "reasoningEffort": "medium",
        "created_at": f"2026-10-21T00:00:0{order}+00:00",
        "updated_at": f"2026-10-21T00:00:0{order}+00:00",
        "terminal_reason": None,
        "card_path": f"cards/{task_id}/task.md",
    }


class QueueStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_layout_and_empty_index_are_created_without_goal_text(self) -> None:
        storage = QueueStorage(self.root)
        storage.ensure_layout()
        self.assertEqual([], storage.load_tasks())
        for name in ("cards", "queue", "events", "runs", "archive"):
            self.assertTrue((self.root / name).is_dir())
        self.assertNotIn("goal", (self.root / "tasks.json").read_text(encoding="utf-8"))

    def test_index_allows_only_the_eleven_contract_fields(self) -> None:
        storage = QueueStorage(self.root)
        record = index_record("sample")
        self.assertEqual(set(INDEX_FIELDS), set(record))
        storage.save_tasks([record])
        polluted = dict(record)
        polluted["goal"] = "must stay in task.md"
        with self.assertRaisesRegex(StorageError, "extra=\\['goal'\\]"):
            storage.save_tasks([polluted])

    def test_events_append_without_rewriting_history(self) -> None:
        storage = QueueStorage(self.root)
        path = storage.append_event("sample", {"seq": 1})
        first_bytes = path.read_bytes()
        storage.append_event("sample", {"seq": 2})
        combined = path.read_bytes()
        self.assertTrue(combined.startswith(first_bytes))
        self.assertEqual([{"seq": 1}, {"seq": 2}], [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()])

    def test_run_six_pack_uses_contract_names(self) -> None:
        storage = QueueStorage(self.root)
        paths = storage.create_run_artifacts("sample", timestamp="20261021T010203Z", run_id="run-1")
        self.assertEqual(set(RUN_PARTS), set(paths))
        self.assertEqual(6, len(list((self.root / "runs" / "sample").iterdir())))
        for part, path in paths.items():
            self.assertEqual(f"sample.20261021T010203Z.run-1.{part}", path.name)

    def test_threshold_archives_only_terminal_index_items_and_keeps_files(self) -> None:
        storage = QueueStorage(self.root, max_index_items=3)
        storage.ensure_layout()
        preserved_card = storage.cards_dir / "done-old" / "task.md"
        preserved_card.parent.mkdir(parents=True)
        preserved_card.write_text("historical body", encoding="utf-8")
        records = [
            index_record("done-old", "COMPLETED", 0),
            index_record("cancelled", "CANCELLED", 1),
            index_record("queued-a", "QUEUED", 2),
            index_record("queued-b", "QUEUED", 3),
        ]
        remaining = storage.save_tasks(records)
        self.assertEqual(3, len(remaining))
        self.assertNotIn("done-old", {task["task_id"] for task in remaining})
        self.assertTrue(preserved_card.exists(), "archive must never delete task bodies")
        archived = [json.loads(line) for line in (storage.archive_dir / "index-items.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual("done-old", archived[0]["task_id"])

    def test_default_threshold_triggers_only_above_ten_thousand(self) -> None:
        storage = QueueStorage(self.root)
        records = [index_record("done-old", "COMPLETED", 0)]
        records.extend(index_record(f"queued-{number}", "QUEUED", number) for number in range(10_000))
        remaining = storage.save_tasks(records)
        self.assertEqual(10_000, len(remaining))
        self.assertNotIn("done-old", {task["task_id"] for task in remaining})


if __name__ == "__main__":
    unittest.main()
