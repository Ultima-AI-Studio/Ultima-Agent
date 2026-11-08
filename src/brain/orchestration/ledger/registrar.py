"""Best-effort bridge from the markdown queue registration to SQLite."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
from typing import Any, Literal, Mapping

from .store import LedgerStore


LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class RegisterResult:
    status: Literal["ok", "degraded"]
    reason: str | None = None


class LedgerRegistrar:
    """Register one queue work order without ever making ledger a hard dependency."""

    def __init__(
        self,
        store_or_path: LedgerStore | str | Path,
        *,
        project_root: str | Path,
    ) -> None:
        self._store = store_or_path if isinstance(store_or_path, LedgerStore) else None
        self._path = None if self._store is not None else Path(store_or_path)
        self.project_root = Path(project_root)

    def register(self, work_order: Any) -> RegisterResult:
        if os.getenv("ULTIMA_LEDGER_DISABLED") == "1":
            return RegisterResult("ok", "disabled by ULTIMA_LEDGER_DISABLED=1")

        data = self._work_order_data(work_order)
        work_order_id = str(data.get("work_order_id") or data.get("task_id") or "")
        try:
            store, owns_store = self._open_store()
            try:
                self._write(store, data)
            finally:
                if owns_store:
                    store.close()
        except Exception as exc:  # ledger is an explicitly best-effort side effect
            reason = f"{type(exc).__name__}: {exc}"
            LOGGER.warning("ledger registration degraded for %s: %s", work_order_id, reason)
            return RegisterResult("degraded", reason)
        return RegisterResult("ok")

    def _open_store(self) -> tuple[LedgerStore, bool]:
        if self._store is not None:
            return self._store, False
        assert self._path is not None
        if not self._path.parent.is_dir():
            raise FileNotFoundError(f"ledger directory does not exist: {self._path.parent}")
        return LedgerStore(self._path), True

    def _write(self, store: LedgerStore, data: Mapping[str, Any]) -> None:
        project_id = str(data.get("project_id") or data.get("project_key") or "ultimaagent")
        project_name = str(data.get("project_name") or self._project_name(project_id))
        goal_id = str(data.get("goal_id") or "queue-registration")
        work_order_id = str(data.get("work_order_id") or data.get("task_id") or "")
        if not work_order_id:
            raise ValueError("work order id is required")
        title = str(data.get("title") or work_order_id)
        write_scope = list(data.get("write_scope") or data.get("permissions") or ())
        acceptance = list(data.get("acceptance") or ())
        source_hash = str(data.get("source_hash") or self._source_hash(data))

        with store.transaction():
            store.put_project(project_id, project_name, self.project_root)
            store.put_goal(
                project_id,
                goal_id,
                "Queue registration",
                allowed_write_roots=write_scope,
                acceptance=acceptance,
                prohibited=[],
            )
            store.put_work_order(
                project_id,
                work_order_id,
                goal_id,
                title,
                category=str(data.get("category") or "orchestration"),
                state="ready",
                revision=int(data.get("revision") or 1),
                source_hash=source_hash,
                write_scope=write_scope,
                acceptance=acceptance,
            )

    @staticmethod
    def _work_order_data(work_order: Any) -> dict[str, Any]:
        if isinstance(work_order, Mapping):
            return dict(work_order)
        if hasattr(work_order, "as_dict"):
            return dict(work_order.as_dict())
        if is_dataclass(work_order):
            return asdict(work_order)
        if hasattr(work_order, "__dict__"):
            return dict(vars(work_order))
        raise TypeError("work_order must be a mapping or record object")

    @staticmethod
    def _source_hash(data: Mapping[str, Any]) -> str:
        payload = json.dumps(data, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    @staticmethod
    def _project_name(project_id: str) -> str:
        if project_id.startswith("ultima"):
            return "Ultima" + project_id[len("ultima") :].capitalize()
        return project_id.capitalize()
