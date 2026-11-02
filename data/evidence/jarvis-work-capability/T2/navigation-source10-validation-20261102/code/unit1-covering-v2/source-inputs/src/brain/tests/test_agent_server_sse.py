from __future__ import annotations

import http.client
import hashlib
import json
import re
import threading
from contextlib import contextmanager
from http.server import ThreadingHTTPServer
from pathlib import Path

import pytest

from src.brain import agent_server
from src.brain.events.bus import EventBus


@contextmanager
def running_server(monkeypatch: pytest.MonkeyPatch, bus: EventBus):
    monkeypatch.setattr(agent_server, "EVENT_BUS", bus, raising=False)
    server = ThreadingHTTPServer(("127.0.0.1", 0), agent_server._Handler)
    server.daemon_threads = True
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server.server_address
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def read_sse(response: http.client.HTTPResponse) -> dict[str, str]:
    fields: dict[str, str] = {}
    while True:
        line = response.readline().decode("utf-8").rstrip("\r\n")
        if not line:
            return fields
        key, _, value = line.partition(":")
        fields[key] = value.lstrip()


def test_history_route_returns_filtered_json_and_caps_limit(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = EventBus()
    bus.emit_event("message_in", {"text": "l1"})
    bus.emit_event("tool_call", {"tool": "search"})
    bus.emit_event("tick", {"tick": 1})

    with running_server(monkeypatch, bus) as (host, port):
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/events/history?path=l1&limit=999")
        response = connection.getresponse()
        payload = json.loads(response.read())
        connection.close()

    assert response.status == 200
    assert response.getheader("Content-Type") == "application/json; charset=utf-8"
    assert [event["type"] for event in payload] == ["message_in"]
    assert len(payload) <= 240


def test_sse_sends_headers_connected_sticky_history_and_live(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = EventBus()
    sticky = bus.set_sticky("agent_name_updated", {"name": "Jarvis"})
    history = bus.emit_event("message_in", {"text": "hello"})

    with running_server(monkeypatch, bus) as (host, port):
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/events?client_id=test-client&last_event_id=0")
        response = connection.getresponse()
        connected_frame = read_sse(response)
        sticky_frame = read_sse(response)
        history_frame = read_sse(response)
        live = bus.emit_event("tick", {"tick": 7})
        live_frame = read_sse(response)
        response.close()
        connection.close()

    assert response.status == 200
    assert response.getheader("Content-Type") == "text/event-stream"
    assert response.getheader("Cache-Control") == "no-cache"
    assert response.getheader("Connection") == "keep-alive"
    assert response.getheader("Access-Control-Allow-Origin") == "*"
    assert connected_frame["event"] == "connected"
    assert json.loads(connected_frame["data"])["data"]["client_id"] == "test-client"
    assert sticky_frame == {
        "id": sticky["id"],
        "event": sticky["type"],
        "data": json.dumps(sticky, ensure_ascii=False, separators=(",", ":")),
    }
    assert history_frame["id"] == history["id"]
    assert live_frame["id"] == live["id"]


def test_sse_resume_only_replays_events_after_cursor(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = EventBus()
    first = bus.emit_event("message_in", {"text": "already seen"})
    second = bus.emit_event("message", {"text": "new"})

    with running_server(monkeypatch, bus) as (host, port):
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", f"/events?client_id=resume&last_event_id={first['id']}")
        response = connection.getresponse()
        connected_frame = read_sse(response)
        replayed_frame = read_sse(response)
        response.close()
        connection.close()

    assert connected_frame["event"] == "connected"
    assert replayed_frame["id"] == second["id"]


def test_sse_emits_ping_when_idle(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = EventBus()
    monkeypatch.setattr(agent_server, "SSE_PING_SECONDS", 0.05, raising=False)

    with running_server(monkeypatch, bus) as (host, port):
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/events?client_id=idle")
        response = connection.getresponse()
        read_sse(response)
        ping_frame = read_sse(response)
        response.close()
        connection.close()

    assert ping_frame["event"] == "ping"


def test_health_and_ask_behaviors_do_not_regress(monkeypatch: pytest.MonkeyPatch) -> None:
    bus = EventBus()
    monkeypatch.setattr(
        agent_server,
        "ask_once",
        lambda query, max_tokens=None: {"content": query, "tool_results": [], "usage": {}},
    )
    with running_server(monkeypatch, bus) as (host, port):
        connection = http.client.HTTPConnection(host, port, timeout=2)
        connection.request("GET", "/health")
        health_response = connection.getresponse()
        health = json.loads(health_response.read())
        connection.request(
            "POST",
            "/ask",
            body=json.dumps({"query": "hello"}),
            headers={"Content-Type": "application/json"},
        )
        ask_response = connection.getresponse()
        ask = json.loads(ask_response.read())
        connection.close()

    assert health_response.status == 200
    assert health["ok"] is True
    assert ask_response.status == 200
    assert ask == {"content": "hello", "tool_results": [], "usage": {}, "ok": True}


def test_hud_uses_real_sse_with_resume_and_preserves_frozen_style() -> None:
    page = Path("docs/previews/hud-live-four-corner/hud-live-four-corner.html").read_text(
        encoding="utf-8"
    )
    style = re.search(r"<style>(.*?)</style>", page, re.S)

    assert style is not None
    assert hashlib.sha256(style.group(1).encode("utf-8")).hexdigest() == (
        "f336fd77a4cbdfd963ee2305bae28181565cc364f78cf69b94ebb5ef5ba97ab1"
    )
    assert "new EventSource(eventsUrl)" in page
    assert "clearDemoContent();connectSSE();" in page
    assert "ultima_hud_last_event_id" in page
    assert "setTimeout(connectSSE,3000)" in page
    assert "eventSource.addEventListener" in page
    assert "if(corner==='w-sys'&&type!=='tick')" in page
    assert "if(corner==='w-msg')" in page
    assert "真实模式" in page and "演示模式" in page
    for event_type in (
        "message_in",
        "tick",
        "message",
        "tool_executing",
        "tool_call",
        "task_advance",
        "audit_record",
    ):
        assert event_type in page
