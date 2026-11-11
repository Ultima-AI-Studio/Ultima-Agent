"""Read-only relay decisions for the queue-status dispatch authority.

The relay maps queue-status values into the existing ``QueueState`` enum only
for decisions.  It never maps states back and never writes task state.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
from typing import Any, Mapping, Sequence

from .dispatcher import BACKGROUND_CREATION_FLAGS
from .state_machine import QueueState


class RelayContractError(ValueError):
    """Raised when relay input cannot be handled without guessing."""


# queue-status has no values corresponding to QueueState.SELF_CHECK,
# QueueState.FAILED, or any relay-local fallback. Unknown input fails closed.
STATUS_TO_STATE: dict[str, QueueState] = {
    "pending": QueueState.QUEUED,
    "executing": QueueState.EXECUTING,
    "audit": QueueState.AUDIT,
    "frozen": QueueState.COMPLETED,
    "closed": QueueState.COMPLETED,
    "blocked": QueueState.BLOCKED,
    "cancelled": QueueState.CANCELLED,
}


@dataclass(frozen=True)
class RelayPolicy:
    eligible_orders: tuple[str, ...] = ()
    depends_on: Mapping[str, tuple[str, ...]] = field(default_factory=dict)
    max_actions_per_tick: int = 1
    max_actions_per_day: int = 2
    cooldown_s: float = 30.0
    real_dispatch_enabled: bool = False
    max_consecutive_failures: int = 2
    max_runtime_seconds: int = 1800

    @property
    def dependsOn(self) -> Mapping[str, tuple[str, ...]]:
        """Expose the policy file's spelling without duplicating its data."""
        return self.depends_on


@dataclass(frozen=True)
class Candidate:
    order: str
    record: Mapping[str, Any]


@dataclass
class RelayState:
    day_key: str = ""
    actions_today: int = 0
    halted: bool = False
    halt_reason: str | None = None
    last_order: str | None = None
    last_run: str | None = None
    attempts: int = 0
    consecutive_failures: int = 0
    last_failure: Mapping[str, Any] | None = None
    backoff_until: str | None = None


@dataclass(frozen=True)
class GateResult:
    stop_reason: str
    reason: str
    candidate: Candidate | None = None


@dataclass(frozen=True)
class DispatchOutcome:
    ready: bool
    code: int
    reason: str
    payload: Mapping[str, Any] = field(default_factory=dict)


class RelayStateStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def load(self) -> RelayState:
        if not self.path.exists():
            return RelayState()
        try:
            raw = self.path.read_bytes()
            if raw.startswith(b"\xef\xbb\xbf") or b"\r" in raw:
                raise RelayContractError("relay-state must be UTF-8 without BOM and use LF")
            data = json.loads(raw.decode("utf-8"))
            if not isinstance(data, dict):
                raise RelayContractError("relay-state must be an object")
            return RelayState(**data)
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError) as exc:
            if isinstance(exc, RelayContractError):
                raise
            raise RelayContractError(f"invalid relay-state: {exc}") from exc

    def save(self, state: RelayState) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = (
            json.dumps(asdict(state), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")
        temporary = self.path.with_name(
            f".{self.path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp"
        )
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
        finally:
            if temporary.exists():
                temporary.unlink()


class DispatcherClient:
    def __init__(
        self,
        *,
        root: str | Path,
        policy: RelayPolicy,
        execute_requested: bool,
        script_path: str | Path | None = None,
        python_executable: str | Path | None = None,
        env: Mapping[str, str] | None = None,
    ) -> None:
        self.root = Path(root)
        self.policy = policy
        self.execute_requested = execute_requested
        self.script_path = Path(script_path or self.root / "scripts" / "dispatch-work-order.py")
        self.python_executable = str(python_executable or sys.executable)
        self.env = dict(env) if env is not None else None

    def precheck(self, order: str) -> DispatchOutcome:
        completed = subprocess.run(
            self._command(order),
            cwd=self.root,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
            creationflags=BACKGROUND_CREATION_FLAGS,
            env=self.env,
            check=False,
        )
        payload, parse_reason = self._parse_output(completed.stdout)
        ready = completed.returncode == 0 and payload.get("ready") is True
        reason = self._reason(payload, completed.stderr, parse_reason)
        return DispatchOutcome(ready, completed.returncode, reason, payload)

    def execute(self, order: str) -> DispatchOutcome:
        if not (
            self.policy.real_dispatch_enabled is True
            and self.execute_requested is True
            and order in self.policy.eligible_orders
        ):
            raise RelayContractError("real dispatch disabled")

        log_dir = self.root / "tasks" / "queue" / "relay-logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S%fZ")
        stem = f"{stamp}-{order}-{uuid.uuid4().hex[:8]}"
        stdout_path = log_dir / f"{stem}.stdout.log"
        stderr_path = log_dir / f"{stem}.stderr.log"
        command = [
            *self._command(order),
            "--execute",
            "--max-runtime-seconds",
            str(self.policy.max_runtime_seconds),
        ]
        with stdout_path.open("wb") as stdout_stream, stderr_path.open("wb") as stderr_stream:
            process = subprocess.Popen(
                command,
                cwd=self.root,
                stdin=subprocess.DEVNULL,
                stdout=stdout_stream,
                stderr=stderr_stream,
                shell=False,
                creationflags=BACKGROUND_CREATION_FLAGS,
                close_fds=True,
                env=self.env,
            )
            code = process.wait()
        stdout = stdout_path.read_text(encoding="utf-8", errors="replace")
        stderr = stderr_path.read_text(encoding="utf-8", errors="replace")
        payload, parse_reason = self._parse_output(stdout)
        ready = code == 0 and payload.get("ready", True) is not False
        reason = self._reason(payload, stderr, parse_reason)
        return DispatchOutcome(ready, code, reason, payload)

    def _command(self, order: str) -> list[str]:
        prompt = self.root / "tasks" / "queue" / "prompts" / f"{order}.txt"
        return [
            self.python_executable,
            str(self.script_path),
            "--order",
            order,
            "--prompt",
            str(prompt),
        ]

    @staticmethod
    def _parse_output(stdout: str) -> tuple[Mapping[str, Any], str]:
        for line in reversed(stdout.splitlines()):
            if not line.strip():
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                return payload, ""
        return {}, "dispatcher produced no JSON object"

    @staticmethod
    def _reason(
        payload: Mapping[str, Any], stderr: str, parse_reason: str
    ) -> str:
        for key in ("reason", "errors", "blocked"):
            if key in payload:
                return str(payload[key])
        if parse_reason:
            return parse_reason
        if stderr.strip():
            return stderr.strip().splitlines()[-1]
        return "dispatcher completed"


class QueueStatusView:
    """Strictly read queue-status; this class intentionally has no save method."""

    def __init__(self, root: str | Path, *, project: str = "UltimaAgent") -> None:
        self.root = Path(root)
        self.project = project
        self.path = self.root / "tasks" / "queue" / "queue-status.json"

    def records(self) -> list[Mapping[str, Any]]:
        try:
            raw = self.path.read_bytes()
        except OSError as exc:
            raise RelayContractError(f"cannot read queue-status: {exc}") from exc
        if raw.startswith(b"\xef\xbb\xbf"):
            raise RelayContractError("queue-status must not contain a UTF-8 BOM")
        if b"\r" in raw:
            raise RelayContractError("queue-status must use LF line endings")
        try:
            document = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RelayContractError(f"invalid queue-status JSON: {exc}") from exc
        records = document.get("records") if isinstance(document, dict) else None
        if not isinstance(records, list) or not all(
            isinstance(record, dict) for record in records
        ):
            raise RelayContractError("queue-status records must be a list of objects")
        return records

    def project_records(self) -> list[Mapping[str, Any]]:
        return [
            record for record in self.records() if record.get("project") == self.project
        ]


def _resolve_shared_queue(root: Path) -> Path:
    override = os.environ.get("GORCH_SHARED_QUEUE")
    if override:
        return Path(override)
    for base in (root, *root.parents):
        candidate = base / "_shared" / "queue"
        if candidate.is_dir():
            return candidate
    return root.parent / "_shared" / "queue"


class RelayGate:
    def __init__(self, root: str | Path) -> None:
        self.root = Path(root)

    def evaluate(
        self,
        view: QueueStatusView,
        policy: RelayPolicy,
        state: RelayState,
        now: datetime,
    ) -> GateResult:
        pause_markers = (
            self.root / "tasks" / ".pause-dispatch",
            _resolve_shared_queue(self.root) / ".pause-dispatch",
        )
        if any(marker.exists() for marker in pause_markers):
            return GateResult("PAUSED", "dispatch pause marker exists")
        if state.halted:
            return GateResult("HALTED", state.halt_reason or "relay is halted")
        if state.backoff_until:
            try:
                backoff_until = datetime.fromisoformat(state.backoff_until)
            except ValueError:
                return GateResult("HALTED", "invalid failure backoff timestamp")
            if now.astimezone(UTC) < backoff_until.astimezone(UTC):
                return GateResult("HALTED", "failure backoff is active")

        records = view.project_records()
        if any(
            to_state(record.get("state")) in {QueueState.EXECUTING, QueueState.AUDIT}
            for record in records
        ):
            return GateResult("WIP_BUSY", "project has executing or audit work")

        day_key = now.astimezone(UTC).date().isoformat()
        actions_today = state.actions_today if state.day_key == day_key else 0
        if actions_today >= policy.max_actions_per_day:
            return GateResult("QUOTA_EXHAUSTED", "daily action quota exhausted")

        candidate = select_candidate(records, policy)
        if candidate is not None:
            return GateResult("READY", "candidate passed read-only gates", candidate)

        by_order = {
            record.get("work_order"): record
            for record in records
            if isinstance(record.get("work_order"), str)
        }
        for order in policy.eligible_orders:
            record = by_order.get(order)
            if record is None or to_state(record.get("state")) is not QueueState.QUEUED:
                continue
            ready, reason = dependency_ready(order, records, policy)
            if not ready:
                return GateResult("DEPENDENCY_NOT_READY", reason)
        return GateResult("NO_CANDIDATE", "no eligible pending order")


class RelayPump:
    def __init__(
        self,
        *,
        root: str | Path,
        view: QueueStatusView,
        policy: RelayPolicy,
        state: RelayState,
        execute: bool,
        dispatcher: DispatcherClient | None = None,
        state_store: RelayStateStore | None = None,
    ) -> None:
        self.root = Path(root)
        self.view = view
        self.policy = policy
        self.state = state
        self.execute = execute
        self.dispatcher = dispatcher
        self.state_store = state_store

    def pump_once(self, max_actions: int) -> dict[str, Any]:
        if (
            not isinstance(max_actions, int)
            or isinstance(max_actions, bool)
            or max_actions <= 0
        ):
            raise RelayContractError("max_actions must be a positive integer")

        if not self.execute:
            result = RelayGate(self.root).evaluate(
                self.view, self.policy, self.state, datetime.now(UTC)
            )
            return {
                "stop_reason": result.stop_reason,
                "candidate": result.candidate.order if result.candidate else None,
                "would_dispatch": result.candidate is not None,
                "reason": (
                    "candidate ready for dry-run"
                    if result.stop_reason == "READY"
                    else result.reason
                ),
            }
        if self.dispatcher is None or self.state_store is None:
            raise RelayContractError("execute mode requires dispatcher and state store")

        attempted: set[str] = set()
        actions = 0
        for _ in range(max_actions):
            now = datetime.now(UTC)
            result = RelayGate(self.root).evaluate(
                self.view, self.policy, self.state, now
            )
            if result.stop_reason != "READY" or result.candidate is None:
                return {
                    "stop_reason": result.stop_reason,
                    "candidate": result.candidate.order if result.candidate else None,
                    "would_dispatch": False,
                    "reason": result.reason,
                    "actions": actions,
                }
            order = result.candidate.order
            if order in attempted:
                return {
                    "stop_reason": "SAME_ORDER_THIS_TICK",
                    "candidate": order,
                    "would_dispatch": False,
                    "reason": "same order already attempted in this tick",
                    "actions": actions,
                }
            attempted.add(order)

            precheck = self.dispatcher.precheck(order)
            if not precheck.ready:
                self._record_failure(order, precheck, now)
                return {
                    "stop_reason": "PRECHECK_NOT_READY",
                    "candidate": order,
                    "would_dispatch": False,
                    "reason": precheck.reason,
                    "actions": actions,
                }

            outcome = self.dispatcher.execute(order)
            if outcome.code != 0 or not outcome.ready:
                self._record_failure(order, outcome, now)
                return {
                    "stop_reason": "HALTED" if self.state.halted else "DISPATCH_FAILED",
                    "candidate": order,
                    "would_dispatch": True,
                    "reason": outcome.reason,
                    "actions": actions,
                }

            day_key = now.date().isoformat()
            if self.state.day_key != day_key:
                self.state.day_key = day_key
                self.state.actions_today = 0
            self.state.actions_today += 1
            self.state.last_order = order
            run = outcome.payload.get("run")
            self.state.last_run = str(run) if run is not None else None
            self.state.attempts += 1
            self.state.consecutive_failures = 0
            self.state.last_failure = None
            self.state.backoff_until = None
            self.state_store.save(self.state)
            actions += 1
        return {
            "stop_reason": "DISPATCHED",
            "candidate": self.state.last_order,
            "would_dispatch": True,
            "reason": "bounded action limit reached",
            "actions": actions,
        }

    def _record_failure(
        self, order: str, outcome: DispatchOutcome, now: datetime
    ) -> None:
        self.state.attempts += 1
        self.state.consecutive_failures += 1
        self.state.last_failure = {
            "order": order,
            "code": outcome.code,
            "reason": outcome.reason,
            "ts": now.isoformat(),
        }
        self.state.backoff_until = (
            now + timedelta(seconds=self.policy.cooldown_s)
        ).isoformat()
        if self.state.consecutive_failures >= self.policy.max_consecutive_failures:
            self.state.halted = True
            self.state.halt_reason = (
                f"{self.state.consecutive_failures} consecutive dispatch failures"
            )
        self.state_store.save(self.state)


def to_state(raw: str) -> QueueState:
    try:
        return STATUS_TO_STATE[raw]
    except (KeyError, TypeError) as exc:
        raise RelayContractError(f"unknown queue-status state: {raw!r}") from exc


def orders_in_state(
    records: Sequence[Mapping[str, Any]], state: QueueState
) -> list[Mapping[str, Any]]:
    return [record for record in records if to_state(record.get("state")) is state]


def dependency_ready(
    order: str,
    records: Sequence[Mapping[str, Any]],
    policy: RelayPolicy,
) -> tuple[bool, str]:
    if order not in policy.depends_on:
        return False, f"dependency declaration missing for {order}"

    by_order = {record.get("work_order"): record for record in records}
    for dependency in policy.depends_on[order]:
        record = by_order.get(dependency)
        if record is None:
            return False, f"dependency {dependency} is missing"
        raw_state = record.get("state")
        state = to_state(raw_state)
        if state is QueueState.BLOCKED:
            return False, f"dependency {dependency} is blocked"
        if state is not QueueState.COMPLETED:
            return False, f"dependency {dependency} is {raw_state}"
    return True, "dependencies complete"


def select_candidate(
    records: Sequence[Mapping[str, Any]], policy: RelayPolicy
) -> Candidate | None:
    by_order: dict[str, Mapping[str, Any]] = {}
    for record in records:
        to_state(record.get("state"))
        order = record.get("work_order")
        if isinstance(order, str):
            by_order[order] = record

    for order in policy.eligible_orders:
        record = by_order.get(order)
        if record is None or to_state(record.get("state")) is not QueueState.QUEUED:
            continue
        ready, _ = dependency_ready(order, records, policy)
        if ready:
            return Candidate(order=order, record=record)
    return None
