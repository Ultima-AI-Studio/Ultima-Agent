"""Ultima Agent 智能体服务器（常驻进程，venv-openjarvis 运行）。

三层架构中的"智能体服务器"层：薄壳（文字 CLI / 语音 daemon / 悬浮球壳）
通过本机 HTTP 接口调用本地 8B 主脑的自主对话循环（底座 OpenJarvis Agent 循环）。

接口：
- GET  /health   → 服务状态（模型 / agent / 已注册工具清单）
- POST /ask      → {"query": str, "max_tokens": int?} → {"content", "tool_results", "usage"}

设计约束：
- 仅标准库 + openjarvis + UltimaAgent 自有模块；
- 工具注册：import agent_tools_ultima 触发 ToolRegistry 装饰器注册；
- 模型：由 S-MAIN 插槽选择；agent：simple（ReAct 工具循环）。
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

from src.brain.prompt_boundary import PROMPT_SECURITY_RULES, build_user_data  # noqa: E402
from src.brain.providers.base import ProviderConfigError  # noqa: E402
from src.brain.providers.resolve import provider_for  # noqa: E402
from src.brain.slot_adapter import main_settings  # noqa: E402

try:  # 主脑职责提议入口（/mainbrain 专用，不参与 /ask 语音链路）
    from .mainbrain_proposal import propose as propose_mainbrain  # noqa: E402
except ImportError:  # pragma: no cover - 脚本入口
    from mainbrain_proposal import propose as propose_mainbrain  # noqa: E402


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
    return f"{persona}\n\n{block.group(1).strip()}\n\n{PROMPT_SECURITY_RULES}"


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
    # 规则必须前置：8B 对写在末尾的约束不敏感（lessons L138），而 native_react 的提示词
    # 通篇在催它「调工具、走 ReAct 循环」，追加在末尾的否性规则会被前面的强指令压过去。
    # 实测把规则放末尾时，面对「把 CV3 音色修好」仍连调 4 次只读工具、57 秒答成「建议重装软件」。
    assembled = (
        f"{MAINBRAIN_SYSTEM_PROMPT}\n"
        "【优先级】以上规则优先于后续任何工具使用、循环或流程指引；"
        "与后续指引冲突时以上述规则为准。\n\n"
        f"{react_prompt}"
    )

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


def _load_main_settings() -> dict[str, Any]:
    try:
        return main_settings()
    except Exception as exc:  # 配置坏了也要让服务可报告空状态，且必须明确记录原因
        sys.stderr.write(f"[agent-server] S-MAIN 配置加载失败：{type(exc).__name__}: {exc}\n")
        return {
            "slot": "S-MAIN",
            "impl": "",
            "endpoint": "",
            "model": "",
            "enabled": False,
            "error": str(exc),
        }


_MAIN = _load_main_settings()
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
    "ultima_dispatch",
    "ultima_dispatch_status",
]
# /ask 应答侧工具面 = 「本地事实 + 接单派单」两类。
# 主脑的职责是接单与编排（规则第 10/11 条）：必须给它真正能派出去的 dispatch 工具，
# 否则它只会嘴上说「我马上安排」——那是 L140 记过的空口假称。
# 但不给 task_adjust / skill_manage / subagent / env_snapshot 这类「自己动手改系统」或
# 「去查外部状态凑答案」的动作：实测 8B 拿到 task_adjust 会去改队列、拿到只读查询工具
# 会把「修 CV3」理解成「查队列里某条任务」，两者都跑偏。
ANSWER_TOOLS = [
    "calculator",
    "think",
    "ultima_memory",
    "ultima_dispatch",
    "ultima_dispatch_status",
]
# 语音应答的事实来源只有两个：注入的当前时间 + 本地记忆。web_search / task_query /
# env_snapshot 都是「去查外部状态」，属主脑侧。实测留着 task_query 时，8B 会把
# 「把 CV3 音色修好」理解成「改队列里的某条任务」：查队列→调 task_adjust→失败→兜底。
DEFAULT_MAX_TOKENS = 1024
# /ask 的 ReAct 轮次预算：默认 10 轮会让 8B 反复调同一个只读工具不收敛
# （实测同一个 ultima_task_query 连调 3 次、57 秒仍答偏）。2 轮＝最多一次工具＋一次收尾作答。
ASK_MAX_TURNS = 2
MAX_BODY_BYTES = 1024 * 1024  # 请求体上限 1MB（本地接口防异常大包）
SSE_PING_SECONDS = 15.0
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
# 排队上限（秒）：语音侧 worker_timeout_seconds=90，这里必须明显小于它，
# 否则语音轮次会在队列里被饿到超时（见 L158）。
ASK_LOCK_TIMEOUT = 40.0
_manager_token: str | None = None


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
        # OpenJarvis engine keys are not provider impl names. Its current local
        # engine supports both the canonical Ollama impl and the frozen
        # ``ollama-8b`` S-MAIN default; other providers have no safe mapping.
        engine_key = {"ollama": "ollama", "ollama-8b": "ollama"}.get(
            str(_MAIN.get("impl") or "").lower()
        )
        if engine_key is None:
            raise ProviderConfigError(
                f"S-MAIN impl 无法映射到 OpenJarvis engine: {_MAIN.get('impl') or '<empty>'}"
            )
        _jars = Jarvis(engine_key=engine_key, model=str(_MAIN.get("model") or ""))
        # 本实例只服务 /ask（语音应答，不是长任务编排）。把 ReAct 轮次预算从默认 10 压到 2：
        # ultima_subagent 派出的子代理是另一个 Jarvis 实例，不受此设置影响。
        try:
            _jars._config.agent.max_turns = ASK_MAX_TURNS
        except Exception as exc:  # noqa: BLE001 - 压不下预算也不该让 /ask 起不来
            sys.stderr.write(f"[agent-server] max_turns 设置失败（忽略）：{exc}\n")
    return _jars


_GROUNDED_TAG = re.compile(r"\bgrounded\s*[:：=]\s*(?:true|false)\b", re.IGNORECASE)

_CLAIM_ACTIONS = (
    r"整理|重命名|删除|删掉|创建|新建|保存|修改|改好|修复|安装|卸载|"
    r"下载|上传|打开|移动|复制"
)
_CLAIM_PATTERNS = (
    re.compile(
        rf"(?:我|我们|本人|这边)?[^。！？!?]{{0,12}}(?:已|已经|刚刚|刚才)"
        rf"[^。！？!?]{{0,12}}(?:{_CLAIM_ACTIONS})(?:了|好|完|完毕)?"
        r"[^。！？!?\s]{1,24}"
    ),
    re.compile(
        rf"(?:我|我们|本人|这边|帮你|给你|替你|为您)[^。！？!?]{{0,12}}"
        rf"(?:{_CLAIM_ACTIONS})[^。！？!?\s]{{1,24}}(?:了|好|完|完毕)"
    ),
)
_DELEGATED_ACTION_PATTERN = re.compile(rf"(?:{_CLAIM_ACTIONS})")
_SERVILE_TAIL_PATTERN = re.compile(
    r"[，。！\s]*(?:需要我|要不要我|要我|我可以帮你|还需不需要|还需要我|"
    r"您还有其他问题|你还有其他问题|还有其他问题|还有别的问题|有其他问题)"
    r".{0,12}(?:吗|么)[？?]?\s*$"
)


def _claim_clean(content: str) -> str:
    """把虚假的第一人称完成态操作句替换为能力边界话术。"""
    if not content:
        return content

    def replace_sentence(match: re.Match[str]) -> str:
        sentence = match.group(0)
        stripped = sentence.strip()
        if re.search(r"(?:吗|么|是否|是不是|有没有)[？?]?\s*$|[？?]\s*$", stripped):
            return sentence
        if not any(pattern.search(stripped) for pattern in _CLAIM_PATTERNS):
            return sentence
        leading = sentence[: len(sentence) - len(sentence.lstrip())]
        trailing = sentence[len(sentence.rstrip()) :]
        return f"{leading}这个我做不到，需要真的去执行。{trailing}"

    return re.sub(r"[^。！？!?]+[。！？!?]?", replace_sentence, content)


def _clean_content(content: str) -> str:
    """清理响应文本：只保留 Final Answer 之后的内容，并剥掉内部标记；无标记则原样返回。"""
    if not content:
        return content
    marker = "Final Answer:"
    if marker in content:
        content = content.split(marker, 1)[1]
    # 8B 会把内部依据标记当正文念出来（如 "grounded:false  不确定…"），语音场景里这是噪音。
    # 行为层提示词压不住（lessons L138），只能在出口统一剥离。
    content = _GROUNDED_TAG.sub("", content)
    servile_tail = _SERVILE_TAIL_PATTERN.search(content)
    if servile_tail is not None:
        matched = servile_tail.group(0)
        punctuation = "！" if "！" in matched else "。" if "。" in matched else ""
        content = f"{content[:servile_tail.start()]}{punctuation}"
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
    try:
        result = provider_for(_MAIN).chat(
            system_prompt=STRUCTURED_REPLY_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_payload}],
            temperature=None,
            max_tokens=None,
            json_schema=REPLY_JSON_SCHEMA,
            disable_thinking=True,
            timeout=STRUCTURED_REPLY_TIMEOUT_SECONDS,
        )
    except (HTTPError, URLError, TimeoutError, OSError, UnicodeError, ValueError, TypeError) as exc:
        raise StructuredReplyError(f"structured provider request failed: {type(exc).__name__}") from exc
    return parse_structured_reply(result.content)


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


# ---------------------------------------------------------- 分段应答（语音）
# 语音通道的关键不是把总时延压到最小，而是「不许静默」：用户可以等 30 秒，
# 但中间必须知道它有没有断。所以任务类诉求走分段应答：
#   ① 分类完成立刻回「好的，我现在去安排」（约 1s，不等派单）
#   ② 派单完成立刻回「已派给 DeepSeek，派单号 X」（派单本身 0.03s）
#   ③ 外脑方案回来再由后台线程推一条（见 agent_tools_ultima._notify_event）
# 分类只问一件事（要不要动手），输出截到 8 token，不产生长推理。
# 走这条路的另一个好处：8B 没有机会在自由生成里撒谎说「我已经修好了」。

_ASK_ACK_TEXT = "好的，我现在去安排。"

# 验收表态：只有用户亲口说这些词，才收回探针、宣布完成；说别的（尤其否定）都不收。
_ACCEPT_PATTERN = re.compile(
    r"^(可以|可以了|行|行了|好的|好|ok|OK|Ok|okay|没问题|没毛病|通过|就这样|就这样吧|"
    r"不错|挺好|满意|成|中)[。！!，,~～\s]*$"
)
# 否定/返工信号：命中就当普通诉求走，绝不因为句子里带个「行」就把探针收了。
_REJECT_HINT = re.compile(r"不行|不好|重做|重来|不对|有问题|不满意|再改|还要改")


def _try_accept(query: str) -> dict[str, Any] | None:
    """用户表态验收时就地收探针：不再派单，宣布这单完成。

    只在「确实有待验收的单子」时生效；没有待验收单时，这句「可以」按普通回答处理。
    """
    text = (query or "").strip()
    if _REJECT_HINT.search(text):
        return None
    if not _ACCEPT_PATTERN.match(text):
        return None
    try:
        try:
            from .agent_tools_ultima import accept_latest
        except ImportError:  # pragma: no cover - 脚本入口
            from agent_tools_ultima import accept_latest

        payload = accept_latest()
    except Exception:
        return None
    if not payload:
        return None
    done = "好，这单我收了，任务算完成。"
    EVENT_BUS.emit_event("message", {"text": done, "role": "jarvis"})
    # phase 里出现「完成」，四角壳左下窗口会自动把这张任务卡清掉
    EVENT_BUS.emit_event(
        "task_advance",
        {
            "task_id": str(payload.get("task") or "")[:18],
            "phase": "已完成 · 验收通过",
            "state": "done",
        },
    )
    return {
        "content": done,
        "reply_text": done,
        "intent": "accept",
        "dispatch_id": payload.get("dispatch_id", ""),
        "tool_results": [],
    }

_ASK_CLASSIFY_SYSTEM = (
    "你只需要做一件事：判断用户这句话，是要你动手改东西（改代码、修功能、开发、制作、设计、接入、优化），"
    "还是只要一个回答（查时间、问状态、问原因、闲聊）。\n"
    "边界：只想「是哪一类」。不要展开方案，不要猜文件路径，不要规划步骤，不要补充其他判断，不要联想用户还想要什么。\n"
    "想清楚就直接输出两个词之一：动手 或 回答。拿不准就输出 回答。"
)

# 明显是「问事」的句式不进模型，直接按查询处理，避免把提问误派成工单
_QUERY_HINT = re.compile(
    r"[?？]|几点|几号|多少|什么|怎么样|为什么|是不是|有没有|能不能|谁|哪里|哪个|如何"
)
_METHOD_ASK = re.compile(r"怎么|怎样|如何|为什么|是什么|什么是|啥是|能不能|可不可以|会不会")
_DELEGATE_HINT = re.compile(r"帮我|给我|替我|帮我做|你去|你帮我|麻烦你")
_DIAGNOSE_PATTERNS = re.compile(
    r"怎么办|怎么解决|怎么修|报错|蓝屏|打不开|闪退|卡死|异常|失败|不工作|报\d{3}"
)


# 危险/越界诉求的代码层前置门。8B 面对"帮我X"会一律判成 task 并接单派出去
# （规则 R10「非查询类就接单」比 R5「违规用兜底话术」更具体，模型实际选了 R10），
# 行为层提示词压不住（lessons L138）。所以这里命中就绝不进入 task 分支。
_RISK_PATTERNS = (
    # 语序双向：既要抓「删掉D盘」，也要抓「D盘全删了」
    re.compile(r"(删|清空|清掉|格式化|抹掉|销毁|清除|干掉).{0,12}(盘|硬盘|文件|文件夹|目录|数据|数据库|记录|全部|所有|整块)"),
    re.compile(r"(盘|硬盘|文件|文件夹|目录|数据|数据库|记录|全部|所有).{0,12}(删|清空|清掉|格式化|抹掉|销毁|清除|干掉)"),
    re.compile(r"(rm\s+-rf|format\s+[a-z]:|del\s+/[sfq])", re.IGNORECASE),
    re.compile(r"(编|编造|捏造|伪造|杜撰|生成).{0,12}(假|虚假|不实|造谣).{0,12}(新闻|消息|报道|谣言|传言)"),
    re.compile(r"(造谣|散布谣言|伪造证据|伪造公文|伪造签名)"),
    re.compile(r"(冒充|假装成|伪装成).{0,8}(官方|客服|公安|警察|银行|领导|他本人)"),
    re.compile(r"(攻击|入侵|破解|脱壳|提权|绕过).{0,10}(系统|服务器|账号|密码|验证码|认证|限制|防火墙|风控)"),
)
_RISK_REFUSAL = "这个我不做，也不会派出去。"

# 能力边界门：这些实时数据当前没有任何工具能取（tools 只有 calculator/think/memory/dispatch），
# 8B 被问到时会在"不知道"和"编一个"之间摇摆——实测同一句天气问两次，一次说不知道、一次
# 编出"有雨、1到5度、西北风3到4级"。编出来的实时数据最危险（听起来完全可信），
# 所以这类必须代码层拦成固定话术，不给模型自由发挥的机会。
_NO_TOOL_PATTERNS = (
    re.compile(r"(天气|气温|下雨|降雨|温度|空气质量|PM2\.?5|紫外线|风力|几度)"),
    re.compile(r"(股价|汇率|金价|油价|大盘|涨停|跌停|市值|行情)"),
    re.compile(r"(航班|列车|火车票|机票|车次|路况|堵车)"),
)
_NO_TOOL_REPLY = "这个我查不了，我这边没有联网的实时数据。"


def _no_tool_gate(query: str) -> str | None:
    """命中"需要实时数据但无工具可用"的查询时返回固定话术；未命中返回 None。"""
    for pattern in _NO_TOOL_PATTERNS:
        if pattern.search(query):
            return _NO_TOOL_REPLY
    return None


def _risk_gate(query: str) -> str | None:
    """命中危险/越界诉求时返回拒答话术；未命中返回 None。"""
    for pattern in _RISK_PATTERNS:
        if pattern.search(query):
            return f"{_RISK_REFUSAL}刚才那句我理解的是越界操作，不再展开。"
    return None


def _classify_intent(query: str) -> str:
    """返回 'task'（该接单派出去）或 'query'（直接回答）。任何异常都退回 query。"""
    if _QUERY_HINT.search(query):
        return "query"
    if _METHOD_ASK.search(query) and not _DELEGATE_HINT.search(query):
        return "query"
    try:
        # 保留模型的思考，只是把思考框在「只判类别」这一个边界里（见上面的 system）。
        # 不能关思考：关了就等于把主脑的脑子摘掉，它以后只能靠外脑。
        # 但也不能让 num_predict 太紧：thinking 会先吃掉 token，短预算会返回空内容。
        result = provider_for(_MAIN).chat(
            system_prompt=_ASK_CLASSIFY_SYSTEM,
            messages=[{"role": "user", "content": query}],
            temperature=0,
            max_tokens=256,
            disable_thinking=False,
            timeout=15,
        )
        verdict = result.content
    except Exception:  # 分类失败不影响主流程，按查询走
        return "query"
    return "task" if "动手" in verdict else "query"


def _ask_task_branch(query: str) -> dict[str, Any]:
    """任务类分段应答：先答应，再派单，后续由后台线程逐环节汇报。"""
    EVENT_BUS.emit_event("message", {"text": _ASK_ACK_TEXT, "role": "jarvis"})
    EVENT_BUS.emit_event("stream_start", {"text": "已接单，正在派给审计外脑…"})
    # 四角壳左下任务窗口：这张卡一出现，就代表探针挂上了，直到用户验收才摘
    EVENT_BUS.emit_event(
        "task_advance",
        {
            "task_id": " ".join((query or "").split())[:18],
            "phase": "已接单 · 正在派给策划部",
            "state": "accepted",
        },
    )

    dispatch_id = ""
    try:
        try:
            from .agent_tools_ultima import UltimaDispatchTool
        except ImportError:  # pragma: no cover - 脚本入口
            from agent_tools_ultima import UltimaDispatchTool

        result = UltimaDispatchTool().execute(task=query)
        dispatch_id = str((result.metadata or {}).get("dispatch_id") or "")
        if result.success:
            # 对用户只说人话，不报工单号；单号留在 metadata 供进度查询用。
            follow = "已派给策划部，正在出方案。那边一有反馈我马上告诉你。"
        else:
            follow = str(result.content)
    except Exception as exc:  # 派单失败也必须说出来，不能装作派了
        follow = f"派单没成功：{exc}"

    EVENT_BUS.emit_event("message", {"text": follow, "role": "jarvis"})
    return {
        "content": _ASK_ACK_TEXT + follow,
        "reply_text": follow,
        "intent": "task",
        "dispatch_id": dispatch_id,
        "tool_results": [],
    }


# 查询类直连：不进 ReAct 工具循环。8B 一旦看到工具清单就会反复试，
# 实测一次问答能被拖到 30 秒；单次直连带规则 + 当前时间，3-5 秒出话。
_DIAGNOSE_SYSTEM = (
    "【本轮诊断方式】说明可能原因，并给出一到三条用户可以自行尝试的排查方向。"
    "禁止说‘你再说一遍’，禁止反问，禁止声称查看过任何日志、文件、后台或系统状态。"
    "你没有文件系统、屏幕或系统状态访问能力；不知道的事实必须明确说不知道。"
)
# 诊断回答只要求一到三条排查方向，给足 160 token 即可；
# 不设上限会让 qwen3 边思考边铺陈，实测单轮被拖到 12.8~18.5 秒。
_DIAGNOSE_MAX_TOKENS = 160
# 常见故障的确定性排查方向。8B 在诊断场景会被自己的派单话术带偏
# （实测关闭思考后直接吐"我马上安排。已派给 DeepSeek。"），
# 开思考又要 12~18 秒；因此常见故障走规则表 0 秒直答，罕见故障才回模型。
_DIAGNOSE_DIRECTIONS = (
    (
        re.compile(r"蓝屏|0x[0-9A-Fa-f]{4,}"),
        "可以先记下蓝屏错误代码并重启电脑；如果再次出现，再检查最近安装的驱动或系统更新。",
    ),
    (
        re.compile(r"报\s*500|500\s*错误|[45]xx"),
        "可以先看服务端日志里那条完整堆栈，再确认数据库连接和最近上线的改动。",
    ),
    (
        re.compile(r"闪退|崩溃|crash"),
        "可以先记下崩溃的时间点和操作步骤，再检查最近的版本更新或插件变化。",
    ),
    (
        re.compile(r"打不开|启动不了|起不来"),
        "可以先确认进程是否还在、端口有没有被占用，再看最近的配置改动。",
    ),
    (
        re.compile(r"卡死|卡住|无响应"),
        "可以先强制结束进程并记下当时的资源占用，再排查是否有死循环或磁盘写满。",
    ),
    (
        re.compile(r"报错|异常|失败|不工作"),
        "可以先记录完整报错原文并稳定重现一次，再对照最近的配置或依赖变更。",
    ),
)
_QUERY_SYSTEM = (
    "【本轮回话方式】只用一到三句话直接回答，不要调用任何工具，不要规划步骤，"
    "不要展开方案，不要反问用户是否需要帮忙，不要加服务性结尾，不要联想用户还想问什么。"
    "不知道就说不知道。"
    "也不要建议用户联系技术支持、联系客服、查阅官方文档或找运维——你没有这些渠道，说这些等于骗人。"
)
_QUERY_CAPABILITY_SYSTEM = (
    "【本轮能力边界】你没有手、没有文件系统访问、没有屏幕、没有网络。"
    "你不能打开、整理、重命名、删除、创建、保存任何文件或程序。"
    "用户要求你做这类事时，只能说明‘我做不到，这需要真的去执行’，并指出这属于执行类任务；"
    "绝不能描述成已经做完。"
)


def _diagnose_clean(query: str, content: str) -> str:
    """移除诊断反问；模型未给排查动作时补一条确定性方向。"""
    statements: list[str] = []
    for sentence in re.findall(r"[^。！？!?]+[。！？!?]?", content):
        stripped = sentence.strip()
        if "你再说一遍" in stripped or stripped.endswith(("？", "?")):
            continue
        statements.append(stripped)
    cleaned = "".join(statements)
    if re.search(r"先|检查|重启|确认|尝试|排查|记录", cleaned):
        return cleaned
    if re.search(r"蓝屏", query):
        direction = "可以先记录蓝屏错误代码并重启电脑；如果再次出现，再检查近期驱动或系统更新。"
    else:
        direction = "可以先记录完整报错并重现一次，再检查最近的配置或依赖变更。"
    return f"{cleaned}{direction}"


def _ask_diagnose_branch(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """诊断类：一次直连给排查方向，不调工具、不假装查看过现场。"""
    import datetime as _dt

    # 常见故障走确定性规则表：0 秒出话，也不会被派单话术带偏。
    for pattern, direction in _DIAGNOSE_DIRECTIONS:
        if pattern.search(query):
            EVENT_BUS.emit_event("message", {"text": direction, "role": "jarvis"})
            return {
                "content": direction,
                "reply_text": direction,
                "confidence": 1.0,
                "grounded": True,
                "intent": "query",
                "tool_results": [],
                "usage": {},
            }

    now = _dt.datetime.now()
    weekdays = "一二三四五六日"
    time_ctx = "[当前时间：{0:%Y-%m-%d} {0:%H:%M} 星期{1}（北京时间）]".format(
        now, weekdays[now.weekday()]
    )
    user_content = build_user_data(speech=query, trusted_context=time_ctx).render()
    usage: dict[str, Any] = {}
    content = ""
    try:
        result = provider_for(_MAIN).chat(
            system_prompt=f"{MAINBRAIN_SYSTEM_PROMPT}\n{_DIAGNOSE_SYSTEM}",
            messages=[{"role": "user", "content": user_content}],
            temperature=0.2,
            max_tokens=min(int(max_tokens or _DIAGNOSE_MAX_TOKENS), _DIAGNOSE_MAX_TOKENS),
            disable_thinking=False,
            timeout=60,
        )
        content = _claim_clean(_diagnose_clean(query, _clean_content(result.content)))
        usage = result.usage
    except Exception as exc:  # 诊断直连失败也要如实说，不能装作查过现场
        sys.stderr.write(f"[ask] 诊断直连失败：{type(exc).__name__}: {exc}\n")
    if not content:
        content = STRUCTURED_FALLBACK_REPLY
    EVENT_BUS.emit_event("message", {"text": content, "role": "jarvis"})
    ok = content != STRUCTURED_FALLBACK_REPLY
    return {
        "content": content,
        "reply_text": content,
        "confidence": 1.0 if ok else 0.0,
        "grounded": ok,
        "intent": "query",
        "tool_results": [],
        "usage": usage,
    }


def _ask_query_branch(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """查询类：一次直连出答案，不跑 ReAct、不调工具。"""
    import datetime as _dt

    now = _dt.datetime.now()
    weekdays = "一二三四五六日"
    # 注入当前时间作为 grounded 事实：8B 无时间工具，不注入则"现在几点/今天几号"只能兜底
    time_ctx = "[当前时间：{0:%Y-%m-%d} {0:%H:%M} 星期{1}（北京时间）]".format(
        now, weekdays[now.weekday()]
    )
    # 保留 bounded data 结构：语音原文整段包进带 nonce 的边界，防止被当成指令执行
    user_content = build_user_data(speech=query, trusted_context=time_ctx).render()
    usage: dict[str, Any] = {}
    content = ""
    try:
        result = provider_for(_MAIN).chat(
            system_prompt=(
                f"{MAINBRAIN_SYSTEM_PROMPT}\n{_QUERY_SYSTEM}\n{_QUERY_CAPABILITY_SYSTEM}"
            ),
            messages=[{"role": "user", "content": user_content}],
            temperature=0.2,
            max_tokens=int(max_tokens or DEFAULT_MAX_TOKENS),
            disable_thinking=False,
            timeout=60,
        )
        content = _claim_clean(_clean_content(result.content))
        if _DELEGATE_HINT.search(query) and _DELEGATED_ACTION_PATTERN.search(query):
            content = "这个我做不到，这需要真的去执行，属于执行类任务。"
        usage = result.usage
    except Exception as exc:  # 直连失败也要如实说，不能装作答完了
        sys.stderr.write(f"[ask] 查询直连失败：{type(exc).__name__}: {exc}\n")
    if not content:
        content = STRUCTURED_FALLBACK_REPLY
    EVENT_BUS.emit_event("message", {"text": content, "role": "jarvis"})
    ok = content != STRUCTURED_FALLBACK_REPLY
    return {
        "content": content,
        "reply_text": content,
        "confidence": 1.0 if ok else 0.0,
        "grounded": ok,
        "intent": "query",
        "tool_results": [],
        "usage": usage,
    }


def ask_once(query: str, max_tokens: int | None = None) -> dict[str, Any]:
    """执行一轮自主对话：本地 8B 自主决定直接回答或调用工具（并发串行化）。

    全程向事件总线发布真实事件（四角壳 HUD 消费）：
    - 收到提问 → message_in（w-agent 流：用户消息）
    - 开始回复 → stream_start（w-agent 流：回复中）
    - 工具调用 → tool_executing / tool_call（w-hb 流）
    - 完成回复 → message（w-msg 流：AI 气泡）
    """
    EVENT_BUS.emit_event("message_in", {"text": query, "role": "user"})
    # 先看这句是不是「验收表态」：是，就收掉待验收的探针并宣布完成，不再派单
    accepted = _try_accept(query)
    if accepted is not None:
        return accepted
    # 危险/越界诉求：代码层直接拒，不进分类、不进任务分支、不派单
    denied = _risk_gate(query)
    if denied is not None:
        EVENT_BUS.emit_event("message", {"text": denied, "role": "jarvis"})
        return {
            "content": denied,
            "reply_text": denied,
            "confidence": 1.0,
            "grounded": False,
            "intent": "refused",
            "tool_results": [],
            "usage": {},
        }
    # 能力边界：需要实时数据但没有对应工具 → 固定话术，不让模型编
    no_tool = _no_tool_gate(query)
    if no_tool is not None:
        EVENT_BUS.emit_event("message", {"text": no_tool, "role": "jarvis"})
        return {
            "content": no_tool,
            "reply_text": no_tool,
            "confidence": 1.0,
            "grounded": False,
            "intent": "no_tool",
            "tool_results": [],
            "usage": {},
        }
    # 分段应答第一段：先判这是「要动手的活」还是「要个回答」。
    # 任务类立刻答应并派单，不进 ReAct——既快，也断掉它自由编「我已经修好了」的路。
    if _classify_intent(query) == "task":
        return _ask_task_branch(query)
    if _DIAGNOSE_PATTERNS.search(query) and not _DELEGATE_HINT.search(query):
        return _ask_diagnose_branch(query, max_tokens)
    # 排队上限：语音侧的 worker_timeout_seconds=90，若无限等锁，一次批量/长请求
    # 就能把语音轮次饿到超时（本轮真实事故）。拿不到锁就明确回"正忙"，让语音
    # 在预算内有一句话可说，而不是等到超时。
    if not _ask_lock.acquire(timeout=ASK_LOCK_TIMEOUT):
        busy = "我这边正忙，稍等一下再说。"
        EVENT_BUS.emit_event("message", {"text": busy, "role": "jarvis"})
        return {
            "content": busy,
            "reply_text": busy,
            "confidence": 0.0,
            "grounded": False,
            "intent": "busy",
            "tool_results": [],
            "usage": {},
        }
    try:
        EVENT_BUS.emit_event("stream_start", {"text": "Ultima 正在回复…"})
        # 查询类不再进 ReAct：一次直连出答案（ReAct 两轮实测 30 秒，太慢）
        return _ask_query_branch(query, max_tokens)
    finally:
        _ask_lock.release()


def _health_payload() -> dict[str, Any]:
    model = str(_MAIN.get("model") or "")
    configured = bool(_MAIN.get("enabled") and str(_MAIN.get("endpoint") or "").strip())
    payload: dict[str, Any] = {
        "ok": True,
        "model": model,
        "agent": AGENT,
        "tools": ANSWER_TOOLS,
        "provider": str(_MAIN.get("impl") or ""),
        "provider_model": model,
        "provider_configured": configured,
    }
    if not configured:
        payload["provider_note"] = "主脑未配置，/ask 将无法作答"
    return payload


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
            # 返回 8B 实际可调用的工具白名单（应答侧），而非全部注册工具
            self._send_json(200, _health_payload())
            return
        if route == "/events":
            self._serve_events(query)
            return
        if route == "/events/history":
            self._serve_event_history(query)
            return
        self._send_json(404, {"ok": False, "error": "未找到该路径。"})

    def do_POST(self) -> None:  # noqa: N802
        route = self.path.split("?")[0].rstrip("/") or "/"
        if route not in ("/ask", "/mainbrain"):
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
        if route == "/mainbrain":
            # 主脑职责入口：阶段 1 只提议，不派发、不写队列、不签冻结
            try:
                result = propose_mainbrain(query)
                result["ok"] = True
                self._send_json(200, result)
            except Exception as exc:  # 提议异常返回可读错误
                self._send_json(500, {"ok": False, "error": f"主脑提议失败：{exc}"})
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
        f"[agent-server] 启动：http://{HOST}:{PORT} model={_MAIN.get('model') or ''} agent={AGENT} "
        f"answer_tools={ANSWER_TOOLS} registered={len(TOOLS)}\n"
    )
    threading.Thread(target=_hud_tick_loop, daemon=True).start()
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
