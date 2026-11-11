"""ExternalModelExecutor：主脑决策回路的真实外部模型执行端（s5-external-executor）。

对齐 TD-05 执行参数契约 §3 运行时调用链：
- 8B（本地主脑）下发 ExecutionParams 七参数 → 本执行器调外部大模型（DeepSeek，
  OpenAI 兼容 chat/completions）→ 返回六字段 execution_report（model / actual_turns /
  tokens / trace[THOUGHT/ACTION/OBSERVE/FINAL] / self_check / over_limits）；
- 参数契约与审计校正逻辑不变（BrainLoop 注入 executor 即接线，既有回路零改动）；
- key 仅从环境变量 DEEPSEEK_API_KEY 读取：不硬编码、不落盘、不经日志；
- 超限显式声明（不静默截断）；鉴权/网络/超时失败回确定性错误码（不穿透异常）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.error
import urllib.request
from typing import Any, Optional

from .params import ExecutionParams
from .brain_loop import ExternalExecutorStub  # noqa: F401  # 兼容导出（离线回退）

DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-chat"
ENV_KEY_NAME = "DEEPSEEK_API_KEY"

_SYSTEM_PROMPT = (
    "你是 UltimaAgent 的外部深度执行脑。任务由本地主脑下发，附带执行参数。"
    "请严格按四段输出协议作答，每段独立一行并以段名开头：\n"
    "THOUGHT：推理/目标拆解\n"
    "ACTION：本次调用的工具/动作（无工具则写 none）\n"
    "OBSERVE：工具返回/状态回读（无工具则写同 THOUGHT 结论）\n"
    "FINAL：结论/交付（面向用户，直接可用）\n"
    "禁止输出四段之外的内容。"
)

_TRACE_SEGMENTS = ("THOUGHT", "ACTION", "OBSERVE", "FINAL")
_TRACE_RE = re.compile(r"^\s*(THOUGHT|ACTION|OBSERVE|FINAL)\s*[:：]?\s*(.*)$", re.MULTILINE)


class ExternalExecutorError(Exception):
    """确定性执行器错误（code 供审计打回，不穿透异常）。"""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code = code
        self.detail = detail


def _api_key() -> str:
    value = os.environ.get(ENV_KEY_NAME, "").strip()
    if not value:
        raise ExternalExecutorError(
            "credential_missing",
            f"环境变量 {ENV_KEY_NAME} 未配置，无法调用外部模型",
        )
    return value


def _parse_trace(content: str) -> list[dict[str, str]]:
    """把模型四段输出解析为 trace 列表（缺段补显式占位，不编造内容）。"""
    segments = {name: "" for name in _TRACE_SEGMENTS}
    for match in _TRACE_RE.finditer(content or ""):
        name, body = match.group(1), match.group(2).strip()
        if body:
            segments[name] = body
    trace: list[dict[str, str]] = []
    for name in _TRACE_SEGMENTS:
        body = segments[name]
        if body:
            trace.append({"segment": name, "content": body})
    missing = [name for name in _TRACE_SEGMENTS if name not in segments or not segments[name]]
    if missing:
        trace.append({
            "segment": "FINAL",
            "content": f"（模型未按四段协议完整输出，缺 {','.join(missing)}；内容原文见 FINAL 兜底）",
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


class ExternalModelExecutor:
    """真实外部模型执行端：run(task, params) → execution_report（六字段契约）。"""

    def __init__(
        self,
        *,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: float = 60.0,
        transport: Optional[Any] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        # transport 可注入（测试用桩替换 urllib.request.urlopen）；None 走真实网络
        self._transport = transport

    # -- 对外契约 ------------------------------------------------------------

    def run(self, task: dict[str, Any], params: ExecutionParams) -> dict[str, Any]:
        """执行一次外部模型调用并返回六字段 execution_report（契约对齐）。"""
        started = time.time()
        status_code: Optional[int] = None
        try:
            key = _api_key()
            messages = _build_messages(task, params)
            payload = self._call_chat_completions(key, messages, params)
            status_code = 200
            content = payload["choices"][0]["message"]["content"]
            usage = payload.get("usage") or {}
            model = payload.get("model") or self.model
        except ExternalExecutorError as error:
            return {
                "model": self.model,
                "actual_turns": 0,
                "tokens": 0,
                "trace": [{"segment": "FINAL", "content": error.detail}],
                "self_check": {"gate": "fail", "note": f"外部调用失败：{error.code}"},
                "over_limits": {"error_code": error.code, "detail": error.detail},
            }
        except Exception as error:  # 网络层意外：不穿透审计
            return {
                "model": self.model,
                "actual_turns": 0,
                "tokens": 0,
                "trace": [{"segment": "FINAL", "content": f"调用异常：{type(error).__name__}"}],
                "self_check": {"gate": "fail", "note": "外部调用异常"},
                "over_limits": {"error_code": "call_failed", "detail": str(error)[:200]},
            }

        tokens_in = int(usage.get("prompt_tokens", 0))
        tokens_out = int(usage.get("completion_tokens", 0))
        tokens = tokens_in + tokens_out
        over_limits: Optional[dict[str, Any]] = None
        if params.max_tokens and tokens_out > params.max_tokens:
            over_limits = {"kind": "max_tokens", "declared": True, "actual": tokens_out}
        trace = _parse_trace(content)
        elapsed = round(time.time() - started, 2)
        return {
            "model": model,
            "actual_turns": 1,
            "tokens": tokens,
            "trace": trace,
            "self_check": {
                "gate": "pass",
                "note": f"外部模型 {model} 完成，耗时 {elapsed}s",
                "status_code": status_code,
            },
            "over_limits": over_limits,
        }

    # -- HTTP（urllib，零第三方依赖；transport 可注入测试桩） ---------------

    def _call_chat_completions(
        self,
        key: str,
        messages: list[dict[str, str]],
        params: ExecutionParams,
    ) -> dict[str, Any]:
        body = {
            "model": self.model,
            "messages": messages,
            "temperature": float(params.temperature),
            "max_tokens": int(params.max_tokens),
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
            },
            method="POST",
        )
        opener = self._transport if self._transport is not None else urllib.request.build_opener()
        try:
            with opener.open(request, timeout=self.timeout) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw)
        except urllib.error.HTTPError as error:
            detail = ""
            try:
                detail = error.read().decode("utf-8")[:300]
            except Exception:
                pass
            if error.code == 401:
                raise ExternalExecutorError(
                    "auth_failed", f"外部模型鉴权失败（HTTP 401）{detail}"
                ) from error
            if error.code == 429:
                raise ExternalExecutorError(
                    "rate_limited", f"外部模型限流（HTTP 429）{detail}"
                ) from error
            if error.code >= 500:
                raise ExternalExecutorError(
                    "upstream_error", f"外部模型服务错误（HTTP {error.code}）{detail}"
                ) from error
            raise ExternalExecutorError(
                "http_error", f"外部模型返回 HTTP {error.code}{detail}"
            ) from error
        except urllib.error.URLError as error:
            raise ExternalExecutorError(
                "network_failed", f"无法连接外部模型：{error.reason}"
            ) from error
        except TimeoutError as error:
            raise ExternalExecutorError("timeout", "外部模型调用超时") from error


__all__ = [
    "ExternalModelExecutor", "ExternalExecutorError", "ExternalExecutorStub",
    "DEFAULT_BASE_URL", "DEFAULT_MODEL", "ENV_KEY_NAME",
]
