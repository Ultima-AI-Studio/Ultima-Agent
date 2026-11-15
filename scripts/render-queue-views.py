"""Validate queue state, then render both Markdown views from JSON.

``tasks/queue/queue-status.json`` is the only mutable queue-state authority.
The project and global Markdown files are deterministic, generated views.
"""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import tempfile
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
AUTHORITY = ROOT / "tasks" / "queue" / "queue-status.json"
PROJECT_VIEW = ROOT / "tasks" / "queue" / "index.md"
GLOBAL_VIEW = ROOT.parent / "_shared" / "queue" / "global-queue-index.md"
STATES = {"frozen", "blocked", "cancelled", "pending", "closed", "audit", "executing"}


def _atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", newline="\n", delete=False, dir=path.parent,
        prefix=path.name + ".", suffix=".tmp",
    ) as stream:
        stream.write(text)
        temporary = Path(stream.name)
    temporary.replace(path)


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


def migrate() -> dict[str, Any]:
    if not AUTHORITY.exists():
        raise FileNotFoundError(
            "queue authority is missing; create it through scripts/queue-writer.py"
        )
    return load_authority()


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
    parser.add_argument(
        "--migrate",
        action="store_true",
        help="require an existing JSON authority; creation belongs to queue-writer",
    )
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
