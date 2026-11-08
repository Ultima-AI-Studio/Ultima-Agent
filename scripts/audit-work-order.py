"""Independent two-round DeepSeek audit for a work order artifact.

Round 1 and round 2 are separate DeepSeek conversations. Round 2 sees round 1's
verdict but is told to re-judge from evidence rather than defer to it. The work
order may only leave AUDIT when both rounds return PASS.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brain.orchestrator import OrchestratorError, call_deepseek


ROUND1_SYSTEM = (
    "You are the independent auditor, round 1. You are NOT the author of the artifact "
    "and you did not produce it. You work in a plain-text environment: NO tools, NO shell, "
    "NO file access. Judge strictly against the work order acceptance gates listed in the card. "
    "Cite the specific gate for every finding. End with a final line exactly "
    "'AUDIT: PASS' or 'AUDIT: FAIL'."
)

ROUND2_SYSTEM = (
    "You are the independent auditor, round 2. You work in a plain-text environment: "
    "NO tools, NO shell, NO file access. Round 1's verdict is supplied as a prior opinion, "
    "not as truth. Re-judge from the evidence yourself. If round 1 missed a gap, or over-"
    "claimed, state the disagreement explicitly. End with a final line exactly "
    "'AUDIT: PASS' or 'AUDIT: FAIL'."
)


def _read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8-sig")


def _verdict(text: str) -> str:
    for line in reversed(text.splitlines()):
        token = line.strip().strip("*_` ").upper()
        if token.startswith("AUDIT"):
            if "PASS" in token:
                return "PASS"
            if "FAIL" in token:
                return "FAIL"
    return "UNKNOWN"


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
        evidence = "\n\n".join(
            f"## {Path(path).name}\n{_read(path)[:6000]}" for path in args.evidence
        )
        base = (
            f"Work order: {args.work_order}\n\n"
            f"## Work order card (acceptance gates)\n{card[:6000]}\n\n"
            f"## Author artifacts\n{evidence or '(no evidence supplied)'}\n"
        )

        round1 = call_deepseek(ROUND1_SYSTEM, base)
        verdict1 = _verdict(round1["response"])

        round2 = call_deepseek(
            ROUND2_SYSTEM,
            base
            + f"\n## Round 1 verdict\n{verdict1}\n\n## Round 1 reasoning\n{round1['response'][:4000]}\n",
        )
        verdict2 = _verdict(round2["response"])

        passed = verdict1 == "PASS" and verdict2 == "PASS"
        audit = {
            "work_order": args.work_order,
            "card": str(args.card),
            "evidence": [str(path) for path in args.evidence],
            "round1": {"verdict": verdict1, "response": round1["response"], "tokens": round1["tokens"]},
            "round2": {"verdict": verdict2, "response": round2["response"], "tokens": round2["tokens"]},
            "audit_passed": passed,
        }
        out = Path(args.run_dir) / "audit.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {"audit_passed": passed, "round1": verdict1, "round2": verdict2, "out": str(out)},
                ensure_ascii=False,
            )
        )
        return 0 if passed else 2
    except (OSError, UnicodeError, OrchestratorError) as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
