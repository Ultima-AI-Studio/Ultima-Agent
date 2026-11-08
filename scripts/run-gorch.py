#!/usr/bin/env python
"""Drive the G-ORCH delivery segment end to end: audit (⑦) then freeze (⑧).

Scope, stated plainly because the first version of this script got it wrong:

* ①-④ (decompose / work order / schedule) produce a *plan*. They are reachable
  from here with ``--plan``, but their output is never handed to the delivery
  audit — a plan is not a deliverable, and grading it against acceptance gates
  written for a code change tests the wrong thing;
* ⑤-⑥ (dispatch and receipt reading) live in ``dispatch-work-order.py``, which
  already records ``receipt_valid`` and ``state`` in ``done.json``;
* ⑦-⑧ is what this chains: a two-round independent audit over real author
  artifacts, then a tag — but only when both rounds passed.

The ordering rule that keeps it honest: a failing audit stops the chain and
never falls through to freezing. The tag step re-reads ``audit.json`` itself
and refuses again on its own, so this script cannot become a way around the
gate.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
STAGES = ("decompose", "work_order", "schedule")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--card", required=True, help="task card carrying the acceptance gates")
    parser.add_argument("--run-dir", type=Path, required=True,
                        help="run holding the author artifacts and, after this chain, audit.json")
    parser.add_argument("--evidence", nargs="*", default=[], help="author artifacts to be audited")
    parser.add_argument("--plan", metavar="REQUIREMENT", default=None,
                        help="run ①-④ first from this requirement; its output is kept out of the audit")
    parser.add_argument("--push", action="store_true")
    parser.add_argument("--skip-freeze", action="store_true")
    return parser


def _call(script: str, argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, str(SCRIPTS / script), *argv],
                          capture_output=True, text=True, cwd=ROOT)


def _stages_all_completed(run_dir: Path) -> tuple[bool, dict]:
    """When --plan ran, refuse to proceed on anything but honest COMPLETED."""
    verdicts = {}
    for stage in STAGES:
        path = run_dir / "stages" / f"{stage}.json"
        if not path.is_file():
            verdicts[stage] = "missing"
            continue
        try:
            verdicts[stage] = str(json.loads(path.read_text(encoding="utf-8-sig")).get("verdict") or "absent").lower()
        except (OSError, ValueError):
            verdicts[stage] = "unreadable"
    return all(v == "completed" for v in verdicts.values()), verdicts


def main(argv=None) -> int:
    args = _parser().parse_args(argv)
    steps: list[dict] = []

    def record(name: str, proc: subprocess.CompletedProcess, **extra) -> None:
        steps.append({"step": name, "exit_code": proc.returncode,
                      "stdout": (proc.stdout or "").strip()[-800:],
                      "stderr": (proc.stderr or "").strip()[-800:], **extra})

    if args.plan is not None:
        proc = _call("orchestrate-order.py", ["--requirement", args.plan, "--run-dir", str(args.run_dir)])
        record("plan", proc)
        if proc.returncode != 0:
            return _finish(args.run_dir, steps, "blocked", "plan stage failed; nothing to audit")
        complete, verdicts = _stages_all_completed(args.run_dir)
        steps[-1]["verdicts"] = verdicts
        if not complete:
            return _finish(args.run_dir, steps, "blocked",
                           f"plan verdicts not all COMPLETED: {verdicts}")

    if not args.evidence:
        return _finish(args.run_dir, steps, "blocked",
                       "no evidence supplied; an audit with no artifact can only FAIL")

    # ⑦
    proc = _call("audit-work-order.py",
                 ["--work-order", args.work_order, "--card", args.card,
                  "--run-dir", str(args.run_dir), "--evidence", *args.evidence])
    record("audit", proc)
    if proc.returncode != 0:
        return _finish(args.run_dir, steps, "audit-failed",
                       "independent audit did not pass; freeze refused")

    # ⑧
    if args.skip_freeze:
        return _finish(args.run_dir, steps, "audited", "audit passed; froze nothing (--skip-freeze)")
    freeze_argv = ["--work-order", args.work_order, "--run-dir", str(args.run_dir)]
    if args.push:
        freeze_argv.append("--push")
    proc = _call("freeze-work-order.py", freeze_argv)
    record("freeze", proc)
    if proc.returncode != 0:
        return _finish(args.run_dir, steps, "freeze-failed", "audit passed but the freeze step refused")
    return _finish(args.run_dir, steps, "frozen", "audit passed and the tag was created")


def _finish(run_dir: Path, steps: list[dict], outcome: str, reason: str) -> int:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"outcome": outcome, "reason": reason, "run_dir": str(run_dir),
               "steps": steps, "finished_at": datetime.now(timezone.utc).isoformat()}
    (run_dir / "pipeline.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"outcome": outcome, "reason": reason, "run_dir": str(run_dir)}, ensure_ascii=False))
    return 0 if outcome in {"audited", "frozen"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
