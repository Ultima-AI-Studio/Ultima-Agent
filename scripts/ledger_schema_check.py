"""Compare UltimaAgent's frozen core ledger contract with Manager's schema.

The Manager checkout is read-only input.  The JSON report contains all thirteen
tables found in ``store.py`` and field-level differences for the five frozen
core tables.  Exit status is 0 only when all thirteen tables are present and
the core contract has zero differences.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_MANAGER_STORE = Path(r"H:\UltimaAI\UltimaManager\src\manager\store.py")
DEFAULT_OUTPUT = Path("docs/reports/wo-ultimaagent-20261108-0030-t0-schema-result.json")
EXPECTED_TABLES = (
    "projects",
    "goals",
    "work_orders",
    "stages",
    "runs",
    "external_actors",
    "legacy_records",
    "approvals",
    "plans",
    "events",
    "handoffs",
    "continuation_contracts",
    "interventions",
)

# Frozen from H:\UltimaAI\UltimaManager\src\manager\store.py at T0.  This is
# deliberately independent of the live file so a later Manager schema change
# produces a reproducible non-zero diff instead of silently rewriting baseline.
CORE_SCHEMA_SQL = r"""
CREATE TABLE IF NOT EXISTS projects (
    project_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    root_path TEXT NOT NULL,
    adapter_json TEXT NOT NULL DEFAULT '{}',
    ownership_state TEXT NOT NULL DEFAULT 'managed_new',
    ownership_reason TEXT,
    paused INTEGER NOT NULL DEFAULT 0,
    last_dispatch_seq INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS goals (
    project_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,
    title TEXT NOT NULL,
    revision INTEGER NOT NULL,
    approved INTEGER NOT NULL,
    allowed_write_roots_json TEXT NOT NULL,
    acceptance_json TEXT NOT NULL,
    prohibited_json TEXT NOT NULL,
    max_tasks INTEGER NOT NULL,
    hold INTEGER NOT NULL DEFAULT 0,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, goal_id),
    FOREIGN KEY (project_id) REFERENCES projects(project_id)
);
CREATE TABLE IF NOT EXISTS work_orders (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    goal_id TEXT NOT NULL,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    state TEXT NOT NULL,
    revision INTEGER NOT NULL,
    source_hash TEXT NOT NULL,
    write_scope_json TEXT NOT NULL,
    acceptance_json TEXT NOT NULL,
    idle_reason TEXT,
    reservation TEXT,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (project_id, work_order_id),
    FOREIGN KEY (project_id, goal_id) REFERENCES goals(project_id, goal_id)
);
CREATE TABLE IF NOT EXISTS stages (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    goal_id TEXT NOT NULL DEFAULT '',
    goal_revision INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 0,
    dependencies_json TEXT NOT NULL DEFAULT '[]',
    write_scope_json TEXT NOT NULL DEFAULT '[]',
    acceptance_json TEXT NOT NULL DEFAULT '[]',
    task_contract_json TEXT NOT NULL DEFAULT '{}',
    reservation TEXT,
    reserved_at REAL,
    reservation_owner_pid INTEGER,
    reservation_owner_identity TEXT,
    repair_count INTEGER NOT NULL DEFAULT 0,
    max_repairs INTEGER NOT NULL DEFAULT 2,
    created_seq INTEGER NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    PRIMARY KEY (project_id, work_order_id, stage_id),
    FOREIGN KEY (project_id, work_order_id)
      REFERENCES work_orders(project_id, work_order_id)
);
CREATE TABLE IF NOT EXISTS runs (
    project_id TEXT NOT NULL,
    work_order_id TEXT NOT NULL,
    stage_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    goal_id TEXT NOT NULL DEFAULT '',
    goal_revision INTEGER NOT NULL DEFAULT 0,
    state TEXT NOT NULL,
    source_hash TEXT NOT NULL,
    cwd TEXT NOT NULL,
    allowed_write_roots_json TEXT NOT NULL,
    evidence_dir TEXT NOT NULL,
    reservation TEXT NOT NULL,
    created_at REAL NOT NULL DEFAULT 0,
    pid INTEGER,
    process_identity TEXT,
    exit_code INTEGER,
    started_at REAL,
    finished_at REAL,
    receipt_status TEXT,
    receipt_evidence_json TEXT NOT NULL DEFAULT '[]',
    review_findings_json TEXT NOT NULL DEFAULT '[]',
    delivery_source_hash TEXT,
    acceptance_result_json TEXT NOT NULL DEFAULT '{}',
    transport_facts_json TEXT NOT NULL DEFAULT '{}',
    PRIMARY KEY (project_id, work_order_id, stage_id, run_id),
    FOREIGN KEY (project_id, work_order_id, stage_id)
      REFERENCES stages(project_id, work_order_id, stage_id)
);
"""

_TABLE_PATTERN = re.compile(
    r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+(?P<name>[A-Za-z_]\w*)\s*"
    r"\((?P<body>.*?)\)\s*;",
    re.IGNORECASE | re.DOTALL,
)
_CONSTRAINT_PREFIXES = ("PRIMARY KEY", "FOREIGN KEY", "UNIQUE", "CHECK", "CONSTRAINT")


def _split_sql_items(body: str) -> list[str]:
    items: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None
    index = 0
    while index < len(body):
        char = body[index]
        if quote:
            current.append(char)
            if char == quote:
                if index + 1 < len(body) and body[index + 1] == quote:
                    current.append(body[index + 1])
                    index += 1
                else:
                    quote = None
        elif char in {"'", '"'}:
            quote = char
            current.append(char)
        elif char == "(":
            depth += 1
            current.append(char)
        elif char == ")":
            depth -= 1
            current.append(char)
        elif char == "," and depth == 0:
            item = " ".join("".join(current).split())
            if item:
                items.append(item)
            current = []
        else:
            current.append(char)
        index += 1
    item = " ".join("".join(current).split())
    if item:
        items.append(item)
    return items


def extract_schema(source: str) -> dict[str, dict[str, Any]]:
    schema: dict[str, dict[str, Any]] = {}
    for match in _TABLE_PATTERN.finditer(source):
        columns: list[dict[str, str]] = []
        constraints: list[str] = []
        for item in _split_sql_items(match.group("body")):
            if item.upper().startswith(_CONSTRAINT_PREFIXES):
                constraints.append(item)
                continue
            name, _, definition = item.partition(" ")
            columns.append({"name": name.strip('"`[]'), "definition": definition})
        schema[match.group("name")] = {
            "columns": columns,
            "constraints": constraints,
        }
    return schema


FROZEN_CORE = extract_schema(CORE_SCHEMA_SQL)


def compare_schema(
    actual: dict[str, dict[str, Any]],
    expected: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    differences: list[dict[str, Any]] = []
    for table, expected_table in expected.items():
        observed = actual.get(table)
        if observed is None:
            differences.append({"table": table, "kind": "missing_table"})
            continue
        expected_columns = {
            column["name"]: column["definition"] for column in expected_table["columns"]
        }
        observed_columns = {column["name"]: column["definition"] for column in observed["columns"]}
        for name in sorted(expected_columns.keys() | observed_columns.keys()):
            if name not in observed_columns:
                differences.append({"table": table, "field": name, "kind": "missing_field"})
            elif name not in expected_columns:
                differences.append({"table": table, "field": name, "kind": "unexpected_field"})
            elif observed_columns[name] != expected_columns[name]:
                differences.append(
                    {
                        "table": table,
                        "field": name,
                        "kind": "definition_mismatch",
                        "expected": expected_columns[name],
                        "actual": observed_columns[name],
                    }
                )
        if observed["constraints"] != expected_table["constraints"]:
            differences.append(
                {
                    "table": table,
                    "kind": "constraints_mismatch",
                    "expected": expected_table["constraints"],
                    "actual": observed["constraints"],
                }
            )
    return differences


def compare_core(actual: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return compare_schema(actual, FROZEN_CORE)


def _manager_revision(store_path: Path) -> str | None:
    try:
        completed = subprocess.run(
            ["git", "-C", str(store_path.parents[2]), "rev-parse", "--short", "HEAD"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def build_report(
    store_path: Path,
    contract_schema: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source_bytes = store_path.read_bytes()
    actual = extract_schema(source_bytes.decode("utf-8"))
    contract = actual if contract_schema is None else contract_schema
    differences = compare_schema(actual, contract)
    core_differences = compare_core(actual)
    missing_tables = [name for name in EXPECTED_TABLES if name not in actual]
    unexpected_tables = [name for name in actual if name not in EXPECTED_TABLES]
    passed = not differences and not core_differences and not missing_tables and not unexpected_tables
    return {
        "work_order": "wo-ultimaagent-20261108-0030",
        "gate": "T0",
        "status": "PASS" if passed else "FAIL",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(store_path.resolve()),
            "git_revision": _manager_revision(store_path),
            "mtime_utc": datetime.fromtimestamp(store_path.stat().st_mtime, timezone.utc).isoformat(),
            "sha256": hashlib.sha256(source_bytes).hexdigest(),
        },
        "expected_table_count": len(EXPECTED_TABLES),
        "actual_table_count": len(actual),
        "table_names": list(actual),
        "missing_tables": missing_tables,
        "unexpected_tables": unexpected_tables,
        "core_tables": list(FROZEN_CORE),
        "core_field_counts": {name: len(actual[name]["columns"]) for name in FROZEN_CORE if name in actual},
        "difference_count": len(differences),
        "differences": differences,
        "core_difference_count": len(core_differences),
        "core_differences": core_differences,
        "non_core_difference_count": sum(
            difference.get("table") not in FROZEN_CORE for difference in differences
        ),
        "observed_schema_sha256": hashlib.sha256(
            json.dumps(actual, ensure_ascii=False, sort_keys=True).encode("utf-8")
        ).hexdigest(),
        "contract_schema": contract,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manager-store", type=Path, default=DEFAULT_MANAGER_STORE)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    contract_schema = None
    if args.output.is_file():
        try:
            previous = json.loads(args.output.read_text(encoding="utf-8"))
            contract_schema = previous.get("contract_schema") or previous.get("schema")
        except (OSError, json.JSONDecodeError, TypeError):
            contract_schema = None
    report = build_report(args.manager_store, contract_schema)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        f"{report['actual_table_count']} tables; "
        f"{report['difference_count']} differences "
        f"(core {report['core_difference_count']}); {report['status']}"
    )
    print(args.output.resolve())
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
