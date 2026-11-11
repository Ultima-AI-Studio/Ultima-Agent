"""Windowless entry point for the read-only relay decision loop.

The disabled-by-default scheduled task ``UltimaAgent-RelayLoop`` is intended to
launch this file with ``tools/venv-openjarvis/Scripts/pythonw.exe``.  This file
does not register or enable that task.
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import sys
import tempfile
import threading
from typing import Any, Sequence


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tasks.queue_engine.dispatcher import process_identity
from tasks.queue_engine.relay import (
    DispatcherClient,
    QueueStatusView,
    RelayContractError,
    RelayPolicy,
    RelayPump,
    RelayStateStore,
)


POLICY_PATH = ROOT / "tasks" / "queue" / "relay-policy.json"
STATE_PATH = ROOT / "tasks" / "queue" / "relay-state.json"
TEMP_ROOT = Path(os.environ.get("TEMP") or tempfile.gettempdir())
PID_PATH = TEMP_ROOT / "ultima-relay.pid"
STOP_PATH = TEMP_ROOT / "ultima-relay.stop"


class RelayPidLock:
    """Own the relay singleton only when PID and creation identity both match."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.pid = os.getpid()
        self.identity = process_identity(self.pid)
        if self.identity is None:
            raise RelayContractError("cannot determine relay process identity")
        self.acquired = False

    def acquire(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        for _ in range(2):
            owner = self._owner()
            if owner is not None:
                pid, identity = owner
                if process_identity(pid) == identity:
                    raise RelayContractError("relay already running")
                self.path.unlink(missing_ok=True)
            payload = (
                json.dumps(
                    {"pid": self.pid, "identity": self.identity},
                    ensure_ascii=False,
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            try:
                with self.path.open("xb") as stream:
                    stream.write(payload)
                    stream.flush()
                    os.fsync(stream.fileno())
                self.acquired = True
                return
            except FileExistsError:
                continue
        raise RelayContractError("relay singleton lock raced")

    def release(self) -> None:
        if self.acquired and self._owner() == (self.pid, self.identity):
            self.path.unlink(missing_ok=True)
        self.acquired = False

    def _owner(self) -> tuple[int, str] | None:
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
            pid = value.get("pid")
            identity = value.get("identity")
            if type(pid) is int and isinstance(identity, str):
                return pid, identity
        except (FileNotFoundError, OSError, UnicodeDecodeError, json.JSONDecodeError):
            return None
        return None


def load_policy(path: str | Path = POLICY_PATH) -> RelayPolicy:
    policy_path = Path(path)
    try:
        raw = policy_path.read_bytes()
    except OSError as exc:
        raise RelayContractError(f"cannot read relay policy: {exc}") from exc
    if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
        raise RelayContractError("relay policy must be UTF-8 without BOM and use LF")
    try:
        document = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RelayContractError(f"invalid relay policy: {exc}") from exc
    if not isinstance(document, dict):
        raise RelayContractError("relay policy must be an object")

    allowed = {
        "eligible_orders",
        "dependsOn",
        "max_actions_per_tick",
        "max_actions_per_day",
        "cooldown_s",
        "real_dispatch_enabled",
        "max_consecutive_failures",
        "max_runtime_seconds",
    }
    unknown = sorted(set(document) - allowed)
    if unknown:
        raise RelayContractError(f"unknown relay policy fields: {unknown}")

    eligible = document.get("eligible_orders", [])
    dependencies = document.get("dependsOn", {})
    if not isinstance(eligible, list) or not all(isinstance(item, str) for item in eligible):
        raise RelayContractError("eligible_orders must be a list of strings")
    if not isinstance(dependencies, dict) or not all(
        isinstance(order, str)
        and isinstance(items, list)
        and all(isinstance(item, str) for item in items)
        for order, items in dependencies.items()
    ):
        raise RelayContractError("dependsOn must map orders to string lists")

    values: dict[str, Any] = {
        "max_actions_per_tick": document.get("max_actions_per_tick", 1),
        "max_actions_per_day": document.get("max_actions_per_day", 2),
        "cooldown_s": document.get("cooldown_s", 30.0),
        "real_dispatch_enabled": document.get("real_dispatch_enabled", False),
        "max_consecutive_failures": document.get("max_consecutive_failures", 2),
        "max_runtime_seconds": document.get("max_runtime_seconds", 1800),
    }
    for key in (
        "max_actions_per_tick",
        "max_actions_per_day",
        "max_consecutive_failures",
        "max_runtime_seconds",
    ):
        if type(values[key]) is not int or values[key] <= 0:
            raise RelayContractError(f"{key} must be a positive integer")
    if (
        isinstance(values["cooldown_s"], bool)
        or not isinstance(values["cooldown_s"], (int, float))
        or values["cooldown_s"] < 0
    ):
        raise RelayContractError("cooldown_s must be a non-negative number")
    if type(values["real_dispatch_enabled"]) is not bool:
        raise RelayContractError("real_dispatch_enabled must be a boolean")

    return RelayPolicy(
        eligible_orders=tuple(eligible),
        depends_on={order: tuple(items) for order, items in dependencies.items()},
        **values,
    )


def make_pump(*, root: Path, execute: bool) -> tuple[RelayPump, RelayPolicy]:
    policy = load_policy(root / "tasks" / "queue" / "relay-policy.json")
    store = RelayStateStore(root / "tasks" / "queue" / "relay-state.json")
    state = store.load()
    dispatcher = None
    if execute:
        dispatcher = DispatcherClient(
            root=root,
            policy=policy,
            execute_requested=True,
        )
    return (
        RelayPump(
            root=root,
            view=QueueStatusView(root),
            policy=policy,
            state=state,
            execute=execute,
            dispatcher=dispatcher,
            state_store=store if execute else None,
        ),
        policy,
    )


def write_stop_marker(path: str | Path = STOP_PATH) -> None:
    marker = Path(path)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("stop\n", encoding="utf-8", newline="\n")


def emit_json(value: Any, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    if stream is not None:
        print(
            json.dumps(value, ensure_ascii=False, sort_keys=True),
            file=stream,
            flush=True,
        )


def run(
    stop_event: threading.Event,
    interval_s: float,
    *,
    pump: RelayPump,
    max_actions: int,
    stop_path: str | Path = STOP_PATH,
) -> dict[str, Any] | None:
    if interval_s <= 0:
        raise RelayContractError("interval_s must be positive")
    marker = Path(stop_path)
    last_result: dict[str, Any] | None = None
    while not stop_event.is_set() and not marker.exists():
        last_result = pump.pump_once(max_actions)
        emit_json(last_result)
        if stop_event.wait(interval_s):
            break
    return last_result


def _parser() -> argparse.ArgumentParser:
    pythonw = ROOT / "tools" / "venv-openjarvis" / "Scripts" / "pythonw.exe"
    script = ROOT / "scripts" / "relay-loop.py"
    parser = argparse.ArgumentParser(
        description="Bounded automatic relay loop (dry-run by default).",
        epilog=(
            "Registration example only; this script never enables it: "
            f'schtasks /Create /TN UltimaAgent-RelayLoop /SC ONLOGON /TR "'
            f"{pythonw} {script} --start --dry-run\" /F"
        ),
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--start", action="store_true", help="run the interval loop")
    action.add_argument("--once", action="store_true", help="run one bounded tick")
    action.add_argument("--status", action="store_true", help="read relay state as JSON")
    action.add_argument("--stop", action="store_true", help="write the stop marker")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="do not invoke the dispatcher")
    mode.add_argument("--execute", action="store_true", help="request policy-gated dispatch")
    parser.add_argument("--interval-s", type=float, default=30.0)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        if args.status:
            state = RelayStateStore(STATE_PATH).load()
            emit_json(
                {
                    "halted": state.halted,
                    "actions_today": state.actions_today,
                    "last_order": state.last_order,
                }
            )
            return 0
        if args.stop:
            write_stop_marker(STOP_PATH)
            emit_json({"stop_requested": True})
            return 0

        lock = RelayPidLock(PID_PATH)
        lock.acquire()
        try:
            STOP_PATH.unlink(missing_ok=True)
            pump, policy = make_pump(root=ROOT, execute=args.execute)
            if args.once:
                result = pump.pump_once(policy.max_actions_per_tick)
                emit_json(result)
            else:
                run(
                    threading.Event(),
                    args.interval_s,
                    pump=pump,
                    max_actions=policy.max_actions_per_tick,
                    stop_path=STOP_PATH,
                )
            return 0
        finally:
            lock.release()
    except (OSError, RelayContractError) as exc:
        emit_json(
            {"error": str(exc), "type": type(exc).__name__},
            error=True,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
