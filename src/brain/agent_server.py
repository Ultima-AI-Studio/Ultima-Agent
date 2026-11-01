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
import importlib.util
import os
import queue
import re
import subprocess
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlparse
from urllib.request import Request, urlopen

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

JARVIS_PERSONA_PATH = (
    PROJECT_ROOT
    / "libs"
    / "base"
    / "openjarvis"
    / "configs"
    / "openjarvis"
    / "prompts"
    / "personas"
    / "jarvis.md"
)
MAINBRAIN_RULES_PATH = PROJECT_ROOT / "docs" / "specs" / "mainbrain-rules-baseline.md"


def _read_required_prompt(path: Path, label: str) -> str:
    try:
        content = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise RuntimeError(f"{label} prompt source unavailable: {path}") from exc
    if not content:
        raise RuntimeError(f"{label} prompt source is empty: {path}")
    return content


def _load_mainbrain_system_prompt() -> str:
    """Load jarvis.md and the v1.0 authoritative rule block once at startup."""
    persona = _read_required_prompt(JARVIS_PERSONA_PATH, "Jarvis persona")
    baseline = _read_required_prompt(MAINBRAIN_RULES_PATH, "mainbrain rules")
    if "v1.0" not in baseline:
        raise RuntimeError("mainbrain rules baseline is not v1.0")
    block = re.search(r"```\s*\r?\n(.*?)\r?\n```", baseline, re.DOTALL)
    if block is None or not block.group(1).strip():
        raise RuntimeError("mainbrain rules baseline has no embeddable rule block")
    return f"{persona}\n\n{block.group(1).strip()}"


MAINBRAIN_SYSTEM_PROMPT = _load_mainbrain_system_prompt()

from openjarvis import Jarvis  # noqa: E402
from openjarvis.core.registry import ToolRegistry  # noqa: E402

try:  # 包导入用于测试；脚本入口走 fallback
    from .reply.schema import (  # type: ignore[attr-defined] # noqa: E402
        REPLY_JSON_SCHEMA,
        StructuredReply,
        StructuredReplyError,
        parse_structured_reply,
    )
except ImportError:  # pragma: no cover - 脚本入口
    from reply.schema import (  # type: ignore[no-redef] # noqa: E402
        REPLY_JSON_SCHEMA,
        StructuredReply,
        StructuredReplyError,
        parse_structured_reply,
    )


def _install_mainbrain_system_prompt() -> str:
    """Append the cached mainbrain block to native_react's real SYSTEM prompt."""
    from openjarvis.agents import native_react

    original_loader = native_react.load_system_prompt_override
    react_prompt = original_loader("native_react") or native_react.REACT_SYSTEM_PROMPT
    assembled = f"{react_prompt}\n\n{MAINBRAIN_SYSTEM_PROMPT}"

    def load_with_mainbrain(agent_name: str) -> str | None:
        if agent_name == "native_react":
            return assembled
        return original_loader(agent_name)

    native_react.load_system_prompt_override = load_with_mainbrain
    return assembled


NATIVE_REACT_SYSTEM_PROMPT = _install_mainbrain_system_prompt()

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
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
STRUCTURED_REPLY_TIMEOUT_SECONDS = 180
STRUCTURED_FALLBACK_REPLY = "这个问题我暂时无法可靠回答。"
STRUCTURED_REPLY_SYSTEM_PROMPT = """\
你是本地 Agent 的最终回答边界。输出必须严格匹配给定 JSON Schema，禁止 markdown 和额外文本。
reply_text 最多两句，不含营销、关注、点赞或订阅话术。
confidence 是 0 到 1 的自评置信度。
grounded 仅当 reply_text 能被用户原文或工具证据直接支持时为 true；草稿本身不是证据。
无法确认时将 grounded 设为 false，并在 reply_text 中简短说明无法可靠回答。
"""


def _load_reply_style_once() -> tuple[tuple[str, ...], int]:
    try:
        from .voice.voice_profile import load_profile
    except ImportError:  # pragma: no cover - script entry
        from voice.voice_profile import load_profile

    style = load_profile()["style"]
    return tuple(style["banned_phrases"]), int(style["max_sentences"])


REPLY_BANNED_PHRASES, REPLY_MAX_SENTENCES = _load_reply_style_once()
EVENT_BUS = get_event_bus()

_jars: Jarvis | None = None
_ask_lock = threading.Lock()  # Jarvis 单例非线程安全，串行化并发推理
_manager_token: str | None = None
_work_service = None
_runtime_root: Path | None = None
_isolated = False


def _run_work_agent(query, *, binding, tools, max_tokens=None):
    with _ask_lock:
        from openjarvis.core.events import EventType
        jars = get_jarvis()
        trace = []
        def collect(event):
            trace.append(dict(type=event.event_type.value, timestamp=event.timestamp, data=event.data))
        kinds = (EventType.INFERENCE_END, EventType.TOOL_CALL_START, EventType.TOOL_CALL_END)
        for kind in kinds:
            jars._bus.subscribe(kind, collect)
        try:
            result = jars.ask_full(query, agent=AGENT, tools=tools, context=False,
                                   max_tokens=max_tokens or 2048)
            result['trace'] = trace
            return result
        finally:
            for kind in kinds:
                jars._bus.unsubscribe(kind, collect)



def _hardware_summary() -> str:
    """Return a compact, dependency-free hardware summary for the HUD tick."""
    memory_gb = 0
    try:
        import ctypes

        class _MemoryStatus(ctypes.Structure):
            _fields_ = [
                ("length", ctypes.c_ulong),
                ("memory_load", ctypes.c_ulong),
                ("total_physical", ctypes.c_ulonglong),
                ("available_physical", ctypes.c_ulonglong),
                ("total_page_file", ctypes.c_ulonglong),
                ("available_page_file", ctypes.c_ulonglong),
                ("total_virtual", ctypes.c_ulonglong),
                ("available_virtual", ctypes.c_ulonglong),
                ("available_extended_virtual", ctypes.c_ulonglong),
            ]

        status = _MemoryStatus()
        status.length = ctypes.sizeof(status)
        if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
            memory_gb = round(status.total_physical / (1024**3))
    except (AttributeError, OSError):
        pass
    memory = f" · {memory_gb}GB" if memory_gb else ""
    return f"{os.cpu_count() or 0}C{memory}"


def _network_totals() -> tuple[int, int]:
    """Read Windows interface byte totals without adding a runtime dependency."""
    try:
        completed = subprocess.run(
            ["netstat", "-e"],
            capture_output=True,
            text=True,
            encoding="mbcs",
            errors="ignore",
            timeout=2,
            check=False,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        for line in (completed.stdout or "").splitlines():
            values = re.findall(r"\d+", line)
            if len(values) == 2 and max(map(int, values)) > 1024:
                return int(values[0]), int(values[1])
    except (OSError, subprocess.SubprocessError):
        pass
    return 0, 0


def _read_manager_token() -> str:
    global _manager_token
    if _manager_token is not None:
        return _manager_token
    security_path = PROJECT_ROOT.parent / "UltimaManager" / "src" / "manager" / "security.py"
    spec = importlib.util.spec_from_file_location("ultima_manager_security", security_path)
    if spec is None or spec.loader is None:
        raise RuntimeError("Manager credential module is unavailable")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _manager_token = str(module.CredentialStore().read())
    return _manager_token


def _manager_active_tasks() -> list[dict[str, str]]:
    """Read the authenticated Manager task view; never expose its capability."""
    request = Request(
        "http://127.0.0.1:18766/api/v1/tasks?project_id=UltimaAgent",
        headers={"Authorization": "Bearer " + _read_manager_token()},
    )
    with urlopen(request, timeout=3) as response:
        payload = json.load(response)
    active_states = {"executing", "in_progress", "running", "develop", "plan", "plan_review", "audit"}
    tasks: list[dict[str, str]] = []
    for item in payload.get("items", []):
        state = str(item.get("state", "")).lower()
        if state in active_states:
            tasks.append(
                {
                    "work_order_id": str(item.get("work_order_id", "")),
                    "title": str(item.get("title", ""))[:120],
                    "state": state,
                }
            )
    for item in payload.get("legacy", []):
        state = str(item.get("registry_state", "")).lower()
        if state in active_states:
            tasks.append(
                {
                    "work_order_id": str(item.get("work_order_id", "")),
                    "title": str(item.get("registry_detail", ""))[:120],
                    "state": state,
                }
            )
    return tasks


def _hud_tick_loop() -> None:
    """Publish sticky system/Manager fields consumed by the eight-anchor HUD."""
    previous_rx, previous_tx = _network_totals()
    previous_time = time.monotonic()
    manager_tasks: list[dict[str, str]] = []
    manager_ok = False
    next_manager_read = 0.0
    tick = 0
    while True:
        tick += 1
        now = time.monotonic()
        rx, tx = _network_totals()
        elapsed = max(now - previous_time, 0.001)
        down_bps = max(0, round((rx - previous_rx) / elapsed)) if previous_rx else 0
        up_bps = max(0, round((tx - previous_tx) / elapsed)) if previous_tx else 0
        previous_rx, previous_tx, previous_time = rx, tx, now
        if now >= next_manager_read:
            try:
                manager_tasks = _manager_active_tasks()
                manager_ok = True
            except (HTTPError, URLError, OSError, RuntimeError, ValueError):
                manager_tasks = []
                manager_ok = False
            next_manager_read = now + 10.0
        EVENT_BUS.set_sticky(
            "tick",
            {
                "tick": tick,
                "hardware": _hardware_summary(),
                "connection": "Agent + Manager" if manager_ok else "Agent online",
                "down_bps": down_bps,
                "up_bps": up_bps,
                "manager_ok": manager_ok,
                "manager_tasks": manager_tasks,
                "queue_count": len(manager_tasks),
            },
        )
        time.sleep(2.0)


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
        if _isolated:
            from openjarvis.core.config import JarvisConfig
            config = JarvisConfig()
            config.telemetry.enabled = False
            config.analytics.enabled = False
            config.agent.context_from_memory = False
            # Relocate all dataclass path settings, including lazily opened stores.
            from dataclasses import fields, is_dataclass
            def relocate(obj, prefix='sdk'):
                for field in fields(obj):
                    value = getattr(obj, field.name)
                    if is_dataclass(value):
                        relocate(value, prefix + '-' + field.name)
                    elif isinstance(value, str) and ('path' in field.name or field.name.endswith('_dir')):
                        setattr(obj, field.name, str(_runtime_root / (prefix + '-' + field.name)))
            relocate(config)
            config._config_dir = _runtime_root
            _jars = Jarvis(config=config, engine_key=ENGINE_KEY, model=MODEL)
        else:
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


def _structured_evidence(tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for item in tool_results:
        evidence.append(
            {
                "tool_name": str(item.get("tool_name", "tool")),
                "success": bool(item.get("success")),
                "content": str(item.get("content", ""))[:4000],
            }
        )
    return evidence


def _request_structured_reply(
    query: str,
    draft: str,
    tool_results: list[dict[str, Any]],
    *,
    retry_note: str | None = None,
) -> StructuredReply:
    """Render the exposed answer through Ollama's native JSON Schema grammar."""
    user_payload = json.dumps(
        {
            "user_query": query,
            "agent_draft": draft,
            "tool_evidence": _structured_evidence(tool_results),
            "retry_note": retry_note,
        },
        ensure_ascii=False,
    )
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": STRUCTURED_REPLY_SYSTEM_PROMPT},
            {"role": "user", "content": user_payload},
        ],
        "stream": False,
        "think": False,
        "format": REPLY_JSON_SCHEMA,
    }
    request = Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=STRUCTURED_REPLY_TIMEOUT_SECONDS) as response:
            body = json.loads(response.read().decode("utf-8"))
        content = body.get("message", {}).get("content", "")
        if not isinstance(content, str):
            raise StructuredReplyError("Ollama message content must be a string")
        return parse_structured_reply(content)
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise StructuredReplyError(f"structured Ollama request failed: {type(exc).__name__}") from exc


def _fallback_verifier():
    try:
        from .routing.reply_verifier import get_reply_verifier
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import get_reply_verifier

    return get_reply_verifier(REPLY_BANNED_PHRASES, REPLY_MAX_SENTENCES)


def _structured_verifier():
    try:
        from .routing.reply_verifier import get_reply_verifier
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import get_reply_verifier

    return get_reply_verifier(
        REPLY_BANNED_PHRASES,
        REPLY_MAX_SENTENCES,
        enforce_grounded=True,
        enforce_confidence=True,
    )


def _verified_reply(reply: StructuredReply):
    try:
        from .routing.reply_verifier import ReplySchema
    except ImportError:  # pragma: no cover - script entry
        from routing.reply_verifier import ReplySchema

    return _structured_verifier().verify(
        ReplySchema(
            reply_text=reply.reply_text,
            confidence=reply.confidence,
            grounded=reply.grounded,
        )
    )


def _fixed_structured_fallback() -> StructuredReply:
    return StructuredReply(STRUCTURED_FALLBACK_REPLY, 1.0, True)


def _constrain_reply(
    query: str,
    draft: str,
    tool_results: list[dict[str, Any]],
) -> tuple[StructuredReply, bool]:
    """Enforce structure, grounding and confidence with at most one retry."""
    try:
        candidate = _request_structured_reply(query, draft, tool_results)
    except StructuredReplyError:
        try:
            from .routing.reply_verifier import ReplySchema
        except ImportError:  # pragma: no cover - script entry
            from routing.reply_verifier import ReplySchema

        checked = _fallback_verifier().verify(ReplySchema(reply_text=draft))
        if checked.accepted and checked.text:
            # A sanitized draft still lacks trustworthy generated metadata.
            _verified_reply(StructuredReply(checked.text, 0.0, False))
        return _fixed_structured_fallback(), True

    checked = _verified_reply(candidate)
    if checked.accepted:
        return StructuredReply(checked.text, candidate.confidence, candidate.grounded), False
    if "confidence_below_threshold" in checked.issues or "confidence_required" in checked.issues:
        return _fixed_structured_fallback(), True
    if "grounded_required" in checked.issues:
        try:
            retried = _request_structured_reply(
                query,
                draft,
                tool_results,
                retry_note=(
                    "上一回答 grounded=false，未通过真实性门。只重答这一次；"
                    "仅在用户原文或工具证据直接支持时 grounded=true，否则明确无法可靠回答。"
                ),
            )
        except StructuredReplyError:
            return _fixed_structured_fallback(), True
        retry_checked = _verified_reply(retried)
        if retry_checked.accepted:
            return StructuredReply(
                retry_checked.text,
                retried.confidence,
                retried.grounded,
            ), False
    return _fixed_structured_fallback(), True


def ask_once(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """执行一轮自主对话：本地 14B 自主决定直接回答或调用工具（并发串行化）。

    全程向事件总线发布真实事件（四角壳 HUD 消费）：
    - 收到提问 → message_in（w-agent 流：用户消息）
    - 开始回复 → stream_start（w-agent 流：回复中）
    - 工具调用 → tool_executing / tool_call（w-hb 流）
    - 完成回复 → message（w-msg 流：AI 气泡）
    """
    EVENT_BUS.emit_event("message_in", {"text": query, "role": "user"})
    j = get_jarvis()
    with _ask_lock:
        EVENT_BUS.emit_event("stream_start", {"text": "Ultima 正在回复…"})
        # 注入当前时间作为 grounded 事实：8B 无时间工具，不注入则"现在几点/今天几号"只能兜底
        import datetime as _dt

        _now = _dt.datetime.now()
        _weekdays = "一二三四五六日"
        _time_ctx = "[当前时间：{0:%Y-%m-%d} {0:%H:%M} 星期{1}（北京时间）]".format(
            _now, _weekdays[_now.weekday()]
        )
        query_with_ctx = f"{_time_ctx} {query}"
        result = j.ask_full(
            query_with_ctx,
            agent=AGENT,
            tools=TOOLS,
            context=False,
            max_tokens=max_tokens or DEFAULT_MAX_TOKENS,
        )
    draft = _clean_content(result.get("content", ""))
    tool_results = result.get("tool_results", [])
    structured_reply, degraded = _constrain_reply(query_with_ctx, draft, tool_results)
    content = structured_reply.reply_text
    for tr in tool_results:
        EVENT_BUS.emit_event(
            "tool_executing",
            {"tool": tr.get("tool_name", "tool"), "name": tr.get("tool_name", "tool")},
        )
        EVENT_BUS.emit_event(
            "tool_call",
            {
                "tool": tr.get("tool_name", "tool"),
                "name": tr.get("tool_name", "tool"),
                "text": (tr.get("content") or "")[:200],
                "ok": bool(tr.get("success")),
            },
        )
    EVENT_BUS.emit_event("message", {"text": content, "role": "jarvis"})
    return {
        "content": content,
        "reply_text": structured_reply.reply_text,
        "confidence": structured_reply.confidence,
        "grounded": structured_reply.grounded,
        "structured_reply": structured_reply.to_dict(),
        "structured_degraded": degraded,
        "tool_results": tool_results,
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
            if payload.get('mode') == 'work':
                if _work_service is None:
                    result = dict(request_id=payload.get('request_id'), session_id=payload.get('session_id'), task_id=None, status='failed', content='', artifacts=[], tool_results=[], error='Work output root is not configured')
                elif set(payload) - {'mode', 'query', 'request_id', 'session_id', 'context', 'max_tokens'}:
                    result = dict(status='failed', error='Unknown work request or authority fields', artifacts=[], content='', tool_results=[])
                else:
                    result = _work_service.submit_work(query, request_id=payload.get('request_id'), session_id=payload.get('session_id'), context=payload.get('context'), max_tokens=max_tokens)
            elif payload.get('mode') not in (None, 'chat'):
                self._send_json(400, {'ok': False, 'error': 'Unsupported mode'})
                return
            else:
                result = ask_once(query, max_tokens=max_tokens)
            result["ok"] = True
            self._send_json(200, result)
        except Exception as exc:  # 推理异常返回可读错误
            self._send_json(500, {"ok": False, "error": f"推理失败：{exc}"})


def main(argv=None) -> int:
    import argparse
    global PORT, _runtime_root, _isolated, _work_service
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--runtime-root', type=Path)
    parser.add_argument('--work-output-root', type=Path)
    parser.add_argument('--isolated', action='store_true')
    args = parser.parse_args(argv)
    PORT = args.port
    _isolated = args.isolated
    _runtime_root = args.runtime_root.resolve() if args.runtime_root else None
    if _isolated and (_runtime_root is None or args.work_output_root is None):
        parser.error('--isolated requires --runtime-root and --work-output-root')
    if _runtime_root:
        _runtime_root.mkdir(parents=True, exist_ok=True)
    if args.work_output_root:
        from src.brain.work_service import WorkService
        _work_service = WorkService(args.work_output_root, runner=_run_work_agent)
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

    _lock = (_runtime_root / "agent-server.pid") if _isolated else Path(tempfile.gettempdir()) / "ultima-agent-server.pid"

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
    if not _isolated:
        threading.Thread(target=_hud_tick_loop, daemon=True).start()
    # RU-05 启动自检：后台静默线程，失败不阻断主链路（N6/N7）
    if not _isolated:
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
