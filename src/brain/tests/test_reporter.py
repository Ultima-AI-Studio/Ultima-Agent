from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.reporter import respond_to_text
from tasks.queue_engine import QueuePlanner, QueueState, QueueStorage, StateMachine, spawn_hidden


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


def enqueue(storage: QueueStorage, task_id: str) -> None:
    card = storage.cards_dir / task_id / "task.md"
    card.parent.mkdir(parents=True, exist_ok=True)
    card.write_text(f"# 任务卡\n\n- **标题**：任务 {task_id}\n", encoding="utf-8")
    QueuePlanner(storage).enqueue(record(task_id))


def migrate(storage: QueueStorage, task_id: str, path: tuple[QueueState, ...]) -> None:
    tasks = storage.load_tasks()
    index = next(number for number, item in enumerate(tasks) if item["task_id"] == task_id)
    current = tasks[index]
    machine = StateMachine(storage)
    for state in path:
        current, _ = machine.transition(
            current,
            state,
            actor="auditor" if state is QueueState.COMPLETED else "developer",
            reason="场景失败" if state is QueueState.FAILED else f"场景迁移到 {state.value}",
            audit_passed=state is QueueState.COMPLETED,
        )
    tasks[index] = current
    storage.save_tasks(tasks)


class AggregateReporterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.storage = QueueStorage(self.root)
        self.storage.ensure_layout()
        for number in range(1, 20):
            task_id = f"normal-{number:02d}"
            enqueue(self.storage, task_id)
            migrate(
                self.storage,
                task_id,
                (
                    QueueState.EXECUTING,
                    QueueState.SELF_CHECK,
                    QueueState.AUDIT,
                    QueueState.COMPLETED,
                ),
            )
        enqueue(self.storage, "failed-20")
        migrate(
            self.storage,
            "failed-20",
            (QueueState.EXECUTING, QueueState.FAILED),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_twenty_tasks_one_failure_is_real_and_aggregated(self) -> None:
        response = respond_to_text("请查一下任务状态。", queue_root=self.root)
        self.assertTrue(response.handled)
        self.assertTrue(response.ok)
        print("SCENARIO_20_TASKS_1_FAILURE\n" + response.text)
        lines = response.text.splitlines()
        self.assertEqual("当前共 20 个任务，有 1 个异常。", lines[0])
        self.assertIn("失败任务 failed-20", lines[1])
        self.assertIn("原因：场景失败", lines[1])
        self.assertIn("其余 19 个任务当前无失败或冻结，已聚合省略。", lines[2])
        for number in range(1, 20):
            self.assertNotIn(f"normal-{number:02d}", response.text)

    def test_explicit_drilldown_supports_normal_and_failed_ids(self) -> None:
        normal = respond_to_text(
            "查任务状态", queue_root=self.root, detail_task_id="normal-01"
        )
        self.assertTrue(normal.ok)
        self.assertIn("normal-01", normal.text)
        self.assertIn("已完成（通过）", normal.text)

        failed = respond_to_text(
            "查任务状态", queue_root=self.root, detail_task_id="failed-20"
        )
        self.assertTrue(failed.ok)
        self.assertIn("失败", failed.text)
        self.assertIn("场景失败", failed.text)

    def test_unknown_and_path_style_ids_are_refused(self) -> None:
        unknown = respond_to_text(
            "查任务状态", queue_root=self.root, detail_task_id="does-not-exist"
        )
        self.assertFalse(unknown.ok)
        self.assertIn("未找到任务", unknown.text)

        for unsafe in (r"..\tasks.json", "../tasks.json", r"C:\secret.txt", "/etc/passwd"):
            with self.subTest(unsafe=unsafe), patch(
                "src.brain.reporter.read_queue_status",
                side_effect=AssertionError("path-style id must fail before queue read"),
            ):
                refused = respond_to_text(
                    "查任务状态", queue_root=self.root, detail_task_id=unsafe
                )
                self.assertFalse(refused.ok)
                self.assertIn("任务 ID 非法", refused.text)

    def test_unmatched_text_does_not_read_or_interrupt(self) -> None:
        with patch(
            "src.brain.reporter.read_queue_status",
            side_effect=AssertionError("unmatched text must not read the queue"),
        ):
            response = respond_to_text("你好，今天继续工作。", queue_root=self.root)
        self.assertFalse(response.handled)
        self.assertTrue(response.ok)
        self.assertEqual("", response.text)

    def test_w4_non_requests_never_read_or_interrupt(self) -> None:
        non_requests = (
            "先不查任务状态",
            "不需要查任务状态",
            "先别看任务队列",
            "我看过任务状态了",
            "任务状态我看过了",
            "我昨天看了任务状态",
            "我们讨论过查询任务状态",
            "这段日志写着查任务状态",
            "他说查任务状态",
            "查任务状态这个功能以后再做",
        )
        for text in non_requests:
            with self.subTest(text=text), patch(
                "src.brain.reporter.read_queue_status"
            ) as read_status:
                response = respond_to_text(text, queue_root=self.root)
                self.assertFalse(response.handled)
                self.assertTrue(response.ok)
                self.assertEqual("", response.text)
                read_status.assert_not_called()

    def test_storage_failure_is_not_reported_as_an_empty_queue(self) -> None:
        missing = self.root / "missing"
        missing.mkdir()
        response = respond_to_text("查任务状态", queue_root=missing)
        self.assertTrue(response.handled)
        self.assertFalse(response.ok)
        self.assertTrue(response.text.startswith("状态读取失败："))
        self.assertNotIn("0 个任务", response.text)

    def test_cli_runs_hidden_and_exits_zero_for_normal_query(self) -> None:
        process = spawn_hidden(
            [
                sys.executable,
                "-X",
                "utf8",
                str(PROJECT_ROOT / "src" / "brain" / "cli.py"),
                "--root",
                str(self.root),
                "查任务状态",
            ],
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(0, process.returncode, stderr.decode("utf-8", errors="replace"))
        self.assertIn("当前共 20 个任务，有 1 个异常。", stdout.decode("utf-8"))


if __name__ == "__main__":
    unittest.main()
