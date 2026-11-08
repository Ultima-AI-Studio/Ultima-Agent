from __future__ import annotations

import importlib.util
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
