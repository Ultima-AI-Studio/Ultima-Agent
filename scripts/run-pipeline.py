#!/usr/bin/env python
"""Run the existing G-ORCH stages once without duplicating their gates."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirement")
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--card", required=True)
    parser.add_argument("--prompt")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-plan", action="store_true")
    parser.add_argument("--skip-dispatch", action="store_true")
    parser.add_argument("--skip-freeze", action="store_true")
    parser.add_argument("--evidence", nargs="*", default=[])
    parser.add_argument("--push", action="store_true")
    return parser


def _call(script: str, argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPTS / script), *argv],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _command(script: str, argv: list[str]) -> list[str]:
    return [sys.executable, str(SCRIPTS / script), *argv]


def _record(
    steps: list[dict], step: str, proc: subprocess.CompletedProcess, **extra
) -> None:
    steps.append(
        {
            "step": step,
            "exit_code": proc.returncode,
            "stdout": (proc.stdout or "").strip()[-800:],
            "stderr": (proc.stderr or "").strip()[-800:],
            **extra,
        }
    )


def _skipped(steps: list[dict], step: str, reason: str) -> None:
    steps.append(
        {
            "step": step,
            "exit_code": 0,
            "stdout": "",
            "stderr": "",
            "skipped": True,
            "reason": reason,
        }
    )


def _blocked_dispatch_outcome(done: dict) -> tuple[str, int]:
    """Distinguish a bad receipt from a real receipt waiting for the audit slot."""
    if done.get("state") != "blocked":
        return "blocked", 2
    if done.get("receipt_valid") is False:
        return "blocked-for-invalid-receipt", 2
    if done.get("receipt_valid") is True and done.get("audit_slot_busy") is True:
        return "paused-for-audit-slot", 0
    return "blocked", 2


def _json_lines(text: str) -> list[dict]:
    rows = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except (TypeError, ValueError):
            continue
        if isinstance(value, dict):
            rows.append(value)
    return rows


def _dispatch_run(proc: subprocess.CompletedProcess) -> Path | None:
    for row in reversed(_json_lines(proc.stdout or "")):
        value = row.get("run")
        if value:
            return Path(value)
    return None


def _load_done(run_dir: Path) -> dict | None:
    try:
        value = json.loads((run_dir / "done.json").read_text(encoding="utf-8-sig"))
    except (OSError, TypeError, ValueError):
        return None
    return value if isinstance(value, dict) else None


def _finish(
    run_dir: Path,
    steps: list[dict],
    outcome: str,
    reason: str,
    exit_code: int,
) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "outcome": outcome,
        "reason": reason,
        "run_dir": str(run_dir),
        "steps": steps,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    (run_dir / "pipeline.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(
        json.dumps(
            {"outcome": outcome, "reason": reason, "run_dir": str(run_dir)},
            ensure_ascii=False,
        )
    )
    return exit_code


def _argvs(args: argparse.Namespace, run_dir: str) -> list[tuple[str, str, list[str]]]:
    plan = ["--requirement", args.requirement, "--run-dir", str(args.run_dir)]
    dispatch_base = [
        "--order",
        args.work_order,
        "--prompt",
        args.prompt,
        "--card",
        args.card,
    ]
    verify = ["--work-order", args.work_order, "--run-dir", run_dir]
    audit = [
        "--work-order",
        args.work_order,
        "--card",
        args.card,
        "--run-dir",
        run_dir,
        "--evidence",
        *args.evidence,
    ]
    freeze = ["--work-order", args.work_order, "--run-dir", run_dir]
    if args.push:
        freeze.append("--push")
    return [
        ("plan", "orchestrate-order.py", plan),
        ("dispatch-dor", "dispatch-work-order.py", [*dispatch_base, "--dry-run-dor"]),
        ("dispatch", "dispatch-work-order.py", [*dispatch_base, "--execute"]),
        ("verify", "verify-order.py", verify),
        ("audit", "audit-work-order.py", audit),
        ("freeze", "freeze-work-order.py", freeze),
    ]


def _validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if not args.skip_plan and not args.requirement:
        parser.error("--requirement is required unless --skip-plan is set")
    if not args.skip_dispatch and not args.prompt:
        parser.error("--prompt is required unless --skip-dispatch is set")
    if not args.evidence:
        parser.error("--evidence must name at least one audit artifact")


def main(argv: Sequence[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    _validate_args(parser, args)

    downstream_run = str(args.run_dir) if args.skip_dispatch else "<dispatch-run-dir>"
    commands = _argvs(args, downstream_run)
    if args.dry_run:
        for step, script, command_argv in commands:
            if step == "plan" and args.skip_plan:
                continue
            if step in {"dispatch-dor", "dispatch"} and args.skip_dispatch:
                continue
            if step == "freeze" and args.skip_freeze:
                continue
            print(json.dumps({"step": step, "argv": _command(script, command_argv)}, ensure_ascii=False))
        return 0

    steps: list[dict] = []
    active_run = Path(args.run_dir)

    if args.skip_plan:
        _skipped(steps, "plan", "--skip-plan")
    else:
        _, script, command_argv = commands[0]
        proc = _call(script, command_argv)
        _record(steps, "plan", proc)
        if proc.returncode != 0:
            return _finish(active_run, steps, "plan-failed", "plan stage failed", 2)

    if args.skip_dispatch:
        _skipped(steps, "dispatch-dor", "--skip-dispatch")
        _skipped(steps, "dispatch", "--skip-dispatch")
    else:
        for index in (1, 2):
            step, script, command_argv = commands[index]
            proc = _call(script, command_argv)
            _record(steps, step, proc)
            if step == "dispatch-dor" and proc.returncode != 0:
                return _finish(
                    active_run,
                    steps,
                    "dispatch-dor-failed",
                    "dispatch definition-of-ready gate failed",
                    2,
                )
            if step != "dispatch":
                continue

            discovered = _dispatch_run(proc)
            if discovered is not None:
                active_run = discovered
            done = _load_done(active_run)
            if done is None:
                return _finish(
                    active_run,
                    steps,
                    "dispatch-failed",
                    "dispatch did not produce a readable done.json",
                    2,
                )
            if done.get("state") == "blocked" or proc.returncode != 0:
                outcome, code = _blocked_dispatch_outcome(done)
                reason = {
                    "blocked-for-invalid-receipt": "dispatch receipt is invalid",
                    "paused-for-audit-slot": "valid receipt is waiting for an audit slot",
                }.get(outcome, "dispatch ended blocked for a non-slot reason")
                return _finish(active_run, steps, outcome, reason, code)
            if done.get("receipt_valid") is not True or done.get("state") != "audit":
                return _finish(
                    active_run,
                    steps,
                    "dispatch-failed",
                    "dispatch receipt is not ready for audit",
                    2,
                )

    verify_argv = ["--work-order", args.work_order, "--run-dir", str(active_run)]
    proc = _call("verify-order.py", verify_argv)
    _record(steps, "verify", proc)
    if proc.returncode != 0:
        return _finish(
            active_run,
            steps,
            "verify-failed",
            "deterministic verification did not pass; audit was not run",
            2,
        )

    audit_argv = [
        "--work-order",
        args.work_order,
        "--card",
        args.card,
        "--run-dir",
        str(active_run),
        "--evidence",
        *args.evidence,
    ]
    proc = _call("audit-work-order.py", audit_argv)
    _record(steps, "audit", proc)
    if proc.returncode != 0:
        return _finish(
            active_run,
            steps,
            "audit-failed",
            "audit did not pass; freeze was not run",
            2,
        )

    if args.skip_freeze:
        _skipped(steps, "freeze", "--skip-freeze")
        return _finish(
            active_run,
            steps,
            "audited",
            "audit passed; freeze skipped by request",
            0,
        )

    freeze_argv = ["--work-order", args.work_order, "--run-dir", str(active_run)]
    if args.push:
        freeze_argv.append("--push")
    proc = _call("freeze-work-order.py", freeze_argv)
    _record(steps, "freeze", proc)
    if proc.returncode != 0:
        return _finish(
            active_run,
            steps,
            "freeze-failed",
            "audit passed but freeze refused",
            2,
        )
    return _finish(active_run, steps, "frozen", "audit passed and tag was created", 0)


if __name__ == "__main__":
    raise SystemExit(main())
