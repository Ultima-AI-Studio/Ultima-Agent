"""Validate and freeze one work-order baseline with an auditable gate receipt."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import glob
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class FreezeError(RuntimeError):
    """A closed freeze-gate failure that maps to exit code 3."""


def git(root: Path, *args: str) -> str:
    return subprocess.check_output(
        ["git", *args],
        cwd=root,
        timeout=60,
        creationflags=CREATE_NO_WINDOW,
        text=True,
        encoding="utf-8",
    ).strip()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_matches(root: Path, patterns: list[str]) -> list[Path]:
    matches: list[Path] = []
    for pattern in patterns:
        candidate = Path(pattern)
        expanded = glob.glob(str(candidate if candidate.is_absolute() else root / pattern), recursive=True)
        files = sorted({Path(item).resolve() for item in expanded})
        if not files:
            raise FreezeError(f"evidence glob 没有命中：{pattern}")
        for path in files:
            if not path.is_file() or path.stat().st_size == 0:
                raise FreezeError(f"evidence 必须存在且非空：{path}")
            if path not in matches:
                matches.append(path)
    return matches


def _walk_fields(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield key, child
            yield from _walk_fields(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_fields(child)


def _pass_value(value) -> bool:
    if value is True:
        return True
    return isinstance(value, str) and value.strip().lower() in {"pass", "true"}


def validate_json_evidence(paths: list[Path]) -> None:
    for path in paths:
        if path.suffix.lower() != ".json":
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise FreezeError(f"evidence JSON 不可读：{path}: {exc}") from exc
        for key, value in _walk_fields(payload):
            lowered = key.lower()
            if lowered == "status" and not (isinstance(value, str) and value.strip().lower() == "pass"):
                raise FreezeError(f"evidence status 必须为 PASS：{path}: {value!r}")
            if lowered == "all_technical_pass" or re.fullmatch(r"all_.*pass", lowered):
                if not _pass_value(value):
                    raise FreezeError(f"evidence {key} 必须为 true/PASS：{path}: {value!r}")


def _relative_or_absolute(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def build_gate(args, root: Path, baseline: str, evidence: list[Path]) -> dict:
    return {
        "gate": args.tag,
        "decision": "PASS",
        "approved_by": "owner",
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "order": args.order,
        "baseline_commit": baseline,
        "evidence": [
            {"path": _relative_or_absolute(path, root), "sha256": sha256(path)} for path in evidence
        ],
        "approval_text": args.approve_text or "",
        "scope": f"{args.order} baseline {baseline}",
        "known_limit": args.known_limit or "",
        "schema_version": "1.0",
    }


def validate_gate(args, root: Path) -> tuple[dict, Path]:
    head = git(root, "rev-parse", "HEAD")
    if head != args.baseline:
        raise FreezeError(f"baseline mismatch: HEAD={head} expected={args.baseline}")
    if git(root, "diff", "--name-only"):
        raise FreezeError("tracked worktree changed")
    if git(root, "diff", "--cached", "--name-only"):
        raise FreezeError("staged changes present")
    if git(root, "tag", "--list", args.tag):
        raise FreezeError(f"tag already exists: {args.tag}")
    evidence = _evidence_matches(root, args.evidence)
    validate_json_evidence(evidence)
    gate_path = args.gate_json or root / "tasks" / "queue" / "gates" / f"{args.tag}.json"
    if not gate_path.is_absolute():
        gate_path = root / gate_path
    return build_gate(args, root, head, evidence), gate_path


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--order", required=True)
    parser.add_argument("--baseline", required=True)
    parser.add_argument("--tag", required=True)
    parser.add_argument("--evidence", required=True, action="append")
    parser.add_argument("--gate-json", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--approve-text")
    parser.add_argument("--known-limit")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    root = Path.cwd().resolve()
    try:
        gate, gate_path = validate_gate(args, root)
        rendered = json.dumps(gate, ensure_ascii=False, indent=2)
        if args.dry_run:
            print("DRY-RUN actions:")
            print(f"- would write gate JSON: {gate_path}")
            print(f"- would create annotated tag: {args.tag} -> {args.baseline}")
            print("GATE_JSON_BEGIN")
            print(rendered)
            print("GATE_JSON_END")
            return 0

        gate_path.parent.mkdir(parents=True, exist_ok=True)
        with gate_path.open("x", encoding="utf-8") as stream:
            stream.write(rendered)
            stream.write("\n")
        receipt_sha = sha256(gate_path)
        message = f"{args.order} freeze gate {gate_path.name} sha256={receipt_sha}"
        subprocess.run(
            ["git", "tag", "-a", args.tag, args.baseline, "-m", message],
            cwd=root,
            check=True,
            timeout=60,
            creationflags=CREATE_NO_WINDOW,
        )
        tag_commit = git(root, "rev-parse", args.tag + "^{}")
        if tag_commit != args.baseline:
            raise FreezeError(f"tag readback mismatch: {tag_commit} != {args.baseline}")
        print(json.dumps({"status": "PASS", "gate_json": str(gate_path), "tag_commit": tag_commit}, ensure_ascii=False))
        return 0
    except (FreezeError, OSError, subprocess.SubprocessError) as exc:
        print(f"FAIL: {exc}")
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
