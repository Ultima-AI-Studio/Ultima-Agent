"""Freeze a work order by tagging it, but only after a passing two-round audit.

Gate order is enforced here rather than left to convention: without a readable
`audit.json` whose `audit_passed` is exactly true, no tag is created.
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


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if completed.returncode != 0:
        raise RuntimeError((completed.stderr or completed.stdout).strip()[:300])
    return completed.stdout.strip()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--message", default="")
    parser.add_argument("--push", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    audit_path = Path(args.run_dir) / "audit.json"
    if not audit_path.is_file():
        print(
            json.dumps({"blocked": True, "reason": "no audit.json; audit must run before freezing"}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2

    try:
        audit = json.loads(audit_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        print(json.dumps({"blocked": True, "reason": f"unreadable audit.json: {exc}"}, ensure_ascii=False), file=sys.stderr)
        return 2

    if audit.get("audit_passed") is not True:
        print(
            json.dumps(
                {
                    "blocked": True,
                    "reason": "audit_passed is not true; refusing to freeze",
                    "round1": audit.get("round1", {}).get("verdict"),
                    "round2": audit.get("round2", {}).get("verdict"),
                },
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 2

    stamp = datetime.now().strftime("%Y%m%d")
    tag = f"{args.work_order}-freeze-{stamp}"
    message = args.message.strip() or f"{args.work_order} frozen after two-round audit PASS"

    try:
        _git("tag", "-a", tag, "-m", message)
        if args.push:
            _git("push", "origin", tag)
    except RuntimeError as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2

    print(json.dumps({"frozen": True, "tag": tag, "pushed": bool(args.push), "head": _git("rev-parse", "HEAD")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
