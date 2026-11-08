from __future__ import annotations

import importlib.util
import copy
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "ledger_schema_check.py"
MANAGER_STORE = Path(r"H:\UltimaAI\UltimaManager\src\manager\store.py")


def _load_checker():
    spec = importlib.util.spec_from_file_location("ledger_schema_check", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_manager_schema_has_13_tables_and_core_contract_has_no_differences():
    checker = _load_checker()

    actual = checker.extract_schema(MANAGER_STORE.read_text(encoding="utf-8"))
    differences = checker.compare_core(actual)

    assert list(actual) == [
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
    ]
    assert differences == []
    assert len(actual["work_orders"]["columns"]) == 15
    assert len(actual["runs"]["columns"]) == 25


def test_cli_writes_lf_only_json_report(tmp_path: Path):
    output = tmp_path / "schema-result.json"

    subprocess.run(
        [
            sys.executable,
            "-B",
            str(SCRIPT),
            "--manager-store",
            str(MANAGER_STORE),
            "--output",
            str(output),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert b"\r\n" not in output.read_bytes()


def test_all_13_tables_are_compared_field_by_field():
    checker = _load_checker()
    actual = checker.extract_schema(MANAGER_STORE.read_text(encoding="utf-8"))
    changed = copy.deepcopy(actual)
    changed["external_actors"]["columns"][0]["definition"] = "INTEGER PRIMARY KEY"

    differences = checker.compare_schema(changed, actual)

    assert differences == [
        {
            "table": "external_actors",
            "field": "actor_id",
            "kind": "definition_mismatch",
            "expected": "TEXT PRIMARY KEY",
            "actual": "INTEGER PRIMARY KEY",
        }
    ]
