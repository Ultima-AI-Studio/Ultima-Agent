"""Second-round model review of a delivered work order, judged gate by gate.

Two changes from the first version, both from how maker-checker is actually
practised:

1. **A checklist, not an open brief.** Every reviewer gets the card's gates as a
   numbered list and must return a verdict per gate. Free-form "look for problems"
   produces a different set of findings on every run, so the audit's quality is
   not reproducible; a per-gate checklist makes it comparable and lets a failing
   gate be pointed at directly.
2. **Gates decide, not the closing flourish.** The first version took the final
   'AUDIT: PASS' line as the verdict, so a reviewer that contradicted itself
   mid-report still passed. Now any gate returning FAIL fails the round, whatever
   the summary line says.

What this is not, stated plainly because calling it more would be false: two
rounds of the same model, on the same evidence, under the same identity is not
maker-checker. The independence that control needs — a second party who cannot
approve their own work — does not exist here, so the deterministic checks in
``verify-order.py`` carry the review responsibility and this pass is a second
look at the same material.

It is also not merely advisory, despite what the first version claimed: freezing
requires ``audit_passed is True`` here, so this review is a necessary affirmative
as well as a veto. That is a quality gate in front of a tag, not a four-eyes
control, and it should be described as the former every time it is mentioned.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Sequence

# The acceptance table is parsed in one place (``gorch_contract``), so a row this
# script skips is a row the freeze gate would also skip - or, worse, one each reads
# differently. Importing from the sibling directory keeps a single definition.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gorch_contract import acc_rows, gate_waivers, stage_gates   # noqa: E402
from order_naming import resolve_card_path  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]

# The DeepSeek call is implemented here rather than imported from
# src.brain.orchestrator. Importing that module pulls in its retry stack, which
# made this gate unrunnable anywhere that stack was not installed — a review step
# that fails on an import error reports nothing about the work order. The wire
# format is the same; only the dependency is gone.

DEEPSEEK_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"
# This is a batching threshold, not a truncation or rejection threshold. Objects are
# never sliced: an object larger than the threshold gets its own full-text batch.
OBJECT_BATCH_BYTE_LIMIT = max(1, int(os.environ.get("ULTIMA_AUDIT_BATCH_BYTES", "64000")))


class OrchestratorError(RuntimeError):
    """A model call that did not return a usable answer."""


def _api_key() -> str:
    key = os.environ.get("DEEPSEEK_API_KEY", "").strip()
    if key:
        return key
    env_path = ROOT / "config" / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("DEEPSEEK_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    raise OrchestratorError("DEEPSEEK_API_KEY not found in the environment or config/.env")


def _base_url() -> str:
    base = os.environ.get("DEEPSEEK_API_BASE", "").strip().rstrip("/")
    if base:
        return base + "/chat/completions" if base.endswith("/v1") or "/chat" not in base else base
    env_path = ROOT / "config" / ".env"
    try:
        for line in env_path.read_text(encoding="utf-8-sig").splitlines():
            if line.strip().startswith("DEEPSEEK_API_BASE"):
                value = line.split("=", 1)[1].strip().strip('"').strip("'").rstrip("/")
                return value + "/chat/completions"
    except OSError:
        pass
    return DEEPSEEK_URL


def call_deepseek(system: str, user: str) -> dict:
    """One review round. Returns the response text plus the model that produced it."""
    payload = json.dumps({
        "model": os.environ.get("ULTIMA_AUDIT_MODEL", DEFAULT_MODEL),
        "messages": [{"role": "system", "content": system},
                     {"role": "user", "content": user}],
        "temperature": 0,
    }).encode("utf-8")
    request = urllib.request.Request(
        _base_url(), data=payload, method="POST",
        headers={"Content-Type": "application/json",
                 "Authorization": f"Bearer {_api_key()}"})
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:300]
        raise OrchestratorError(f"DeepSeek HTTP {exc.code}: {detail}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise OrchestratorError(f"DeepSeek unreachable: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise OrchestratorError(f"DeepSeek returned non-JSON: {exc}") from exc
    try:
        usage = body.get("usage") or {}
        # The model field records what actually answered, not what was requested:
        # the endpoint has been observed returning a different model name than the
        # request carried, and an audit that cannot name its reviewer is not an audit.
        return {"response": body["choices"][0]["message"]["content"],
                "model": body.get("model", "unknown"),
                "requested_model": os.environ.get("ULTIMA_AUDIT_MODEL", DEFAULT_MODEL),
                "tokens": usage.get("total_tokens")}
    except (KeyError, IndexError, TypeError) as exc:
        raise OrchestratorError(f"DeepSeek response missing choices: {exc}") from exc


_ROUND1 = (
    "You are the second reviewer, round 1. The deterministic checks have already run and passed; "
    "your job is a second look at material those checks allowed, not a claim of independence - "
    "you share the author's model family and evidence, so review quality here comes from judging "
    "one gate at a time, not from any separation of parties.\n\n"
    "You work in a plain-text environment: NO tools, NO shell, NO file access.\n\n"
    "Judge one gate at a time. For every gate listed below, emit exactly one line in this form:\n"
    "    <gate id>: PASS - <the specific evidence you relied on>\n"
    "    <gate id>: FAIL - <what is missing or wrong, and what evidence would settle it>\n\n"
    "Then, after all gates, emit one line with the overall result.\n"
    "Rules: do not skip a gate; do not pass a gate you have no evidence for - a gate with no "
    "supporting artifact is FAIL, not UNKNOWN; do not restate the gate text as evidence."
)

_ROUND2 = (
    "You are the second reviewer, round 2. You work in a plain-text environment: "
    "NO tools, NO shell, NO file access.\n\n"
    "Round 1's per-gate verdicts are supplied as a prior opinion, not as truth. Re-judge every "
    "gate from the evidence yourself and emit one line per gate in the same form as round 1:\n"
    "    <gate id>: PASS - <evidence>\n"
    "    <gate id>: FAIL - <what is wrong>\n"
    "Where you disagree with round 1, say so on that gate's line. Then emit the overall line."
)


def _decode(data: bytes) -> str:
    """Text for the reviewer, from bytes already read for hashing.

    The reviewer's copy and the recorded digest must come from the same read; two
    reads let a file be swapped in between and the audit would certify content the
    model never saw.
    """
    return data.decode("utf-8-sig", errors="replace")


def _audit_object(path: str | Path, role: str, data: bytes,
                  *, attested_sha256: str | None = None,
                  attested_bytes: int | None = None) -> dict:
    digest = hashlib.sha256(data).hexdigest()
    return {
        "path": str(path),
        "name": Path(path).name,
        "role": role,
        "data": data,
        "text": _decode(data),
        "sha256": digest,
        "bytes": len(data),
        "attested_sha256": attested_sha256 or digest,
        "attested_bytes": len(data) if attested_bytes is None else int(attested_bytes),
    }


def _object_batches(objects: list[dict], limit: int = OBJECT_BATCH_BYTE_LIMIT) -> list[list[dict]]:
    batches: list[list[dict]] = []
    current: list[dict] = []
    current_bytes = 0
    for item in objects:
        size = int(item["bytes"])
        if current and current_bytes + size > limit:
            batches.append(current)
            current, current_bytes = [], 0
        current.append(item)
        current_bytes += size
        if size > limit:
            batches.append(current)
            current, current_bytes = [], 0
    if current:
        batches.append(current)
    return batches


def _coverage(objects: list[dict], batches: list[list[dict]]) -> tuple[list[dict], list[dict], list[dict]]:
    injected = {item["path"]: 0 for item in objects}
    for batch in batches:
        for item in batch:
            injected[item["path"]] += int(item["bytes"])
    incomplete, visible, integrity_errors = [], [], []
    for item in objects:
        record = {
            "path": item["path"],
            "role": item["role"],
            "sha256": item["attested_sha256"],
            "attested_bytes": item["attested_bytes"],
            "injected_bytes": injected[item["path"]],
        }
        if item["sha256"] != item["attested_sha256"]:
            integrity_errors.append({**record, "actual_sha256": item["sha256"]})
        if record["injected_bytes"] < record["attested_bytes"]:
            incomplete.append({**record, "missing_bytes": record["attested_bytes"] - record["injected_bytes"]})
        else:
            visible.append(record)
    return incomplete, visible, integrity_errors


def _batch_prompt(batch: list[dict], index: int, count: int) -> str:
    parts = []
    for item in batch:
        parts.append(
            f"## Object {item['role']}: {item['path']}\n"
            f"sha256={item['attested_sha256']} bytes={item['attested_bytes']}\n"
            f"{item['text']}"
        )
    return f"## Object batch {index}/{count}\n\n" + "\n\n".join(parts)


def _aggregate_round(results: list[dict], gate_ids: list[str]) -> dict:
    per_gate = {
        gate: ("PASS" if all(result["per_gate"].get(gate) == "PASS" for result in results) else "FAIL")
        for gate in gate_ids
    }
    models = {str(result.get("model") or "unknown") for result in results}
    return {
        "passed": bool(results) and all(result["passed"] for result in results),
        "per_gate": per_gate,
        "overall": "PASS" if results and all(result["passed"] for result in results) else "FAIL",
        "model": next(iter(models)) if len(models) == 1 else "mixed",
        "response": "\n\n".join(result["response"] for result in results),
        "tokens": sum(int(result.get("tokens") or 0) for result in results),
        "batches": results,
    }


def _audit_passed(
    round1: dict, round2: dict, incomplete: list[str], integrity_errors: list[str]
) -> bool:
    """Aggregate the two round verdicts without re-grading evidence size."""
    return bool(round1["passed"] and round2["passed"] and not integrity_errors)


def gates(card: str) -> list[dict]:
    """Acceptance gates as (id, criterion, how-to-judge) from the card's table.

    The parsing lives in ``gorch_contract`` so the audit and the freeze gate cannot
    disagree about which rows count. A row that opens with an ACC id but carries no
    criterion, or no method, is a failure rather than a skipped row; duplicate ids
    are fatal, not merged, because two rows numbered ACC-2 give one verdict the power
    to stand in for two different criteria.
    """
    rows = acc_rows(card)
    return rows if rows else stage_gates(card)


def _card_id(card_path: str | Path) -> str:
    """Read the id from either supported canonical card shape."""
    path = Path(card_path)
    if path.name == "task.md" and path.parent.parent.name == "cards":
        return path.parent.name
    if path.suffix == ".md" and path.parent.name == "queue":
        return path.stem
    raise ValueError(
        f"card {path} is not at tasks/cards/<id>/task.md or tasks/queue/*.md; "
        "its id cannot be read")


def _waiver_for(card_path: str | Path, work_order: str) -> dict | None:
    """工单为这张卡声明的唯一一条 waiver，或 None。

    0 条是"没有豁免"；超过 1 条是两份豁免争同一个替代判据，谁都不能作准，直接拒绝。
    """
    card = _card_id(card_path)
    order_file = resolve_card_path(work_order, ROOT / "tasks" / "queue")
    try:
        text = order_file.read_text(encoding="utf-8-sig")
    except (OSError, UnicodeError) as exc:
        raise ValueError(f"could not read the work order for its manifest: {exc}")
    matching = [w for w in gate_waivers(text) if w["card"] == card]
    if len(matching) > 1:
        raise ValueError(
            f"the order declares {len(matching)} waivers for card {card}; one card takes one")
    return matching[0] if matching else None


def per_gate(text: str, gate_ids: list[str]) -> dict[str, str]:
    """Collect verdicts per gate; any FAIL wins, and a contradiction is a FAIL.

    The earlier version kept the *last* verdict for a gate, so a reviewer who wrote
    FAIL and later wrote PASS passed - the opposite of "any non-PASS fails the
    round". Now the worst verdict for a gate stands, and disagreeing with yourself
    is not resolvable by repeating.
    """
    ordered: dict[str, list[str]] = {}
    for line in text.splitlines():
        stripped = line.strip().strip("*_` ")
        # The evidence after the verdict must be non-empty: a bare "ACC-1: PASS"
        # asserts a conclusion without saying what it saw.
        # `Gate T3` and a bare `T3` name the same gate: the stage-gate parser
        # labels queue-card gates `Gate Tn`, while a reviewer answering a queue
        # card writes `T0: FAIL - ...`. Refusing the bare form read a full verdict
        # set back as all-MISSING, which is a parser defect, not a laxer verdict.
        match = re.match(
            r"(ACC-\d+|Gate\s+T\d+|T\d+|WAIVER:[A-Za-z0-9][A-Za-z0-9-]*)\s*[：:]\s*"
            r"(PASS|FAIL)\s*[-—:：]\s*(\S.*)$", stripped, re.IGNORECASE)
        if not match:
            continue
        raw_gate = match.group(1)
        # ACC 门统一大写；waiver key 后面是仓库里的小写卡 id，不能被 upper 改写。
        if raw_gate.upper().startswith("ACC-"):
            gid = raw_gate.upper()
        elif raw_gate.upper().startswith("GATE") or re.fullmatch(r"T\d+", raw_gate.upper()):
            gid = f"Gate T{int(re.search(r'\d+', raw_gate).group())}"
        else:
            gid = "WAIVER:" + raw_gate.split(":", 1)[1].lower()
        ordered.setdefault(gid, []).append(match.group(2).upper())

    result: dict[str, str] = {}
    for gid in gate_ids:
        seen = ordered.get(gid)
        if not seen:
            result[gid] = "MISSING"
        elif "FAIL" in seen:
            result[gid] = "FAIL"
        elif len(set(seen)) > 1:
            result[gid] = "FAIL"
        elif len(seen) != 1:
            # Two PASS lines for one gate is not one verdict: the contract is
            # exactly one per gate, and picking either of them leaves the reader
            # unable to say which one the review stands on.
            result[gid] = "AMBIGUOUS"
        else:
            result[gid] = "PASS"
    return result


def overall(text: str) -> str:
    """The closing verdict, which must be exactly one line and self-consistent.

    Taking the last match let a trailing ``AUDIT: PASS`` erase an earlier
    ``AUDIT: FAIL`` in the same response — the reviewer could state both and the
    second one won. Every exact closing line is collected instead: one is required,
    and a contradiction resolves to CONTRADICTORY rather than to whichever came
    last.
    """
    seen = []
    for line in text.splitlines():
        token = line.strip().strip("*_` ").upper()
        # `Overall: FAIL - ...` carries the same closing verdict as `AUDIT: FAIL`.
        # Requiring the whole line to be exactly `AUDIT: ...` turned a stated
        # verdict with a qualifier into UNKNOWN, which is a parser defect.
        match = re.fullmatch(
            r"(?:AUDIT|OVERALL)\s*[：:]\s*(PASS|FAIL)(?:\s*[-—:：]\s*\S.*)?", token)
        if match:
            seen.append(match.group(1))
    if not seen:
        return "UNKNOWN"
    if len(set(seen)) > 1:
        return "CONTRADICTORY"
    if len(seen) != 1:
        # The contract is exactly one closing line. Two identical verdicts are not
        # one verdict: which of them the reader is meant to trust is undefined.
        return "AMBIGUOUS"
    return seen[0]


def _round_passed(text: str, gate_ids: list[str]) -> tuple[bool, dict[str, str]]:
    """A round passes when every declared gate passed and nothing contradicts it.

    Three separate traps are closed here:

    * ``all([])`` is True, so a response that yielded no per-gate verdict at all
      used to pass on the strength of a single ``Overall: PASS`` line. Completeness
      is now required before the per-gate result is read as agreement.
    * A closing line of ``CONTRADICTORY``/``AMBIGUOUS`` still fails the round: two
      disagreeing statements are not a verdict.
    * A missing closing line is a formatting defect, not a substantive one. The
      gates decide, which is what this review says elsewhere; so an absent overall
      line no longer vetoes gates that each returned an explicit PASS. Round 1
      omitted its closing line while every gate passed, and that veto alone held
      a finished review as failed.
    """
    gates_result = per_gate(text, gate_ids)
    complete = bool(gate_ids) and all(gid in gates_result for gid in gate_ids)
    all_gates = complete and all(v == "PASS" for v in gates_result.values())
    verdict = overall(text)
    if verdict in {"FAIL", "CONTRADICTORY", "AMBIGUOUS"}:
        return False, gates_result
    if all_gates and verdict in {"PASS", "UNKNOWN"}:
        return True, gates_result
    return False, gates_result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-order", required=True)
    parser.add_argument("--card", required=True, help="work order card carrying the acceptance gates")
    parser.add_argument("--evidence", nargs="*", default=[], help="author artifacts to be audited")
    parser.add_argument("--run-dir", required=True, type=Path)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        # The card is read once. Reading it again for the hash left a window where
        # the checklist came from one version and the recorded digest, the prompt
        # text and the frozen object came from another.
        try:
            card_bytes = Path(args.card).read_bytes()
        except OSError as exc:
            print(json.dumps({"blocked": True, "reason": f"unreadable card: {exc}"},
                             ensure_ascii=False), file=sys.stderr)
            return 2
        card = _decode(card_bytes)
        gate_list = gates(card)
        if not gate_list:
            # 卡上没有 ACC 门表。只有当工单在 manifest 里为这张卡声明了一条 waiver
            # （理由 + 可解析的替代测试）时，审计才有东西可判；否则一律拒。
            try:
                waiver = _waiver_for(args.card, args.work_order)
            except ValueError as exc:
                print(json.dumps({"blocked": True, "reason": str(exc)},
                                 ensure_ascii=False), file=sys.stderr)
                return 2
            if waiver is None:
                print(json.dumps({
                    "blocked": True,
                    "reason": "card lists no ACC gates and the order declares no waiver; "
                              "a checklist audit has nothing to judge"},
                    ensure_ascii=False), file=sys.stderr)
                return 2
            gate_list = [{
                "id": f"WAIVER:{waiver['card']}",
                "criterion": f"no ACC table; substituted by {waiver['instead']} — "
                             f"{waiver['because']}",
                "how": "the substitute test must have actually executed and passed "
                       "for the verified commit",
            }]
        gate_ids = [g["id"] for g in gate_list]
        checklist = "\n".join(f"- {g['id']}: {g['criterion']} (judged by: {g['how']})" for g in gate_list)

        objects = [_audit_object(args.card, "work_order_card", card_bytes)]
        for p in args.evidence:
            # One read, one set of bytes. Reading the text and then re-reading for
            # the digest lets the file be swapped in between: the model would judge
            # content A while the recorded hash belongs to B, and freeze — which
            # only checks the hash — would agree.
            try:
                data = Path(p).read_bytes()
            except OSError as exc:
                print(json.dumps({"blocked": True, "reason": f"unreadable evidence: {p}: {exc}"},
                                 ensure_ascii=False), file=sys.stderr)
                return 2
            objects.append(_audit_object(p, "author_artifact", data))

        batches = _object_batches(objects)
        incomplete, visible, integrity_errors = _coverage(objects, batches)
        round1_batches: list[dict] = []
        round2_batches: list[dict] = []
        for index, batch in enumerate(batches, start=1):
            base = (
                f"Work order: {args.work_order}\n\n"
                f"## Gates to judge\n{checklist}\n\n"
                f"## Complete objects supplied for this review\n"
                f"{_batch_prompt(batch, index, len(batches))}\n"
            )
            first = call_deepseek(_ROUND1, base)
            first_passed, first_gates = _round_passed(first["response"], gate_ids)
            round1_batches.append({
                **first,
                "batch": index,
                "objects": [item["path"] for item in batch],
                "passed": first_passed,
                "per_gate": first_gates,
                "overall": overall(first["response"]),
            })

            second = call_deepseek(
                _ROUND2,
                base + f"\n## Round 1 per-gate verdicts\n{json.dumps(first_gates, ensure_ascii=False)}\n"
                       f"\n## Round 1 reasoning\n{first['response']}\n",
            )
            second_passed, second_gates = _round_passed(second["response"], gate_ids)
            round2_batches.append({
                **second,
                "batch": index,
                "objects": [item["path"] for item in batch],
                "passed": second_passed,
                "per_gate": second_gates,
                "overall": overall(second["response"]),
            })

        round1 = _aggregate_round(round1_batches, gate_ids)
        round2 = _aggregate_round(round2_batches, gate_ids)
        passed = _audit_passed(round1, round2, incomplete, integrity_errors)

        def _meta(item: dict) -> dict:
            covered = next((row for row in visible if row["path"] == item["path"]), None)
            return {
                "path": item["path"],
                "bytes": item["bytes"],
                "sha256": item["sha256"],
                "shown_chars": len(item["text"]),
                "injected_bytes": 0 if covered is None else covered["injected_bytes"],
                "complete": covered is not None,
            }

        card_meta = _meta(objects[0])
        evidence_meta = [_meta(item) for item in objects[1:]]
        # Bind this verdict to the exact artifacts it judged. Without these three
        # fields nothing prevents a passing audit recorded for one run from being
        # copied into another run directory, or being replayed after a fresh
        # verification produced a different receipt.
        bound: dict = {"run_id": Path(args.run_dir).name}
        for key, name in (("verify_sha256", "verify.json"), ("done_sha256", "done.json")):
            try:
                bound[key] = hashlib.sha256((Path(args.run_dir) / name).read_bytes()).hexdigest()
            except OSError:
                bound[key] = None

        audit = {
            "work_order": args.work_order,
            **bound,
            "card": str(args.card),
            "card_meta": card_meta,
            "evidence": [str(p) for p in args.evidence],
            "evidence_meta": evidence_meta,
            "incomplete_inputs": incomplete,
            "visible": visible,
            "integrity_errors": integrity_errors,
            "object_batches": [
                {
                    "batch": index,
                    "objects": [item["path"] for item in batch],
                    "bytes": sum(int(item["bytes"]) for item in batch),
                }
                for index, batch in enumerate(batches, start=1)
            ],
            "gates": gate_ids,
            "round1": round1,
            "round2": round2,
            "audit_passed": passed,
            # Stated in the artifact itself so nobody mistakes scope later.
            "authority": "quality gate: required for a freeze, cannot authorize what verify-order.py refused; not an independent-party check",
        }
        out = Path(args.run_dir) / "audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"audit_passed": passed, "round1": round1["per_gate"],
                          "round2": round2["per_gate"],
                          "visible": visible,
                          "out": str(out)}, ensure_ascii=False))
        return 0 if passed else 2
    except (OSError, UnicodeError, ValueError, OrchestratorError) as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
