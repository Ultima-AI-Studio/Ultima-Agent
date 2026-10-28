r"""S11 学习闭环 · 单测（正式可复跑版）。

覆盖（对应批次规划 S11 T1/T2/T3）：
  1. 轨迹采集：从追加式审计日志提取执行轨迹（按 flow 分组、相位/耗时/成败判定）
  2. 成败判定：rejected / replanned / partial / approved 状态机判定
  3. 评测器：成功率 / 平均耗时 / P90 / 兜底次数 / 各意图聚合 / 基准线建立与升降信号
  4. 改进器：工具优先级前移、重试上限上调（封顶）、失败/兜底用例沉淀（留痕闭环）
  5. 回归：审计日志只读不破坏（verify 仍 ok）；确定性（同输入同结果）

运行：
  H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -X utf8 -m unittest discover -s src\brain\tests -p "test_learning_loop_s11.py" -v
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.guardrails.audit_log import AppendOnlyAuditLog  # noqa: E402
from src.brain.learn.evaluator import Evaluator, EvalReport  # noqa: E402
from src.brain.learn.improver import Improver, MAX_RETRY_BOOST  # noqa: E402
from src.brain.learn.trace_collector import TraceCollector, TraceRecord  # noqa: E402


def _seed_flow(audit: AppendOnlyAuditLog, flow_id: str, *, success: bool = True,
               intent: str = "task_status", rejected: bool = False) -> None:
    """向审计日志写入一条完整回路事件序列（模拟 brain_loop.mark）。"""
    events = [
        ("loop.receive", {"detail": "entry=cli"}),
        ("loop.intent", {"detail": intent}),
        ("loop.domain", {"detail": "task"}),
        ("loop.paradigm", {"detail": "7 环全过"}),
        ("loop.plan", {"detail": "task-xyz"}),
        ("loop.dispatch", {"detail": "task-xyz"}),
        ("loop.gate", {"detail": "scope 全过"}),
        ("loop.execute", {"detail": "stub-executor"}),
    ]
    if rejected:
        events.append(("loop.audit.permission", {"detail": "passed=False 动作越界（不在白名单）: {'ultima_danger'}"}))
    elif success:
        events.append(("loop.audit.direction", {"detail": "passed=True 方向未偏离"}))
        events.append(("loop.audit.permission", {"detail": "passed=True 动作均在白名单内"}))
        events.append(("loop.audit.consistency", {"detail": "passed=True 与本地记忆一致"}))
        events.append(("loop.audit.structure", {"detail": "passed=True 结构与参数明细齐全"}))
        events.append(("loop.orchestrate", {"detail": "回执"}))
        events.append(("loop.express", {"detail": "任务已完成"}))
        events.append(("loop.present", {"detail": "idle"}))
        events.append(("loop.memory", {"detail": "archived=True"}))
    else:
        events.append(("loop.audit.direction", {"detail": "passed=False 自评未达标"}))
    for et, payload in events:
        audit.append(et, "ultima.brain.loop", payload, session_id=flow_id)


class TestTraceCollector(unittest.TestCase):
    """轨迹采集与成败判定。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = AppendOnlyAuditLog(Path(self.tmp.name) / "audit.jsonl")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_collect_groups_by_flow(self) -> None:
        _seed_flow(self.audit, "flow-aaaa", success=True, intent="task_status")
        _seed_flow(self.audit, "flow-bbbb", success=True, intent="voice_query")
        collector = TraceCollector(self.audit)
        traces = collector.collect()
        self.assertEqual(len(traces), 2)
        flows = {t.flow_id for t in traces}
        self.assertEqual(flows, {"flow-aaaa", "flow-bbbb"})

    def test_approved_status_and_phases(self) -> None:
        _seed_flow(self.audit, "flow-ok", success=True)
        traces = TraceCollector(self.audit).collect()
        self.assertEqual(len(traces), 1)
        rec = traces[0]
        self.assertEqual(rec.status, "approved")
        self.assertIn("execute", rec.phases)
        self.assertIn("orchestrate", rec.phases)
        self.assertIn("memory", rec.phases)
        self.assertGreaterEqual(rec.loop_trace_count, 14)
        self.assertEqual(rec.intent, "task_status")
        self.assertEqual(rec.domain, "task")

    def test_rejected_status(self) -> None:
        _seed_flow(self.audit, "flow-no", success=False, rejected=True)
        traces = TraceCollector(self.audit).collect()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].status, "rejected")

    def test_replanned_status(self) -> None:
        _seed_flow(self.audit, "flow-rp", success=False, rejected=False)
        traces = TraceCollector(self.audit).collect()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].status, "replanned")

    def test_partial_status_when_execute_missing(self) -> None:
        self.audit.append("loop.intent", "ultima.brain.loop", {"detail": "x"}, session_id="flow-p")
        traces = TraceCollector(self.audit).collect()
        self.assertEqual(len(traces), 1)
        self.assertEqual(traces[0].status, "partial")

    def test_audit_log_untouched(self) -> None:
        _seed_flow(self.audit, "flow-ok", success=True)
        TraceCollector(self.audit).collect()
        verify = self.audit.verify()
        self.assertTrue(verify.get("ok"))


class TestEvaluator(unittest.TestCase):
    """评测与基准线。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = AppendOnlyAuditLog(Path(self.tmp.name) / "audit.jsonl")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _traces(self) -> list[TraceRecord]:
        _seed_flow(self.audit, "flow-1", success=True, intent="task_status")
        _seed_flow(self.audit, "flow-2", success=True, intent="task_status")
        _seed_flow(self.audit, "flow-3", success=True, intent="voice_query")
        _seed_flow(self.audit, "flow-4", success=False, rejected=True, intent="task_status")
        return TraceCollector(self.audit).collect()

    def test_report_metrics(self) -> None:
        report = Evaluator().evaluate(self._traces())
        self.assertEqual(report.total, 4)
        self.assertEqual(report.success, 3)
        self.assertEqual(report.rejected, 1)
        self.assertAlmostEqual(report.success_rate, 0.75)
        self.assertGreater(report.avg_duration_ms, 0.0)
        self.assertGreaterEqual(report.p90_duration_ms, report.avg_duration_ms - 1e-6)
        self.assertIn("task_status", report.by_intent)
        self.assertEqual(report.by_intent["task_status"]["total"], 3)
        self.assertEqual(report.by_intent["task_status"]["rejected"], 1)

    def test_baseline_establish_and_signal(self) -> None:
        traces = self._traces()  # 只采集一次（审计日志只写一轮事件）
        evaluator = Evaluator(baseline_path=Path(self.tmp.name) / "baseline.json")
        report1 = evaluator.evaluate(traces)
        self.assertEqual(report1.signal, "no_baseline")
        # 第二批同质（同一批轨迹）：steady
        report2 = evaluator.evaluate(traces)
        self.assertEqual(report2.signal, "steady")
        self.assertIsNotNone(report2.baseline)

    def test_improved_signal_on_better_rate(self) -> None:
        evaluator = Evaluator(success_rate_delta=0.05)
        bad = self._traces()
        evaluator.evaluate(bad)  # 建立基准（内存）
        good = [t for t in bad if t.status == "approved"]
        report = evaluator.evaluate(good)
        self.assertEqual(report.signal, "improved")

    def test_determinism(self) -> None:
        traces = self._traces()
        e1 = Evaluator()
        e2 = Evaluator()
        d1 = e1.evaluate(traces).as_dict()
        d2 = e2.evaluate(traces).as_dict()
        d1.pop("ts", None)
        d2.pop("ts", None)
        self.assertEqual(d1, d2)


class TestImprover(unittest.TestCase):
    """改进器：参数调整 + 用例沉淀 + 留痕。"""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.audit = AppendOnlyAuditLog(Path(self.tmp.name) / "audit.jsonl")
        self.case_dir = Path(self.tmp.name) / "cases"

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def _traces_with_failures(self) -> list[TraceRecord]:
        _seed_flow(self.audit, "flow-1", success=True, intent="task_status")
        _seed_flow(self.audit, "flow-2", success=False, rejected=True, intent="task_status")
        _seed_flow(self.audit, "flow-3", success=False, rejected=False, intent="voice_query")
        return TraceCollector(self.audit).collect()

    def test_tool_priority_shift_on_low_success(self) -> None:
        traces = self._traces_with_failures()
        report = Evaluator().evaluate(traces)
        improver = Improver(tool_orders={"task_status": ["ultima_task_query", "ultima_scene_exec"]})
        actions = improver.improve(report, traces)
        tool_acts = [a for a in actions if a.kind == "tool_priority"]
        self.assertGreaterEqual(len(tool_acts), 1)
        self.assertEqual(improver.tool_orders["task_status"],
                         ["ultima_scene_exec", "ultima_task_query"])

    def test_retry_policy_capped(self) -> None:
        traces = self._traces_with_failures()
        report = Evaluator().evaluate(traces)
        improver = Improver(retry_limits={"task_status": MAX_RETRY_BOOST})
        actions = improver.improve(report, traces)
        retry_acts = [a for a in actions if a.kind == "retry_policy"]
        self.assertEqual(retry_acts, [])  # 已达封顶不再上调
        self.assertEqual(improver.retry_limits["task_status"], MAX_RETRY_BOOST)

    def test_case_sink_and_audit_trail(self) -> None:
        traces = self._traces_with_failures()
        report = Evaluator().evaluate(traces)
        improver = Improver(adjust_log=self.audit, case_dir=self.case_dir)
        actions = improver.improve(report, traces)
        sink_acts = [a for a in actions if a.kind == "case_sink"]
        self.assertGreaterEqual(len(sink_acts), 1)
        # 用例文件落盘
        files = list(self.case_dir.glob("case-*.json"))
        self.assertEqual(len(files), len(sink_acts))
        # 留痕可回读
        entries = improver.log_entries()
        self.assertGreaterEqual(len(entries), len(sink_acts))
        # 审计链未被破坏
        self.assertTrue(self.audit.verify().get("ok"))

    def test_no_actions_when_all_green(self) -> None:
        _seed_flow(self.audit, "flow-ok1", success=True)
        _seed_flow(self.audit, "flow-ok2", success=True)
        traces = TraceCollector(self.audit).collect()
        report = Evaluator().evaluate(traces)
        improver = Improver()
        actions = improver.improve(report, traces)
        self.assertEqual(actions, [])


class TestTraceRecordSerialization(unittest.TestCase):
    """TraceRecord 序列化可回放。"""

    def test_as_dict_roundtrip(self) -> None:
        rec = TraceRecord(
            flow_id="flow-x", ts="2026-10-24T00:00:00Z", intent="task_status",
            domain="task", tools=("ultima_task_query",),
            phases=("receive", "execute"), durations_ms={"total": 12.3},
            verdicts=({"check": "direction", "detail": "passed=True"},),
            status="approved", model="stub-executor", loop_trace_count=14,
        )
        data = rec.as_dict()
        self.assertEqual(data["flow_id"], "flow-x")
        self.assertEqual(data["tools"], ["ultima_task_query"])
        self.assertEqual(data["status"], "approved")


if __name__ == "__main__":
    unittest.main()
