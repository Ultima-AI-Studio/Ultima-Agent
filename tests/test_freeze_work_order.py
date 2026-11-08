from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freeze_work_order.py"
M4_ROOT = ROOT.parent / "ultimaagent-m4-ledger-20261108"
ORDER = "wo-ultimaagent-20261108-0030"
TAG = "test-dryrun-only"
EVIDENCE = r"docs\reports\wo-ultimaagent-20261108-0030*"


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=M4_ROOT, text=True, encoding="utf-8").strip()


def run_freeze(*extra: str, baseline: str | None = None, tag: str = TAG, evidence: str = EVIDENCE):
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--order",
            ORDER,
            "--baseline",
            baseline or git("rev-parse", "HEAD"),
            "--tag",
            tag,
            "--evidence",
            evidence,
            "--dry-run",
            *extra,
        ],
        cwd=M4_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )


def gate_json(stdout: str) -> dict:
    payload = stdout.split("GATE_JSON_BEGIN\n", 1)[1].split("\nGATE_JSON_END", 1)[0]
    return json.loads(payload)


def test_dry_run_outputs_complete_gate_json_without_tag_or_file():
    baseline = git("rev-parse", "HEAD")
    tags_before = git("tag", "--list")
    gate = M4_ROOT / "tasks" / "queue" / "gates" / f"{TAG}.json"
    files_before = set(gate.parent.iterdir()) if gate.parent.exists() else set()

    completed = run_freeze(baseline=baseline)

    tags_after = git("tag", "--list")
    files_after = set(gate.parent.iterdir()) if gate.parent.exists() else set()
    payload = gate_json(completed.stdout)
    assert completed.returncode == 0
    assert payload["decision"] == "PASS"
    assert payload["order"] == ORDER
    assert payload["baseline_commit"] == baseline
    assert payload["gate"] == TAG
    assert payload["evidence"]
    assert all({"path", "sha256"} <= item.keys() for item in payload["evidence"])
    assert tags_after == tags_before
    assert files_after == files_before
    assert not gate.exists()


def test_baseline_mismatch_exits_three():
    completed = run_freeze(baseline="0" * 40)

    assert completed.returncode == 3
    assert "baseline" in completed.stdout.lower()


def test_existing_tag_exits_three_without_mutation():
    existing = git("tag", "--list").splitlines()[0]
    before = git("tag", "--list")

    completed = run_freeze(tag=existing)

    assert completed.returncode == 3
    assert "tag" in completed.stdout.lower()
    assert git("tag", "--list") == before


def test_missing_evidence_exits_three():
    completed = run_freeze(evidence="docs/reports/definitely-missing-0030-*.json")

    assert completed.returncode == 3
    assert "evidence" in completed.stdout.lower()


def test_status_fail_json_is_rejected(tmp_path: Path):
    evidence = tmp_path / "failed.json"
    evidence.write_text('{"status":"FAIL"}', encoding="utf-8")

    completed = run_freeze(evidence=str(evidence))

    assert completed.returncode == 3
    assert "status" in completed.stdout


def test_all_pass_false_json_is_rejected(tmp_path: Path):
    evidence = tmp_path / "failed.json"
    evidence.write_text('{"all_technical_pass":false}', encoding="utf-8")

    completed = run_freeze(evidence=str(evidence))

    assert completed.returncode == 3
    assert "all_technical_pass" in completed.stdout


def test_dry_run_records_approval_text_and_never_writes_custom_gate(tmp_path: Path):
    gate = tmp_path / "custom-gate.json"

    completed = run_freeze(
        "--gate-json",
        str(gate),
        "--approve-text",
        "Owner dry-run approval text",
        "--known-limit",
        "No tag created in T3",
    )

    payload = gate_json(completed.stdout)
    assert completed.returncode == 0
    assert payload["approved_by"] == "owner"
    assert payload["approval_text"] == "Owner dry-run approval text"
    assert payload["known_limit"] == "No tag created in T3"
    assert payload["schema_version"] == "1.0"
    assert not gate.exists()
