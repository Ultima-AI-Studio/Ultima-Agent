"""Run the G-ORCH decompose, work-order, and schedule stages in order."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Sequence


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.brain.orchestrator import OrchestratorError, run_stage


DEFAULT_STAGES = ("decompose", "work_order", "schedule")
ENV_FILE = ROOT / "config" / ".env"


def _load_env_file() -> None:
    """Load config/.env so the key does not depend on a pre-exported shell."""

    if not ENV_FILE.is_file():
        return
    try:
        text = ENV_FILE.read_text(encoding="utf-8-sig")
    except OSError:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def _parse_stages(value: str) -> tuple[str, ...]:
    stages = tuple(part.strip() for part in value.split(",") if part.strip())
    if not stages:
        raise ValueError("at least one stage is required")
    if len(set(stages)) != len(stages):
        raise ValueError("stages must not contain duplicates")
    unknown = [stage for stage in stages if stage not in DEFAULT_STAGES]
    if unknown:
        raise ValueError(f"unknown stage: {unknown[0]}")
    canonical = tuple(stage for stage in DEFAULT_STAGES if stage in stages)
    if stages != canonical:
        raise ValueError("stages must follow decompose,work_order,schedule order")
    return stages


def _read_requirement(value: str) -> str:
    try:
        candidate = Path(value)
        if candidate.is_file():
            with candidate.open(encoding="utf-8-sig", newline="") as source:
                requirement = source.read()
        else:
            requirement = value
    except OSError:
        requirement = value
    return requirement


def _validate_run_dir(run_dir: Path) -> None:
    if run_dir.exists() and not run_dir.is_dir():
        raise ValueError("run directory points to a file")
    ancestor = run_dir
    while not ancestor.exists():
        if ancestor.parent == ancestor:
            raise ValueError("run directory has no existing ancestor")
        ancestor = ancestor.parent
    if not os.access(ancestor, os.W_OK):
        raise ValueError("run directory is not writable")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirement", required=True)
    parser.add_argument("--run-dir", required=True, type=Path)
    parser.add_argument("--stages", default=",".join(DEFAULT_STAGES))
    parser.add_argument("--dry-run", action="store_true")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        stages = _parse_stages(args.stages)
        requirement = _read_requirement(args.requirement)
        _validate_run_dir(args.run_dir)
        if args.dry_run:
            print(
                json.dumps(
                    {
                        "ready": True,
                        "run_dir": str(args.run_dir),
                        "stages": list(stages),
                    },
                    ensure_ascii=False,
                )
            )
            return 0
        _load_env_file()
        if not os.environ.get("DEEPSEEK_API_KEY", "").strip():
            raise OrchestratorError("DEEPSEEK_API_KEY is required")
        args.run_dir.mkdir(parents=True, exist_ok=True)
        # A rerun intentionally overwrites the prior baseline for this run.
        with (args.run_dir / "requirement.txt").open(
            "w", encoding="utf-8", newline=""
        ) as destination:
            destination.write(requirement)
        for stage in stages:
            run_stage(stage, requirement, args.run_dir)
    except (OSError, UnicodeError, ValueError, OrchestratorError) as exc:
        print(
            json.dumps(
                {"blocked": True, "reason": str(exc)}, ensure_ascii=False
            ),
            file=sys.stderr,
        )
        return 2

    print(
        json.dumps(
            {
                "completed": True,
                "run_dir": str(args.run_dir),
                "stages": list(stages),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
