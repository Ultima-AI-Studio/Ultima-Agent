"""Freeze a work order by tagging the commit that was actually reviewed.

Two gates, and neither is trusted as a stored boolean:

* The deterministic checks are **re-run here**, in this process, rather than read
  from ``verify.json``. A JSON file that any writer in the same directory can
  produce is a claim, not evidence, and it was possible to hand-write one and
  freeze on it.
* The model review in ``audit.json`` is a **required affirmative**, not merely a
  veto: freezing needs ``audit_passed is True``. Two rounds of one model on one
  evidence set is a quality gate in front of a tag; it is not four-eyes, and it
  should not be described as independent review anywhere.

On top of that, the target is a clean commit:

* the working tree must carry no modified tracked file, so the commit the tag
  points at *is* the delivered content — a tag on a commit whose working tree has
  moved freezes something nobody was reviewing;
* the tag is created *at* the verified commit, read back, and deleted if it does
  not resolve there;
* HEAD, tree, status, card and evidence are read once more immediately before the
  tag is written, so the window between checking and acting is as short as the
  filesystem allows rather than spanning the whole function.
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


def _parse_status_z(raw: str) -> list[dict]:
    """Parse ``git status --porcelain=v1 -z`` into entries.

    NUL-separated output is the only reliable form: line-oriented output renders a
    rename as ``R  old -> new``, which puts the whole expression in the path field
    and leaves the new file unhashed.
    """
    entries, parts, index = [], raw.split("\0"), 0
    while index < len(parts):
        item = parts[index]
        if not item:
            index += 1
            continue
        code, path = item[:2], item[3:]
        if "R" in code or "C" in code:
            origin = parts[index + 1] if index + 1 < len(parts) else ""
            entries.append({"code": code, "path": path, "orig": origin})
            index += 2
        else:
            entries.append({"code": code, "path": path})
            index += 1
    return entries


def _status_entries() -> list[dict] | None:
    """The modified-tracked-file set, in the dispatcher's recorded form."""
    completed = subprocess.run([_git_exe(), "status", "--porcelain=v1", "-z", "--untracked-files=no"],
                               cwd=str(ROOT), capture_output=True, text=True,
                               encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        return None
    return _parse_status_z(completed.stdout or "")


def _load(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, ValueError):
        return None


def _load_verifier():
    """Load verify-order.py as a module so its checks can be re-run here."""
    import importlib.util

    path = Path(__file__).resolve().parent / "verify-order.py"
    spec = importlib.util.spec_from_file_location("gorch_verify_order", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # The checks must run against the same tree this process is freezing, which is
    # this module's ROOT (not whatever the verifier defaults to on import).
    module.ROOT = globals()["ROOT"]
    return module


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
    stored_verify = _load(verify_path)
    if stored_verify is None:
        return _refuse("unreadable verify.json")

    # Re-run the deterministic checks in this process. Reading `verified: true`
    # out of a file that any writer in this directory can produce proves only that
    # a file says so.
    try:
        verifier = _load_verifier()
        live_verify = verifier.verify(args.work_order, run_dir)
    except Exception as exc:                       # noqa: BLE001 - surfaced as a refusal
        return _refuse(f"could not re-run the deterministic checks: {exc}")
    verify = live_verify
    if stored_verify.get("verified") is not True or stored_verify.get("verified") != live_verify.get("verified"):
        return _refuse("verify.json disagrees with a fresh run of the checks; the stored verdict is stale or forged",
                       stored=stored_verify.get("verified"), rerun=live_verify.get("verified"),
                       blocking_failures=live_verify.get("blocking_failures"))
    # The receipt the stored verdict was about must still be the receipt here.
    if stored_verify.get("done_sha256") != live_verify.get("done_sha256"):
        return _refuse("done.json changed after verification; the checked receipt is gone",
                       recorded=(stored_verify.get("done_sha256") or "")[:12],
                       now=(live_verify.get("done_sha256") or "missing")[:12])
    if live_verify.get("verified") is not True:
        return _refuse("deterministic verification did not pass on a fresh run; refusing to freeze",
                       blocking_failures=live_verify.get("blocking_failures"))

    # An artifact that names another order is another order's evidence.
    if str(stored_verify.get("work_order") or "") != args.work_order:
        return _refuse("verify.json was produced for a different work order",
                       found=stored_verify.get("work_order"), expected=args.work_order)

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
    if live_entries is None:
        return _refuse("could not read the working tree status; refusing to freeze on an unknown state")
    if not isinstance(recorded_entries, list):
        return _refuse("verify.json recorded no status set; the tested working state is unidentified")
    if live_entries != recorded_entries:
        added = [e["path"] for e in live_entries if e not in recorded_entries][:10]
        return _refuse("the working tree differs from the set verification saw; the frozen state is untested",
                       newly_differing=added)

    # A tag names a commit. With modified tracked files present, that commit is
    # not the content under review: the tree being checked is still uncommitted,
    # so the freeze would certify something the tag does not contain.
    if live_entries:
        return _refuse("working tree is not clean; the tag would name a commit that is not the delivered content",
                       modified=[e["path"] for e in live_entries][:10])

    # The audit graded specific bytes. If the card or an evidence file changed
    # afterwards, the verdict describes material that is no longer here. Missing
    # metadata is a refusal, not a skip: an audit that did not record what it read
    # gives nothing to hold on to.
    artifact_issues = []
    card_path = str(audit.get("card") or "").strip()
    card_meta = audit.get("card_meta") or {}
    if not card_path:
        return _refuse("audit.json names no card; the reviewed material is unidentified")
    if not card_meta.get("sha256"):
        return _refuse("audit.json recorded no card hash; the card it read cannot be identified", card=card_path)
    current = _sha256_file(Path(card_path))
    if current != card_meta["sha256"]:
        return _refuse("the card changed after the audit; the verdict no longer describes it",
                       card=card_path, recorded=card_meta["sha256"][:12], now=(current or "missing")[:12])

    evidence_meta = audit.get("evidence_meta") or []
    if not evidence_meta:
        return _refuse("audit.json recorded no evidence hashes; the material it reviewed cannot be identified")
    audited = [str(m.get("path") or "").strip() for m in evidence_meta]
    named = [str(p) for p in (audit.get("evidence") or [])]
    if not audited or any(not p for p in audited):
        return _refuse("audit.json lists evidence without a path; the reviewed set is incomplete")
    if sorted(audited) != sorted(named):
        return _refuse("audit.json evidence list and evidence_meta disagree on what was read",
                       listed=len(named), hashed=len(audited))
    for meta in evidence_meta:
        path = str(meta.get("path") or "").strip()
        if not meta.get("sha256"):
            return _refuse("audit.json has an evidence entry with no hash", evidence=path)
        now = _sha256_file(Path(path))
        if now != meta["sha256"]:
            return _refuse("audited evidence changed after the audit; the verdict no longer describes it",
                           evidence=path, recorded=meta["sha256"][:12], now=(now or "missing")[:12])

    # Truncated material cannot have been read in full, and an audit that ran on
    # a partial view is the kind of pass this whole step exists to prevent.
    if audit.get("incomplete_inputs"):
        return _refuse("the audit ran on truncated material; its verdict does not cover the whole artifact",
                       incomplete=audit["incomplete_inputs"][:10])

    stamp = datetime.now().strftime("%Y%m%d")
    tag = f"{args.work_order}-freeze-{stamp}"
    message = args.message.strip() or f"{args.work_order} frozen: verified + audited at {verified_head[:12]}"

    try:
        # Read the state once more immediately before writing the ref. The checks
        # above took a dozen filesystem reads; anything that moved during them
        # would otherwise be frozen under a verdict about a different state.
        head_again = _git("rev-parse", "HEAD")
        tree_again = _tree_oid()
        entries_again = _status_entries()
        if head_again != verified_head or tree_again != tree_now or entries_again != live_entries:
            return _refuse("state moved while the checks were running; nothing was frozen",
                           head=(head_again or "")[:12], tree=(tree_again or "")[:12],
                           entries=len(entries_again or []))

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
