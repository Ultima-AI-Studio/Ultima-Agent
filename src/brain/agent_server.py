"""Ultima Agent 智能体服务器（常驻进程，venv-openjarvis 运行）。

三层架构中的"智能体服务器"层：薄壳（文字 CLI / 语音 daemon / 悬浮球壳）
通过本机 HTTP 接口调用本地 14B 主脑的自主对话循环（底座 OpenJarvis Agent 循环）。

接口：
- GET  /health   → 服务状态（模型 / agent / 已注册工具清单）
- POST /ask      → {"query": str, "max_tokens": int?} → {"content", "tool_results", "usage"}

设计约束：
- 仅标准库 + openjarvis + UltimaAgent 自有模块；
- 工具注册：import agent_tools_ultima 触发 ToolRegistry 装饰器注册；
- 模型：ollama + qwen2.5:14b（本地主脑）；agent：simple（ReAct 工具循环）。
"""

from __future__ import annotations

import json
import importlib
import os
import queue
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openjarvis import Jarvis  # noqa: E402
from openjarvis.core.registry import ToolRegistry  # noqa: E402

try:  # 包导入用于测试；脚本入口走 fallback
    from .events import get_event_bus  # type: ignore[attr-defined] # noqa: E402
except ImportError:  # pragma: no cover - 脚本入口
    from events import get_event_bus  # type: ignore[no-redef] # noqa: E402

HOST = "127.0.0.1"
PORT = 8756

ENGINE_KEY = "ollama"
MODEL = "qwen3-8b-uncensored"
AGENT = "native_react"
TOOLS = [
    "calculator",
    "think",
    "ultima_subagent",
    "ultima_skill_manage",
    "ultima_memory",
    "ultima_web_search",
    "ultima_task_query",
    "ultima_task_adjust",
    "ultima_env_snapshot",
]
DEFAULT_MAX_TOKENS = 1024
MAX_BODY_BYTES = 1024 * 1024  # 请求体上限 1MB（本地接口防异常大包）
SSE_PING_SECONDS = 15.0
EVENT_BUS = get_event_bus()

_jars: Jarvis | None = None
_ask_lock = threading.Lock()  # Jarvis 单例非线程安全，串行化并发推理


def _ensure_tools_registered() -> None:
    """只加载一次工具注册模块，并兼容脚本/包两种模块身份。"""
    if "agent_tools_ultima" in sys.modules:
        return
    package_name = f"{__package__}.agent_tools_ultima" if __package__ else ""
    if package_name and package_name in sys.modules:
        sys.modules["agent_tools_ultima"] = sys.modules[package_name]
        return
    module = importlib.import_module(".agent_tools_ultima", __package__) if __package__ else importlib.import_module("agent_tools_ultima")
    sys.modules.setdefault("agent_tools_ultima", module)


# ---------------------------------------------------------------------------
# RU-05 启动自检接线（工单⑧ T2）：主链路启动后后台静默查更新。
# N6 静默降级：通道异常/无网络只记日志，不打扰、不误报新版；N7 零弹窗。
# ---------------------------------------------------------------------------
def _startup_update_check() -> None:
    """后台线程：启动自检（best-effort，任何异常只记日志，不阻断主链路）。"""
    try:
        from src.update.triggers import UpdateTriggerEngine
        from src.update.channel import UpdateChannel

        repo = "Ultima-AI-Studio/Ultima-Agent"
        current = "0.1.0"  # 与宿主壳 csproj Version 对齐（当前发布基线）
        state_file = PROJECT_ROOT / ".runtime" / "update-state.json"
        channel = UpdateChannel(repo)
        engine = UpdateTriggerEngine(
            channel,
            current_version_provider=lambda: current,
            target_path=PROJECT_ROOT / "dist",
            state_file=state_file,
        )
        engine.startup_check()
    except Exception as exc:  # noqa: BLE001 - 静默降级（N6），不阻断启动
        sys.stderr.write(f"[agent-server] startup update check skipped (silent): {exc}\n")


def get_jarvis() -> Jarvis:
    global _jars
    if _jars is None:
        _ensure_tools_registered()
        _jars = Jarvis(engine_key=ENGINE_KEY, model=MODEL)
    return _jars


def _clean_content(content: str) -> str:
    """清理 ReAct 响应文本：只保留 Final Answer 之后的内容；无标记则原样返回。"""
    if not content:
        return content
    marker = "Final Answer:"
    if marker in content:
        return content.split(marker, 1)[1].strip()
    return content.strip()


def ask_once(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """执行一轮自主对话：本地 14B 自主决定直接回答或调用工具（并发串行化）。"""
    j = get_jarvis()
    with _ask_lock:
        result = j.ask_full(
            query,
            agent=AGENT,
            tools=TOOLS,
            context=False,
            max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        )
    return {
        "content": _clean_content(result.get("content", "")),
        "tool_results": result.get("tool_results", []),
        "usage": result.get("usage", {}),
    }


class _Handler(BaseHTTPRequestHandler):
    server_version = "UltimaAgentServer/0.1"
    protocol_version = "HTTP/1.1"

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[agent-server] {fmt % args}\n")

    def _send_json(self, status: int, payload: Any) -> None:
        try:
            body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        except (TypeError, ValueError) as exc:  # 载荷不可序列化：返回可读 500
            body = json.dumps(
                {"ok": False, "error": f"响应序列化失败：{exc}"}, ensure_ascii=False
            ).encode("utf-8")
            status = 500
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _write_sse(self, event_type: str, payload: dict[str, Any], event_id: str = "") -> None:
        lines = []
        if event_id:
            lines.append(f"id: {event_id}")
        lines.append(f"event: {event_type}")
        lines.append(
            "data: "
            + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        )
        self.wfile.write(("\n".join(lines) + "\n\n").encode("utf-8"))
        self.wfile.flush()

    def _serve_events(self, query: dict[str, list[str]]) -> None:
        client_id = (query.get("client_id") or [""])[0] or "anonymous"
        last_event_id = (query.get("last_event_id") or [""])[0]
        if not last_event_id:
            last_event_id = self.headers.get("Last-Event-ID", "")

        pending: queue.Queue[dict[str, Any]] = queue.Queue()
        unsubscribe = EVENT_BUS.subscribe(pending.put)
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.send_header("X-Accel-Buffering", "no")
            self.end_headers()

            history = EVENT_BUS.history()
            latest_event_id = history[-1]["id"] if history else ""
            connected = {
                "type": "connected",
                "data": {
                    "client_id": client_id,
                    "service_time": time.time(),
                    "resumed_from_event_id": last_event_id,
                    "latest_event_id": latest_event_id,
                },
                "ts": time.time(),
            }
            self._write_sse("connected", connected)

            sent_ids: set[str] = set()
            for event in EVENT_BUS.get_sticky().values():
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])

            replay = EVENT_BUS.get_after(last_event_id) if last_event_id else history
            for event in replay:
                if event["id"] in sent_ids:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])

            while True:
                try:
                    event = pending.get(timeout=SSE_PING_SECONDS)
                except queue.Empty:
                    ping = {
                        "type": "ping",
                        "data": {"service_time": time.time()},
                        "ts": time.time(),
                    }
                    self._write_sse("ping", ping)
                    continue
                if event["id"] in sent_ids:
                    continue
                self._write_sse(event["type"], event, event["id"])
                sent_ids.add(event["id"])
        except (BrokenPipeError, ConnectionResetError, OSError):
            return
        finally:
            unsubscribe()

    def _serve_event_history(self, query: dict[str, list[str]]) -> None:
        path = (query.get("path") or ["all"])[0].lower()
        try:
            requested_limit = int((query.get("limit") or ["240"])[0])
            if requested_limit < 0:
                raise ValueError
            payload = EVENT_BUS.history(path=path, limit=min(requested_limit, 240))
        except ValueError:
            self._send_json(400, {"ok": False, "error": "path 或 limit 参数无效。"})
            return
        self._send_json(200, payload)

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        route = parsed.path.rstrip("/") or "/"
        query = parse_qs(parsed.query)
        if route == "/health":
            # 返回 14B 实际可调用的工具白名单，而非全部注册工具
            self._send_json(200, {"ok": True, "model": MODEL, "agent": AGENT, "tools": TOOLS})
            return
        if route == "/events":
            self._serve_events(query)
            return
        if route == "/events/history":
            self._serve_event_history(query)
            return
        self._send_json(404, {"ok": False, "error": "未找到该路径。"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path.rstrip("/") != "/ask":
            self._send_json(404, {"ok": False, "error": "未找到该路径。"})
            return
        length = int(self.headers.get("Content-Length") or 0)
        if length > MAX_BODY_BYTES:
            self._send_json(413, {"ok": False, "error": "请求体过大。"})
            return
        raw = self.rfile.read(length) if length else b"{}"
        try:
            payload = json.loads(raw.decode("utf-8"))
            query = str(payload.get("query", "")).strip()
        except (json.JSONDecodeError, UnicodeDecodeError):
            self._send_json(400, {"ok": False, "error": "请求体不是合法 JSON。"})
            return
        if not query:
            self._send_json(400, {"ok": False, "error": "query 不能为空。"})
            return
        try:
            max_tokens = payload.get("max_tokens")
            if max_tokens is not None:
                max_tokens = int(max_tokens)  # 非数字 → 400 参数错误（不误报推理失败）
        except (TypeError, ValueError):
            self._send_json(400, {"ok": False, "error": "max_tokens 必须为整数。"})
            return
        try:
            result = ask_once(query, max_tokens=max_tokens)
            result["ok"] = True
            self._send_json(200, result)
        except Exception as exc:  # 推理异常返回可读错误
            self._send_json(500, {"ok": False, "error": f"推理失败：{exc}"})


def main() -> int:
    # 单实例守卫（2026-10-27 性能修复）：ThreadingHTTPServer 默认
    # allow_reuse_address=True，双实例可同时 bind 同一端口 → 每次测试
    # 拉一个新实例且不回收，进程累积吃满机器。先探测端口/再查 pid 锁。
    try:
        import urllib.request as _urlreq

        with _urlreq.urlopen(f"http://{HOST}:{PORT}/health", timeout=1) as _resp:
            sys.stderr.write("[agent-server] 已有实例在运行（health 有响应），本实例退出。\n")
            return 0
    except Exception:
        pass  # 端口无响应：继续，尝试自己接管

    import ctypes
    import tempfile

    _lock = Path(tempfile.gettempdir()) / "ultima-agent-server.pid"

    def _holder_alive() -> bool:
        try:
            old = int(_lock.read_text().strip())
            h = ctypes.windll.kernel32.OpenProcess(0x1000, False, old)
            if h:
                ctypes.windll.kernel32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    if _holder_alive():
        sys.stderr.write("[agent-server] 已有实例在运行（pid 锁存活），本实例退出。\n")
        return 0
    try:
        _lock.write_text(str(os.getpid()), encoding="utf-8")
    except Exception:
        pass

    import atexit

    def _cleanup_lock() -> None:
        try:
            if _lock.read_text().strip() == str(os.getpid()):
                _lock.unlink(missing_ok=True)
        except Exception:
            pass

    atexit.register(_cleanup_lock)

    # 端口独占（Windows SO_EXCLUSIVEADDRUSE）：禁 SO_REUSEADDR 双 bind，
    # 极端竞态下两个实例同时启动时，后到者 bind 失败自动退出，杜绝双实例并存。
    import socket as _sock_mod

    _sock = _sock_mod.socket(_sock_mod.AF_INET, _sock_mod.SOCK_STREAM)
    _sock.setsockopt(_sock_mod.SOL_SOCKET, _sock_mod.SO_EXCLUSIVEADDRUSE, 1)
    try:
        _sock.bind((HOST, PORT))
    except OSError:
        sys.stderr.write(f"[agent-server] 端口 {PORT} 已被占用（已有实例在运行），本实例退出。\n")
        return 0
    _sock.listen(128)
    server = ThreadingHTTPServer((HOST, PORT), _Handler, bind_and_activate=False)
    server.socket = _sock
    sys.stderr.write(
        f"[agent-server] 启动：http://{HOST}:{PORT} model={MODEL} agent={AGENT} tools={TOOLS}\n"
    )
    # RU-05 启动自检：后台静默线程，失败不阻断主链路（N6/N7）
    threading.Thread(target=_startup_update_check, daemon=True).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        sys.stderr.write("[agent-server] 收到终止信号，退出。\n")
    finally:
        server.server_close()
        if _jars is not None:
            _jars.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
