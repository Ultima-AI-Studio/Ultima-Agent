"""wo-ultimaagent-20261108-0026 T1 unified audit report tests."""

from __future__ import annotations

import importlib
import tempfile
import unittest
from pathlib import Path

from src.brain.guardrails.reviewer import IndependentReviewer


def _module():
    try:
        return importlib.import_module("src.brain.guardrails.audit_report")
    except ModuleNotFoundError as exc:
        raise AssertionError("unified audit report generator is missing") from exc


def _review(*findings: tuple[str, str, str]):
    reviewer = IndependentReviewer("eng.audit")
    for severity, item, detail in findings:
        reviewer.add_finding(severity, item, detail)
    reviewer.checked.extend(["tests", "receipt"])
    return reviewer.gate()


def _data(*, evidence: bool = True, review=None):
    module = _module()
    evidence_items = (
        module.AuditEvidence(
            evidence_id="EV-001",
            path="tasks/queue/runs/example/test.log",
            kind="test",
            summary="Focused audit tests passed.",
        ),
    ) if evidence else ()
    return module.AuditReportData(
        work_order="wo-example-001",
        report_id="audit-example-001",
        generated_at="2026-11-08T00:00:00Z",
        audit_session_id="audit-session-001",
        source="ultima.guard.audit",
        review=review or _review(("minor", "wording", "Clarify one heading.")),
        scope=("Prompt loader", "Report generator"),
        methods=("Focused unittest", "Receipt readback"),
        evidence=evidence_items,
        retests=(
            module.RetestRecord(
                command="python -m unittest test_audit_report -v",
                result="PASS (4 tests)",
                evidence="EV-001",
            ),
        ),
    )


class TestAuditReportRenderer(unittest.TestCase):
    def test_report_has_all_fixed_sections_and_summary(self) -> None:
        report = _module().render_audit_report(_data())

        for section in (
            "## 报告头元信息",
            "## 审计范围与方法",
            "## 分级汇总",
            "## 逐项发现",
            "## 交付门结论",
            "## 证据索引",
            "## 复测记录",
        ):
            self.assertIn(section, report)
        self.assertIn("| blocker | 0 |", report)
        self.assertIn("| minor | 1 |", report)
        self.assertIn("Gate: **PASS**", report)
        self.assertIn("结论：**通过**", report)

    def test_no_evidence_cannot_render_pass_conclusion(self) -> None:
        report = _module().render_audit_report(_data(evidence=False, review=_review()))

        self.assertIn("Gate: **HOLD**", report)
        self.assertIn("EVIDENCE_REQUIRED", report)
        self.assertNotIn("通过", report)

    def test_blocker_forces_fail_even_with_evidence(self) -> None:
        review = _review(("blocker", "missing-test", "Required test did not run."))
        report = _module().render_audit_report(_data(review=review))

        self.assertIn("Gate: **FAIL**", report)
        self.assertNotIn("结论：**通过**", report)

    def test_table_values_are_escaped(self) -> None:
        module = _module()
        data = _data()
        data.evidence = (
            module.AuditEvidence("EV-001", "a|b.md", "report", "line1\nline2"),
        )
        report = module.render_audit_report(data)

        self.assertIn("a\\|b.md", report)
        self.assertIn("line1<br>line2", report)

    def test_writer_persists_exact_rendered_report(self) -> None:
        module = _module()
        data = _data()
        expected = module.render_audit_report(data)
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "audit.md"
            module.write_audit_report(path, data)
            self.assertEqual(path.read_text(encoding="utf-8"), expected)


if __name__ == "__main__":
    unittest.main(verbosity=2)
