"""Freeze a work order by tagging it, but only when two independent gates agree.

Gate structure, and why it is this way:

* ``verify.json`` carries the **authority**. It is produced by deterministic
  checks — exit code, receipt validity, whether the receipt is still on the
  current tree, whether the declared files landed. Anyone can re-run those and
  get the same answer, so they do not depend on who wrote the code.
* ``audit.json`` carries a **veto**. A model audit cannot authorize anything the
  deterministic checks could not establish, but it can stop a pass the checks
  allowed. Model judgement is an opinion; mechanical fact is the gate.

Freezing needs both: verified is true AND the audit did not fail. Either alone
is insufficient, and neither can be produced by the party being checked.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]


def _git_exe() -> str:
    """A bare `git` is not resolvable in every session; find it explicitly."""
    import shutil

    found = shutil.which("git") or shutil.which("git.exe")
    if found:
        return found
    for candidate in (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe"):
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError("git executable not found")


def _git(*args: str) -> str:
    completed = subprocess.run(
        [_git_exe(), *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip()[:300])
    return completed.stdout.strip()


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _refuse(reason: str, **extra) -> int:
    print(json.dumps({"blocked": True, "reason": reason, **extra}, ensure_ascii=False), file=sys.stderr)
    return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--message", default="")
    parser.add_argument("--push", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    run_dir = Path(args.run_dir)

    verify_path = run_dir / "verify.json"
    if not verify_path.is_file():
        return _refuse("no verify.json; deterministic verification must run before freezing")
    verify = _load(verify_path)
    if verify is None:
        return _refuse("unreadable verify.json")
    if verify.get("verified") is not True:
        return _refuse("deterministic verification did not pass; refusing to freeze",
                       blocking_failures=verify.get("blocking_failures"))

    audit_path = run_dir / "audit.json"
    if not audit_path.is_file():
        return _refuse("no audit.json; audit must run before freezing")
    audit = _load(audit_path)
    if audit is None:
        return _refuse("unreadable audit.json")
    if audit.get("audit_passed") is not True:
        return _refuse("audit_passed is not true; refusing to freeze",
                       round1=(audit.get("round1") or {}).get("verdict"),
                       round2=(audit.get("round2") or {}).get("verdict"))

    # Re-check staleness at the moment of tagging, not only at verify time:
    # HEAD can move between the two steps and that is exactly the stale-green case.
    try:
        head_now = _git("rev-parse", "HEAD")
        verified_head = str(verify.get("head") or "").strip()
        if verified_head and head_now != verified_head:
            return _refuse("HEAD moved since verification; the verified tree is no longer the one being tagged",
                           verified_head=verified_head[:12], head_now=head_now[:12])
    except RuntimeError as exc:
        return _refuse(str(exc))

    stamp = datetime.now().strftime("%Y%m%d")
    tag = f"{args.work_order}-freeze-{stamp}"
    message = args.message.strip() or f"{args.work_order} frozen: verified + two-round audit PASS"

    try:
        _git("tag", "-a", tag, "-m", message)
        if args.push:
            _git("push", "origin", tag)
    except RuntimeError as exc:
        return _refuse(str(exc))

    print(json.dumps({"frozen": True, "tag": tag, "pushed": bool(args.push),
                      "head": _git("rev-parse", "HEAD")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
