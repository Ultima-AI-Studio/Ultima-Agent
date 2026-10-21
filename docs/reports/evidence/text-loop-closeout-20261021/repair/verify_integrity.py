from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
ROUND1 = ROOT / "docs/reports/evidence/w4-independent-20261021/round1"
sys.path.insert(0, str(ROOT))

EXPECTED_ROUND1 = {
    "developer-text-tests.txt": "bb1644d14071a19b1a26c270eae7cfc2d93c1ba4024c116cacd6263793c398bb",
    "evidence-sha256.json": "b9e729c618b6fe89b515fd269437ab4d17854f1c6b28b67a3797864b123870fa",
    "frozen-baseline-after.txt": "dcc5117d02ffddf0aa1405925338a745f9280ade3a232f3f0229abd4fcb8bc6c",
    "frozen-baseline-before.txt": "dcc5117d02ffddf0aa1405925338a745f9280ade3a232f3f0229abd4fcb8bc6c",
    "independent-results.json": "b68643f1b0c96e196135d6661c05bf99ae687640c13186c250044e869409f136",
    "original-developer-summary.json": "a96f5f5faee9c423dfd9657f780fd5189f552830d8b2ddde2db47403f6b1f66d",
    "original-queue-engine-first-failure.txt": "78fe90428af24d29d036027c2170dc641e2a8bcf3f49a9ee11332eae0a06395f",
    "original-queue-engine-full-retry.txt": "04f4860ceb8b38fee11aba530372658e30c4599a137e3af542225cde5e2cb919",
    "original-queue-engine-targeted-retry.txt": "4a98a12c6a7eec292ee3aeca14fa86ea6b15ecf64b282b19c241d9ae451de2f8",
    "queue-engine-independent-regression.txt": "6f98f65ad6efa94255ace39861b05231f77d1087546d2484e0c370e0368aecbc",
    "real-20-1-output.txt": "d5ed8c4a6dca10b219bbe8f3e3b647901ad5f075ccbf4ab07684290abc9f78f4",
    "review-report.md": "b49eb8f787df04c812e9334305423f1ff706a35ffb1636588cf40954d5aae3ef",
    "review_checks.py": "c5bd1038639f1aea6dea61d427254127e0332a65b292dccf3ca4a1c7d9f25d84",
    "seal_evidence.py": "b8d583e58ee00f14491b27da950dd7bda5354d2fc4cbffb2e5323c66f3ffa258",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    baseline = json.loads((OUT / "pre-repair-baseline.json").read_text(encoding="utf-8"))
    actual_engine = {
        path.name: sha256(path)
        for path in sorted((ROOT / "tasks/queue_engine").glob("*.py"))
    }
    actual_round1 = {
        path.name: sha256(path) for path in sorted(ROUND1.glob("*")) if path.is_file()
    }
    results = json.loads(
        (OUT / "independent-review-rerun/independent-results.json").read_text(
            encoding="utf-8"
        )
    )
    frozen = json.loads(
        (OUT / "independent-review-rerun/frozen-baseline-after.txt").read_text(
            encoding="utf-8"
        )
    )
    tag = subprocess.run(
        ["git", "-C", str(ROOT), "rev-list", "-n", "1", "v0.1-frozen"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    repair_reports = [
        ROOT / "logs/execution-reports/wo-s1-task-text-loop/w4-repair-summary.json",
        ROOT / "logs/execution-reports/s1-task-intent-parse/w4-repair-summary.json",
        ROOT / "logs/execution-reports/s1-task-queue-source/w4-repair-summary.json",
        ROOT / "logs/execution-reports/s1-task-aggregate-report/w4-repair-summary.json",
    ]
    parsed_reports = [json.loads(path.read_text(encoding="utf-8")) for path in repair_reports]
    checks = {
        "v0.1_tag_fixed": tag.returncode == 0
        and tag.stdout.strip() == baseline["v0.1_tag_commit"],
        "v0.1_manifest_36_of_36": frozen["status"] == "PASS"
        and frozen["manifest_items"] == 36
        and frozen["manifest_matching"] == 36,
        "production_tasks_unchanged": sha256(ROOT / "tasks/tasks.json")
        == baseline["production_tasks_sha256"],
        "frozen_queue_engine_unchanged": actual_engine
        == baseline["frozen_queue_engine"],
        "independent_round1_unchanged": actual_round1 == EXPECTED_ROUND1,
        "text_suite_16_of_16": "RETURN_CODE 0" in (OUT / "green-text-suite.txt").read_text(encoding="utf-8")
        and "Ran 16 tests" in (OUT / "green-text-suite.txt").read_text(encoding="utf-8"),
        "independent_script_49_of_49": results["passed"] == 49
        and results["failed"] == 0
        and all(run["returncode"] == 0 for run in results["runs"]),
        "independent_positive_rate_95_percent": results["positive_rate"] == 0.95,
        "actual_cli_exit_zero": "RETURN_CODE 0" in (OUT / "final-cli-query.txt").read_text(encoding="utf-8"),
        "repair_reports_keep_w4_open": all(
            report["version"] == "S1/v0.3"
            and report["independent_w4_completed"] is False
            and report["scope_violation"] is False
            for report in parsed_reports
        ),
    }
    result = {
        "version": "S1/v0.3",
        "work_order": "wo-s1-task-text-loop",
        "status": "PASS" if all(checks.values()) else "FAIL",
        "checks": checks,
        "v0.1_tag_commit": tag.stdout.strip(),
        "production_tasks_sha256": sha256(ROOT / "tasks/tasks.json"),
        "independent_w4_completed": False,
    }
    target = OUT / "post-repair-integrity.json"
    target.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
