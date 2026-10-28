"""s1-remote-update 更新 UI 服务桥（T2 · RU-08 呈现层）。

为 src/ui/update_page.html 提供本地 HTTP 端点：
- GET  /update-state.json → 引擎状态文件（供 UI 轮询展示）
- POST /update/check     → 触发手动检查（RU-06）
- POST /update/apply     → 触发静默强制更新（RU-07）

实现：纯 stdlib http.server（零依赖、零弹窗 CREATE_NO_WINDOW 由调用方保证，
服务本身不创建任何窗口）。绑定 127.0.0.1 回环，仅本机可达。
"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable

from .triggers import UpdateTriggerEngine

HOST = "127.0.0.1"
DEFAULT_PORT = 47810


def _json_bytes(obj: dict) -> bytes:
    return json.dumps(obj, ensure_ascii=False).encode("utf-8")


class _Handler(BaseHTTPRequestHandler):
    engine: UpdateTriggerEngine | None = None
    ui_dir: Path | None = None
    log_fn: Callable[[str], None] = lambda _m: None

    def log_message(self, fmt: str, *args: Any) -> None:  # 静默：不打印到 stdout
        self.__class__.log_fn(f"[ui-server] {fmt % args}")

    def do_GET(self) -> None:  # noqa: N802
        path = self.path.rstrip("/") or "/"
        if path in ("/", "/index.html", "/update_page.html"):
            page = self.ui_dir / "update_page.html"
            if page is None or not Path(page).is_file():
                self._send(404, b"update page not found", "text/plain")
                return
            self._send(200, Path(page).read_bytes(), "text/html; charset=utf-8")
            return
        if path == "/update-state.json":
            self._send(200, _state_bytes(self.engine), "application/json")
            return
        self._send(404, b"not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        path = self.path.rstrip("/")
        engine = self.engine
        if engine is None:
            self._send(503, b"engine not ready", "text/plain")
            return
        if path == "/update/check":
            result = engine.manual_check()
            self._send_ok(_result_bytes(result), "application/json")
            return
        if path == "/update/apply":
            result = engine.apply()
            self._send_ok(_result_bytes(result), "application/json")
            return
        self._send(404, b"not found", "text/plain")

    def _send_ok(self, body: bytes | None, ctype: str) -> None:
        if body is None:
            body = b"not found"
            self._send(404, body, "text/plain")
            return
        self._send(200, body, ctype)

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


def _state_bytes(engine: UpdateTriggerEngine | None) -> bytes:
    if engine is None:
        return _json_bytes({"status": "idle", "error": "engine not ready"})
    return _json_bytes(engine.state.to_dict())


def _result_bytes(result: Any) -> bytes:
    if result is None:
        return _json_bytes({"status": "no_update"})
    return _json_bytes(
        {
            "updated": result.updated,
            "rolled_back": result.rolled_back,
            "error": result.error,
            "old_version": result.old_version,
            "new_version": result.new_version,
        }
    )


class UpdateUiServer:
    """零弹窗更新 UI 服务：threading 后台起服，stop() 关闭。"""

    def __init__(
        self,
        engine: UpdateTriggerEngine,
        ui_dir: Path,
        port: int = DEFAULT_PORT,
        log_fn: Callable[[str], None] | None = None,
    ) -> None:
        self.engine = engine
        self.ui_dir = ui_dir
        self.port = port
        self.log_fn = log_fn or (lambda _m: None)
        self._httpd: ThreadingHTTPServer | None = None
        self._thread: threading.Thread | None = None

    def start(self) -> str:
        _Handler.engine = self.engine
        _Handler.ui_dir = self.ui_dir
        _Handler.log_fn = self.log_fn
        self._httpd = ThreadingHTTPServer((HOST, self.port), _Handler)
        self.port = self._httpd.server_address[1]  # port=0 时取实际分配端口
        self._thread = threading.Thread(target=self._httpd.serve_forever, daemon=True)
        self._thread.start()
        return f"http://{HOST}:{self.port}/"

    def stop(self) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
            self._httpd = None
