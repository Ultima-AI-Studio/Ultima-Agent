"""Package capacity reservations sharing the existing dispatch lock primitive."""

from __future__ import annotations

import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Callable

from .dispatcher import DispatchLock, process_identity


FIELDS = {
    "schemaVersion", "reservationId", "runId", "packageId", "attemptId",
    "leaseId", "revision", "admissionToken", "pid", "processIdentity",
    "issuedAt", "expiresAt", "state",
}


class ReservationError(RuntimeError):
    def __init__(self, reason: str) -> None:
        super().__init__(reason)
        self.reason = reason


def _timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ReservationStore:
    def __init__(self, root: str | Path, *, process_probe: Callable[[int], str | None] = process_identity) -> None:
        self.root = Path(root)
        self.path = self.root / "capacity-reservations.json"
        self.lock_path = self.root / ".dispatch.lock"
        self.process_probe = process_probe

    def _load(self) -> dict[str, dict[str, object]]:
        if not self.path.exists():
            return {}
        value = json.loads(self.path.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise ReservationError("FOREIGN_RECORD")
        return value

    def _save(self, records: dict[str, dict[str, object]]) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_suffix(f".tmp-{os.getpid()}")
        temporary.write_text(json.dumps(records, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(temporary, self.path)

    def read(self, reservation_id: str) -> dict[str, object] | None:
        with DispatchLock(self.lock_path):
            record = self._load().get(reservation_id)
            return dict(record) if record is not None else None

    def acquire(
        self,
        record: dict[str, object],
        *,
        capacity: int,
        expected_admission_token: str,
        expected_revision: int,
    ) -> dict[str, object]:
        if set(record) != FIELDS:
            raise ReservationError("FOREIGN_RECORD")
        if record["admissionToken"] != expected_admission_token:
            raise ReservationError("ADMISSION_TOKEN_STALE")
        if record["revision"] != expected_revision:
            raise ReservationError("REVISION_CONFLICT")
        with DispatchLock(self.lock_path):
            records = self._load()
            key = str(record["reservationId"])
            current = records.get(key)
            identity = tuple(record[name] for name in ("runId", "packageId", "attemptId", "leaseId"))
            if current is not None:
                if set(current) != FIELDS:
                    raise ReservationError("FOREIGN_RECORD")
                current_identity = tuple(current[name] for name in ("runId", "packageId", "attemptId", "leaseId"))
                if current_identity != identity:
                    raise ReservationError("RESERVATION_CONFLICT")
                if current["admissionToken"] != expected_admission_token:
                    raise ReservationError("ADMISSION_TOKEN_STALE")
                if current["revision"] != expected_revision:
                    raise ReservationError("REVISION_CONFLICT")
                return dict(current)
            active = sum(item.get("state") == "ACTIVE" for item in records.values())
            if capacity < 1 or active >= capacity:
                raise ReservationError("RESERVATION_CONFLICT")
            stored = dict(record)
            stored["state"] = "ACTIVE"
            records[key] = stored
            self._save(records)
            return dict(stored)

    def release(self, reservation_id: str, *, run_id: str, lease_id: str) -> dict[str, object]:
        with DispatchLock(self.lock_path):
            records = self._load()
            record = records.get(reservation_id)
            if record is None or set(record) != FIELDS:
                raise ReservationError("FOREIGN_RECORD")
            if record["runId"] != run_id or record["leaseId"] != lease_id:
                raise ReservationError("OWNER_MISMATCH")
            if record["state"] != "RELEASED":
                record["state"] = "RELEASED"
                self._save(records)
            return dict(record)

    def recover(self, reservation_id: str, *, run_id: str, lease_id: str, now: datetime) -> str:
        with DispatchLock(self.lock_path):
            records = self._load()
            record = records.get(reservation_id)
            if record is None or set(record) != FIELDS:
                return "FOREIGN_RECORD"
            if record["runId"] != run_id or record["leaseId"] != lease_id:
                return "FOREIGN_RECORD"
            if record["state"] != "ACTIVE":
                return "RELEASED"
            if now.astimezone(UTC) < _timestamp(str(record["expiresAt"])).astimezone(UTC):
                return "LEASE_ACTIVE"
            pid, stored_identity = record["pid"], record["processIdentity"]
            if not isinstance(pid, int) or pid <= 0 or not isinstance(stored_identity, str) or not stored_identity:
                return "PROCESS_IDENTITY_UNKNOWN"
            try:
                observed = self.process_probe(pid)
            except Exception:
                return "PROCESS_IDENTITY_UNKNOWN"
            if observed == stored_identity:
                return "LEASE_ACTIVE"
            if observed is not None:
                return "PROCESS_IDENTITY_MISMATCH"
            record["state"] = "RELEASED"
            self._save(records)
            return "RECOVERED"
