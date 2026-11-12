"""s3-orchestrator 验收测试（M10/M11 队列编排 · ACCEPT-1~6）。"""

import tempfile
import unittest
from pathlib import Path

from src.brain.orchestration.queue import (
    TaskQueue,
    OrchestratorError,
    SevenRingCheck,
    PHASES,
)


def make_tmp() -> Path:
    return Path(tempfile.mkdtemp(prefix="orch_s3_"))


class TestOrchestrator(unittest.TestCase):
    def test_full_loop(self):  # ACCEPT-1
        d = make_tmp()
        q = TaskQueue(d)
        t = q.create("主任务", priority=80, permissions=("cap:intent.parse", "cap:memory.read"))
        q.enqueue(t.task_id)
        for ph in PHASES[2:]:
            q.advance(t.task_id, ph)
        self.assertEqual(t.phase, "回执")
        self.assertTrue(t.receipt is None)  # complete 前无回执
        q.complete(t.task_id, {"ok": True})
        self.assertEqual(t.receipt, {"ok": True})

    def test_no_phase_jump(self):  # 状态机不跳迁
        d = make_tmp()
        q = TaskQueue(d)
        t = q.create("T", priority=10)
        with self.assertRaises(OrchestratorError):
            q.advance(t.task_id, "执行")  # 跳过排队

    def test_subagent_privilege_limited(self):  # ACCEPT-2
        d = make_tmp()
        q = TaskQueue(d)
        parent = q.create("主任务", permissions=("cap:intent.parse", "cap:memory.read"))
        # 子任务权限 ⊆ 主任务 → 通过
        sub = q.dispatch_subtask(parent.task_id, "子任务", ("cap:memory.read",))
        self.assertEqual(sub.parent_task, parent.task_id)
        # 越权 → 拒绝
        with self.assertRaises(OrchestratorError):
            q.dispatch_subtask(parent.task_id, "越权子任务", ("cap:exec.run",))

    def test_replan(self):  # ACCEPT-3
        d = make_tmp()
        q = TaskQueue(d)
        t = q.create("失败任务")
        r1 = q.replan(t.task_id, note="网络超时")
        self.assertTrue(r1["replanned"])
        r2 = q.replan(t.task_id, note="再试")
        r3 = q.replan(t.task_id, note="三试")
        r4 = q.replan(t.task_id, note="超预算")
        self.assertFalse(r4["replanned"])
        self.assertEqual(t.replan_count, 3)
        self.assertTrue(any("失败重规划" in h.get("note", "") for h in t.history))

    def test_view_consistent(self):  # ACCEPT-4
        d = make_tmp()
        q = TaskQueue(d)
        t1 = q.create("低优", priority=10)
        t2 = q.create("高优", priority=90)
        view = q.view()
        self.assertEqual(view[0]["task_id"], t2.task_id)  # 高优先在前
        self.assertIn("state", view[0])
        self.assertIn("priority", view[0])

    def test_seven_ring_pre_check(self):  # ACCEPT-5
        d = make_tmp()
        q = TaskQueue(d)
        t = q.create("T", priority=10)
        check = SevenRingCheck()
        r = check.pre_dispatch(t.task_id, "voice.speak")
        self.assertFalse(r["allowed"])  # 7 环未走完，防直达
        self.assertIsNotNone(r["missing"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
