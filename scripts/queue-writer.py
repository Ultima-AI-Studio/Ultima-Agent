"""Single atomic writer for tasks/queue/queue-status.json."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tasks.queue_engine.dispatcher import DispatchLock


QUEUE_STATUS = ROOT / "tasks" / "queue" / "queue-status.json"
STATES = {"frozen", "blocked", "cancelled", "pending", "closed", "audit", "executing"}
REQUIRED_FIELDS = {
    "project",
    "work_order",
    "state",
    "audit_passed",
    "dispatched_at",
    "audit_run",
    "freeze_commit",
    "note",
}


def _claim_id(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("new queue writes require a non-empty claim_id")
    return value.strip()


def validate_document(document: dict[str, Any]) -> list[dict[str, Any]]:
    if document.get("schema_version") != 1:
        raise ValueError("queue-status.json schema_version must be 1")
    records = document.get("records")
    if not isinstance(records, list):
        raise ValueError("queue-status.json records must be a list")
    identities: set[tuple[str, str]] = set()
    claims: set[str] = set()
    for index, record in enumerate(records):
        if not isinstance(record, dict) or not REQUIRED_FIELDS.issubset(record):
            raise ValueError(f"record {index} lacks required fields")
        if record["state"] not in STATES:
            raise ValueError(f"record {index} has invalid state")
        identity = (str(record["project"]), str(record["work_order"]))
        if not all(identity) or identity in identities:
            raise ValueError(f"record {index} has a missing or duplicate identity")
        identities.add(identity)
        if "claim_id" in record:
            claim = _claim_id(record["claim_id"])
            if claim in claims:
                raise ValueError(f"record {index} has a duplicate claim_id")
            claims.add(claim)
    return records


def _result(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": record["project"],
        "work_order": record["work_order"],
        "claim_id": record["claim_id"],
        "state": record["state"],
        "note": record["note"],
        "dispatched_at": record.get("dispatched_at"),
        "audit_run": record.get("audit_run"),
    }


def _default_lock_path(queue_path: Path) -> Path:
    identity = hashlib.sha256(str(queue_path.resolve()).casefold().encode("utf-8")).hexdigest()[:20]
    return Path(tempfile.gettempdir()) / f"ultimaagent-queue-writer-{identity}.lock"


def _atomic_replace(
    path: Path,
    updated: bytes,
    original: bytes,
    replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], Any],
) -> None:
    descriptor, raw_temporary = tempfile.mkstemp(
        dir=path.parent, prefix=path.name + ".", suffix=".tmp"
    )
    temporary = Path(raw_temporary)
    replaced = False
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(updated)
            stream.flush()
            os.fsync(stream.fileno())
        if path.read_bytes() != original:
            raise RuntimeError("queue changed after lock-in readback")
        replace_func(temporary, path)
        replaced = True
        if path.read_bytes() != updated:
            raise RuntimeError("queue atomic replacement verification failed")
    except BaseException:
        if replaced:
            restore_descriptor, raw_restore = tempfile.mkstemp(
                dir=path.parent, prefix=path.name + ".restore.", suffix=".tmp"
            )
            restore = Path(raw_restore)
            try:
                with os.fdopen(restore_descriptor, "wb") as stream:
                    stream.write(original)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(restore, path)
            finally:
                restore.unlink(missing_ok=True)
        raise
    finally:
        temporary.unlink(missing_ok=True)


def apply_update(
    *,
    queue_path: str | Path,
    action: str,
    project: str,
    work_order: str,
    claim_id: str | None,
    target: str,
    note: str,
    expected_state: str | None = None,
    expected_run: str | None = None,
    expected_sha256: str | None = None,
    dispatched_at: str | None = None,
    audit_run: str | None = None,
    lock_path: str | Path | None = None,
    replace_func: Callable[[str | os.PathLike[str], str | os.PathLike[str]], Any] = os.replace,
) -> dict[str, Any]:
    path = Path(queue_path)
    claim = _claim_id(claim_id)
    if action not in {"claim", "transition"}:
        raise ValueError("action must be claim or transition")
    if target not in STATES:
        raise ValueError("target is not a queue state")
    lock = DispatchLock(Path(lock_path) if lock_path else _default_lock_path(path))
    with lock:
        original = path.read_bytes()
        version = hashlib.sha256(original).hexdigest()
        if expected_sha256 is not None and version != expected_sha256:
            raise RuntimeError("queue expected version does not match")
        try:
            document = json.loads(original.decode("utf-8-sig"))
        except (UnicodeError, ValueError) as exc:
            raise ValueError(f"queue-status.json is not valid JSON: {exc}") from exc
        records = validate_document(document)
        claimed = [record for record in records if record.get("claim_id") == claim]
        if claimed:
            if len(claimed) != 1 or (
                claimed[0]["project"], claimed[0]["work_order"]
            ) != (project, work_order):
                raise ValueError("claim_id already belongs to another queue record")
            if action == "claim":
                first = _result(claimed[0])
                return {
                    "duplicate": True,
                    "first_result": first,
                    "result": first,
                    "version": version,
                }
        matches = [
            record
            for record in records
            if record["project"] == project and record["work_order"] == work_order
        ]
        if len(matches) != 1:
            raise ValueError("queue identity is not registered exactly once")
        record = matches[0]
        if action == "transition" and record.get("claim_id") != claim:
            raise ValueError("claim_id is stale or does not own this dispatch")
        if expected_state is not None and record.get("state") != expected_state:
            raise RuntimeError("queue state changed before writer update")
        if expected_run is not None and expected_run not in str(record.get("note") or ""):
            raise RuntimeError("queue run changed before writer update")
        record["claim_id"] = claim
        record["state"] = target
        record["note"] = note
        if target == "executing":
            record["dispatched_at"] = dispatched_at or datetime.now(timezone.utc).isoformat()
        if target == "audit":
            record["audit_run"] = audit_run
        validate_document(document)
        updated = (json.dumps(document, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
        _atomic_replace(path, updated, original, replace_func)
        result = _result(record)
        return {
            "duplicate": False,
            "result": result,
            "version": hashlib.sha256(updated).hexdigest(),
        }


def selftest() -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="queue-writer-selftest-") as raw:
        root = Path(raw)
        queue = root / "queue-status.json"
        lock = root / "writer.lock"
        document = {
            "schema_version": 1,
            "records": [
                {
                    "project": "UltimaAgent",
                    "work_order": "wo-selftest-20261114-0001",
                    "state": "pending",
                    "audit_passed": False,
                    "dispatched_at": None,
                    "audit_run": None,
                    "freeze_commit": None,
                    "note": "fixture",
                }
            ],
        }
        queue.write_text(json.dumps(document) + "\n", encoding="utf-8")
        request = dict(
            queue_path=queue,
            action="claim",
            project="UltimaAgent",
            work_order="wo-selftest-20261114-0001",
            claim_id="selftest-claim",
            target="executing",
            note="selftest",
            expected_state="pending",
            lock_path=lock,
        )
        first = apply_update(**request)
        after_first = queue.read_bytes()
        duplicate = apply_update(**request)
        if first["duplicate"] or not duplicate["duplicate"] or queue.read_bytes() != after_first:
            raise AssertionError("duplicate claim changed the queue")
        document["records"][0]["state"] = "pending"
        queue.write_text(json.dumps(document) + "\n", encoding="utf-8")
        before_failure = queue.read_bytes()

        def fail_replace(_source, _target):
            raise PermissionError("selftest replacement failure")

        try:
            apply_update(**request, replace_func=fail_replace)
        except PermissionError:
            pass
        else:
            raise AssertionError("replacement failure was not propagated")
        if queue.read_bytes() != before_failure:
            raise AssertionError("replacement failure changed the queue")
        return {"selftest": "PASS", "duplicate": True, "isolated_root": str(root)}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--selftest", action="store_true")
    parser.add_argument("--queue", type=Path, default=QUEUE_STATUS)
    parser.add_argument("--action", choices=["claim", "transition"])
    parser.add_argument("--project", default="UltimaAgent")
    parser.add_argument("--work-order")
    parser.add_argument("--claim-id")
    parser.add_argument("--target", choices=sorted(STATES))
    parser.add_argument("--note")
    parser.add_argument("--expected-state")
    parser.add_argument("--expected-run")
    parser.add_argument("--expected-sha256")
    parser.add_argument("--dispatched-at")
    parser.add_argument("--audit-run")
    parser.add_argument("--lock", type=Path)
    args = parser.parse_args()
    if args.selftest:
        print(json.dumps(selftest(), ensure_ascii=False))
        return 0
    required = (args.action, args.work_order, args.target, args.note)
    if any(value is None for value in required):
        parser.error("--action, --work-order, --target and --note are required")
    result = apply_update(
        queue_path=args.queue,
        action=args.action,
        project=args.project,
        work_order=args.work_order,
        claim_id=args.claim_id,
        target=args.target,
        note=args.note,
        expected_state=args.expected_state,
        expected_run=args.expected_run,
        expected_sha256=args.expected_sha256,
        dispatched_at=args.dispatched_at,
        audit_run=args.audit_run,
        lock_path=args.lock,
    )
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"blocked": True, "reason": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise SystemExit(2)
