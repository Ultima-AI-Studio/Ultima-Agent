from __future__ import annotations

from datetime import UTC, datetime
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import threading
import time

import pytest

from tasks.queue_engine.relay import (
    DispatcherClient,
    QueueStatusView,
    RelayContractError,
    RelayGate,
    RelayPump,
    RelayPolicy,
    RelayState,
    RelayStateStore,
    dependency_ready,
    orders_in_state,
    select_candidate,
    to_state,
)
from tasks.queue_engine.state_machine import QueueState


REPO_ROOT = Path(__file__).resolve().parents[2]
RELAY_LOOP_SPEC = importlib.util.spec_from_file_location(
    "relay_loop_entry", REPO_ROOT / "scripts" / "relay-loop.py"
)
assert RELAY_LOOP_SPEC is not None and RELAY_LOOP_SPEC.loader is not None
relay_loop_entry = importlib.util.module_from_spec(RELAY_LOOP_SPEC)
RELAY_LOOP_SPEC.loader.exec_module(relay_loop_entry)


def record(order: str, state: str) -> dict[str, object]:
    return {
        "project": "UltimaAgent",
        "work_order": order,
        "state": state,
        "audit_passed": None,
        "dispatched_at": None,
        "audit_run": None,
        "freeze_commit": None,
        "note": "fixture",
    }


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("pending", QueueState.QUEUED),
        ("executing", QueueState.EXECUTING),
        ("audit", QueueState.AUDIT),
        ("frozen", QueueState.COMPLETED),
        ("closed", QueueState.COMPLETED),
        ("blocked", QueueState.BLOCKED),
        ("cancelled", QueueState.CANCELLED),
    ],
)
def test_to_state_maps_all_seven_queue_status_values(
    raw: str, expected: QueueState
) -> None:
    assert to_state(raw) is expected


def test_to_state_rejects_unknown_status_fail_closed() -> None:
    with pytest.raises(RelayContractError, match="unknown queue-status state: 'weird'"):
        to_state("weird")


def test_orders_in_state_uses_the_one_way_mapping() -> None:
    records = [record("queued", "pending"), record("done", "frozen")]

    assert [item["work_order"] for item in orders_in_state(records, QueueState.QUEUED)] == [
        "queued"
    ]
    assert [
        item["work_order"] for item in orders_in_state(records, QueueState.COMPLETED)
    ] == ["done"]


def test_dependency_ready_distinguishes_missing_declaration() -> None:
    policy = RelayPolicy(eligible_orders=("next",), depends_on={})

    ready, reason = dependency_ready("next", [record("next", "pending")], policy)

    assert ready is False
    assert reason == "dependency declaration missing for next"


def test_dependency_ready_distinguishes_unfinished_dependency() -> None:
    policy = RelayPolicy(eligible_orders=("next",), depends_on={"next": ("first",)})

    ready, reason = dependency_ready(
        "next", [record("first", "pending"), record("next", "pending")], policy
    )

    assert ready is False
    assert reason == "dependency first is pending"


def test_dependency_ready_distinguishes_blocked_dependency() -> None:
    policy = RelayPolicy(eligible_orders=("next",), depends_on={"next": ("first",)})

    ready, reason = dependency_ready(
        "next", [record("first", "blocked"), record("next", "pending")], policy
    )

    assert ready is False
    assert reason == "dependency first is blocked"


def test_select_candidate_honors_whitelist_order_not_numeric_order() -> None:
    larger_first = "wo-ultimaagent-20261111-0099"
    smaller_second = "wo-ultimaagent-20261111-0001"
    policy = RelayPolicy(
        eligible_orders=(larger_first, smaller_second),
        depends_on={larger_first: (), smaller_second: ()},
    )
    records = [record(smaller_second, "pending"), record(larger_first, "pending")]

    candidate = select_candidate(records, policy)

    assert candidate is not None
    assert candidate.order == larger_first


def write_status(root: Path, records: list[dict[str, object]]) -> QueueStatusView:
    path = root / "tasks" / "queue" / "queue-status.json"
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps({"schema_version": 1, "records": records}, ensure_ascii=False, indent=2)
        + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return QueueStatusView(root)


def ready_policy(order: str = "next", **overrides: object) -> RelayPolicy:
    values: dict[str, object] = {
        "eligible_orders": (order,),
        "depends_on": {order: ()},
    }
    values.update(overrides)
    return RelayPolicy(**values)


@pytest.mark.parametrize(
    "marker", ["tasks/.pause-dispatch", "_shared/queue/.pause-dispatch"]
)
def test_gate_reports_paused_for_each_dispatch_marker(tmp_path: Path, marker: str) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    pause = tmp_path / marker
    pause.parent.mkdir(parents=True, exist_ok=True)
    pause.write_text("paused\n", encoding="utf-8")

    result = RelayGate(tmp_path).evaluate(
        view, ready_policy(), RelayState(), datetime(2026, 11, 11, tzinfo=UTC)
    )

    assert result.stop_reason == "PAUSED"


@pytest.mark.parametrize("busy_state", ["executing", "audit"])
def test_gate_reports_wip_busy_for_executing_and_audit(
    tmp_path: Path, busy_state: str
) -> None:
    view = write_status(
        tmp_path, [record("busy", busy_state), record("next", "pending")]
    )

    result = RelayGate(tmp_path).evaluate(
        view, ready_policy(), RelayState(), datetime(2026, 11, 11, tzinfo=UTC)
    )

    assert result.stop_reason == "WIP_BUSY"


def test_gate_reports_quota_exhausted(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    state = RelayState(day_key="2026-11-11", actions_today=2)

    result = RelayGate(tmp_path).evaluate(
        view, ready_policy(max_actions_per_day=2), state, datetime(2026, 11, 11, tzinfo=UTC)
    )

    assert result.stop_reason == "QUOTA_EXHAUSTED"


def test_gate_resets_quota_logically_across_utc_day(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    state = RelayState(day_key="2026-11-10", actions_today=99)

    result = RelayGate(tmp_path).evaluate(
        view, ready_policy(max_actions_per_day=2), state, datetime(2026, 11, 11, tzinfo=UTC)
    )

    assert result.stop_reason == "READY"
    assert result.candidate is not None


def test_gate_reports_no_candidate(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("done", "frozen")])

    result = RelayGate(tmp_path).evaluate(
        view, ready_policy(), RelayState(), datetime(2026, 11, 11, tzinfo=UTC)
    )

    assert result.stop_reason == "NO_CANDIDATE"


def test_dry_run_starts_no_subprocess_and_writes_no_relay_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    calls = 0

    def forbidden_popen(*args: object, **kwargs: object) -> None:
        nonlocal calls
        calls += 1
        raise AssertionError("dry-run must not start a subprocess")

    monkeypatch.setattr(subprocess, "Popen", forbidden_popen)
    pump = RelayPump(
        root=tmp_path,
        view=view,
        policy=ready_policy(),
        state=RelayState(),
        execute=False,
    )

    result = pump.pump_once(1)

    assert result == {
        "stop_reason": "READY",
        "candidate": "next",
        "would_dispatch": True,
        "reason": "candidate ready for dry-run",
    }
    assert calls == 0
    assert not (tmp_path / "tasks" / "queue" / "relay-state.json").exists()


def test_queue_status_view_exposes_no_write_entrypoint(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("next", "pending")])

    with pytest.raises(AttributeError):
        view.save(None)  # type: ignore[attr-defined]


def test_relay_loop_status_is_read_only_json(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    state_path = tmp_path / "relay-state.json"
    monkeypatch.setattr(relay_loop_entry, "STATE_PATH", state_path)

    assert relay_loop_entry.main(["--status"]) == 0

    assert json.loads(capsys.readouterr().out) == {
        "halted": False,
        "actions_today": 0,
        "last_order": None,
    }
    assert not state_path.exists()


def test_relay_loop_stop_exits_within_one_interval(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    interval_s = 0.2
    stop_path = tmp_path / "ultima-relay.stop"
    first_tick = threading.Event()

    class CountingPump:
        def pump_once(self, max_actions: int) -> dict[str, object]:
            assert max_actions == 1
            first_tick.set()
            return {"stop_reason": "NO_CANDIDATE"}

    monkeypatch.setattr(relay_loop_entry, "STOP_PATH", stop_path)
    thread = threading.Thread(
        target=relay_loop_entry.run,
        args=(threading.Event(), interval_s),
        kwargs={"pump": CountingPump(), "max_actions": 1, "stop_path": stop_path},
    )
    thread.start()
    assert first_tick.wait(1.0)

    started = time.monotonic()
    assert relay_loop_entry.main(["--stop"]) == 0
    thread.join(interval_s + 0.2)
    elapsed = time.monotonic() - started

    assert not thread.is_alive()
    assert elapsed <= interval_s + 0.1
    assert stop_path.read_text(encoding="utf-8") == "stop\n"
    capsys.readouterr()


@pytest.mark.parametrize("value", [0, -1, True, 1.5])
def test_pump_rejects_non_positive_or_non_integer_action_bounds(
    tmp_path: Path, value: object
) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    pump = RelayPump(
        root=tmp_path,
        view=view,
        policy=ready_policy(),
        state=RelayState(),
        execute=False,
    )

    with pytest.raises(RelayContractError, match="max_actions must be a positive integer"):
        pump.pump_once(value)  # type: ignore[arg-type]


def fake_dispatcher(
    root: Path, *, precheck_ready: bool = True, execute_exit: int = 0
) -> tuple[Path, Path, dict[str, str]]:
    script = root / "fake-dispatch.py"
    log = root / "fake-dispatch.log"
    prompt = root / "tasks" / "queue" / "prompts" / "next.txt"
    prompt.parent.mkdir(parents=True, exist_ok=True)
    prompt.write_text("docs/INDEX.md next\n", encoding="utf-8")
    script.write_text(
        "\n".join(
            [
                "import argparse, json, os, sys",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--order', required=True)",
                "parser.add_argument('--prompt', required=True)",
                "parser.add_argument('--execute', action='store_true')",
                "parser.add_argument('--max-runtime-seconds')",
                "args = parser.parse_args()",
                "mode = 'execute' if args.execute else 'precheck'",
                "with open(os.environ['FAKE_DISPATCH_LOG'], 'a', encoding='utf-8') as stream:",
                "    stream.write(mode + '\\n')",
                f"if not args.execute and not {precheck_ready!r}:",
                "    print(json.dumps({'ready': False, 'reason': 'fixture refused'}))",
                "    raise SystemExit(2)",
                f"code = {execute_exit!r} if args.execute else 0",
                "print(json.dumps({'ready': code == 0, 'order': args.order, 'run': 'fixture-run', 'reason': 'fixture'}))",
                "raise SystemExit(code)",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    env = dict(os.environ)
    env["FAKE_DISPATCH_LOG"] = str(log)
    return script, log, env


def e2e_dispatcher(
    root: Path, orders: tuple[str, ...]
) -> tuple[Path, Path, dict[str, str]]:
    script = root / "fake-e2e-dispatch.py"
    log = root / "fake-e2e-dispatch.jsonl"
    for order in orders:
        prompt = root / "tasks" / "queue" / "prompts" / f"{order}.txt"
        prompt.parent.mkdir(parents=True, exist_ok=True)
        prompt.write_text(f"docs/INDEX.md {order}\n", encoding="utf-8")
    script.write_text(
        "\n".join(
            [
                "import argparse, json, os",
                "from pathlib import Path",
                "parser = argparse.ArgumentParser()",
                "parser.add_argument('--order', required=True)",
                "parser.add_argument('--prompt', required=True)",
                "parser.add_argument('--execute', action='store_true')",
                "parser.add_argument('--max-runtime-seconds')",
                "args = parser.parse_args()",
                "mode = 'execute' if args.execute else 'precheck'",
                "with open(os.environ['FAKE_DISPATCH_LOG'], 'a', encoding='utf-8', newline='\\n') as stream:",
                "    stream.write(json.dumps({'order': args.order, 'mode': mode}) + '\\n')",
                "if args.execute:",
                "    status = Path(os.environ['FAKE_QUEUE_STATUS'])",
                "    document = json.loads(status.read_text(encoding='utf-8'))",
                "    for record in document['records']:",
                "        if record['work_order'] == args.order:",
                "            record['state'] = 'frozen'",
                "    status.write_text(json.dumps(document, ensure_ascii=False, indent=2) + '\\n', encoding='utf-8', newline='\\n')",
                "print(json.dumps({'ready': True, 'order': args.order, 'run': 'fixture-' + args.order}))",
                "",
            ]
        ),
        encoding="utf-8",
        newline="\n",
    )
    env = dict(os.environ)
    env["FAKE_DISPATCH_LOG"] = str(log)
    env["FAKE_QUEUE_STATUS"] = str(
        root / "tasks" / "queue" / "queue-status.json"
    )
    return script, log, env


@pytest.mark.parametrize(
    ("enabled", "requested", "eligible"),
    [(False, True, ("next",)), (True, False, ("next",)), (True, True, ("other",))],
)
def test_real_dispatch_requires_policy_execute_and_whitelist_triple_gate(
    tmp_path: Path, enabled: bool, requested: bool, eligible: tuple[str, ...]
) -> None:
    script, _, env = fake_dispatcher(tmp_path)
    policy = RelayPolicy(
        eligible_orders=eligible,
        depends_on={order: () for order in eligible},
        real_dispatch_enabled=enabled,
    )
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=requested,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )

    with pytest.raises(RelayContractError, match="^real dispatch disabled$"):
        client.execute("next")


def test_precheck_not_ready_never_calls_execute(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    script, log, env = fake_dispatcher(tmp_path, precheck_ready=False)
    policy = ready_policy(real_dispatch_enabled=True)
    store = RelayStateStore(tmp_path / "tasks" / "queue" / "relay-state.json")
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=True,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )
    pump = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=RelayState(),
        execute=True,
        dispatcher=client,
        state_store=store,
    )

    result = pump.pump_once(1)

    assert result["stop_reason"] == "PRECHECK_NOT_READY"
    assert log.read_text(encoding="utf-8").splitlines() == ["precheck"]


def test_nonzero_execute_enters_backoff_then_halts_at_failure_limit(
    tmp_path: Path,
) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    script, log, env = fake_dispatcher(tmp_path, execute_exit=7)
    policy = ready_policy(real_dispatch_enabled=True, cooldown_s=60.0)
    store = RelayStateStore(tmp_path / "tasks" / "queue" / "relay-state.json")
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=True,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )

    first = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=store.load(),
        execute=True,
        dispatcher=client,
        state_store=store,
    ).pump_once(1)
    state_after_first = store.load()
    first_halted = state_after_first.halted
    recorded_backoff = state_after_first.backoff_until
    first_failure = state_after_first.last_failure
    state_after_first.backoff_until = "2000-01-01T00:00:00+00:00"
    second = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=state_after_first,
        execute=True,
        dispatcher=client,
        state_store=store,
    ).pump_once(1)
    state_after_second = store.load()

    assert first["stop_reason"] == "DISPATCH_FAILED"
    assert first_halted is False
    assert recorded_backoff is not None
    assert first_failure is not None
    assert first_failure["code"] == 7
    assert second["stop_reason"] == "HALTED"
    assert state_after_second.halted is True
    assert state_after_second.consecutive_failures == 2
    assert log.read_text(encoding="utf-8").splitlines() == [
        "precheck",
        "execute",
        "precheck",
        "execute",
    ]


def test_same_order_is_not_dispatched_twice_in_one_tick(tmp_path: Path) -> None:
    view = write_status(tmp_path, [record("next", "pending")])
    script, log, env = fake_dispatcher(tmp_path)
    policy = ready_policy(real_dispatch_enabled=True, max_actions_per_tick=2)
    store = RelayStateStore(tmp_path / "tasks" / "queue" / "relay-state.json")
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=True,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )
    pump = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=RelayState(),
        execute=True,
        dispatcher=client,
        state_store=store,
    )

    result = pump.pump_once(2)

    assert result["stop_reason"] == "SAME_ORDER_THIS_TICK"
    assert result["actions"] == 1
    assert log.read_text(encoding="utf-8").splitlines() == ["precheck", "execute"]
    persisted = (tmp_path / "tasks" / "queue" / "relay-state.json").read_bytes()
    assert not persisted.startswith(b"\xef\xbb\xbf")
    assert b"\r" not in persisted


def test_fixture_e2e_dispatches_a_then_dependent_b(tmp_path: Path) -> None:
    order_a = "A"
    order_b = "B"
    view = write_status(
        tmp_path, [record(order_a, "pending"), record(order_b, "pending")]
    )
    script, log, env = e2e_dispatcher(tmp_path, (order_a, order_b))
    policy = RelayPolicy(
        eligible_orders=(order_a, order_b),
        depends_on={order_a: (), order_b: (order_a,)},
        real_dispatch_enabled=True,
    )
    store = RelayStateStore(tmp_path / "tasks" / "queue" / "relay-state.json")
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=True,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )

    first = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=store.load(),
        execute=True,
        dispatcher=client,
        state_store=store,
    ).pump_once(1)
    second = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=store.load(),
        execute=True,
        dispatcher=client,
        state_store=store,
    ).pump_once(1)

    events = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
    dispatch_order = [event["order"] for event in events if event["mode"] == "execute"]
    assert first["candidate"] == order_a
    assert second["candidate"] == order_b
    assert dispatch_order == ["A", "B"]
    assert events.count({"order": order_b, "mode": "precheck"}) == 1
    assert events.count({"order": order_b, "mode": "execute"}) == 1


def test_fixture_e2e_blocks_b_when_a_is_blocked(tmp_path: Path) -> None:
    order_a = "A"
    order_b = "B"
    view = write_status(
        tmp_path, [record(order_a, "blocked"), record(order_b, "pending")]
    )
    script, log, env = e2e_dispatcher(tmp_path, (order_b,))
    policy = RelayPolicy(
        eligible_orders=(order_b,),
        depends_on={order_b: (order_a,)},
        real_dispatch_enabled=True,
    )
    store = RelayStateStore(tmp_path / "tasks" / "queue" / "relay-state.json")
    client = DispatcherClient(
        root=tmp_path,
        policy=policy,
        execute_requested=True,
        script_path=script,
        python_executable=sys.executable,
        env=env,
    )
    result = RelayPump(
        root=tmp_path,
        view=view,
        policy=policy,
        state=store.load(),
        execute=True,
        dispatcher=client,
        state_store=store,
    ).pump_once(1)

    assert result["stop_reason"] == "DEPENDENCY_NOT_READY"
    assert result["reason"] == "dependency A is blocked"
    assert not log.exists()
