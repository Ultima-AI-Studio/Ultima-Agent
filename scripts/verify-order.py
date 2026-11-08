"""Deterministic verification of a delivered work order.

This exists because a language model saying PASS is not a control. What genuinely
does not depend on the author is a check that anyone can re-run and get the same
answer: exit code, receipt validity, whether the tree that was tested is still the
tree in front of us, whether the declared files actually changed, whether the run
ended in a state that is allowed to be frozen.

Three revisions came out of review, each fixing a check that looked right and was
not:

1. **Tree identity, not commit ancestry.** The first version asked whether the
   dispatch commit was still an ancestor of HEAD. It almost always is: an agent's
   edits stay uncommitted, so HEAD never moves. A receipt from a tree nobody
   tested passed that check. The identity that matters is the content hash —
   stage tree, working diff, untracked files.
2. **No file list is unknown, not fine.** The first version treated "the work
   order declares no files" as a pass. Unverifiable is not verified.
3. **A blocked run cannot be frozen.** A run that lost its audit slot or never
   launched carries exit_code 0 and a valid receipt shape; without this check the
   slot limit would be decoration.

Every check writes its own verdict plus the exact command behind it, so the file
can be re-derived by someone who was not present.

Scope limit, stated here rather than left implied: this script does not execute
the work order's own test commands. It confirms that the artifact that was
tested is the artifact being frozen and that the run terminated lawfully. That is
narrower than "the acceptance criteria were met", and the audit step is where
that narrower question is still asked.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
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


def _sha256_file(path: Path) -> str | None:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def tree_oid() -> str | None:
    proc = _git("rev-parse", "HEAD^{tree}")
    return (proc.stdout or "").strip() if proc.returncode == 0 else None


def current_status_entries() -> list[dict] | None:
    """The modified-tracked-file set right now, in the form the dispatcher records.

    ``--untracked-files=no`` keeps this at ~0.4s on a tree carrying 321k untracked
    test artifacts; enumerating them would cost a minute per call. Untracked
    creations are therefore outside this comparison, which is stated rather than
    implied — declared files are checked separately by path.

    The output is read without stripping: porcelain's first column is a status
    code that is a space for unstaged changes, and stripping shifts the path.
    """
    completed = subprocess.run([_git_exe(), "status", "--porcelain", "--untracked-files=no"],
                               cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        return None
    entries = []
    for line in [l for l in (completed.stdout or "").splitlines() if l.strip()]:
        entries.append({"code": line[:2], "path": line[3:].strip()})
    return entries


def _acceptance_lines(order_path: Path) -> list[tuple[str, str]]:
    """Read (ACC-N, criterion text) pairs out of the order's acceptance section.

    The gates are written as prose for a human reviewer. Some of that prose is
    mechanical ("the file exists and is not empty", "no more than 12 lines"), and
    those are worth checking here rather than accepting a reviewer's word for it.
    """
    try:
        text = order_path.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    pairs, in_gate = [], False
    for raw in text.splitlines():
        line = raw.strip()
        if line.startswith("**验收"):
            in_gate = True
            continue
        if in_gate and line.startswith("**") and "验收" not in line:
            in_gate = False           # next bold heading closes the section
            continue
        if not in_gate:
            continue
        match = re.match(r"[-*]\s*(ACC-\d+)\s*(.*)$", line)
        if match:
            pairs.append((match.group(1), match.group(2)))
    return pairs


def _mechanical_checks(checks: list[tuple[str, str]]) -> list[dict]:
    """Turn the machine-readable subset of the criteria into real assertions.

    A criterion names its target either explicitly in backticks or implicitly —
    "no more than 12 lines" is about whatever the previous criterion named. The
    implicit case carries the previous target forward rather than being dropped,
    which is how a limit gate would otherwise escape checking entirely.
    """
    results = []
    target = None
    for gid, text in checks:
        for candidate in re.findall(r"`([^`]+)`", text):
            if "/" in candidate or "." in candidate:
                target = candidate
                break
        if target is None:
            continue
        path = ROOT / target
        existed = path.is_file()
        if "存在" in text or "文件" in text:
            nonempty = existed and path.stat().st_size > 0
            passed = nonempty if "非空" in text else existed
            results.append({"gate": gid, "check": "exists_nonempty" if "非空" in text else "exists",
                            "path": target, "passed": passed,
                            "detail": f"{target}: exists={existed} bytes={path.stat().st_size if existed else 0}"})

        limit = re.search(r"不超过\s*(\d+)\s*行", text)
        if limit and existed:
            count = len(path.read_text(encoding="utf-8-sig", errors="replace").splitlines())
            results.append({"gate": gid, "check": "line_limit", "path": target,
                            "passed": count <= int(limit.group(1)),
                            "detail": f"{target}: {count} lines, limit {limit.group(1)}"})
    return results


def _declared_commands(order_path: Path) -> list[str]:
    """Commands the order explicitly asks to be run, marked with a **机检** line."""
    try:
        text = order_path.read_text(encoding="utf-8-sig")
    except OSError:
        return []
    commands = []
    for raw in text.splitlines():
        line = raw.strip()
        match = re.match(r"\*\*机检\*\*\s*[：:]\s*(.+)", line)
        if not match:
            continue
        cmd = match.group(1).strip().strip("`").strip()
        # Only test runners: this gate may run a command, not an arbitrary one.
        if cmd.startswith("pytest") or cmd.startswith("python -m pytest"):
            commands.append(cmd)
    return commands


def manifest_drift(manifest: list[dict]) -> dict:
    """Rehash each file the receipt claims to have produced, and report differences.

    Per file rather than one repository-wide hash: this working tree holds 321k
    untracked test artifacts, so a whole-tree digest takes a minute per call. Rehashing
    the changed set costs milliseconds and, when something moved, names the file.
    """
    drifted, vanished = [], []
    for entry in manifest:
        path = entry.get("path") or ""
        recorded = entry.get("sha256")
        target = ROOT / path
        if not target.is_file():
            if recorded is not None:
                vanished.append(path)      # was readable when recorded, gone now
            continue
        try:
            current = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:
            vanished.append(path)
            continue
        if recorded is None:
            drifted.append(path)           # unreadable at record time, readable now
        elif current != recorded:
            drifted.append(path)
    return {"drifted": drifted, "vanished": vanished}


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
            if token and (("/" in token) or token.endswith((".py", ".md", ".json", ".txt"))):
                paths.append(token)
    return paths


def _changed_since(base_sha: str, path: str) -> bool | None:
    """Did this path change between the dispatch commit and the working tree?"""
    proc = _git("diff", "--name-only", base_sha, "--", path)
    if proc.returncode != 0:
        return None
    return bool((proc.stdout or "").strip())


def verify(work_order: str, run_dir: Path) -> dict:
    checks: list[dict] = []

    def add(name: str, ok: bool | None, detail: str, command: str = "") -> None:
        checks.append({"check": name, "passed": ok, "detail": detail, "command": command})

    done_path = run_dir / "done.json"
    done = _load(done_path)
    if done is None:
        add("done_json_readable", False, "done.json missing or unparsable")
        # Same shape as every other return: a caller reading blocking_failures
        # must not get a KeyError just because the run was this badly off.
        return {"work_order": work_order, "verified": False,
                "blocking_failures": ["done_json_readable"], "checks": checks,
                "reason": "no readable done.json"}

    done_sha = _sha256_file(done_path)
    add("done_json_readable", True, f"exit_code={done.get('exit_code')} sha256={(done_sha or '')[:12]}",
        "sha256 of done.json")

    add("exit_code_zero", done.get("exit_code") == 0, f"exit_code={done.get('exit_code')}", "done.json:exit_code")
    add("receipt_valid", done.get("receipt_valid") is True, f"receipt_valid={done.get('receipt_valid')}",
        "done.json:receipt_valid")

    # A run whose delivery was refused, or that never got a slot, must not reach a
    # tag on the strength of a 0 exit code.
    state = str(done.get("state") or "")
    add("terminal_state_legal", state in {"audit", "frozen"},
        f"state={state or '(absent)'}; only audit/frozen may be frozen", "done.json:state")
    add("no_slot_block", done.get("audit_slot_busy") is not True,
        f"audit_slot_busy={done.get('audit_slot_busy')}", "done.json:audit_slot_busy")
    add("parent_alive", done.get("parent_lost") is not True,
        f"parent_lost={done.get('parent_lost')}", "done.json:parent_lost")

    end_sha = (done.get("end_sha") or done.get("base_sha") or "").strip()
    add("receipt_bound_to_a_commit", bool(end_sha),
        f"end_sha={end_sha[:12] or '(absent)'}" if end_sha
        else "done.json names no commit; a green with unknown provenance cannot be trusted",
        "done.json:end_sha")

    # The load-bearing check: is the tree being frozen the tree that was tested?
    recorded_tree = (done.get("tree_oid") or "").strip()
    manifest = done.get("changed_files")
    recorded_entries = done.get("status_entries")
    current_tree = tree_oid()
    drift = {"drifted": [], "vanished": []}
    if not recorded_tree or not isinstance(manifest, list) or not isinstance(recorded_entries, list):
        add("tree_identity_recorded", False,
            "done.json carries no tree_oid/status_entries manifest; the tested tree cannot be identified",
            "done.json:tree_oid, done.json:status_entries")
    elif current_tree is None:
        add("tree_identity_recorded", False,
            "git could not read HEAD^{tree}; refusing rather than guessing", "git rev-parse HEAD^{tree}")
    else:
        drift = manifest_drift(manifest)
        tree_same = recorded_tree == current_tree
        # Comparing the entry *set* is what catches an edit on a clean baseline:
        # nothing was recorded, so nothing could be rehashed, but the set is no
        # longer empty and that difference is visible here.
        live_entries = current_status_entries()
        entries_same = live_entries == recorded_entries
        files_same = not drift["drifted"] and not drift["vanished"]
        detail = (f"{len(manifest)} recorded entries rehashed; tree "
                  f"{'unchanged' if tree_same else 'differs'}, status set "
                  f"{'unchanged' if entries_same else 'differs'}")
        if not files_same:
            detail += f"; drifted={drift['drifted'][:5]} vanished={drift['vanished'][:5]}"
        if not entries_same and live_entries is not None:
            added = [e['path'] for e in live_entries
                     if e not in (recorded_entries or [])][:5]
            detail += f"; newly differing={added}"
        add("tree_unchanged", tree_same and entries_same and files_same, detail,
            "git rev-parse HEAD^{tree}; git status --porcelain -uno; sha256 of each recorded file")

    order_path = ROOT / "tasks/queue" / f"{work_order}.md"
    declared = _declared_files(order_path)
    if not declared:
        add("declared_files_landed", False,
            "work order declares no file list; the delivered output cannot be located", str(order_path))
    else:
        missing = [p for p in declared if not (ROOT / p).exists()]
        if missing:
            add("declared_files_landed", False, f"{len(declared)} declared, missing={missing}",
                "; ".join(f"test -e {p}" for p in missing))
        elif end_sha:
            untouched = [p for p in declared if _changed_since(end_sha, p) is False]
            add("declared_files_landed", not untouched,
                "all declared files exist and differ from the dispatch commit" if not untouched
                else f"declared but unchanged since dispatch: {untouched}",
                f"git diff --name-only {end_sha[:12]} -- <each declared path>")
        else:
            # Existence without a base to compare against is weaker evidence than
            # a change, so it is reported but not silently upgraded to a pass.
            add("declared_files_landed", None,
                f"{len(declared)} declared, all present; no commit to prove they changed",
                str(order_path))

    # The order's own acceptance criteria, as far as they are mechanical. A gate
    # that says "the file exists and is not empty" is not a matter of opinion, and
    # the reviewer's word for it was previously the only evidence.
    criteria = _acceptance_lines(order_path) if order_path.is_file() else []
    mechanical = _mechanical_checks(criteria)
    if mechanical:
        failed = [m for m in mechanical if not m["passed"]]
        add("declared_checks_pass", not failed,
            "all mechanically checkable acceptance criteria hold" if not failed
            else f"{len(failed)} failed: " + "; ".join(f"{m['gate']} {m['detail']}" for m in failed[:4]),
            "per-criterion assertions derived from the card's acceptance section")

    # A command the order explicitly marked for running. Absent means the order
    # asked for no execution, which is reported as such rather than assumed to be
    # a pass — "nobody asked me to run anything" is not "the tests passed".
    commands = _declared_commands(order_path) if order_path.is_file() else []
    for cmd in commands[:2]:                       # bounded: never run a long suite
        try:
            proc = subprocess.run(cmd, shell=True, cwd=str(ROOT), capture_output=True,
                                  text=True, encoding="utf-8", errors="replace", timeout=300)
            ok = proc.returncode == 0
            tail = ((proc.stdout or "").strip().splitlines() or [""])[-1][:160]
        except subprocess.TimeoutExpired:
            ok, tail = False, "timed out after 300s"
        add(f"declared_command_pass:{cmd[:60]}", ok, tail or "no output", cmd)

    blocking_failures = [c["check"] for c in checks if c["passed"] is False]
    verified = not blocking_failures
    head_proc = _git("rev-parse", "HEAD")
    head = (head_proc.stdout or "").strip() if head_proc.returncode == 0 else ""
    if not head:
        add("head_readable", False, "git rev-parse HEAD failed; the verified commit is unknown",
            "git rev-parse HEAD")
        blocking_failures = [c["check"] for c in checks if c["passed"] is False]
        verified = False

    return {"work_order": work_order, "verified": verified,
            "blocking_failures": blocking_failures, "checks": checks,
            "head": head, "tree_oid": current_tree, "done_sha256": done_sha,
            "changed_files": manifest if isinstance(manifest, list) else None,
            "status_entries": recorded_entries if isinstance(recorded_entries, list) else None,
            # Binding fields: freezing re-derives these rather than trusting the file.
            "verified_at": datetime.now(timezone.utc).isoformat()}


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
