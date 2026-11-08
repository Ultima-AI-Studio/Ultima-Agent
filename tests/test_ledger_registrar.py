from __future__ import annotations

from pathlib import Path

from src.brain.orchestration.ledger import LedgerStore
from src.brain.orchestration.ledger.registrar import LedgerRegistrar
from src.brain.orchestration.queue import GlobalQueueRegistrar, TaskRecord


GLOBAL_TABLE = """# test global queue

<!-- queue-summary:start -->
| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| 合计 | 0 | 0 | 0 | 0 | 0 | 0 |
<!-- queue-summary:end -->

<!-- queue-items:start -->
| 项目 | 工单 | 状态 | 依据/说明 |
|---|---|---|---|
<!-- queue-items:end -->
"""


def _queue_registrar(
    tmp_path: Path,
    ledger_registrar: LedgerRegistrar,
) -> tuple[GlobalQueueRegistrar, Path]:
    queue_root = tmp_path / "queue"
    queue_root.mkdir()
    queue_path = queue_root / "global-queue-index.md"
    queue_path.write_text(GLOBAL_TABLE, encoding="utf-8")
    return (
        GlobalQueueRegistrar(
            queue_path,
            allowed_root=queue_root,
            ledger_registrar=ledger_registrar,
        ),
        queue_path,
    )


def _task() -> TaskRecord:
    return TaskRecord(
        task_id="wo-ultimaagent-20261108-0030",
        title="M4 orchestration ledger",
        phase="排队",
        permissions=("src/brain/orchestration", "tests"),
        project_key="ultimaagent",
    )


def test_global_registration_dual_writes_md_and_ledger(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    registrar, queue_path = _queue_registrar(
        tmp_path,
        LedgerRegistrar(store, project_root=tmp_path),
    )

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "ok"
    row = store.get_work_order("ultimaagent", "wo-ultimaagent-20261108-0030")
    assert row["state"] == "ready"
    assert row["write_scope"] == ["src/brain/orchestration", "tests"]


def test_missing_ledger_table_degrades_without_blocking_md(tmp_path: Path, caplog):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    store.connection.execute("DROP TABLE work_orders")
    registrar, queue_path = _queue_registrar(
        tmp_path,
        LedgerRegistrar(store, project_root=tmp_path),
    )

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "degraded"
    assert "work_orders" in registrar.last_ledger_result.reason
    assert "ledger registration degraded" in caplog.text


def test_read_only_ledger_degrades_without_blocking_md(tmp_path: Path):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    store.connection.execute("PRAGMA query_only=ON")
    registrar, queue_path = _queue_registrar(
        tmp_path,
        LedgerRegistrar(store, project_root=tmp_path),
    )

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "degraded"
    assert "readonly" in registrar.last_ledger_result.reason


def test_missing_ledger_directory_degrades_without_blocking_md(tmp_path: Path):
    registrar, queue_path = _queue_registrar(
        tmp_path,
        LedgerRegistrar(tmp_path / "missing" / "ledger.sqlite", project_root=tmp_path),
    )

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "degraded"
    assert "directory does not exist" in registrar.last_ledger_result.reason


def test_disabled_switch_skips_ledger_but_keeps_md(tmp_path: Path, monkeypatch):
    store = LedgerStore(tmp_path / "ledger.sqlite")
    registrar, queue_path = _queue_registrar(
        tmp_path,
        LedgerRegistrar(store, project_root=tmp_path),
    )
    monkeypatch.setenv("ULTIMA_LEDGER_DISABLED", "1")

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "ok"
    assert registrar.last_ledger_result.reason == "disabled by ULTIMA_LEDGER_DISABLED=1"
    assert store.connection.execute("SELECT COUNT(*) FROM work_orders").fetchone()[0] == 0


def test_unexpected_ledger_exception_is_contained_after_md_write(tmp_path: Path):
    class RaisingRegistrar:
        def register(self, work_order):
            raise OSError("injected ledger failure")

    registrar, queue_path = _queue_registrar(tmp_path, RaisingRegistrar())

    md_written = registrar.record(_task(), "排队")

    assert md_written is True
    assert "wo-ultimaagent-20261108-0030" in queue_path.read_text(encoding="utf-8")
    assert registrar.last_ledger_result.status == "degraded"
    assert registrar.last_ledger_result.reason == "OSError: injected ledger failure"
