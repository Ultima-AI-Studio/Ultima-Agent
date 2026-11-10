"""wo-ultimaagent-20261108-0026 T0 audit prompt contract tests."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path


def _module():
    try:
        return importlib.import_module("src.brain.guardrails.audit_prompt")
    except ModuleNotFoundError as exc:
        raise AssertionError("audit prompt loader is missing") from exc


class TestAuditPromptLoader(unittest.TestCase):
    def test_default_prompt_loads_for_independent_auditor(self) -> None:
        prompt = _module().load_audit_prompt("eng.audit")
        self.assertTrue(prompt.strip())

    def test_missing_prompt_fails_closed(self) -> None:
        module = _module()
        missing = Path(tempfile.mkdtemp()) / "missing.md"
        with self.assertRaises(module.AuditPromptError):
            module.load_audit_prompt("eng.audit", path=missing)

    def test_empty_prompt_fails_closed(self) -> None:
        module = _module()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.md"
            path.write_text("  \n", encoding="utf-8")
            with self.assertRaises(module.AuditPromptError):
                module.load_audit_prompt("eng.security", path=path)

    def test_dev_role_is_rejected(self) -> None:
        module = _module()
        with self.assertRaises(module.AuditPromptError):
            module.load_audit_prompt("dev")


class TestAuditOutputAdapter(unittest.TestCase):
    def test_json_schema_uses_existing_severity_vocabulary(self) -> None:
        module = _module()
        finding = module.AUDIT_OUTPUT_JSON_SCHEMA["properties"]["findings"]["items"]
        self.assertEqual(
            finding["properties"]["severity"]["enum"],
            ["blocker", "major", "minor"],
        )
        self.assertEqual(module.AUDIT_OUTPUT_JSON_SCHEMA["required"], ["findings", "gate"])

    def test_valid_output_becomes_review_result(self) -> None:
        module = _module()
        content = json.dumps(
            {
                "findings": [
                    {
                        "severity": "blocker",
                        "item": "missing-evidence",
                        "detail": "No test log was supplied.",
                    },
                    {
                        "severity": "minor",
                        "item": "wording",
                        "detail": "Clarify the report heading.",
                    },
                ],
                "gate": "FAIL",
            }
        )

        result = module.parse_audit_output(content, role="eng.audit")

        self.assertFalse(result.ok)
        self.assertEqual(result.role, "eng.audit")
        self.assertEqual(result.as_dict()["blocker"], 1)
        self.assertEqual(result.as_dict()["minor"], 1)

    def test_gate_must_match_deterministic_reviewer(self) -> None:
        module = _module()
        content = json.dumps(
            {
                "findings": [
                    {"severity": "blocker", "item": "x", "detail": "blocked"}
                ],
                "gate": "PASS",
            }
        )
        with self.assertRaises(module.AuditPromptError):
            module.parse_audit_output(content, role="eng.audit")

    def test_invalid_severity_fails_closed(self) -> None:
        module = _module()
        content = json.dumps(
            {
                "findings": [
                    {"severity": "critical", "item": "x", "detail": "bad"}
                ],
                "gate": "FAIL",
            }
        )
        with self.assertRaises(module.AuditPromptError):
            module.parse_audit_output(content, role="eng.security")

    def test_extra_or_duplicate_fields_fail_closed(self) -> None:
        module = _module()
        extra = json.dumps({"findings": [], "gate": "PASS", "summary": "extra"})
        duplicate = '{"findings":[],"gate":"PASS","gate":"FAIL"}'
        for content in (extra, duplicate):
            with self.subTest(content=content):
                with self.assertRaises(module.AuditPromptError):
                    module.parse_audit_output(content, role="eng.audit")

    def test_dev_cannot_use_output_adapter(self) -> None:
        module = _module()
        with self.assertRaises(module.AuditPromptError):
            module.parse_audit_output('{"findings":[],"gate":"PASS"}', role="dev")


if __name__ == "__main__":
    unittest.main(verbosity=2)
