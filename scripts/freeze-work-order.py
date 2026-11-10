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
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]

# Both tables this gate reads — the order's card list and the card's acceptance
# list — are parsed by ``gorch_contract``, the same code the dispatcher and the
# audit use. A second parser here meant the four scripts could disagree about
# which rows exist, and a row one of them skipped was never reported as missing.
sys.path.insert(0, str(ROOT / "scripts"))
from gorch_contract import acc_rows, gate_waivers, order_cards as contract_order_cards   # noqa: E402
from order_naming import resolve_card_path  # noqa: E402


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


def _audit_inconsistencies(audit: dict) -> list[str]:
    """Reasons the recorded two-round result is not actually a pass.

    Trusting the top-level boolean let a fully forged audit through, and worse: an
    audit whose every round said FAIL could still freeze as long as someone left
    ``audit_passed: true`` beside it. The rounds are recomputed here instead of
    believed.
    """
    problems: list[str] = []
    for key in ("round1", "round2"):
        round_ = audit.get(key)
        if not isinstance(round_, dict):
            problems.append(f"{key} is not an object")
            continue
        if round_.get("passed") is not True:
            problems.append(f"{key}.passed={round_.get('passed')!r}")
        per_gate = round_.get("per_gate")
        if not isinstance(per_gate, dict) or not per_gate:
            problems.append(f"{key}.per_gate missing")
        else:
            not_pass = [g for g, v in per_gate.items() if str(v).upper() != "PASS"]
            if not_pass:
                problems.append(f"{key}.per_gate not all PASS: {not_pass[:5]}")
        overall = str(round_.get("overall") or "").upper()
        if overall != "PASS":
            problems.append(f"{key}.overall={round_.get('overall')!r}")
        if not str(round_.get("model") or "").strip():
            problems.append(f"{key}.model missing")
    if audit.get("audit_passed") is not True:
        problems.append("audit_passed is not true")
    return problems


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
    receipt = _load(run_dir / "done.json") or {}
    if str(audit.get("work_order") or "") != args.work_order:
        return _refuse("audit.json was produced for a different work order",
                       found=audit.get("work_order"), expected=args.work_order)

    # The verdict must belong to this run and to these exact artifacts. Without the
    # three bindings below, a passing audit recorded in one run directory can be
    # copied into another, or replayed after a fresh verification rewrote the
    # receipt — the audit would then certify content nobody judged.
    if str(audit.get("run_id") or "") != run_dir.name:
        return _refuse("audit.json was produced in a different run directory",
                       found=audit.get("run_id"), expected=run_dir.name)
    verify_sha = _sha256_file(run_dir / "verify.json")
    if not audit.get("verify_sha256") or audit.get("verify_sha256") != verify_sha:
        return _refuse("audit.json does not match this verify.json; the judged result is not the frozen one",
                       recorded=(audit.get("verify_sha256") or "missing")[:12],
                       now=(verify_sha or "missing")[:12])
    if not audit.get("done_sha256") or audit.get("done_sha256") != done_sha:
        return _refuse("audit.json does not match this done.json; the judged receipt is not the frozen one",
                       recorded=(audit.get("done_sha256") or "missing")[:12],
                       now=(done_sha or "missing")[:12])
    if not audit.get("round1") or not audit.get("round2"):
        return _refuse("audit.json records no two-round result; a bare audit_passed flag is not a review")

    if audit.get("audit_passed") is not True:
        return _refuse("audit_passed is not true; refusing to freeze")

    # The rounds must agree with the boolean, not merely accompany it.
    problems = _audit_inconsistencies(audit)
    if problems:
        return _refuse("audit.json is internally inconsistent; a top-level pass cannot "
                       "override what the rounds recorded", problems=problems[:8])

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

    # The card must be the one this order was dispatched on. Otherwise freeze can be
    # handed any weaker card that happens to be internally consistent with its own
    # audit, and the tag would faithfully preserve the wrong input.
    dispatched_card = str(receipt.get("card_sha256") or "").strip()
    if not dispatched_card:
        return _refuse("done.json records no card_sha256; the reviewed card cannot be "
                       "tied to the one the order dispatched on", card=card_path)
    if dispatched_card != card_meta["sha256"]:
        return _refuse("the card handed to freeze is not the card this order dispatched on",
                       dispatched=dispatched_card[:12], supplied=card_meta["sha256"][:12])

    try:
        card_text = Path(card_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return _refuse(f"could not read the card to enumerate its gates: {exc}")

    # The audit must judge every gate the card declares, not the subset it chose to
    # report. Dropping ACC-2..ACC-5 while leaving ACC-1 PASS kept every recorded
    # value internally consistent and still frozen. The table is read by the same
    # parser the audit uses (``| ACC-n | criterion | how |``), so a card that
    # mentions a gate in prose — "范围：不做 ACC-4" — is not counted as one the audit
    # owes a verdict on, while a malformed acceptance row is refused rather than
    # skipped by one script and read by the other.
    try:
        gate_rows = acc_rows(card_text)
    except ValueError as exc:
        return _refuse(f"the card's acceptance table cannot be read: {exc}")
    gate_ids = {row["id"] for row in gate_rows}
    declared_gates = set(str(k) for k in (audit.get("gates") or {}))
    r1 = set(str(k) for k in ((audit.get("round1") or {}).get("per_gate") or {}))
    r2 = set(str(k) for k in ((audit.get("round2") or {}).get("per_gate") or {}))
    if gate_ids and (declared_gates != gate_ids or r1 != gate_ids or r2 != gate_ids):
        return _refuse("audit did not judge every gate the card declares",
                       card=sorted(gate_ids), gates=sorted(declared_gates),
                       round1=sorted(r1), round2=sorted(r2))
    # 空表不再从这里滑过去。这一行原来写作 `if gate_ids and (...)`，于是一张没有
    # ACC 门的卡根本不进比较：任何一份旧回执都能把"谁都没判过"冻成 tag。空表的
    # 判定要等 receipt 与 order 的绑定确认之后（下面的 empty-gates 分支），因为
    # 只有那时候才知道这张卡的 id、也才能读到工单自己的 manifest。

    # Binding only the first card left the rest of a multi-card order free to change.
    # Every card the dispatch recorded has to be the one that is here now — and the
    # record has to name every card the order references, not a subset of it. An
    # empty or missing list used to skip the loop entirely, so an old receipt passed.
    receipt_cards = receipt.get("cards") or []
    if not receipt_cards:
        return _refuse("done.json records no dispatched cards; a multi-card order "
                       "cannot be verified from a receipt that names none")
    order_cards = []
    try:
        order_file = resolve_card_path(args.work_order, Path(ROOT) / "tasks" / "queue")
        order_text = order_file.read_text(encoding="utf-8-sig")
        order_cards = sorted(contract_order_cards(order_text))
    except (OSError, UnicodeError) as exc:
        return _refuse(f"could not read the order to enumerate its cards: {exc}")
    except ValueError as exc:
        return _refuse(f"the order card cannot be resolved or read: {exc}")
    recorded_ids = []
    recorded = {}
    cards_root = (Path(ROOT) / "tasks" / "cards").resolve()
    for rec in receipt_cards:
        path = Path(str(rec.get("path") or ""))
        try:
            key = path.resolve().relative_to(cards_root).parts[0]
        except (ValueError, IndexError):
            return _refuse("a dispatched card sits outside tasks/cards; its id cannot be "
                           "tied to the one the order names", path=str(path))
        if key in recorded:
            return _refuse("the receipt lists the same card more than once", card=key)
        # The path has to be the canonical one. Comparing directory names alone let
        # any file that happened to sit in a directory called <id> stand in for the
        # card, and the hash was then taken from that path rather than from the card.
        if path.resolve() != (cards_root / key / "task.md"):
            return _refuse("a dispatched card is not at tasks/cards/<id>/task.md",
                           card=key, path=str(path))
        recorded[key] = rec
        recorded_ids.append(key)
    recorded_ids.sort()
    if not order_cards:
        return _refuse("the order references no card; nothing ties the run to an artifact")
    if len(receipt_cards) != 1:
        # Audit reviews one card, so a freeze over several would only have hashed them.
        # Until every card's gates are audited, this gate refuses the order instead of
        # signing off gates nobody read.
        return _refuse("this gate audits a single card; the order dispatched more",
                       dispatched=len(receipt_cards))
    if recorded_ids != order_cards:
        return _refuse("the receipt does not name every card the order references",
                       order=order_cards, receipt=recorded_ids)

    # 空 ACC 门表：只有工单为这张卡声明的 waiver 能顶替一次"每门必审"。
    # 没有 waiver 就在这里拒绝 —— 而不是让上面的集合比较被整段短路掉。
    if not gate_ids:
        try:
            waivers = gate_waivers(order_text)
        except ValueError as exc:
            return _refuse(f"the order's manifest cannot be read: {exc}")
        card_id = recorded_ids[0]
        matching = [w for w in waivers if w["card"] == card_id]
        if not matching:
            return _refuse(
                "the card lists no ACC gates and the order declares no waiver; "
                "there is no gate and nothing standing in for one", card=card_id)
        if len(matching) > 1:
            return _refuse(
                f"the order declares {len(matching)} waivers for card {card_id}; "
                "one card takes one", card=card_id)
        waiver = matching[0]
        expected = {f"WAIVER:{card_id}"}
        if declared_gates != expected or r1 != expected or r2 != expected:
            return _refuse(
                "the card has no ACC gates, so the waiver is the only auditable key; "
                "both rounds have to judge exactly it",
                card=card_id, expected=sorted(expected), gates=sorted(declared_gates),
                round1=sorted(r1), round2=sorted(r2))
        # 替代判据本身要有一份真实执行记录，不能只凭格式合法。verifier 回执里的
        # 每项 check 都带它实际跑过的命令；这条 waiver 的目标必须出现在其中，且
        # 那项 check 判过。目录目标（`tests`）同样按这条办，不额外放宽。
        target = waiver["instead"].replace("\\", "/")
        hit = [c for c in (verify.get("checks") or [])
               if target in str(c.get("command") or "").replace("\\", "/")]
        if not hit:
            return _refuse(
                "the waiver's instead target appears in no verifier check; "
                "a substitute that was never run proves nothing",
                card=card_id, instead=waiver["instead"])
        if any(c.get("passed") is not True for c in hit):
            return _refuse(
                "the verifier check running the waiver's instead target did not pass",
                card=card_id, instead=waiver["instead"],
                failed=[c.get("check") for c in hit if c.get("passed") is not True])

    changed_cards = []
    for cid in order_cards:
        path = cards_root / cid / "task.md"
        now = _sha256_file(path) if path.is_file() else None
        if now != recorded[cid].get("sha256"):
            changed_cards.append(cid)
    if changed_cards:
        return _refuse("a card the order referenced changed after dispatch",
                       changed=changed_cards[:8])

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
    headline = args.message.strip() or f"{args.work_order} frozen: verified + audited at {verified_head[:12]}"

    # The tag carries its own receipt. A hash recorded in a JSON file that lives in
    # a run directory proves nothing once that directory is cleaned up, and card and
    # evidence are generally outside the commit being tagged. Writing the reviewed
    # material into the tag message makes the freeze reconstructable from the tag
    # alone.
    try:
        if not card_text:
            card_text = Path(card_path).read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        return _refuse(f"could not read the card for the tag receipt: {exc}")
    receipt = [
        headline, "",
        "── freeze receipt ──",
        f"work_order: {args.work_order}",
        f"run_id: {run_dir.name}",
        f"head: {verified_head}",
        f"tree_oid: {tree_now}",
        f"verify_sha256: {verify_sha}",
        f"done_sha256: {done_sha}",
        f"audit_sha256: {_sha256_file(audit_path)}",
        f"audit_rounds: {audit['round1'].get('overall')} / {audit['round2'].get('overall')} "
        f"(model {audit['round1'].get('model')})",
        f"card: {card_path} sha256={card_meta['sha256']}",
        "evidence:",
    ]
    for meta in evidence_meta:
        receipt.append(f"  {meta.get('path')} sha256={meta.get('sha256')} bytes={meta.get('bytes')}")
        # A hash only proves "the same blob, later". The run directory and the ignored
        # evidence tree can both be cleaned up, so the bytes go into the tag too.
        try:
            body = Path(str(meta.get("path"))).read_text(encoding="utf-8-sig")
            receipt += ["  ── body ──", body[:6000]]
        except (OSError, UnicodeError):
            receipt.append("  ── body not readable at freeze time ──")
    receipt += ["", "── cards dispatched ──"]
    for rec in (receipt_cards or []):
        receipt.append(f"  {rec.get('path')} sha256={rec.get('sha256')}")
    receipt += ["", "── card as reviewed ──", card_text]
    message = "\n".join(receipt)

    try:
        # Read the state once more immediately before writing the ref. The checks
        # above took a dozen filesystem reads; anything that moved during them
        # would otherwise be frozen under a verdict about a different state. The
        # audited material is re-read here too, because a card or evidence file
        # swapped after its hash check would leave the tag describing a review of
        # content that is no longer present.
        head_again = _git("rev-parse", "HEAD")
        tree_again = _tree_oid()
        entries_again = _status_entries()
        card_again = _sha256_file(Path(card_path))
        evidence_again = {str(m.get("path") or "").strip(): _sha256_file(Path(m.get("path") or ""))
                          for m in evidence_meta}
        moved = [p for p, h in evidence_again.items() if h != next(
            (m.get("sha256") for m in evidence_meta if str(m.get("path") or "").strip() == p), None)]
        if (head_again != verified_head or tree_again != tree_now or entries_again != live_entries
                or card_again != card_meta["sha256"] or moved):
            return _refuse("state moved while the checks were running; nothing was frozen",
                           head=(head_again or "")[:12], tree=(tree_again or "")[:12],
                           entries=len(entries_again or []), card=(card_again or "missing")[:12],
                           evidence=moved[:5])

        # Tag the commit that was verified, not whatever HEAD happens to be.
        _git("tag", "-a", tag, verified_head, "-m", message)
        tagged = _git("rev-parse", f"{tag}^{{}}")
        if tagged != verified_head:
            _git("tag", "-d", tag)
            return _refuse("the tag resolved to a different commit; tag removed",
                           tagged=tagged[:12], expected=verified_head[:12])
        if args.push:
            # A tag that exists locally but not on the remote is a half-done freeze.
            # Remove it and say so, rather than returning "blocked" while leaving a
            # ref that the next run will find and trust.
            try:
                _git("push", "origin", tag)
            except RuntimeError as exc:
                _git("tag", "-d", tag)
                return _refuse(f"push failed; the local tag was removed so no half-frozen state remains: {exc}")
    except RuntimeError as exc:
        return _refuse(str(exc))

    print(json.dumps({"frozen": True, "tag": tag, "pushed": bool(args.push),
                      "head": verified_head, "tree_oid": tree_now}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
