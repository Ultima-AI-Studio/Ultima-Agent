"""Freeze a work order by tagging it, but only when the evidence still holds.

Two gates, with deliberately different powers:

* ``verify.json`` carries the **authority**. Deterministic checks — exit code,
  receipt validity, whether the tested tree is still the tree here, whether the
  declared files actually changed. Anyone can re-run them and get the same answer.
* ``audit.json`` carries a **veto**. Model judgement can stop what the checks
  allowed; it cannot authorize what the checks refused.

Both are required. Nothing here trusts a stored boolean on its own:

* the artifacts must name the same work order as this command, so one order's
  pass cannot be replayed onto another;
* ``done.json`` must still hash to what verification recorded, so the receipt
  cannot be swapped after it was checked;
* the tree digest is recomputed, so edits made between verify and freeze are
  caught;
* the tag is created *at* the verified commit rather than at whatever HEAD is at
  that instant, and the resulting tag is read back to confirm it.
"""

from __future__ import annotations

import argparse
import hashlib
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


def _status_entries() -> list[dict] | None:
    """The modified-tracked-file set, in the dispatcher's recorded form.

    Read without stripping: porcelain's first column is a status code that is a
    space for unstaged changes, and stripping shifts each path by one character.
    """
    completed = subprocess.run([_git_exe(), "status", "--porcelain", "--untracked-files=no"],
                               cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        return None
    return [{"code": line[:2], "path": line[3:].strip()}
            for line in (completed.stdout or "").splitlines() if line.strip()]


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


def _tree_oid() -> str | None:
    try:
        return _git("rev-parse", "HEAD^{tree}")
    except RuntimeError:
        return None


def _manifest_drift(manifest: list[dict]) -> dict:
    """Rehash each file verification recorded, independently of verify-order.py."""
    drifted, vanished = [], []
    for entry in manifest:
        path = entry.get("path") or ""
        recorded = entry.get("sha256")
        target = ROOT / path
        if not target.is_file():
            if recorded is not None:
                vanished.append(path)
            continue
        try:
            current = hashlib.sha256(target.read_bytes()).hexdigest()
        except OSError:
            vanished.append(path)
            continue
        if recorded is None or current != recorded:
            drifted.append(path)
    return {"drifted": drifted, "vanished": vanished}


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

    # An artifact that names another order is another order's evidence.
    if str(verify.get("work_order") or "") != args.work_order:
        return _refuse("verify.json was produced for a different work order",
                       found=verify.get("work_order"), expected=args.work_order)
    if verify.get("verified") is not True:
        return _refuse("deterministic verification did not pass; refusing to freeze",
                       blocking_failures=verify.get("blocking_failures"))

    # The receipt cannot be swapped after it was checked.
    done_sha = _sha256_file(run_dir / "done.json")
    if not verify.get("done_sha256"):
        return _refuse("verify.json recorded no done.json hash; the receipt is unbound")
    if done_sha != verify.get("done_sha256"):
        return _refuse("done.json changed after verification; the checked receipt is gone",
                       recorded=(verify.get("done_sha256") or "")[:12], now=(done_sha or "missing")[:12])

    audit_path = run_dir / "audit.json"
    if not audit_path.is_file():
        return _refuse("no audit.json; audit must run before freezing")
    audit = _load(audit_path)
    if audit is None:
        return _refuse("unreadable audit.json")
    if str(audit.get("work_order") or "") != args.work_order:
        return _refuse("audit.json was produced for a different work order",
                       found=audit.get("work_order"), expected=args.work_order)
    if audit.get("audit_passed") is not True:
        return _refuse("audit_passed is not true; refusing to freeze")

    verified_head = str(verify.get("head") or "").strip()
    if not verified_head:
        return _refuse("verify.json carries no commit; there is nothing to tag against")

    try:
        head_now = _git("rev-parse", "HEAD")
        if head_now != verified_head:
            return _refuse("HEAD moved since verification; the verified commit is not the current one",
                           verified_head=verified_head[:12], head_now=head_now[:12])
        tree_now = _tree_oid()
    except RuntimeError as exc:
        return _refuse(str(exc))

    recorded_tree = str(verify.get("tree_oid") or "").strip()
    manifest = verify.get("changed_files")
    if not recorded_tree or not isinstance(manifest, list):
        return _refuse("verify.json recorded no tree identity; the frozen content is unidentified")
    if tree_now != recorded_tree:
        return _refuse("tree content changed after verification; refusing to tag a tree nobody checked",
                       recorded=recorded_tree[:12], now=(tree_now or "unreadable")[:12])
    drift = _manifest_drift(manifest)
    if drift["drifted"] or drift["vanished"]:
        return _refuse("files changed after verification; the checked artifact is gone",
                       drifted=drift["drifted"][:10], vanished=drift["vanished"][:10])

    recorded_entries = verify.get("status_entries")
    live_entries = _status_entries()
    if isinstance(recorded_entries, list) and live_entries is not None and live_entries != recorded_entries:
        added = [e["path"] for e in live_entries if e not in recorded_entries][:10]
        return _refuse("the working tree differs from the set verification saw; the frozen state is untested",
                       newly_differing=added)

    # The audit graded specific bytes. If the card or an evidence file changed
    # afterwards, the verdict describes material that is no longer here.
    artifact_issues = []
    card_path = str(audit.get("card") or "").strip()
    card_meta = audit.get("card_meta") or {}
    if card_path and card_meta.get("sha256"):
        current = _sha256_file(Path(card_path))
        if current != card_meta["sha256"]:
            artifact_issues.append({"artifact": card_path, "kind": "card",
                                    "recorded": card_meta["sha256"][:12], "now": (current or "missing")[:12]})
    for meta in (audit.get("evidence_meta") or []):
        path = str(meta.get("path") or "").strip()
        if not path or not meta.get("sha256"):
            continue
        current = _sha256_file(Path(path))
        if current != meta["sha256"]:
            artifact_issues.append({"artifact": path, "kind": "evidence",
                                    "recorded": meta["sha256"][:12], "now": (current or "missing")[:12]})
    if artifact_issues:
        return _refuse("audited material changed after the audit; the verdict no longer describes it",
                       artifacts=artifact_issues[:10])

    # Truncated material cannot have been read in full, and an audit that ran on
    # a partial view is the kind of pass this whole step exists to prevent.
    if audit.get("incomplete_inputs"):
        return _refuse("the audit ran on truncated material; its verdict does not cover the whole artifact",
                       incomplete=audit["incomplete_inputs"][:10])

    stamp = datetime.now().strftime("%Y%m%d")
    tag = f"{args.work_order}-freeze-{stamp}"
    message = args.message.strip() or f"{args.work_order} frozen: verified + audited at {verified_head[:12]}"

    try:
        # Tag the commit that was verified, not whatever HEAD happens to be.
        _git("tag", "-a", tag, verified_head, "-m", message)
        tagged = _git("rev-parse", f"{tag}^{{}}")
        if tagged != verified_head:
            _git("tag", "-d", tag)
            return _refuse("the tag resolved to a different commit; tag removed",
                           tagged=tagged[:12], expected=verified_head[:12])
        if args.push:
            _git("push", "origin", tag)
    except RuntimeError as exc:
        return _refuse(str(exc))

    print(json.dumps({"frozen": True, "tag": tag, "pushed": bool(args.push),
                      "head": verified_head, "tree_oid": tree_now}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
