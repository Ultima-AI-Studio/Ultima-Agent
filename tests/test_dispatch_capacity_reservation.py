from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
import json
from pathlib import Path

import pytest

from tasks.queue_engine.capacity_reservation import ReservationError, ReservationStore


NOW = datetime(2026, 11, 15, tzinfo=UTC)


def item(rid="r1", *, run="run", package="pkg", attempt="a1", lease="l1", token="t1", revision=1, pid=100, identity="born"):
    return {
        "schemaVersion": 1, "reservationId": rid, "runId": run, "packageId": package,
        "attemptId": attempt, "leaseId": lease, "revision": revision,
        "admissionToken": token, "pid": pid, "processIdentity": identity,
        "issuedAt": NOW.isoformat(), "expiresAt": (NOW - timedelta(seconds=1)).isoformat(),
        "state": "ACTIVE",
    }


def acquire(store, record):
    return store.acquire(record, capacity=2, expected_admission_token="t1", expected_revision=1)


def test_acquire_is_atomic_and_visible_to_another_store(tmp_path: Path):
    first, second = ReservationStore(tmp_path), ReservationStore(tmp_path)
    acquire(first, item())
    observed = second.read("r1")
    assert (observed["reservationId"], observed["packageId"], observed["attemptId"]) == ("r1", "pkg", "a1")


def test_concurrent_acquire_has_exactly_one_winner(tmp_path: Path):
    def contender(name):
        try:
            ReservationStore(tmp_path).acquire(item(run=name), capacity=1, expected_admission_token="t1", expected_revision=1)
            return "OK"
        except (ReservationError, RuntimeError) as exc:
            return getattr(exc, "reason", "RESERVATION_CONFLICT")
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(contender, ("one", "two")))
    assert results.count("OK") == 1
    assert results.count("RESERVATION_CONFLICT") == 1


def test_release_is_idempotent_and_rejects_owner_mismatch(tmp_path: Path):
    store = ReservationStore(tmp_path)
    acquire(store, item())
    assert store.release("r1", run_id="run", lease_id="l1")["state"] == "RELEASED"
    assert store.release("r1", run_id="run", lease_id="l1")["state"] == "RELEASED"
    with pytest.raises(ReservationError, match="OWNER_MISMATCH"):
        store.release("r1", run_id="other", lease_id="l1")


def test_stale_token_and_revision_fail_closed(tmp_path: Path):
    store = ReservationStore(tmp_path)
    with pytest.raises(ReservationError, match="ADMISSION_TOKEN_STALE"):
        store.acquire(item(token="old"), capacity=1, expected_admission_token="t1", expected_revision=1)
    with pytest.raises(ReservationError, match="REVISION_CONFLICT"):
        store.acquire(item(revision=0), capacity=1, expected_admission_token="t1", expected_revision=1)


def test_recover_reaps_only_expired_exited_owned_record(tmp_path: Path):
    store = ReservationStore(tmp_path, process_probe=lambda _pid: None)
    original = acquire(store, item())
    assert store.recover("r1", run_id="run", lease_id="l1", now=NOW) == "RECOVERED"
    updated = store.read("r1")
    assert updated["state"] == "RELEASED"
    assert {k: v for k, v in updated.items() if k != "state"} == {k: v for k, v in original.items() if k != "state"}


def test_recover_retains_live_reused_unknown_and_foreign_records(tmp_path: Path):
    cases = [(lambda _pid: "born", "LEASE_ACTIVE"), (lambda _pid: "new", "PROCESS_IDENTITY_MISMATCH"),
             (lambda _pid: (_ for _ in ()).throw(OSError()), "PROCESS_IDENTITY_UNKNOWN")]
    for index, (probe, reason) in enumerate(cases):
        root = tmp_path / str(index); store = ReservationStore(root, process_probe=probe); acquire(store, item())
        assert store.recover("r1", run_id="run", lease_id="l1", now=NOW) == reason
        assert store.read("r1")["state"] == "ACTIVE"
    store = ReservationStore(tmp_path / "foreign", process_probe=lambda _pid: None); acquire(store, item())
    assert store.recover("r1", run_id="other", lease_id="l1", now=NOW) == "FOREIGN_RECORD"
    foreign_root = tmp_path / "foreign-schema"; foreign_store = ReservationStore(foreign_root, process_probe=lambda _pid: None)
    record = item(); record["unknownField"] = "foreign"
    foreign_root.mkdir(); (foreign_root / "capacity-reservations.json").write_text(json.dumps({"r1": record}), encoding="utf-8")
    assert foreign_store.recover("r1", run_id="run", lease_id="l1", now=NOW) == "FOREIGN_RECORD"
