"""Deterministic verification of a delivered work order.

This exists because a language model saying PASS is not a control. The point of
four eyes is that the second pair does not depend on the first pair's judgement.
A second model run is the same model twice, not a second pair. What genuinely
does not depend on the author is a check that anyone can re-run and get the same
answer: exit code, receipt validity, whether the receipt is still valid on the
current tree, whether the declared files actually landed, whether the tree is
still the one that was tested.

So this script is the thing that grants a pass, and the LLM audit is advisory.
Freezing requires `verified: true` here; a model audit can only veto, never
authorize what this step could not establish.

Every check writes its own verdict plus the exact command and output it came
from, so the whole file can be re-derived by someone who was not present.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Sequence

ROOT = Path(__file__).resolve().parents[1]


def _git_exe() -> str:
    """`git` is not on PATH in every session that runs this; resolve it explicitly."""
    import shutil

    found = shutil.which("git") or shutil.which("git.exe")
    if found:
        return found
    for candidate in (r"C:\Program Files\Git\cmd\git.exe", r"C:\Program Files\Git\bin\git.exe"):
        if Path(candidate).is_file():
            return candidate
    raise RuntimeError("git executable not found; cannot verify tree state")


def _git(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [_git_exe(), *args], cwd=str(ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _declared_files(order_path: Path) -> list[str]:
    """Paths the work order says it will touch, taken from its `**文件**：` lines."""
    if not order_path.is_file():
        return []
    paths = []
    for line in order_path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"\s*(?:-\s*)?\*\*文件\*\*\s*[：:]\s*(.+)", line)
        if not match:
            continue
        for token in re.split(r"[，,、;；]", match.group(1)):
            token = token.strip().strip("`").strip()
            if token and "/" in token or token.endswith((".py", ".md", ".json", ".txt")):
                paths.append(token)
    return paths


def verify(work_order: str, run_dir: Path) -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool | None, detail: str, command: str = "") -> None:
        checks.append({"check": name, "passed": ok, "detail": detail, "command": command})

    done = _load(run_dir / "done.json")
    if done is None:
        add("done_json_readable", False, "done.json missing or unparsable")
        # Same shape as every other return: a caller reading blocking_failures
        # must not get a KeyError just because the run was this badly off.
        return {"work_order": work_order, "verified": False,
                "blocking_failures": ["done_json_readable"], "checks": checks,
                "reason": "no readable done.json"}
    add("done_json_readable", True, f"exit_code={done.get('exit_code')}")

    add("exit_code_zero", done.get("exit_code") == 0, f"exit_code={done.get('exit_code')}")
    add("receipt_valid", done.get("receipt_valid") is True, f"receipt_valid={done.get('receipt_valid')}")

    # The single most dangerous failure this step exists to catch: a receipt that
    # was green on a tree that is no longer the tree we would be tagging.
    base_sha = (done.get("base_sha") or "").strip()
    if not base_sha:
        add("receipt_bound_to_a_commit", False,
            "done.json carries no base_sha; a green receipt with unknown provenance cannot be trusted")
    else:
        head = _git("rev-parse", "HEAD")
        add("head_readable", head.returncode == 0, (head.stdout or head.stderr).strip()[:200],
            "git rev-parse HEAD")
        ancestor = _git("merge-base", "--is-ancestor", base_sha, "HEAD")
        current_sha = (head.stdout or "").strip()
        add("not_stale", ancestor.returncode == 0,
            f"base_sha={base_sha[:12]} still an ancestor of HEAD={current_sha[:12]}"
            if ancestor.returncode == 0
            else f"base_sha={base_sha[:12]} is no longer on HEAD={current_sha[:12]}; the receipt is stale",
            f"git merge-base --is-ancestor {base_sha} HEAD")

    order_path = ROOT / "tasks/queue" / f"{work_order}.md"
    declared = _declared_files(order_path)
    if declared:
        missing = [p for p in declared if not (ROOT / p).exists()]
        add("declared_files_landed", not missing,
            f"{len(declared)} declared, missing={missing}" if missing else f"{len(declared)} declared, all present")
    else:
        add("declared_files_landed", None, "work order declares no file list; not checkable")

    status = _git("status", "--short")
    dirty = [line for line in (status.stdout or "").splitlines() if line.strip()]
    add("worktree_state_recorded", True, f"{len(dirty)} uncommitted entries at verify time")

    blocking_failures = [c["check"] for c in checks if c["passed"] is False]
    verified = not blocking_failures
    return {"work_order": work_order, "verified": verified,
            "blocking_failures": blocking_failures, "checks": checks,
            "head": _git("rev-parse", "HEAD").stdout.strip()}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        payload = verify(args.work_order, Path(args.run_dir))
    except RuntimeError as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    out = Path(args.run_dir) / "verify.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"verified": payload["verified"], "blocking_failures": payload["blocking_failures"],
                      "out": str(out)}, ensure_ascii=False))
    return 0 if payload["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
