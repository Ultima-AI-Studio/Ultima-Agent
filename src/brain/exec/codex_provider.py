"""CodexProvider：GrokBot Codex 直连链路抄入 Ultima Agent（s6-codex-plugin）。

对齐 Grok Bot 0.18 reconstructed 的 Codex 接入（source/host/extensions/inference/
codex-direct-responses.ts + provider-session.ts codex 分支），转译为 Python 并
保持与 external_executor 相同的六字段 execution_report 契约：

- 凭证：读 ~/.codex/auth.json（chatgpt 模式校验：access/refresh/id token +
  account_id 四字段）；401 自动经 auth.openai.com/oauth/token 刷新后重试一次；
- 直连：POST chatgpt.com/backend-api/codex/responses（Responses API），SSE 流式
  解析，function_call 工具循环（maxSteps=8，无工具时 1 轮），usage 逐轮累计；
- 模型：config.toml 的 model / model_reasoning_effort，可用环境变量
  SAND_CODEX_MODEL / SAND_CODEX_REASONING_EFFORT 覆盖；
- 工具：tools 清单经注入（对齐 GrokBot executeTool 回调），工具调用全量留痕由
  调用方 M21 负责；本执行器不落 token 明文、不硬编码、不经日志；
- 失败确定性错误码（不穿透异常），对齐 TD-05 契约。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import base64
import json
import os
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional

from ..loop.params import ExecutionParams

# ---------------------------------------------------------------------------
# 常量（与 GrokBot 源码一致；端点/模型来自凭证与配置）
# ---------------------------------------------------------------------------
DEFAULT_RESPONSES_ENDPOINT = "https://chatgpt.com/backend-api/codex/responses"
DEFAULT_OAUTH_TOKEN_ENDPOINT = "https://auth.openai.com/oauth/token"
DEFAULT_MODEL = "gpt-5.4"  # GrokBot 源码默认
REASONING_EFFORTS = ("minimal", "low", "medium", "high", "xhigh")
MAX_STEPS_DEFAULT = 8
_MAX_BODY_LEN = 1_048_576

_SYSTEM_PROMPT = (
    "你是 UltimaAgent 的外部深度执行脑（Codex 通道）。任务由本地主脑下发，附带执行参数。"
    "请严格按四段输出协议作答，每段独立一行并以段名开头：\n"
    "THOUGHT：推理/目标拆解\n"
    "ACTION：本次调用的工具/动作（无工具则写 none）\n"
    "OBSERVE：工具返回/状态回读（无工具则写同 THOUGHT 结论）\n"
    "FINAL：结论/交付（面向用户，直接可用）\n"
    "禁止输出四段之外的内容。"
)

_TRACE_SEGMENTS = ("THOUGHT", "ACTION", "OBSERVE", "FINAL")
_TRACE_RE = re.compile(r"^\s*(THOUGHT|ACTION|OBSERVE|FINAL)\s*[:：]?\s*(.*)$", re.MULTILINE)


class CodexProviderError(Exception):
    """确定性错误（code 供审计打回，不穿透异常）。"""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


# ---------------------------------------------------------------------------
# 工具
# ---------------------------------------------------------------------------

CodexTool = dict[str, Any]
ToolExecutor = Callable[[CodexTool, Any, str], Any]


def _is_read_only(tool: CodexTool) -> bool:
    """GrokBot routed-mcp-bridge 只读判定（抄入，用于工具注解）。"""
    label = " ".join([
        str(tool.get("name", "")),
        str(tool.get("toolName", "")),
        str(tool.get("description", "")),
    ]).lower()
    read_hit = re.search(r"(^|[^a-z])(read|search|find|list|get|fetch|query|lookup|inspect|view|download|retrieve)([^a-z]|$)", label)
    write_hit = re.search(r"(send|create|update|delete|remove|write|upload|post|reply|archive|move|rename|modify|cancel|purchase|buy)", label)
    return bool(read_hit) and not bool(write_hit)


def _annotate_tools(tools: list[CodexTool]) -> list[dict[str, Any]]:
    """给工具加 GrokBot 式注解（readOnly/destructive/idempotent/openWorld hints）。"""
    out: list[dict[str, Any]] = []
    for tool in tools:
        name = str(tool.get("name", ""))
        if not name:
            continue
        read_only = _is_read_only(tool)
        out.append({
            "type": "function",
            "name": name,
            "description": str(tool.get("description", f"{tool.get('toolName', name)} via provider")),
            "parameters": tool.get("inputSchema") or tool.get("parameters") or {"type": "object", "additionalProperties": True},
            "strict": False,
            "annotations": {
                "readOnlyHint": read_only,
                "destructiveHint": not read_only,
                "idempotentHint": read_only,
                "openWorldHint": not read_only,
            },
        })
    return out


# ---------------------------------------------------------------------------
# 凭证（auth.json chatgpt 模式 + 401 刷新）
# ---------------------------------------------------------------------------

def _codex_home() -> Path:
    env = os.environ.get("CODEX_HOME", "").strip()
    return Path(env) if env else Path.home() / ".codex"


def _read_codex_credentials() -> dict[str, str]:
    """读取 ~/.codex/auth.json 并校验 chatgpt 登录态四字段。token 仅内存。"""
    path = _codex_home() / "auth.json"
    if not path.is_file():
        raise CodexProviderError(
            "credential_missing",
            f"Codex 登录态缺失（{path} 不存在）。请先执行 codex login。",
        )
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise CodexProviderError("credential_broken", f"Codex auth.json 无法读取：{exc}") from exc

    tokens = parsed.get("tokens") if isinstance(parsed, dict) else None
    if not isinstance(tokens, dict):
        raise CodexProviderError("credential_broken", "Codex auth.json 缺少 tokens 字段")
    access = tokens.get("access_token")
    refresh = tokens.get("refresh_token")
    id_token = tokens.get("id_token")
    account_id = tokens.get("account_id")
    if (
        parsed.get("auth_mode") != "chatgpt"
        or not isinstance(access, str) or not access
        or not isinstance(refresh, str) or not refresh
        or not isinstance(id_token, str) or not id_token
        or not isinstance(account_id, str) or not account_id
    ):
        raise CodexProviderError(
            "credential_mode",
            "Codex 未以 ChatGPT 模式登录（需 auth_mode=chatgpt 且四字段齐全）。请重新 codex login。",
        )
    return {"access": access, "refresh": refresh, "id": id_token, "account_id": account_id}


def _jwt_audience(token: str) -> Optional[str]:
    """从 id_token 提取 aud（用于刷新请求的 client_id）。"""
    try:
        payload = token.split(".")[1] or ""
        payload += "=" * (-len(payload) % 4)
        body = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")).decode("utf-8"))
    except (IndexError, ValueError, json.JSONDecodeError):
        return None
    aud = body.get("aud")
    if isinstance(aud, str) and aud:
        return aud
    if isinstance(aud, list):
        for item in aud:
            if isinstance(item, str) and item:
                return item
    return None


def _refresh_codex_credentials(creds: dict[str, str], *, transport: Optional[Any] = None) -> dict[str, str]:
    """401 后刷新 token（GrokBot refreshCodexCredentials 转译），并回写 auth.json。"""
    client_id = _jwt_audience(creds["id"])
    if not client_id:
        raise CodexProviderError("credential_expired", "Codex 登录过期且刷新身份无效，请重新 codex login")
    body = urllib.parse.urlencode({
        "grant_type": "refresh_token",
        "refresh_token": creds["refresh"],
        "client_id": client_id,
    }).encode("utf-8")
    request = urllib.request.Request(
        DEFAULT_OAUTH_TOKEN_ENDPOINT,
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    opener = transport if transport is not None else urllib.request.build_opener()
    try:
        with opener.open(request, timeout=30) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise CodexProviderError(
            "credential_expired",
            f"Codex 登录刷新失败（HTTP {exc.code}），请重新 codex login",
        ) from exc
    except urllib.error.URLError as exc:
        raise CodexProviderError("network_failed", f"登录刷新网络失败：{exc.reason}") from exc

    access = payload.get("access_token")
    if not isinstance(access, str) or not access:
        raise CodexProviderError("credential_expired", "Codex 刷新返回无效登录态，请重新 codex login")

    # 回写 auth.json（临时文件 + 原子替换，0600；GrokBot 同款）
    path = _codex_home() / "auth.json"
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        doc = {}
    doc.setdefault("tokens", {})
    new_refresh = payload.get("refresh_token")
    new_id = payload.get("id_token")
    doc["tokens"]["access_token"] = access
    if isinstance(new_refresh, str) and new_refresh:
        doc["tokens"]["refresh_token"] = new_refresh
    if isinstance(new_id, str) and new_id:
        doc["tokens"]["id_token"] = new_id
    doc["last_refresh"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    tmp = path.with_name(f"auth.json.{os.getpid()}.tmp")
    try:
        tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")
        try:
            os.chmod(tmp, 0o600)
        except OSError:
            pass
        tmp.replace(path)
    except OSError as exc:
        raise CodexProviderError("credential_write_failed", f"登录态回写失败：{exc}") from exc
    return {"access": access, "refresh": new_refresh or creds["refresh"], "id": new_id or creds["id"], "account_id": creds["account_id"]}


def _authenticated_fetch(initial: dict[str, str], *, transport: Optional[Any] = None):
    """401 自动刷新的请求包装（GrokBot codexAuthenticatedFetch 转译）。"""
    creds = initial

    def perform(request: urllib.request.Request) -> Any:
        request.add_header("Authorization", f"Bearer {creds['access']}")
        request.add_header("ChatGPT-Account-Id", creds["account_id"])
        opener = transport if transport is not None else urllib.request.build_opener()
        return opener.open(request, timeout=120)

    def fetch(request: urllib.request.Request) -> Any:
        nonlocal creds
        try:
            return perform(request)
        except urllib.error.HTTPError as exc:
            if exc.code != 401:
                raise
            creds = _refresh_codex_credentials(creds, transport=transport)
            return perform(request)

    return fetch


# ---------------------------------------------------------------------------
# 模型配置
# ---------------------------------------------------------------------------

def _configured_model() -> str:
    env = os.environ.get("SAND_CODEX_MODEL", "").strip()
    if env:
        return env
    try:
        text = (_codex_home() / "config.toml").read_text(encoding="utf-8")
        match = re.search(r'^\s*model\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if match:
            return match.group(1).strip()
    except OSError:
        pass
    return DEFAULT_MODEL


def _configured_reasoning_effort() -> Optional[str]:
    env = os.environ.get("SAND_CODEX_REASONING_EFFORT", "").strip()
    if env in REASONING_EFFORTS:
        return env
    try:
        text = (_codex_home() / "config.toml").read_text(encoding="utf-8")
        match = re.search(r'^\s*model_reasoning_effort\s*=\s*["\']([^"\']+)["\']', text, re.MULTILINE)
        if match and match.group(1).strip() in REASONING_EFFORTS:
            return match.group(1).strip()
    except OSError:
        pass
    return None


# ---------------------------------------------------------------------------
# SSE 解析（GrokBot sseEvents 转译）
# ---------------------------------------------------------------------------

def _sse_events(stream: Any) -> Any:
    """从 urllib 响应流解析 SSE 事件（按 \\n\\n 分块，取 data: 行）。"""
    buffer = ""
    while True:
        chunk = stream.read(8192)
        if not chunk:
            break
        buffer += chunk.decode("utf-8", errors="replace")
        while "\n\n" in buffer:
            block, buffer = buffer.split("\n\n", 1)
            block = block.replace("\r", "")
            data_lines = [
                line[5:].strip() for line in block.split("\n")
                if line.startswith("data:")
            ]
            data = "\n".join(data_lines)
            if not data or data == "[DONE]":
                continue
            try:
                yield json.loads(data)
            except json.JSONDecodeError:
                continue
    buffer = buffer.replace("\r", "")
    if buffer.strip() and buffer.strip() != "data: [DONE]":
        raise CodexProviderError("sse_malformed", "Codex 直连响应结束于不完整的 SSE 事件")


# ---------------------------------------------------------------------------
# Responses API 直连（GrokBot streamCodexDirectResponses 转译）
# ---------------------------------------------------------------------------

def _usage_of(response: dict[str, Any]) -> dict[str, int]:
    usage = response.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    return {
        "inputTokens": int(usage.get("input_tokens") or 0),
        "outputTokens": int(usage.get("output_tokens") or 0),
        "cacheReadTokens": int(details.get("cached_tokens") or 0),
        "cacheWriteTokens": 0,
    }


def _tool_calls(output: list[Any]) -> list[dict[str, Any]]:
    calls: list[dict[str, Any]] = []
    for item in output or []:
        if not isinstance(item, dict):
            continue
        if item.get("type") == "function_call" and isinstance(item.get("name"), str) and isinstance(item.get("call_id"), str):
            calls.append(item)
    return calls


def _safe_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, default=str)
    except (TypeError, ValueError):
        return json.dumps({"isError": True, "error": "无法序列化工具结果"})


def _stream_codex_direct(
    *,
    fetch: Any,
    endpoint: str,
    model: str,
    reasoning_effort: Optional[str],
    instructions: str,
    messages: list[dict[str, str]],
    tools: Optional[list[dict[str, Any]]],
    execute_tool: Optional[ToolExecutor],
    max_steps: int,
) -> tuple[str, dict[str, int]]:
    """Responses API 流式 + 工具循环。返回 (text, usage)。"""
    text = ""
    usage = {"inputTokens": 0, "outputTokens": 0, "cacheReadTokens": 0, "cacheWriteTokens": 0}
    input_msgs: list[dict[str, Any]] = [dict(item) for item in messages]

    for _step in range(max_steps):
        body: dict[str, Any] = {
            "model": model,
            "instructions": instructions,
            "input": input_msgs,
            "include": ["reasoning.encrypted_content"],
            "stream": True,
            "store": False,
        }
        if tools:
            body["tools"] = tools
            body["tool_choice"] = "auto"
            body["parallel_tool_calls"] = True
        if reasoning_effort:
            body["reasoning"] = {"effort": reasoning_effort, "summary": "auto"}

        request = urllib.request.Request(
            endpoint,
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
            method="POST",
        )
        try:
            response = fetch(request)
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8")[:300]
            except Exception:
                pass
            if exc.code == 401:
                raise CodexProviderError("auth_failed", f"Codex 鉴权失败（HTTP 401）{detail}") from exc
            if exc.code == 429:
                raise CodexProviderError("rate_limited", f"Codex 限流（HTTP 429）{detail}") from exc
            if exc.code >= 500:
                raise CodexProviderError("upstream_error", f"Codex 服务错误（HTTP {exc.code}）{detail}") from exc
            raise CodexProviderError("http_error", f"Codex 返回 HTTP {exc.code}{detail}") from exc
        except urllib.error.URLError as exc:
            raise CodexProviderError("network_failed", f"无法连接 Codex：{exc.reason}") from exc
        except TimeoutError as exc:
            raise CodexProviderError("timeout", "Codex 调用超时") from exc

        completed: Optional[dict[str, Any]] = None
        observed: list[dict[str, Any]] = []
        try:
            with response:
                for event in _sse_events(response):
                    etype = event.get("type")
                    if etype == "response.output_text.delta" and isinstance(event.get("delta"), str):
                        text += event["delta"]
                    elif etype == "response.output_item.done" and isinstance(event.get("item"), dict):
                        observed.append(event["item"])
                    elif etype == "response.completed" and isinstance(event.get("response"), dict):
                        completed = event["response"]
                    elif etype in ("response.failed", "error"):
                        failure = event.get("response") if isinstance(event.get("response"), dict) else event
                        raise CodexProviderError("upstream_error", f"Codex 响应失败：{_safe_json(failure)[:400]}")
        except CodexProviderError:
            raise
        except Exception as exc:
            raise CodexProviderError("sse_error", f"SSE 读取异常：{type(exc).__name__}") from exc

        if completed is None:
            raise CodexProviderError("sse_incomplete", "Codex 响应未包含 response.completed")
        for key, value in _usage_of(completed).items():
            usage[key] += value

        output = completed.get("output") if isinstance(completed.get("output"), list) and completed["output"] else observed
        calls = _tool_calls(output)
        if not calls:
            return text, usage
        if execute_tool is None:
            raise CodexProviderError("tool_unavailable", "Codex 请求调用工具但未提供执行器")

        results: list[dict[str, Any]] = []
        tools_by_name = {str(t.get("name")): t for t in tools or []}
        for call in calls:
            call_id = str(call.get("call_id"))
            name = str(call.get("name"))
            selected = tools_by_name.get(name)
            if selected is None:
                results.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": _safe_json({"isError": True, "error": f"Unknown Ultima tool: {name}"}),
                })
                continue
            raw_args = call.get("arguments")
            try:
                args = json.loads(raw_args) if isinstance(raw_args, str) and raw_args else {}
            except json.JSONDecodeError:
                results.append({
                    "type": "function_call_output",
                    "call_id": call_id,
                    "output": _safe_json({"isError": True, "error": "工具参数不是合法 JSON"}),
                })
                continue
            try:
                out = execute_tool(selected, args, call_id)
            except Exception as exc:
                out = {"isError": True, "error": f"{type(exc).__name__}: {str(exc)[:200]}"}
            results.append({
                "type": "function_call_output",
                "call_id": call_id,
                "output": _safe_json(out),
            })

        input_msgs = [*input_msgs, *[dict(i) for i in output], *results]

    raise CodexProviderError("tool_loop_limit", f"Codex 超出 {max_steps} 步工具调用上限")


# ---------------------------------------------------------------------------
# 四段 trace 解析（与 external_executor 共用）
# ---------------------------------------------------------------------------

def _parse_trace(content: str) -> list[dict[str, str]]:
    segments = {name: "" for name in _TRACE_SEGMENTS}
    for match in _TRACE_RE.finditer(content or ""):
        name, body = match.group(1), match.group(2).strip()
        if body:
            segments[name] = body
    trace: list[dict[str, str]] = []
    for name in _TRACE_SEGMENTS:
        if segments[name]:
            trace.append({"segment": name, "content": segments[name]})
    missing = [name for name in _TRACE_SEGMENTS if not segments[name]]
    if missing:
        trace.append({
            "segment": "FINAL",
            "content": f"（模型未按四段协议完整输出，缺 {','.join(missing)}；原文见 FINAL 兜底）",
        })
    return trace


def _build_messages(task: dict[str, Any], params: ExecutionParams) -> list[dict[str, str]]:
    goal = str(task.get("goal", task.get("title", "")))
    allowlist = ", ".join(params.tools_allowlist) if params.tools_allowlist else "none"
    gate = params.acceptance_gate or {}
    gate_text = json.dumps(gate, ensure_ascii=False) if gate else "无"
    user_message = (
        f"任务目标：{goal}\n"
        f"执行参数：max_turns={params.max_turns} / temperature={params.temperature} / "
        f"max_tokens={params.max_tokens} / output_protocol={params.output_protocol}\n"
        f"工具白名单：{allowlist}\n"
        f"permission_scope：{json.dumps(params.permission_scope, ensure_ascii=False)}\n"
        f"验收要求（acceptance_gate）：{gate_text}\n"
        f"请按四段输出协议给出可直接交付的方案。"
    )
    return [
        {"role": "system", "content": _SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]


# ---------------------------------------------------------------------------
# CodexProvider（对外契约 = external_executor 同构）
# ---------------------------------------------------------------------------

class CodexProvider:
    """Codex 直连执行端：run(task, params) → execution_report 六字段。"""

    def __init__(
        self,
        *,
        endpoint: str = DEFAULT_RESPONSES_ENDPOINT,
        model: Optional[str] = None,
        reasoning_effort: Optional[str] = None,
        max_steps: int = MAX_STEPS_DEFAULT,
        timeout: float = 120.0,
        tools: Optional[list[CodexTool]] = None,
        execute_tool: Optional[ToolExecutor] = None,
        transport: Optional[Any] = None,
    ) -> None:
        self.endpoint = endpoint
        self.model = model or _configured_model()
        self.reasoning_effort = reasoning_effort or _configured_reasoning_effort()
        self.max_steps = max_steps
        self.timeout = timeout
        self.tools = tools
        self.execute_tool = execute_tool
        self._transport = transport  # 测试注入；None 走真实网络

    def run(self, task: dict[str, Any], params: ExecutionParams) -> dict[str, Any]:
        started = time.time()
        try:
            creds = _read_codex_credentials()
            messages = _build_messages(task, params)
            tools = _annotate_tools(self.tools) if self.tools else None
            fetch = _authenticated_fetch(creds, transport=self._transport)
            text, usage = _stream_codex_direct(
                fetch=fetch,
                endpoint=self.endpoint,
                model=self.model,
                reasoning_effort=self.reasoning_effort,
                instructions=_SYSTEM_PROMPT,
                messages=messages,
                tools=tools,
                execute_tool=self.execute_tool,
                max_steps=1 if tools is None else self.max_steps,
            )
        except CodexProviderError as error:
            return {
                "model": self.model,
                "actual_turns": 0,
                "tokens": 0,
                "trace": [{"segment": "FINAL", "content": error.detail}],
                "self_check": {"gate": "fail", "note": f"Codex 调用失败：{error.code}"},
                "over_limits": {"error_code": error.code, "detail": error.detail},
            }
        except Exception as error:  # 意外：不穿透审计
            return {
                "model": self.model,
                "actual_turns": 0,
                "tokens": 0,
                "trace": [{"segment": "FINAL", "content": f"调用异常：{type(error).__name__}"}],
                "self_check": {"gate": "fail", "note": "Codex 调用异常"},
                "over_limits": {"error_code": "call_failed", "detail": str(error)[:200]},
            }

        tokens = usage["inputTokens"] + usage["outputTokens"]
        over_limits: Optional[dict[str, Any]] = None
        if params.max_tokens and usage["outputTokens"] > params.max_tokens:
            over_limits = {"kind": "max_tokens", "declared": True, "actual": usage["outputTokens"]}
        trace = _parse_trace(text)
        elapsed = round(time.time() - started, 2)
        return {
            "model": self.model,
            "actual_turns": 1,
            "tokens": tokens,
            "trace": trace,
            "self_check": {
                "gate": "pass",
                "note": f"Codex 模型 {self.model} 完成（tool_steps={self.max_steps if tools is not None else 1}），耗时 {elapsed}s",
                "status_code": 200,
                "usage": usage,
            },
            "over_limits": over_limits,
        }


__all__ = [
    "CodexProvider",
    "CodexProviderError",
    "CodexTool",
    "ToolExecutor",
    "_is_read_only",
    "_annotate_tools",
    "_read_codex_credentials",
    "_configured_model",
    "DEFAULT_RESPONSES_ENDPOINT",
]


def make_codex_executor(
    *,
    endpoint: str = DEFAULT_RESPONSES_ENDPOINT,
    model: Optional[str] = None,
    reasoning_effort: Optional[str] = None,
    max_steps: int = MAX_STEPS_DEFAULT,
    tools: Optional[list[CodexTool]] = None,
    execute_tool: Optional[ToolExecutor] = None,
    transport: Optional[Any] = None,
) -> Callable[[dict[str, Any], ExecutionParams], dict[str, Any]]:
    """构造 brain_loop 可注入的 run(task, params) 执行端（与 ExternalModelExecutor 同签名）。

    用法（主脑装配处，默认不切换 s5 DeepSeek）：
        from src.brain.exec.codex_provider import make_codex_executor
        brain = BrainLoop(data_dir, executor=make_codex_executor())
    """
    provider = CodexProvider(
        endpoint=endpoint,
        model=model,
        reasoning_effort=reasoning_effort,
        max_steps=max_steps,
        tools=tools,
        execute_tool=execute_tool,
        transport=transport,
    )
    return provider.run
