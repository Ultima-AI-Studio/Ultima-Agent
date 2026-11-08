"""Small SQLite ledger that preserves the frozen Manager core contract."""

from __future__ import annotations

import json
import sqlite3
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Sequence


class VersionConflict(RuntimeError):
    """A compare-and-swap write observed a different durable version."""


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class LedgerStore:
    """Five-table SQLite ledger with explicit transactions and optimistic CAS."""

    _WORK_ORDER_CAS_FIELDS = {"state", "reservation", "idle_reason"}

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._local = threading.local()
        self.connection: sqlite3.Connection | None = sqlite3.connect(
            self.path,
            timeout=10,
            isolation_level=None,
            check_same_thread=False,
        )
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys=ON")
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        schema_path = Path(__file__).with_name("schema.sql")
        try:
            self.connection.executescript(schema_path.read_text(encoding="utf-8"))
        except BaseException:
            self.close()
            raise

    def _connection(self) -> sqlite3.Connection:
        if self.connection is None:
            raise RuntimeError("ledger store is closed")
        return self.connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        """Commit the block atomically; nested blocks use SQLite savepoints."""
        with self._lock:
            connection = self._connection()
            depth = getattr(self._local, "transaction_depth", 0)
            savepoint = f"ledger_tx_{depth}"
            if depth == 0:
                connection.execute("BEGIN IMMEDIATE")
            else:
                connection.execute(f"SAVEPOINT {savepoint}")
            self._local.transaction_depth = depth + 1
            try:
                yield connection
            except BaseException:
                if depth == 0:
                    connection.rollback()
                else:
                    connection.execute(f"ROLLBACK TO SAVEPOINT {savepoint}")
                    connection.execute(f"RELEASE SAVEPOINT {savepoint}")
                raise
            else:
                if depth == 0:
                    connection.commit()
                else:
                    connection.execute(f"RELEASE SAVEPOINT {savepoint}")
            finally:
                self._local.transaction_depth = depth

    def close(self) -> None:
        with self._lock:
            if self.connection is not None:
                self.connection.close()
                self.connection = None

    def put_project(
        self,
        project_id: str,
        name: str,
        root_path: str | Path,
        *,
        adapter: dict[str, Any] | None = None,
        ownership_state: str = "managed_new",
        ownership_reason: str | None = None,
        paused: bool = False,
    ) -> None:
        with self._lock:
            self._connection().execute(
                """INSERT INTO projects(
                       project_id,name,root_path,adapter_json,ownership_state,
                       ownership_reason,paused
                   ) VALUES(?,?,?,?,?,?,?)
                   ON CONFLICT(project_id) DO NOTHING""",
                (
                    project_id,
                    name,
                    str(Path(root_path)),
                    _dump(adapter or {}),
                    ownership_state,
                    ownership_reason,
                    int(paused),
                ),
            )

    def put_goal(
        self,
        project_id: str,
        goal_id: str,
        title: str,
        *,
        revision: int = 1,
        approved: bool = True,
        allowed_write_roots: Sequence[str] = (),
        acceptance: Sequence[str] = (),
        prohibited: Sequence[str] = (),
        max_tasks: int = 1,
        hold: bool = False,
    ) -> None:
        with self._lock:
            self._connection().execute(
                """INSERT INTO goals(
                       project_id,goal_id,title,revision,approved,
                       allowed_write_roots_json,acceptance_json,prohibited_json,
                       max_tasks,hold
                   ) VALUES(?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(project_id,goal_id) DO NOTHING""",
                (
                    project_id,
                    goal_id,
                    title,
                    revision,
                    int(approved),
                    _dump(list(allowed_write_roots)),
                    _dump(list(acceptance)),
                    _dump(list(prohibited)),
                    max_tasks,
                    int(hold),
                ),
            )

    def put_work_order(
        self,
        project_id: str,
        work_order_id: str,
        goal_id: str,
        title: str,
        *,
        category: str,
        state: str,
        revision: int = 1,
        source_hash: str,
        write_scope: Sequence[str] = (),
        acceptance: Sequence[str] = (),
        idle_reason: str | None = None,
        reservation: str | None = None,
    ) -> None:
        with self._lock:
            self._connection().execute(
                """INSERT INTO work_orders(
                       project_id,work_order_id,goal_id,title,category,state,
                       revision,source_hash,write_scope_json,acceptance_json,
                       idle_reason,reservation
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(project_id,work_order_id) DO NOTHING""",
                (
                    project_id,
                    work_order_id,
                    goal_id,
                    title,
                    category,
                    state,
                    revision,
                    source_hash,
                    _dump(list(write_scope)),
                    _dump(list(acceptance)),
                    idle_reason,
                    reservation,
                ),
            )

    def get_work_order(self, project_id: str, work_order_id: str) -> dict[str, Any]:
        with self._lock:
            row = self._connection().execute(
                "SELECT * FROM work_orders WHERE project_id=? AND work_order_id=?",
                (project_id, work_order_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, work_order_id))
        result = dict(row)
        result["write_scope"] = json.loads(result.pop("write_scope_json"))
        result["acceptance"] = json.loads(result.pop("acceptance_json"))
        return result

    def cas_work_order(
        self,
        project_id: str,
        work_order_id: str,
        expected_version: int,
        **fields: Any,
    ) -> dict[str, Any]:
        if not fields:
            raise ValueError("CAS requires at least one field")
        unsupported = set(fields) - self._WORK_ORDER_CAS_FIELDS
        if unsupported:
            raise ValueError(f"unsupported CAS fields: {sorted(unsupported)}")
        assignments = [f"{name}=?" for name in fields]
        assignments.extend(["version=version+1", "updated_at=CURRENT_TIMESTAMP"])
        values = [fields[name] for name in fields]
        values.extend([project_id, work_order_id, expected_version])
        with self.transaction() as connection:
            cursor = connection.execute(
                f"UPDATE work_orders SET {','.join(assignments)} "
                "WHERE project_id=? AND work_order_id=? AND version=?",
                values,
            )
            if cursor.rowcount != 1:
                exists = connection.execute(
                    "SELECT 1 FROM work_orders WHERE project_id=? AND work_order_id=?",
                    (project_id, work_order_id),
                ).fetchone()
                if exists is None:
                    raise KeyError((project_id, work_order_id))
                raise VersionConflict(
                    f"work order version changed: expected {expected_version}"
                )
        return self.get_work_order(project_id, work_order_id)

    def put_stage(
        self,
        project_id: str,
        work_order_id: str,
        stage_id: str,
        *,
        phase: str,
        state: str,
        source_hash: str,
        created_seq: int,
        goal_id: str = "",
        goal_revision: int = 0,
        priority: int = 0,
        dependencies: Sequence[str] = (),
        write_scope: Sequence[str] = (),
        acceptance: Sequence[str] = (),
        task_contract: dict[str, Any] | None = None,
        max_repairs: int = 2,
    ) -> None:
        with self._lock:
            self._connection().execute(
                """INSERT INTO stages(
                       project_id,work_order_id,stage_id,phase,goal_id,goal_revision,
                       state,source_hash,priority,dependencies_json,write_scope_json,
                       acceptance_json,task_contract_json,max_repairs,created_seq
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(project_id,work_order_id,stage_id) DO NOTHING""",
                (
                    project_id,
                    work_order_id,
                    stage_id,
                    phase,
                    goal_id,
                    goal_revision,
                    state,
                    source_hash,
                    priority,
                    _dump(list(dependencies)),
                    _dump(list(write_scope)),
                    _dump(list(acceptance)),
                    _dump(task_contract or {}),
                    max_repairs,
                    created_seq,
                ),
            )

    def put_run(
        self,
        project_id: str,
        work_order_id: str,
        stage_id: str,
        run_id: str,
        *,
        phase: str,
        state: str,
        source_hash: str,
        cwd: str | Path,
        allowed_write_roots: Sequence[str],
        evidence_dir: str | Path,
        reservation: str,
        goal_id: str = "",
        goal_revision: int = 0,
        created_at: float | None = None,
    ) -> None:
        with self._lock:
            self._connection().execute(
                """INSERT INTO runs(
                       project_id,work_order_id,stage_id,run_id,phase,goal_id,
                       goal_revision,state,source_hash,cwd,allowed_write_roots_json,
                       evidence_dir,reservation,created_at
                   ) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                   ON CONFLICT(project_id,work_order_id,stage_id,run_id) DO NOTHING""",
                (
                    project_id,
                    work_order_id,
                    stage_id,
                    run_id,
                    phase,
                    goal_id,
                    goal_revision,
                    state,
                    source_hash,
                    str(Path(cwd)),
                    _dump(list(allowed_write_roots)),
                    str(Path(evidence_dir)),
                    reservation,
                    time.time() if created_at is None else created_at,
                ),
            )

    def list_runs(
        self,
        project_id: str | None = None,
        work_order_id: str | None = None,
        state: str | None = None,
    ) -> list[dict[str, Any]]:
        clauses: list[str] = []
        values: list[str] = []
        for column, value in (
            ("project_id", project_id),
            ("work_order_id", work_order_id),
            ("state", state),
        ):
            if value is not None:
                clauses.append(f"{column}=?")
                values.append(value)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        with self._lock:
            rows = self._connection().execute(
                "SELECT * FROM runs" + where + " ORDER BY created_at,run_id",
                values,
            ).fetchall()
        return [self._decode_run(row) for row in rows]

    def update_run_process(
        self,
        project_id: str,
        work_order_id: str,
        stage_id: str,
        run_id: str,
        pid: int,
        process_identity: str,
        state: str,
    ) -> dict[str, Any]:
        if not isinstance(pid, int) or pid <= 0:
            raise ValueError("running state requires pid > 0")
        if not process_identity:
            raise ValueError("running state requires process_identity")
        if state != "running":
            raise ValueError("update_run_process state must be running")
        with self._lock:
            cursor = self._connection().execute(
                """UPDATE runs SET pid=?,process_identity=?,state=?,started_at=?
                   WHERE project_id=? AND work_order_id=? AND stage_id=? AND run_id=?""",
                (
                    pid,
                    process_identity,
                    state,
                    time.time(),
                    project_id,
                    work_order_id,
                    stage_id,
                    run_id,
                ),
            )
        if cursor.rowcount != 1:
            raise KeyError((project_id, work_order_id, stage_id, run_id))
        return self._get_run(project_id, work_order_id, stage_id, run_id)

    def finish_run(
        self,
        project_id: str,
        work_order_id: str,
        stage_id: str,
        run_id: str,
        *,
        exit_code: int,
        finished_at: float | None = None,
    ) -> dict[str, Any]:
        state = "passed" if exit_code == 0 else "failed"
        with self._lock:
            cursor = self._connection().execute(
                """UPDATE runs SET state=?,exit_code=?,finished_at=?
                   WHERE project_id=? AND work_order_id=? AND stage_id=? AND run_id=?""",
                (
                    state,
                    exit_code,
                    time.time() if finished_at is None else finished_at,
                    project_id,
                    work_order_id,
                    stage_id,
                    run_id,
                ),
            )
        if cursor.rowcount != 1:
            raise KeyError((project_id, work_order_id, stage_id, run_id))
        return self._get_run(project_id, work_order_id, stage_id, run_id)

    def _get_run(
        self,
        project_id: str,
        work_order_id: str,
        stage_id: str,
        run_id: str,
    ) -> dict[str, Any]:
        with self._lock:
            row = self._connection().execute(
                """SELECT * FROM runs
                   WHERE project_id=? AND work_order_id=? AND stage_id=? AND run_id=?""",
                (project_id, work_order_id, stage_id, run_id),
            ).fetchone()
        if row is None:
            raise KeyError((project_id, work_order_id, stage_id, run_id))
        return self._decode_run(row)

    @staticmethod
    def _decode_run(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        for encoded, decoded in (
            ("allowed_write_roots_json", "allowed_write_roots"),
            ("receipt_evidence_json", "receipt_evidence"),
            ("review_findings_json", "review_findings"),
            ("acceptance_result_json", "acceptance_result"),
            ("transport_facts_json", "transport_facts"),
        ):
            result[decoded] = json.loads(result.pop(encoded))
        return result
