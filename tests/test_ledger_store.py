from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from src.brain.orchestration.ledger import LedgerStore, VersionConflict


def _seed(store: LedgerStore, suffix: str = "") -> tuple[str, str, str]:
    project_id = f"ultimaagent{suffix}"
    goal_id = f"goal{suffix}"
    work_order_id = f"wo-ultimaagent-20261108-{30 + len(suffix):04d}"
    store.put_project(project_id, f"UltimaAgent{suffix}", r"H:\UltimaAI\UltimaAgent")
    store.put_goal(
        project_id,
        goal_id,
        "Ledger foundation",
        allowed_write_roots=["src/brain/orchestration"],
        acceptance=["tests pass"],
        prohibited=["UltimaManager writes"],
    )
    store.put_work_order(
        project_id,
        work_order_id,
        goal_id,
        "M4 ledger",
        category="development",
        state="pending",
        source_hash="abc123",
        write_scope=["src/brain/orchestration"],
        acceptance=["T0-T2 green"],
    )
    return project_id, goal_id, work_order_id


def test_creates_exact_five_core_tables_with_manager_column_counts(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")

    tables = {
        row[0]
        for row in store.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
        )
    }
    counts = {
        table: len(store.connection.execute(f"PRAGMA table_info({table})").fetchall())
        for table in tables
    }

    assert tables == {"projects", "goals", "work_orders", "stages", "runs"}
    assert counts == {"projects": 9, "goals": 11, "work_orders": 15, "stages": 21, "runs": 25}
    assert store.connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert store.connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"


def test_put_and_get_work_order_round_trip_json_fields(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, _, work_order_id = _seed(store)

    row = store.get_work_order(project_id, work_order_id)

    assert row["state"] == "pending"
    assert row["write_scope"] == ["src/brain/orchestration"]
    assert row["acceptance"] == ["T0-T2 green"]
    assert row["version"] == 1


def test_repeated_put_is_idempotent_and_keeps_version(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, goal_id, work_order_id = _seed(store)

    store.put_work_order(
        project_id,
        work_order_id,
        goal_id,
        "M4 ledger",
        category="development",
        state="pending",
        source_hash="abc123",
        write_scope=["src/brain/orchestration"],
        acceptance=["T0-T2 green"],
    )

    assert store.get_work_order(project_id, work_order_id)["version"] == 1
    assert store.connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 1


def test_cas_work_order_updates_fields_and_increments_version(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, _, work_order_id = _seed(store)

    updated = store.cas_work_order(
        project_id,
        work_order_id,
        expected_version=1,
        state="executing",
        reservation="worker-1",
    )

    assert updated["state"] == "executing"
    assert updated["reservation"] == "worker-1"
    assert updated["version"] == 2


def test_cas_work_order_raises_on_version_conflict(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, _, work_order_id = _seed(store)
    store.cas_work_order(project_id, work_order_id, expected_version=1, state="executing")

    with pytest.raises(VersionConflict):
        store.cas_work_order(project_id, work_order_id, expected_version=1, state="audit")


def test_transaction_rolls_back_all_writes_on_error(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")

    with pytest.raises(RuntimeError, match="abort"):
        with store.transaction():
            store.put_project("p1", "Project", str(tmp_path))
            store.put_goal("p1", "g1", "Goal")
            raise RuntimeError("abort")

    assert store.connection.execute("SELECT COUNT(*) FROM projects").fetchone()[0] == 0
    assert store.connection.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0


def test_two_threads_can_write_distinct_work_orders(tmp_path: Path):
    path = tmp_path / "ledger.sqlite"
    LedgerStore(path).close()
    barrier = threading.Barrier(2)
    errors: list[BaseException] = []

    def writer(suffix: str) -> None:
        store = LedgerStore(path)
        try:
            barrier.wait(timeout=5)
            _seed(store, suffix)
        except BaseException as exc:  # captured for assertion in the main thread
            errors.append(exc)
        finally:
            store.close()

    threads = [threading.Thread(target=writer, args=(suffix,)) for suffix in ("a", "bb")]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=10)

    assert errors == []
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 2


def test_put_stage_and_run_then_filter_runs(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, _, work_order_id = _seed(store)
    store.put_stage(
        project_id,
        work_order_id,
        "T1",
        phase="implementation",
        state="ready",
        source_hash="abc123",
        created_seq=1,
    )
    store.put_run(
        project_id,
        work_order_id,
        "T1",
        "run-1",
        phase="implementation",
        state="starting",
        source_hash="abc123",
        cwd=str(tmp_path),
        allowed_write_roots=[str(tmp_path)],
        evidence_dir=str(tmp_path / "evidence"),
        reservation="worker-1",
    )

    rows = store.list_runs(project_id=project_id, work_order_id=work_order_id, state="starting")

    assert len(rows) == 1
    assert rows[0]["allowed_write_roots"] == [str(tmp_path)]
    assert rows[0]["receipt_evidence"] == []


def test_running_update_requires_pid_and_process_identity(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    project_id, _, work_order_id = _seed(store)
    store.put_stage(
        project_id,
        work_order_id,
        "T1",
        phase="implementation",
        state="ready",
        source_hash="abc123",
        created_seq=1,
    )
    store.put_run(
        project_id,
        work_order_id,
        "T1",
        "run-1",
        phase="implementation",
        state="starting",
        source_hash="abc123",
        cwd=str(tmp_path),
        allowed_write_roots=[str(tmp_path)],
        evidence_dir=str(tmp_path / "evidence"),
        reservation="worker-1",
    )

    with pytest.raises(ValueError, match="pid"):
        store.update_run_process(project_id, work_order_id, "T1", "run-1", 0, "proc", "running")
    with pytest.raises(ValueError, match="process_identity"):
        store.update_run_process(project_id, work_order_id, "T1", "run-1", 10, "", "running")

    updated = store.update_run_process(
        project_id,
        work_order_id,
        "T1",
        "run-1",
        10,
        "pid:10:start:1",
        "running",
    )
    assert updated["state"] == "running"
    assert updated["pid"] == 10
    assert updated["process_identity"] == "pid:10:start:1"
    assert updated["started_at"] is not None

    finished = store.finish_run(
        project_id,
        work_order_id,
        "T1",
        "run-1",
        exit_code=0,
        finished_at=updated["started_at"] + 1,
    )
    assert finished["state"] == "passed"
    assert finished["exit_code"] == 0
    assert finished["finished_at"] == updated["started_at"] + 1


def test_close_is_idempotent(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")

    store.close()
    store.close()

    assert store.connection is None
