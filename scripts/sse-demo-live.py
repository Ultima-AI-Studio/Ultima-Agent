"""SSE 出口端到端真数据演示驱动（只读不改业务源码）。

在独立进程内复用真实打点模块（HeartbeatTicker / TaskQueue / AppendOnlyAuditLog
/ brain_loop 打点路径），制造真实事件写入内存 EventBus，并起一个临时 SSE
服务器（127.0.0.1:8765，仅演示用）暴露 /events 与 /events/history。
前端四角壳经 ?sse=<port> 切换连接本演示服务，即可看到四角由真实源事件驱动。

本脚本不修改任何业务源文件；不占用 8756 常驻服务；退出即释放 8765。
"""

from __future__ import annotations

import json
import queue as queue_mod
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).resolve().parents[1]  # H:\UltimaAI\UltimaAgent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "src" / "brain"))

from src.brain.events import get_event_bus  # noqa: E402

EVENT_BUS = get_event_bus()
PORT = 8765
SSE_PING_SECONDS = 5.0  # 演示用缩短保活间隔


class _DemoHandler(BaseHTTPRequestHandler):
    server_version = "UltimaAgentDemo/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args) -> None:  # 静默
        return

    def _send_json(self, status: int, payload) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _write_sse(self, event_type: str, payload: dict, event_id: str = "") -> None:
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        lines.append(f"event: {event_type}")
        lines.append("data: " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")))
        self.wfile.write(("\n".join(lines) + "\n\n").encode("utf-8"))
        self.wfile.flush()

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if route == "/health":
            self._send_json(200, {"ok": True, "model": "demo-events", "agent": "demo", "tools": []})
            return
        if route == "/events":
            self._serve_events(query)
            return
        if route == "/events/history":
            path = (query.get("path") or ["all"])[0].lower()
            limit = int((query.get("limit") or ["240"])[0])
            self._send_json(200, EVENT_BUS.history(path=path, limit=min(limit, 240)))
            return
        self._send_json(404, {"ok": False, "error": "not found"})

    def _serve_events(self, query) -> None:
        client_id = (query.get("client_id") or [""])[0] or "anonymous"
        last_event_id = (query.get("last_event_id") or [""])[0]
        pending: queue_mod.Queue = queue_mod.Queue()
        unsubscribe = EVENT_BUS.subscribe(pending.put)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            history = EVENT_BUS.history()
            latest = history[-1]["id"] if history else ""
            self._write_sse("connected", {
                "type": "connected",
                "data": {"client_id": client_id, "service_time": time.time(),
                         "resumed_from_event_id": last_event_id, "latest_event_id": latest},
            })
            sent: set[str] = set()
            for event in EVENT_BUS.get_sticky().values():
                self._write_sse(event["type"], event, event["id"])
                sent.add(event["id"])
            replay = EVENT_BUS.get_after(last_event_id) if last_event_id else history
            for event in replay:
                if event["id"] in sent:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent.add(event["id"])
            while True:
                try:
                    event = pending.get(timeout=SSE_PING_SECONDS)
                except queue_mod.Empty:
                    self._write_sse("ping", {"type": "ping", "data": {"service_time": time.time()}})
                    continue
                if event["id"] in sent:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent.add(event["id"])
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        finally:
            unsubscribe()


def _drive_real_events(stop: threading.Event) -> None:
    """用真实业务模块打点，制造真实事件（非伪造载荷）。"""
    from src.brain.heartbeat.ticker import HeartbeatTicker

    ticker = HeartbeatTicker()  # busy_state_provider 默认 idle → 主动发声路径
    tick_seq = 0
    while not stop.is_set():
        # 1) 心跳 tick（真实 ticker.tick 内部 _emit_safely 打点）
        try:
            result = ticker.tick()
            tick_seq += 1
            _ = result
        except Exception as exc:  # noqa: BLE001
            pass  # tick 内部异常已降级，不伪造 error 事件

        # 2) 任务流转（真实 TaskQueue.create/enqueue/advance，advance 内部
        #    _emit_safely("task_advance") 打点）
        try:
            from src.brain.orchestration.queue import TaskQueue

            q = TaskQueue(ROOT / "data" / "demo-queue.json")
            rec = q.create(f"演示任务 {tick_seq}", priority=0)
            q.enqueue(rec.task_id)
            q.advance(rec.task_id, "派发")
            _ = rec
        except Exception as exc:  # noqa: BLE001
            _ = exc

        # 3) 审计留痕（真实 AppendOnlyAuditLog.append 内部 _emit_safely(
        #    "audit_record") 打点）
        try:
            from src.brain.guardrails.audit_log import AppendOnlyAuditLog

            alog = AppendOnlyAuditLog(ROOT / "data" / "demo-audit.jsonl")
            alog.append("decision", "demo-driver", {"accepted": True, "tick": tick_seq})
        except Exception as exc:  # noqa: BLE001
            _ = exc

        stop.wait(2.0)


def main() -> int:
    stop = threading.Event()
    driver = threading.Thread(target=_drive_real_events, args=(stop,), daemon=True)
    driver.start()

    server = ThreadingHTTPServer(("127.0.0.1", PORT), _DemoHandler)
    sys.stderr.write(f"[sse-demo] 演示 SSE 服务 http://127.0.0.1:{PORT} 已启动\n")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
