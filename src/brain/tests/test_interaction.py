# -*- coding: utf-8 -*-
"""L7 交互循环单测：征询闭环 + 队列调整 + 异步三拍 + 意图规则。

运行：cd src\brain && python -X utf8 tests\test_interaction.py
"""

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]  # H:\UltimaAI\UltimaAgent
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.interaction import (
    InteractionLoop,
    _ADJUST_INTENT,
    _CONFIRM_INTENT,
    _CONSULT_INTENT,
    _INSERT_COMMAND,
    _PRIORITY_COMMAND,
    _normalize_utterance,
)
from tasks.queue_engine import QueuePlanner, QueueState, QueueStorage


def _make_task(task_id: str, priority: int = 50) -> dict:
    return {
        "task_id": task_id,
        "state": "QUEUED",
        "priority": priority,
        "dependsOn": [],
        "parallelGroup": None,
        "fileDomain": ["docs"],
        "reasoningEffort": "low",
        "created_at": "2026-10-25T00:00:00+08:00",
        "updated_at": "2026-10-25T00:00:00+08:00",
        "terminal_reason": None,
        "card_path": f"cards/{task_id}/task.md",
    }


def _make_card(root: Path, task_id: str, title: str) -> None:
    card_dir = root / "cards" / task_id
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "task.md").write_text(
        f"- **标题**：{title}\n- **任务**：{task_id}\n", encoding="utf-8"
    )


class TestIntentRules(unittest.TestCase):
    def test_normalize_trad(self):
        self.assertEqual(_normalize_utterance("把任務優先級調整到80"), "把任务优先级调整到80")

    def test_confirm_intent(self):
        self.assertTrue(_CONFIRM_INTENT.search("确认"))
        self.assertTrue(_CONFIRM_INTENT.search("可以，就这样"))
        self.assertTrue(_CONFIRM_INTENT.search("没问题"))

    def test_consult_intent(self):
        self.assertTrue(_CONSULT_INTENT.search("你觉得怎么样"))
        self.assertTrue(_CONSULT_INTENT.search("行不行"))
        self.assertTrue(_CONSULT_INTENT.search("可以吗"))

    def test_adjust_intent(self):
        self.assertTrue(_ADJUST_INTENT.search("帮我调整一下"))
        self.assertTrue(_ADJUST_INTENT.search("重排"))
        # "插队"是具体指令，归 _try_adjust_command（ADJUST_KEYWORD），非泛意图
        self.assertFalse(_ADJUST_INTENT.search("插队"))
        # "改优先级"含泛"改"字也含具体词"优先级"，handle 路径优先走具体指令
        self.assertTrue(_ADJUST_INTENT.search("改优先级"))

    def test_priority_command(self):
        m = _PRIORITY_COMMAND.search("把 t1 优先级设为 80")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("task_id"), "t1")
        self.assertEqual(m.group("priority"), "80")

    def test_priority_command_trad(self):
        """繁体输入经归一化后应命中优先级指令。"""
        m = _PRIORITY_COMMAND.search(_normalize_utterance("將t1優先級改為90"))
        self.assertIsNotNone(m)
        self.assertEqual(m.group("task_id"), "t1")
        self.assertEqual(m.group("priority"), "90")

    def test_insert_command(self):
        m = _INSERT_COMMAND.search("把 t2 插到 t1 之前")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("task_id"), "t2")
        self.assertEqual(m.group("target"), "t1")

    def test_insert_command_variant(self):
        m = _INSERT_COMMAND.search("将 t3 挪到 t2 前面")
        self.assertIsNotNone(m)
        self.assertEqual(m.group("task_id"), "t3")
        self.assertEqual(m.group("target"), "t2")


class TestInteractionLoop(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        storage = QueueStorage(self.root)
        storage.ensure_layout()
        for task in (_make_task("t1", 50), _make_task("t2", 60), _make_task("t3", 40)):
            _make_card(self.root, task["task_id"], f"任务{task['task_id']}")
            storage.save_tasks(
                [*storage.load_tasks(), task]
                if storage.load_tasks()
                else [task]
            )
        self.loop = InteractionLoop(self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def test_query_then_consult_then_confirm(self):
        """征询闭环：查询 → 征询 → 确认 → 待命。"""
        # 查询
        r1 = self.loop.handle("查一下任务状态")
        self.assertTrue(r1.handled)
        self.assertTrue(r1.ok)
        self.assertEqual(r1.state.phase, "pending_confirm")
        # 征询
        r2 = self.loop.handle("你觉得怎么样")
        self.assertTrue(r2.handled)
        self.assertIn("你觉得怎么样", r2.text)
        # 确认
        r3 = self.loop.handle("确认")
        self.assertTrue(r3.handled)
        self.assertTrue(r3.ok)
        self.assertEqual(r3.state.phase, "idle")

    def test_priority_adjust_roundtrip(self):
        """改优先级：真实写队列引擎，回读验证生效。"""
        r = self.loop.handle("把 t1 优先级设为 80")
        self.assertTrue(r.handled)
        self.assertTrue(r.ok)
        # 回读冻结引擎验证
        storage = QueueStorage(self.root)
        tasks = storage.load_tasks()
        t1 = next(t for t in tasks if t["task_id"] == "t1")
        self.assertEqual(t1["priority"], 80)
        self.assertTrue(r.state.adjusted)

    def test_requeue_before_roundtrip(self):
        """插队：真实写队列引擎，验证顺序变化。"""
        r = self.loop.handle("把 t3 插到 t1 之前")
        self.assertTrue(r.handled)
        self.assertTrue(r.ok)
        # 队列顺序验证
        planner = QueuePlanner(QueueStorage(self.root))
        ordered = [t["task_id"] for t in planner.ordered_tasks()]
        self.assertLess(ordered.index("t3"), ordered.index("t1"))

    def test_adjust_rejected_for_non_queued(self):
        """非 QUEUED 任务拒绝调整（引擎侧校验）。"""
        # 先把 t2 置为非 QUEUED（经状态机迁移）
        storage = QueueStorage(self.root)
        machine_state = __import__("tasks.queue_engine.state_machine", fromlist=["StateMachine"]).StateMachine(storage)
        tasks = storage.load_tasks()
        t2 = next(t for t in tasks if t["task_id"] == "t2")
        updated, _ = machine_state.transition(t2, "EXECUTING", actor="brain", reason="测试")
        tasks = [updated if t["task_id"] == "t2" else t for t in tasks]
        storage.save_tasks(tasks)
        r = self.loop.handle("把 t2 优先级设为 90")
        self.assertTrue(r.handled)
        self.assertFalse(r.ok)
        self.assertIn("调整失败", r.text)

    def test_invalid_task_id_rejected(self):
        """路径型非法 ID 被拒（不解析为合法任务、不静默回落）。"""
        r = self.loop.handle("把 ../x 优先级设为 90")
        self.assertTrue(r.handled)
        self.assertFalse(r.ok)
        self.assertIn("调整", r.text)

    def test_acknowledge_delivery_three_beat(self):
        """异步交付三拍第一拍：告知"稍等"。"""
        ack = self.loop.acknowledge_delivery("已整理完成")
        self.assertEqual(ack, "稍等，我整理一下。")
        self.assertEqual(self.loop.phase, "pending_confirm")
        self.assertEqual(self.loop.last_summary, "已整理完成")

    def test_consult_without_result_stays_idle(self):
        """无已交付结果时征询不误吞。"""
        r = self.loop.handle("你觉得怎么样")
        self.assertFalse(r.handled)  # 未命中，保持静默
        self.assertEqual(r.state.phase, "idle")


if __name__ == "__main__":
    unittest.main(verbosity=2)
