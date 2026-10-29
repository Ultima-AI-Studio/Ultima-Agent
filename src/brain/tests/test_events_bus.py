from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

from src.brain.guardrails import audit_log as audit_log_module
from src.brain.heartbeat import ticker as ticker_module
from src.brain.loop import brain_loop as brain_loop_module
from src.brain.orchestration import audit as workflow_audit_module
from src.brain.orchestration import queue as queue_module
from src.brain.events.bus import EventBus


def test_emit_notifies_subscriber_and_ids_increase() -> None:
    bus = EventBus()
    received: list[dict] = []
    unsubscribe = bus.subscribe(received.append)

    first = bus.emit_event("message_in", {"text": "hello"})
    second = bus.emit_event("tick", {"tick": 1})
    unsubscribe()
    bus.emit_event("tick", {"tick": 2})

    assert [event["id"] for event in received] == [first["id"], second["id"]]
    assert int(first["id"]) < int(second["id"])


def test_get_after_returns_only_events_after_cursor() -> None:
    bus = EventBus()
    first = bus.emit_event("message_in", {"text": "one"})
    second = bus.emit_event("stream_start", {"flow_id": "flow-1"})
    third = bus.emit_event("stream_chunk", {"content": "two"})

    assert bus.get_after(first["id"]) == [second, third]
    assert bus.get_after(third["id"]) == []


def test_journal_keeps_latest_240_events() -> None:
    bus = EventBus()
    emitted = [bus.emit_event("tick", {"tick": index}) for index in range(245)]

    history = bus.history()

    assert len(history) == 240
    assert history[0]["id"] == emitted[5]["id"]
    assert history[-1]["id"] == emitted[-1]["id"]


def test_sticky_set_get_and_clear() -> None:
    bus = EventBus()

    sticky = bus.set_sticky("agent_name_updated", {"name": "Jarvis"})

    assert bus.get_sticky() == {"agent_name_updated": sticky}
    bus.clear_sticky("agent_name_updated")
    assert bus.get_sticky() == {}


def test_concurrent_emit_has_no_loss_or_duplicate_ids() -> None:
    bus = EventBus()

    with ThreadPoolExecutor(max_workers=10) as executor:
        events = list(executor.map(lambda index: bus.emit_event("tick", {"tick": index}), range(100)))

    ids = [event["id"] for event in events]
    assert len(bus.history()) == 100
    assert len(set(ids)) == 100
    assert sorted(map(int, ids)) == list(range(1, 101))


def test_history_filters_l1_l2_l3_paths() -> None:
    bus = EventBus()
    l1 = bus.emit_event("message_in", {"text": "hello"})
    l2 = bus.emit_event("tool_call", {"tool": "search"})
    l3 = bus.emit_event("tick", {"tick": 1})

    assert bus.history(path="l1") == [l1]
    assert bus.history(path="l2") == [l2]
    assert bus.history(path="l3") == [l3]
    assert bus.history(path="all") == [l1, l2, l3]


def test_unknown_cursor_replays_available_history() -> None:
    bus = EventBus()
    events = [bus.emit_event("tick", {"tick": index}) for index in range(3)]

    assert bus.get_after("999999") == events


def test_event_data_is_isolated_from_caller_mutation() -> None:
    bus = EventBus()
    data = {"nested": {"value": 1}}

    event = bus.emit_event("audit_record", data)
    data["nested"]["value"] = 2

    assert event["data"] == {"nested": {"value": 1}}
    assert bus.history()[0]["data"] == {"nested": {"value": 1}}


def test_heartbeat_emits_its_real_tick_result(monkeypatch) -> None:
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        ticker_module,
        "emit_event",
        lambda event_type, data: emitted.append((event_type, data)),
        raising=False,
    )
    ticker = ticker_module.HeartbeatTicker()

    result = ticker.tick()

    assert emitted == [("tick", result)]


def test_brain_loop_emits_real_executor_report(monkeypatch, tmp_path) -> None:
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        brain_loop_module,
        "emit_event",
        lambda event_type, data: emitted.append((event_type, data)),
        raising=False,
    )

    result = brain_loop_module.BrainLoop(tmp_path).run("hello")

    tool_events = [data for event_type, data in emitted if event_type == "tool_call"]
    message_events = [data for event_type, data in emitted if event_type == "message"]
    assert result.report is not None
    assert tool_events[-1]["report"] == result.report
    expected_final = next(
        step["content"] for step in result.report["trace"] if step["segment"] == "FINAL"
    )
    assert message_events[-1] == {"role": "jarvis", "text": expected_final}


def test_queue_emits_real_advanced_record(monkeypatch, tmp_path) -> None:
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        queue_module,
        "emit_event",
        lambda event_type, data: emitted.append((event_type, data)),
        raising=False,
    )
    task_queue = queue_module.TaskQueue(tmp_path)
    record = task_queue.create("real task")
    task_queue.enqueue(record.task_id)

    task_queue.advance(record.task_id, "派发")

    assert emitted[-1] == ("task_advance", record.as_dict())


def test_workflow_audit_emits_real_record(monkeypatch) -> None:
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        workflow_audit_module,
        "emit_event",
        lambda event_type, data: emitted.append((event_type, data)),
        raising=False,
    )
    trail = workflow_audit_module.AuditTrail()

    record = trail.append("flow-1", "review", "queued -> audit", "approved")

    assert emitted == [("audit_record", record.to_dict())]


def test_append_only_audit_log_emits_real_entry(monkeypatch, tmp_path) -> None:
    emitted: list[tuple[str, dict]] = []
    monkeypatch.setattr(
        audit_log_module,
        "emit_event",
        lambda event_type, data: emitted.append((event_type, data)),
        raising=False,
    )
    audit_log = audit_log_module.AppendOnlyAuditLog(tmp_path / "audit.jsonl")

    entry = audit_log.append("decision", "brain", {"accepted": True})

    assert emitted == [("audit_record", entry)]


def test_event_bus_failure_does_not_change_source_return(monkeypatch) -> None:
    def fail_emit(event_type, data):
        raise RuntimeError("event outlet unavailable")

    monkeypatch.setattr(ticker_module, "emit_event", fail_emit, raising=False)
    ticker = ticker_module.HeartbeatTicker()

    assert ticker.tick()["action"] == "主动发声"
