"""Reproduce three stage-gate refusal cases without persistent fake reviews."""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.brain.guardrails.stage_gate import check_stage


def _review_payload(work_order: str, **overrides: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "work_order": work_order,
        "status": "COMPLETED",
        "reviewReason": "synthetic negative-case fixture",
        "stdoutText": "fixture only; no stage was dispatched",
        "evidence": [
            {"path": "proof.log", "kind": "log", "summary": "fixture proof"}
        ],
        "acceptance": [
            {"id": "NEGATIVE", "result": "PASS", "evidence": "fixture"}
        ],
        "ok": True,
        "role": "eng.audit",
        "blocker": 0,
        "major": 0,
        "minor": 0,
        "checked": ["测试复跑: proof.log", "写域核对: proof.log"],
        "findings": [],
    }
    payload.update(overrides)
    return payload


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="stage-gate-negative-") as tmp:
        evidence_root = Path(tmp)
        (evidence_root / "proof.log").write_text("fixture", encoding="utf-8")

        blocker_work_order = "negative-blocker"
        blocker_dir = evidence_root / blocker_work_order / "T0"
        blocker_dir.mkdir(parents=True)
        (blocker_dir / "independent-review.json").write_text(
            json.dumps(
                _review_payload(
                    blocker_work_order,
                    ok=False,
                    blocker=1,
                    acceptance=[
                        {
                            "id": "NEGATIVE",
                            "result": "FAIL",
                            "evidence": "synthetic blocker",
                        }
                    ],
                    findings=[
                        {
                            "role": "eng.audit",
                            "severity": "blocker",
                            "item": "synthetic-blocker",
                            "detail": "must refuse dispatch",
                        }
                    ],
                ),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        dev_work_order = "negative-dev-role"
        dev_dir = evidence_root / dev_work_order / "T0"
        dev_dir.mkdir(parents=True)
        (dev_dir / "independent-review.json").write_text(
            json.dumps(
                _review_payload(dev_work_order, role="dev"),
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

        cases = [
            ("missing-file", "negative-missing-file", "不存在"),
            ("blocker>0", blocker_work_order, "blocker"),
            ("role=dev", dev_work_order, "角色"),
        ]
        results: list[dict[str, Any]] = []
        for name, work_order, expected_reason in cases:
            decision = check_stage(work_order, "T0", evidence_root)
            reason_matched = any(expected_reason in reason for reason in decision.reasons)
            results.append(
                {
                    "case": name,
                    "work_order": work_order,
                    "stage": "T0",
                    "passed": decision.passed,
                    "started": decision.passed,
                    "dispatch_exit_code": 0 if decision.passed else 2,
                    "reasons": decision.reasons,
                    "expected_reason_fragment": expected_reason,
                    "reason_matched": reason_matched,
                }
            )

        all_refused = all(
            not item["passed"]
            and not item["started"]
            and item["dispatch_exit_code"] == 2
            and item["reason_matched"]
            for item in results
        )
        print(
            json.dumps(
                {
                    "case_count": len(results),
                    "all_refused": all_refused,
                    "cases": results,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0 if all_refused else 1


if __name__ == "__main__":
    raise SystemExit(main())
