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

from tasks.queue_engine.audit import AuditEngine, RecoveryManager
from tasks.queue_engine.dispatcher import Dispatcher, visible_window_handles, process_identity
from tasks.queue_engine.priority_deps import QueuePlanner
from tasks.queue_engine.storage import QueueStorage


class AuditE2ETests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.task_root = self.root / "tasks"
        self.report_root = self.root / "logs" / "execution-reports"
        self.registry_path = self.root / "registry.md"
        self.registry_path.write_text("| `task-queue-engine` | queue |\n", encoding="utf-8")
        self.storage = QueueStorage(self.task_root)
        self.storage.ensure_layout()
        card = self.storage.cards_dir / 'e2e/task.md'
        card.parent.mkdir(parents=True)
        card.write_text('- **stage**：S1（阶段一 v0.1）\n## acceptance[]\n- [ ] ACCEPT: chain\n- [ ] ACCEPT: receipt\n', encoding='utf-8')
        (self.storage.queue_dir / 'wo-s1-queue-engine.md').write_text('T1 e2e', encoding='utf-8')
        self.audit_engine = AuditEngine(self.storage, self.report_root, self.registry_path, auditor_id='fixture-independent-auditor')

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def task(self, task_id: str = "e2e") -> dict[str, object]:
        return {
            "task_id": task_id,
            "state": "QUEUED",
            "priority": 50,
            "dependsOn": [],
            "parallelGroup": None,
            "fileDomain": [str(self.task_root), str(self.report_root)],
            "reasoningEffort": "medium",
            "created_at": "2026-10-21T00:00:00+00:00",
            "updated_at": "2026-10-21T00:00:00+00:00",
            "terminal_reason": None,
            "card_path": f"cards/{task_id}/task.md",
        }

    def receipt(self, artifact: Path) -> dict[str, object]:
        return {
            "completion": "任务已完成",
            "landed_files": [str(artifact)],
            "reviewReason": "逐项自核完成",
            "stdoutText": "BUSINESS_OK",
            "evidence": [str(artifact)],
            "acceptance": {"chain": True, "receipt": True},
        }

    def summary(self, task_id: str = "e2e", **overrides: object) -> dict[str, object]:
        value: dict[str, object] = {
            "version": "S1/v0.1",
            "work_order": "wo-s1-queue-engine",
            "task_id": task_id,
            "business_success": True,
            "exit_code": 0,
            "receipt_present": True,
            "developer_skill": "eng.code",
            "auditor_skill": "eng.audit",
            "file_domain_ok": True,
            "registry_entry": "task-queue-engine",
            'developer_id': f'process:{os.getpid()}:{process_identity(os.getpid())}',
            'auditor_id': 'fixture-independent-auditor',
        }
        value.update(overrides)
        return value

    def put_in_audit(self, task_id: str = "e2e") -> dict[str, object]:
        task = self.task(task_id)
        task["state"] = "AUDIT"
        self.storage.save_tasks([task])
        return task

    def test_no_receipt_is_blocked_and_never_completed(self) -> None:
        task = self.put_in_audit()
        result = self.audit_engine.audit(task, None, self.summary(receipt_present=False), auditor_skill="eng.audit")
        self.assertEqual("BLOCKED", result.verdict)
        closed = self.audit_engine.close("e2e", result)
        self.assertEqual("BLOCKED", closed["state"])

    def test_same_developer_and_auditor_skill_is_blocked(self) -> None:
        task = self.put_in_audit()
        artifact = self.task_root / "artifact.txt"
        artifact.write_text("ok", encoding="utf-8")
        result = self.audit_engine.audit(
            task,
            self.receipt(artifact),
            self.summary(developer_skill="eng.audit"),
            auditor_skill="eng.audit",
        )
        self.assertEqual("BLOCKED", result.verdict)
        self.assertIn("开发与审计技能未分离", result.reasons)

    def test_exit_zero_with_business_failure_generates_revision_and_fails_task(self) -> None:
        task = self.put_in_audit()
        artifact = self.task_root / "artifact.txt"
        artifact.write_text("not actually successful", encoding="utf-8")
        result = self.audit_engine.audit(
            task,
            self.receipt(artifact),
            self.summary(exit_code=0, business_success=False),
            auditor_skill="eng.audit",
        )
        self.assertEqual("REVISE", result.verdict)
        self.assertIsNotNone(result.correction_task)
        closed = self.audit_engine.close("e2e", result)
        self.assertEqual("FAILED", closed["state"])

    def test_real_exit_zero_with_business_failure_fails_self_check(self) -> None:
        QueuePlanner(self.storage).enqueue(self.task("business-fail"))
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch(
            "business-fail",
            [sys.executable, "-c", "import json;print(json.dumps({'business_success':False}));raise SystemExit(0)"],
        )
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        self.assertEqual(0, handle.wait(timeout=5))
        recovery = RecoveryManager(self.storage)
        recovered, _ = recovery.recover_finished_run("business-fail")
        self.assertEqual("SELF-CHECK", recovered["state"])
        checked = recovery.finish_self_check_from_run("business-fail")
        self.assertEqual("FAILED", checked["state"])
        self.assertIn("业务结果明确失败", checked["terminal_reason"])

    def test_recovery_after_completed_process_does_not_execute_again(self) -> None:
        QueuePlanner(self.storage).enqueue(self.task("recover"))
        counter = self.task_root / "counter.txt"
        code = (
            "from pathlib import Path;"
            f"p=Path({str(counter)!r});"
            "n=int(p.read_text()) if p.exists() else 0;"
            "p.write_text(str(n+1))"
        )
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch("recover", [sys.executable, "-c", code])
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        self.assertEqual(0, handle.wait(timeout=5))

        recovered, message = RecoveryManager(self.storage).recover_finished_run("recover")
        self.assertEqual("SELF-CHECK", recovered["state"])
        self.assertIn("未重复执行", message)
        duplicate = Dispatcher(self.storage).dispatch("recover", [sys.executable, "-c", code])
        self.assertFalse(duplicate.dispatched)
        self.assertEqual("1", counter.read_text(encoding="utf-8"))
        self.assertEqual(6, len(list((self.storage.runs_dir / "recover").iterdir())))

    @unittest.skipUnless(os.name == "nt", "Windows end-to-end no-window evidence")
    def test_empty_library_real_end_to_end_completes_with_zero_windows(self) -> None:
        self.assertEqual([], self.storage.load_tasks())
        QueuePlanner(self.storage).enqueue(self.task())
        artifact = self.task_root / "cards" / "e2e" / "artifact.txt"
        artifact.parent.mkdir(parents=True, exist_ok=True)
        code = (
            "import json,time;from pathlib import Path;"
            "time.sleep(0.25);"
            f"Path({str(artifact)!r}).write_text('business artifact',encoding='utf-8');"
            "print(json.dumps({'business_success':True}))"
        )
        dispatcher = Dispatcher(self.storage)
        decision = dispatcher.dispatch("e2e", [sys.executable, "-c", code])
        self.assertTrue(decision.dispatched)
        handle = dispatcher.take_process(decision.pid or 0)
        windows: set[int] = set()
        while handle.process.poll() is None:
            windows.update(visible_window_handles(handle.process.pid))
            time.sleep(0.01)
        self.assertEqual(0, handle.wait(timeout=5))
        self.assertEqual(set(), windows)

        recovery = RecoveryManager(self.storage)
        recovered, _ = recovery.recover_finished_run("e2e")
        self.assertEqual("SELF-CHECK", recovered["state"])
        audited = recovery.finish_self_check_from_run("e2e")
        self.assertEqual("AUDIT", audited["state"])

        summary = self.summary()
        summary_path = self.audit_engine.write_summary("e2e", summary)
        result = self.audit_engine.audit(
            audited, self.receipt(artifact), summary, auditor_skill="eng.audit"
        )
        self.assertEqual("PASS", result.verdict)
        completed = self.audit_engine.close("e2e", result)
        self.assertEqual("COMPLETED", completed["state"])
        self.assertTrue(summary_path.exists())
        events = [json.loads(line) for line in (self.storage.events_dir / "e2e.jsonl").read_text(encoding="utf-8").splitlines()]
        self.assertEqual(
            ["EXECUTING", "SELF-CHECK", "AUDIT", "COMPLETED"],
            [event["to"] for event in events],
        )

    def test_closeout_blocks_nonterminal_records_instead_of_deleting_them(self) -> None:
        self.storage.save_tasks([self.task("dangling")])
        changed = RecoveryManager(self.storage).block_nonterminal_closeout()
        self.assertEqual(["dangling"], changed)
        self.assertEqual("BLOCKED", self.storage.load_tasks()[0]["state"])
        self.assertTrue((self.storage.events_dir / "dangling.jsonl").exists())


if __name__ == "__main__":
    unittest.main()
