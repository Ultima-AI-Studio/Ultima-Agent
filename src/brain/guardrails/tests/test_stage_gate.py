"""wo-ultimaagent-20261108-0027 T0 stage-gate contract tests."""

from __future__ import annotations

import importlib
import json
import tempfile
import unittest
from pathlib import Path
from typing import Any


def _module():
    try:
        return importlib.import_module("src.brain.guardrails.stage_gate")
    except ModuleNotFoundError as exc:
        raise AssertionError("stage gate module is missing") from exc


class TestStageGate(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.evidence_root = Path(self._tmp.name)
        self.work_order = "wo-stage-gate-test"
        self.stage = "T0"
        self.review_dir = self.evidence_root / self.work_order / self.stage
        self.review_dir.mkdir(parents=True)
        (self.evidence_root / "review-test.log").write_text(
            "7 tests passed", encoding="utf-8"
        )
        (self.evidence_root / "write-domain.log").write_text(
            "only allowed paths changed", encoding="utf-8"
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def _payload(self, **overrides: Any) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "work_order": self.work_order,
            "status": "COMPLETED",
            "reviewReason": "Independent review completed.",
            "stdoutText": "Tests and write-domain checks passed.",
            "evidence": [
                {
                    "path": "review-test.log",
                    "kind": "log",
                    "summary": "independent test rerun",
                },
                {
                    "path": "write-domain.log",
                    "kind": "log",
                    "summary": "write-domain verification",
                },
            ],
            "acceptance": [
                {
                    "id": "AUDIT-T0",
                    "result": "PASS",
                    "evidence": "independent checks completed",
                }
            ],
            "ok": True,
            "role": "eng.audit",
            "blocker": 0,
            "major": 0,
            "minor": 0,
            "checked": [
                "测试复跑: review-test.log",
                "写域核对: write-domain.log",
            ],
            "findings": [],
        }
        payload.update(overrides)
        return payload

    def _write_review(self, payload: dict[str, Any]) -> Path:
        path = self.review_dir / "independent-review.json"
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return path

    def _check(self):
        return _module().check_stage(
            self.work_order, self.stage, self.evidence_root
        )

    def test_clean_independent_review_passes(self) -> None:
        self._write_review(self._payload())

        result = self._check()

        self.assertTrue(result.passed, result.reasons)
        self.assertEqual(result.reasons, [])

    def test_missing_review_file_is_blocked(self) -> None:
        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("不存在" in reason for reason in result.reasons))

    def test_invalid_json_is_blocked(self) -> None:
        (self.review_dir / "independent-review.json").write_text(
            "{not-json", encoding="utf-8"
        )

        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("非法 JSON" in reason for reason in result.reasons))

    def test_blocker_finding_is_blocked(self) -> None:
        self._write_review(
            self._payload(
                ok=False,
                blocker=1,
                findings=[
                    {
                        "role": "eng.audit",
                        "severity": "blocker",
                        "item": "missing-proof",
                        "detail": "required proof is missing",
                    }
                ],
            )
        )

        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("blocker" in reason for reason in result.reasons))

    def test_dev_role_is_blocked(self) -> None:
        self._write_review(self._payload(role="dev"))

        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("角色" in reason for reason in result.reasons))

    def test_empty_checked_is_blocked(self) -> None:
        self._write_review(self._payload(checked=[]))

        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("checked" in reason for reason in result.reasons))

    def test_checked_without_write_domain_check_is_blocked(self) -> None:
        self._write_review(self._payload(checked=["测试复跑: review-test.log"]))

        result = self._check()

        self.assertFalse(result.passed)
        self.assertTrue(any("写域核对" in reason for reason in result.reasons))


if __name__ == "__main__":
    unittest.main(verbosity=2)
