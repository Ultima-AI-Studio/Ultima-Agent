r"""L7 悬浮球征询载体接线 单测（InteractionOrbBridge 桥接器）。

覆盖：
1. 查询完成 → 悬浮球 talking + 征询 prompt（征询闭环第一步）
2. 征询中 → talking + 征询文本
3. 确认通过 → idle 待命 + 确认提示
4. 调整完成（优先级/插队）→ idle + 调整结果
5. 调整失败 → failed + 失败提示
6. 泛调整等待参数 → listening + 引导文本
7. 无待确认 → idle
8. 异步三拍第一拍 → thinking + "稍等，我整理一下"
9. 渲染指令 orb.render + prompt 透传
10. 事件流 append-only（含 prompt）

运行：tools\python31313\python.exe -X utf8 src\brain\tests\test_interaction_orb.py
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

LIBS_BASE = PROJECT_ROOT / "libs" / "base" / "openjarvis" / "src"
if str(LIBS_BASE) not in sys.path:
    sys.path.insert(0, str(LIBS_BASE))

from src.brain.interaction_orb import InteractionOrbBridge
from tasks.queue_engine import QueueStorage


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


class OrbBridgeCase(unittest.TestCase):
    """带真实队列 fixture 的桥接测试基类。"""

    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        storage = QueueStorage(self.root)
        storage.ensure_layout()
        for task in (_make_task("t1", 50), _make_task("t2", 60), _make_task("t3", 40)):
            _make_card(self.root, task["task_id"], f"任务{task['task_id']}")
            storage.save_tasks(
                [*storage.load_tasks(), task]
                if storage.load_tasks()
                else [task]
            )
        self.bridge = InteractionOrbBridge(self.root)

    def tearDown(self) -> None:
        self._tmp.cleanup()


class TestQueryFlow(OrbBridgeCase):
    def test_query_completed_goes_talking_with_consult_prompt(self):
        response = self.bridge.handle("查一下任务状态", detail_task_id="t1")
        self.assertTrue(response.handled)
        self.assertEqual(self.bridge.orb.state, "talking")
        command = self.bridge.orb_command()
        self.assertEqual(command["kind"], "orb.render")
        self.assertIn("你觉得怎么样", command["prompt"])

    def test_consult_prompt(self):
        self.bridge.handle("查一下任务状态")
        # 征询意图（"你觉得怎么样"）
        response = self.bridge.handle("你觉得怎么样")
        self.assertTrue(response.handled)
        self.assertEqual(self.bridge.orb.state, "talking")
        self.assertIn("你觉得怎么样", self.bridge.orb_command()["prompt"])

    def test_confirm_returns_idle(self):
        self.bridge.handle("查一下任务状态")
        response = self.bridge.handle("确认")
        self.assertEqual(response.reason, "确认通过")
        self.assertEqual(self.bridge.orb.state, "idle")
        self.assertIn("已确认", self.bridge.orb_command()["prompt"])


class TestAdjustFlow(OrbBridgeCase):
    def test_priority_adjust_ok_idle(self):
        self.bridge.handle("查一下任务状态")
        response = self.bridge.handle("把 t1 优先级设为 80")
        self.assertTrue(response.ok)
        self.assertEqual(response.reason, "调整完成")
        self.assertEqual(self.bridge.orb.state, "idle")
        prompt = self.bridge.orb_command()["prompt"]
        self.assertIn("t1", prompt)
        self.assertIn("80", prompt)

    def test_insert_adjust_ok_idle(self):
        self.bridge.handle("查一下任务状态")
        response = self.bridge.handle("把 t3 插到 t2 之前")
        self.assertTrue(response.ok)
        self.assertEqual(self.bridge.orb.state, "idle")
        self.assertIn("t3", self.bridge.orb_command()["prompt"])

    def test_adjust_failed_goes_failed_state(self):
        self.bridge.handle("查一下任务状态")
        response = self.bridge.handle("把 notexist 优先级设为 99")
        self.assertFalse(response.ok)
        self.assertEqual(response.reason, "调整失败")
        self.assertEqual(self.bridge.orb.state, "failed")
        self.assertIn("调整失败", self.bridge.orb_command()["prompt"])

    def test_generic_adjust_waits_listening(self):
        self.bridge.handle("查一下任务状态")
        response = self.bridge.handle("调整一下")
        self.assertTrue(response.ok)
        self.assertEqual(self.bridge.orb.state, "listening")
        self.assertIn("请说明要调整的任务 ID", self.bridge.orb_command()["prompt"])


class TestAsyncAck(OrbBridgeCase):
    def test_acknowledge_delivery_thinking(self):
        text = self.bridge.acknowledge_delivery("查询完成，结果已整理")
        self.assertEqual(text, "稍等，我整理一下。")
        self.assertEqual(self.bridge.orb.state, "thinking")
        command = self.bridge.orb_command()
        self.assertEqual(command["prompt"], "稍等，我整理一下。")

    def test_ack_then_confirm_idle(self):
        self.bridge.acknowledge_delivery()
        response = self.bridge.handle("确认")
        self.assertEqual(self.bridge.orb.state, "idle")


class TestRenderAndAudit(OrbBridgeCase):
    def test_orb_command_contract(self):
        self.bridge.handle("查一下任务状态")
        command = self.bridge.orb_command()
        self.assertEqual(command["kind"], "orb.render")
        self.assertIn("state", command)
        self.assertIn("emotionId", command)
        self.assertIn("label", command)
        self.assertIn("visual", command)
        self.assertIn("prompt", command)

    def test_events_append_only_with_prompt(self):
        self.bridge.handle("查一下任务状态")
        self.bridge.handle("你觉得怎么样")
        self.bridge.handle("确认")
        events = self.bridge.events()
        self.assertEqual(len(events), 3)
        reasons = [event["reason"] for event in events]
        self.assertEqual(reasons, ["查询完成", "征询中", "确认通过"])
        self.assertTrue(all("prompt" in event for event in events))

    def test_empty_input_no_transition(self):
        response = self.bridge.handle("")
        self.assertEqual(self.bridge.orb.state, "idle")
        events = self.bridge.events()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["from_state"], "idle")
        self.assertEqual(events[0]["to_state"], "idle")

    def test_snapshot(self):
        self.bridge.handle("查一下任务状态")
        snapshot = self.bridge.snapshot()
        self.assertEqual(snapshot["orb_state"], "talking")
        self.assertGreater(snapshot["event_count"], 0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
