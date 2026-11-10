"""Migrate queue state once, then render both Markdown views from JSON.

``tasks/queue/queue-status.json`` is the only mutable queue-state authority.
The project and global Markdown files are deterministic, generated views.
"""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "tasks" / "queue" / "queue-status.json"
PROJECT_VIEW = ROOT / "tasks" / "queue" / "index.md"
GLOBAL_VIEW = ROOT.parent / "_shared" / "queue" / "global-queue-index.md"
BACKUP_DIR = ROOT / "tasks" / "queue" / "_backup" / "20261110-0036"
STATES = {"frozen", "blocked", "cancelled", "pending", "closed", "audit", "executing"}
FIXED_AUDIT = {
    "wo-ultimaagent-20261108-0030": False,
    "wo-ultimaagent-20261110-0033": True,
    "wo-ultimaagent-20261110-0035": True,
}


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent,
        prefix=path.name + ".", suffix=".tmp",
    ) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    temporary.replace(path)


def _atomic_json(path: Path, document: dict[str, Any]) -> None:
    _atomic_text(path, json.dumps(document, ensure_ascii=False, indent=2) + "\n")


def _parse_global_rows(path: Path) -> list[dict[str, Any]]:
    text = path.read_text(encoding="utf-8-sig")
    start = text.find("<!-- queue-items:start -->")
    end = text.find("<!-- queue-items:end -->")
    if start < 0 or end <= start:
        raise ValueError("global queue view has no valid queue-items marker pair")
    rows: list[dict[str, Any]] = []
    for source_line, raw in enumerate(text[start:end].splitlines(), 1):
        if not raw.startswith("|"):
            continue
        cells = [cell.strip() for cell in raw.strip().strip("|").split("|")]
        if len(cells) < 4 or cells[2].lower() not in STATES:
            continue
        project, order, state = cells[:3]
        note = "|".join(cells[3:]).strip()
        if not project or not order:
            raise ValueError(f"queue row has an empty identity near marker line {source_line}")
        token = re.search(r"audit_passed\s*[=:]\s*(true|false)", note, re.I)
        audit_passed = None if token is None else token.group(1).lower() == "true"
        if order in FIXED_AUDIT:
            audit_passed = FIXED_AUDIT[order]
        rows.append({
            "project": project,
            "work_order": order,
            "state": state.lower(),
            "audit_passed": audit_passed,
            "dispatched_at": None,
            "audit_run": None,
            "freeze_commit": None,
            "note": note,
        })
    identities = [(row["project"], row["work_order"]) for row in rows]
    if len(set(identities)) != len(identities):
        duplicates = [identity for identity, count in Counter(identities).items() if count > 1]
        raise ValueError(f"duplicate queue identities: {duplicates[:5]}")
    return rows


def _validate(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("schema_version") != 1:
        raise ValueError("queue-status.json schema_version must be 1")
    records = document.get("records")
    if not isinstance(records, list):
        raise ValueError("queue-status.json records must be a list")
    required = {
        "project", "work_order", "state", "audit_passed", "dispatched_at",
        "audit_run", "freeze_commit", "note",
    }
    identities: set[tuple[str, str]] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not required.issubset(record):
            raise ValueError(f"record {index} lacks required fields")
        if record["state"] not in STATES:
            raise ValueError(f"record {index} has invalid state {record['state']!r}")
        if record["audit_passed"] not in (True, False, None):
            raise ValueError(f"record {index} audit_passed must be boolean or null")
        identity = (str(record["project"]), str(record["work_order"]))
        if identity in identities:
            raise ValueError(f"duplicate queue identity {identity}")
        identities.add(identity)
    return records


def load_authority(path: Path = AUTHORITY) -> dict[str, Any]:
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    _validate(document)
    return document


def _snapshot(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        if target.read_bytes() != source.read_bytes():
            raise ValueError(f"existing migration snapshot differs: {target}")
        return
    shutil.copyfile(source, target)


def migrate() -> dict[str, Any]:
    if AUTHORITY.exists():
        return load_authority()
    captured = datetime.now(timezone.utc).isoformat()
    stamp = re.sub(r"[^0-9]", "", captured)[:14] + "Z"
    project_backup = BACKUP_DIR / f"project-index.pre-migration-{stamp}.md"
    global_backup = BACKUP_DIR / f"global-queue-index.pre-migration-{stamp}.md"
    _snapshot(PROJECT_VIEW, project_backup)
    _snapshot(GLOBAL_VIEW, global_backup)
    rows = _parse_global_rows(global_backup)
    document = {
        "schema_version": 1,
        "authority": "tasks/queue/queue-status.json",
        "migrated_at": captured,
        "migration": {
            "project_view_snapshot": project_backup.relative_to(ROOT).as_posix(),
            "project_view_sha256": _sha256(project_backup),
            "global_view_snapshot": global_backup.relative_to(ROOT).as_posix(),
            "global_view_sha256": _sha256(global_backup),
            "rollback": "Restore both snapshots to their original paths, then delete tasks/queue/queue-status.json.",
        },
        "records": rows,
    }
    _validate(document)
    _atomic_json(AUTHORITY, document)
    rollback = (
        "# Queue status migration rollback\n\n"
        "1. Restore `project-index.pre-migration-*.md` to `tasks/queue/index.md`.\n"
        "2. Restore `global-queue-index.pre-migration-*.md` to "
        "`H:/UltimaAI/_shared/queue/global-queue-index.md`.\n"
        "3. Delete `tasks/queue/queue-status.json`.\n\n"
        "Do not merge state from the generated views back into JSON.\n"
    )
    _atomic_text(BACKUP_DIR / "ROLLBACK.md", rollback)
    return document


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if value is True:
        return "true"
    if value is False:
        return "false"
    return str(value).replace("\r", " ").replace("\n", " ").replace("|", "\\|")


def _render(title: str, records: list[dict[str, Any]], authority: dict[str, Any]) -> str:
    distribution = Counter(record["state"] for record in records)
    summary = ", ".join(f"{state}={distribution[state]}" for state in sorted(distribution))
    lines = [
        f"# {title}",
        "",
        "> **由 `scripts/render-queue-views.py` 从 `tasks/queue/queue-status.json` 生成，勿手改。**",
        "> 唯一状态权威：`tasks/queue/queue-status.json`。修改 Markdown 不会回写状态。",
        f"> schema_version={authority['schema_version']} ｜ records={len(records)} ｜ {summary}",
        "",
        "<!-- queue-items:start -->",
        "| 项目 | 工单 | 状态 | audit_passed | 派发时间 | 审计 run | 冻结 commit | 备注 |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record in records:
        lines.append("| " + " | ".join(_cell(record[key]) for key in (
            "project", "work_order", "state", "audit_passed", "dispatched_at",
            "audit_run", "freeze_commit", "note",
        )) + " |")
    lines.extend(["<!-- queue-items:end -->", ""])
    return "\n".join(lines)


def render(document: dict[str, Any]) -> None:
    records = _validate(document)
    _atomic_text(GLOBAL_VIEW, _render("UltimaAI 全局队列（派生视图）", records, document))
    project_records = [record for record in records if record["project"] == "UltimaAgent"]
    _atomic_text(PROJECT_VIEW, _render("UltimaAgent 项目队列（派生视图）", project_records, document))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--migrate", action="store_true", help="create JSON authority once from the current global view")
    parser.add_argument("--check", action="store_true", help="verify both views equal a fresh render")
    args = parser.parse_args()
    document = migrate() if args.migrate else load_authority()
    if args.check:
        records = _validate(document)
        expected_global = _render("UltimaAI 全局队列（派生视图）", records, document)
        expected_project = _render(
            "UltimaAgent 项目队列（派生视图）",
            [record for record in records if record["project"] == "UltimaAgent"],
            document,
        )
        differences = []
        if GLOBAL_VIEW.read_text(encoding="utf-8-sig") != expected_global:
            differences.append(str(GLOBAL_VIEW))
        if PROJECT_VIEW.read_text(encoding="utf-8-sig") != expected_project:
            differences.append(str(PROJECT_VIEW))
        print(json.dumps({"differences": differences}, ensure_ascii=False))
        return 1 if differences else 0
    render(document)
    print(json.dumps({
        "authority": str(AUTHORITY),
        "records": len(document["records"]),
        "distribution": Counter(record["state"] for record in document["records"]),
    }, ensure_ascii=False, default=dict))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
