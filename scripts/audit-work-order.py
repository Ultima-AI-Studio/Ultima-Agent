"""Two-round audit of a delivered work order, judged gate by gate.

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

This script is still advisory relative to `verify-order.py`: it can stop a pass
that deterministic checks allowed, but it cannot grant one they refused.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brain.orchestrator import OrchestratorError, call_deepseek


_ROUND1 = (
    "You are the independent auditor, round 1. You are NOT the author of the artifact "
    "and you did not produce it. You work in a plain-text environment: NO tools, NO shell, "
    "NO file access.\n\n"
    "Judge one gate at a time. For every gate listed below, emit exactly one line in this form:\n"
    "    <gate id>: PASS - <the specific evidence you relied on>\n"
    "    <gate id>: FAIL - <what is missing or wrong, and what evidence would settle it>\n\n"
    "Then, after all gates, emit one line with the overall result.\n"
    "Rules: do not skip a gate; do not pass a gate you have no evidence for - a gate with no "
    "supporting artifact is FAIL, not UNKNOWN; do not restate the gate text as evidence."
)

_ROUND2 = (
    "You are the independent auditor, round 2. You work in a plain-text environment: "
    "NO tools, NO shell, NO file access.\n\n"
    "Round 1's per-gate verdicts are supplied as a prior opinion, not as truth. Re-judge every "
    "gate from the evidence yourself and emit one line per gate in the same form as round 1:\n"
    "    <gate id>: PASS - <evidence>\n"
    "    <gate id>: FAIL - <what is wrong>\n"
    "Where you disagree with round 1, say so on that gate's line. Then emit the overall line."
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def gates(card: str) -> list[dict]:
    """Acceptance gates as (id, criterion, how-to-judge) from the card's table."""
    found = []
    for line in card.splitlines():
        if not line.startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or not re.fullmatch(r"ACC-\d+", cells[0]):
            continue
        found.append({"id": cells[0], "criterion": cells[1], "how": cells[2]})
    return found


def per_gate(text: str, gate_ids: list[str]) -> dict[str, str]:
    """Pull the last verdict line for each gate; missing gates count as FAIL."""
    verdicts: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.strip().strip("*_` ")
        match = re.match(r"(ACC-\d+)\s*[：:]\s*(PASS|FAIL)\b", stripped, re.IGNORECASE)
        if match:
            verdicts[match.group(1).upper()] = match.group(2).upper()
    return {gid: verdicts.get(gid, "MISSING") for gid in gate_ids}


def overall(text: str) -> str:
    for line in reversed(text.splitlines()):
        token = line.strip().strip("*_` ").upper()
        if token.startswith("AUDIT"):
            if "PASS" in token:
                return "PASS"
            if "FAIL" in token:
                return "FAIL"
    return "UNKNOWN"


def _round_passed(text: str, gate_ids: list[str]) -> tuple[bool, dict[str, str]]:
    """A round passes only when every gate passed AND the closing line agrees."""
    gates_result = per_gate(text, gate_ids)
    all_gates = all(v == "PASS" for v in gates_result.values())
    return (all_gates and overall(text) == "PASS"), gates_result


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
        card = _read(args.card)
        gate_list = gates(card)
        if not gate_list:
            print(json.dumps({"blocked": True,
                              "reason": "card lists no ACC gates; a checklist audit has nothing to judge"},
                             ensure_ascii=False), file=sys.stderr)
            return 2
        gate_ids = [g["id"] for g in gate_list]
        checklist = "\n".join(f"- {g['id']}: {g['criterion']} (judged by: {g['how']})" for g in gate_list)

        evidence = "\n\n".join(f"## {Path(p).name}\n{_read(p)[:6000]}" for p in args.evidence)
        base = (
            f"Work order: {args.work_order}\n\n"
            f"## Gates to judge\n{checklist}\n\n"
            f"## Work order card (full text)\n{card[:4000]}\n\n"
            f"## Author artifacts\n{evidence or '(no evidence supplied)'}\n"
        )

        round1 = call_deepseek(_ROUND1, base)
        pass1, gates1 = _round_passed(round1["response"], gate_ids)

        round2 = call_deepseek(
            _ROUND2,
            base + f"\n## Round 1 per-gate verdicts\n{json.dumps(gates1, ensure_ascii=False)}\n"
                   f"\n## Round 1 reasoning\n{round1['response'][:4000]}\n",
        )
        pass2, gates2 = _round_passed(round2["response"], gate_ids)

        passed = pass1 and pass2
        audit = {
            "work_order": args.work_order,
            "card": str(args.card),
            "evidence": [str(p) for p in args.evidence],
            "gates": gate_ids,
            "round1": {"passed": pass1, "per_gate": gates1,
                       "overall": overall(round1["response"]),
                       "response": round1["response"], "tokens": round1["tokens"]},
            "round2": {"passed": pass2, "per_gate": gates2,
                       "overall": overall(round2["response"]),
                       "response": round2["response"], "tokens": round2["tokens"]},
            "audit_passed": passed,
            # Stated in the artifact itself so nobody mistakes scope later.
            "authority": "advisory; a pass here cannot authorize what verify-order.py refused",
        }
        out = Path(args.run_dir) / "audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"audit_passed": passed, "round1": gates1, "round2": gates2,
                          "out": str(out)}, ensure_ascii=False))
        return 0 if passed else 2
    except (OSError, UnicodeError, OrchestratorError) as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
