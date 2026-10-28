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
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from openjarvis import Jarvis  # noqa: E402
from openjarvis.core.registry import ToolRegistry  # noqa: E402

# 触发 Ultima 自定义工具注册（@ToolRegistry.register 装饰器）
import agent_tools_ultima  # noqa: F401,E402

HOST = "127.0.0.1"
PORT = 8756

ENGINE_KEY = "ollama"
MODEL = "qwen2.5:14b"
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

_jars: Jarvis | None = None
_ask_lock = threading.Lock()  # Jarvis 单例非线程安全，串行化并发推理


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

    def log_message(self, fmt: str, *args: Any) -> None:
        sys.stderr.write(f"[agent-server] {fmt % args}\n")

    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
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
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path.rstrip("/") == "/health":
            # 返回 14B 实际可调用的工具白名单，而非全部注册工具
            self._send_json(200, {"ok": True, "model": MODEL, "agent": AGENT, "tools": TOOLS})
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
